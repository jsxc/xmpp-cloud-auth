import logging
import traceback
import unicodedata
import sys
from xclib.ejabberdctl import ejabberdctl

def sanitize(name):
    name = unicode(name)
    printable = set(('Lu', 'Ll', 'Lm', 'Lo', 'Nd', 'Nl', 'No', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'Zs'))
    return str(''.join(c for c in name if unicodedata.category(c) in printable and c != '@'))

class roster_thread:
    def roster_background_thread(self, sr):
        '''Entry for background roster update thread'''
        try:
            logging.debug('roster_thread for ' + str(sr))
            # Allow test hooks with static ejabberd_controller
            if self.ctx.ejabberd_controller is None:
                e = ejabberdctl(self.ctx)
            else:
                e = self.ctx.ejabberd_controller
            groups, commands = self.roster_update_users(e, sr)
            self.roster_update_groups(e, groups)
            # For some reason, the vcard changes are not pushed to the clients. Rinse and repeat.
            for cmd in commands:
                e.execute(cmd)
        except Exception, err:
            (etype, value, tb) = sys.exc_info()
            traceback.print_exception(etype, value, tb)
            logging.warn('roster_groups thread: %s:\n%s'
                         % (str(err), ''.join(traceback.format_tb(tb))))
            return False
        
    def roster_update_users(self, e, sr):
        '''Update users' full names and invert hash

For all *users* we have information about:
- collect the shared roster groups they belong to
- set their full names if not yet defined
Return inverted hash'''
        groups = {}
        commands = []
        for user, desc in sr.iteritems():
            if 'groups' in desc:
                for g in desc['groups']:
                    if g in groups:
                        groups[g].append(user)
                    else:
                        groups[g] = [user]
            if 'name' in desc:
                lhs, rhs = self.jidsplit(user)
                if ('FNC:' + user) in self.ctx.shared_roster_db:
                    cached_name = self.ctx.shared_roster_db['FNC:' + user]
                else:
                    cached_name = None
                logging.debug('u='+user)
                self.ctx.shared_roster_db['FNC:' + user] = desc['name']
                cmd = e.maybe_set_fn(lhs, rhs, desc['name'], cached_name=cached_name)
                if cmd is not None:
                    commands.append(cmd)
        return groups, commands

    def roster_update_groups(self, e, groups):
        '''Update shared roster groups with ejabberdctl

For all the *groups* we have information about:
- create the group (idempotent)
- delete the users that we do not know about anymore
- add the users we know about (idempotent)'''
        cleanname = {}
        for g in groups:
            cleanname[g] = sanitize(g)
            key = 'RGC:%s:%s' % (cleanname[g], self.domain)
            if key in self.ctx.shared_roster_db:
                previous_users = self.ctx.shared_roster_db[key].split('\t')
            else:
                e.execute(['srg_create', cleanname[g], self.domain, cleanname[g], cleanname[g], cleanname[g]])
                # Fill cache (again)
                previous_users = e.members(cleanname[g], self.domain)
            new_users = {}
            for u in groups[g]:
                (lhs, rhs) = self.jidsplit(u)
                fulljid = '%s@%s' % (lhs, rhs)
                new_users[fulljid] = True
                if not fulljid in previous_users:
                    e.execute(['srg_user_add', lhs, rhs, cleanname[g], self.domain])
            for p in previous_users:
                (lhs, rhs) = self.jidsplit(p)
                if p not in new_users:
                    e.execute(['srg_user_del', lhs, rhs, cleanname[g], self.domain])
            members = new_users.keys()
            members.sort()
            self.ctx.shared_roster_db[key] = '\t'.join(members)

        # For all the groups the login user was previously a member of:
        # - delete her from the shared roster group if no longer a member
        key = 'LIG:%s@%s' % (self.username, self.domain)
        if key in self.ctx.shared_roster_db and self.ctx.shared_roster_db[key] != '':
            # Was previously there as well, need to be removed from one?
            previous = self.ctx.shared_roster_db[key].split('\t')
            for p in previous:
                if p not in cleanname.values():
                    e.execute(['srg_user_del', self.username, self.domain, p, self.domain])
            # Only update when necessary
            new = '\t'.join(sorted(cleanname.values()))
            if previous != new:
                self.ctx.shared_roster_db[key] = new
        else: # New, always set
            self.ctx.shared_roster_db[key] = '\t'.join(sorted(cleanname.values()))
