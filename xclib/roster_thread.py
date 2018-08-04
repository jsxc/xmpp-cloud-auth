import logging
import traceback
import unicodedata
import sys
from xclib.ejabberdctl import ejabberdctl
from xclib.utf8 import utf8, unutf8, utf8l

def sanitize(name):
    name = str(name)
    printable = {'Lu', 'Ll', 'Lm', 'Lo', 'Nd', 'Nl', 'No', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'Zs'}
    return ''.join(c for c in name if unicodedata.category(c) in printable and c != '@')

class roster_thread:
    def roster_background_thread(self, sr):
        '''Entry for background roster update thread'''
        try:
            logging.debug('roster_thread for ' + str(sr))
            # Allow test hooks with static ejabberd_controller
            if hasattr(self.ctx, 'ejabberd_controller') and self.ctx.ejabberd_controller is not None:
                e = self.ctx.ejabberd_controller
            else:
                e = ejabberdctl(self.ctx)
            groups, commands = self.roster_update_users(e, sr)
            self.roster_update_groups(e, groups)
            # For some reason, the vcard changes are (were?)
            # not pushed to the clients. Rinse and repeat.
# Maybe no longer necessary with (mostly) synchronous thread?
#            for cmd in commands:
#                e.execute(cmd)
#        except AttributeError:
#            pass # For tests
        except Exception as err:
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
        for user, desc in sr.items():
            if 'groups' in desc:
                for g in desc['groups']:
                    if g in groups:
                        groups[g].append(user)
                    else:
                        groups[g] = [user]
            if 'name' in desc:
                lhs, rhs = self.jidsplit(user)
                jid = '@'.join((lhs, rhs))
                cached_name = None
                for row in self.ctx.db.conn.execute(
                        'SELECT fullname FROM rosterinfo WHERE jid=?',
                        (jid,)):
                    cached_name = row['fullname']
                if cached_name != desc['name']:
                    self.ctx.db.conn.begin()
                    self.ctx.db.conn.execute(
                            '''INSERT OR IGNORE INTO rosterinfo (jid)
                            VALUES (?)''', (jid,))
                    self.ctx.db.conn.execute(
                            '''UPDATE rosterinfo
                            SET fullname = ?
                            WHERE jid = ?''', (desc['name'], jid))
                    self.ctx.db.conn.commit()
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
            key = '@'.join((cleanname[g], self.domain))
            previous_users = ()
            for row in self.ctx.db.conn.execute(
                    '''SELECT userlist FROM rostergroups
                    WHERE groupname=?''', (key,)):
                previous_users = row['userlist'].split('\t')
            if previous_users == ():
                e.execute(['srg_create', cleanname[g], self.domain, cleanname[g], cleanname[g], cleanname[g]])
                # Fill cache (again)
                previous_users = e.members(cleanname[g], self.domain)
            current_users = {}
            for u in groups[g]:
                (lhs, rhs) = self.jidsplit(u)
                fulljid = '%s@%s' % (lhs, rhs)
                current_users[fulljid] = True
                if not fulljid in previous_users:
                    e.execute(['srg_user_add', lhs, rhs, cleanname[g], self.domain])
            for p in previous_users:
                (lhs, rhs) = self.jidsplit(p)
                if p not in current_users:
                    e.execute(['srg_user_del', lhs, rhs, cleanname[g], self.domain])
            # Here, we could use INSERT OR REPLACE, because we fill
            # all the fields. But only until someone would add
            # extra fields, which then would be reset to default values.
            # Better safe than sorry.
            self.ctx.db.conn.begin()
            self.ctx.db.conn.execute(
                    '''INSERT OR IGNORE INTO rostergroups (groupname)
                    VALUES (?)''', (key,))
            self.ctx.db.conn.execute(
                    '''UPDATE rostergroups
                    SET userlist = ?
                    WHERE groupname = ?''', ('\t'.join(sorted(current_users.keys())), key))
            self.ctx.db.conn.commit()

        # For all the groups the login user was previously a member of:
        # - delete her from the shared roster group if no longer a member
        key = '@'.join((self.username, self.domain))
        previous = ()
        for row in self.ctx.db.conn.execute(
                '''SELECT grouplist FROM rosterinfo WHERE jid=?''', (key,)):
            if row['grouplist']: # Not None or ''
                previous = row['grouplist'].split('\t')
        for p in previous:
            if p not in list(cleanname.values()):
                e.execute(['srg_user_del', self.username, self.domain, p, self.domain])
        # Only update when necessary
        new = '\t'.join(sorted(cleanname.values()))
        if previous != new:
            self.ctx.db.conn.begin()
            self.ctx.db.conn.execute(
                    '''INSERT OR IGNORE INTO rosterinfo (jid)
                    VALUES (?)''', (key,))
            self.ctx.db.conn.execute(
                    '''UPDATE rosterinfo
                    SET grouplist = ?
                    WHERE jid = ?''', (new, key))
            self.ctx.db.conn.commit()
