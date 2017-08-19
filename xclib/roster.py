import hashlib
import traceback
import unicodedata
import threading
from xclib.ejabberdctl import ejabberdctl

def sanitize(name):
    printable = set(('Lu', 'Ll', 'Lm', 'Lo', 'Nd', 'Nl', 'No', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'Zs'))
    return ''.join(c for c in name if unicodedata.category(c) in printable and c != '@')

class roster:
    def jidsplit(self, jid, defaultDomain):
        (node, at, dom) = jid.partition('@')
        if at == '':
            return (node, defaultDomain)
        else:
            return (node, dom)

    def roster_groups(self, sr):
        # For all users we have information about:
        # - collect the shared roster groups they belong to
        # - set their full names if not yet defined
        e = ejabberdctl(self.ctx)
        groups = {}
        for u in sr:
            if 'groups' in sr[u]:
                for g in sr[u]['groups']:
                    if g in groups:
                            groups[g] += (u,)
                    else:
                            groups[g] = (u,)
            if 'name' in sr[u]:
                e.set_fn(u, domain, sr[u]['name'])
        # For all the groups we have information about:
        # - create the group (idempotent)
        # - delete the users that we do not know about anymore
        # - add the users we know about
        hashname = {}
        for g in groups:
            hashname[g] = sanitize(g)
            e.execute(['srg_create', hashname[g], domain, hashname[g], hashname[g], hashname[g]])
            previous_users = e.members(hashname[g], domain)
            new_users = {}
            for u in groups[g]:
                (lhs, rhs) = self.jidsplit(u, domain)
                fulljid = '%s@%s' % (lhs, rhs)
                new_users[fulljid] = True
                if not fulljid in previous_users:
                    e.execute(['srg_user_add', lhs, rhs, hashname[g], domain])
            for p in previous_users:
                (lhs, rhs) = self.jidsplit(p, self.domain) # Should always have a domain...
                if p not in new_users:
                    e.execute(['srg_user_del', lhs, rhs, hashname[g], domain])
        # For all the groups the login user was previously a member of:
        # - delete her from the shared roster group if no longer a member
        key = '%s:%s' % (user, domain)
        if key in shared_roster_db:
            # Was previously there as well, need to be removed from one?
            previous = self.ctx.shared_roster_db[key].split('\t')
            for p in previous:
                if p not in hashname.values():
                    e.execute(['srg_user_del', user, domain, p, domain])
            # Only update when necessary
            new = '\t'.join(sorted(hashname.values()))
            if previous != new:
                self.ctx.shared_roster_db[key] = new
        else: # New, always set
            self.ctx.shared_roster_db[key] = '\t'.join(sorted(hashname.values()))
        return groups

    def roster_cloud(self):
        success, code, message, text = self.verbose_cloud_request({
            'operation': 'sharedroster',
            'username':  self.username,
            'domain':    self.authDomain
        })
        if success:
            if code is not None and code != requests.codes.ok:
                return code, None
            else:
                sr = None
                try:
                    sr = message['data']['sharedRoster']
                    return sr, text
                except Exception, e:
                    logging.warn('Weird response: ' + str(e))
                    return message, text
        else:
            return False, None

    def try_roster(self):
        if (self.ctx.ejabberdctl_path is not None):
            try:
                response, text = self.roster_cloud()
                if response is not None and response != False:
                    texthash = hashlib.sha256(text).hexdigest()
                    userhash = 'CACHE:' + username + ':' + domain
                    # Response changed or first response for that user?
                    if not userhash in ctx.shared_roster_db or ctx.shared_roster_db[userhash] != texthash:
                        ctx.shared_roster_db[userhash] = texthash
                        threading.Thread(target=self.roster_groups,
                            args=(secret, domain, username, response)).start()
            except Exception, err:
                (etype, value, tb) = sys.exc_info()
                traceback.print_exception(etype, value, tb)
                logging.warn('try_roster: ' + str(err) + traceback.format_tb(tb))
