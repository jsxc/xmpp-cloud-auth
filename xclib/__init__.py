import logging
import urllib
import requests
import hmac
import hashlib
import sys
import subprocess
import traceback
import unicodedata
import threading
from time import time
from base64 import b64decode
from string import maketrans

usersafe_encoding = maketrans('-$%', 'OIl')

def verify_with_isuser(url, secret, domain, user, timeout):
    xc = xcauth(default_url=url, default_secret=secret, timeout=timeout)
    success, code, response, text = xc.verbose_cloud_request({
        'operation': 'isuser',
        'username':  user,
        'domain':    domain
    }, secret, url);
    return success, code, response

class xcauth:
    def __init__(self, default_url=None, default_secret=None,
                ejabberdctl=None, shared_roster_db=None,
                domain_db=None, cache_db=None,
                ttls={'query': 3600, 'verify': 86400, 'unreach': 7*86400},
                bcrypt_rounds=12, timeout=5):
        self.default_url=default_url
        self.default_secret=default_secret
        self.ejabberdctl_path=ejabberdctl
        self.domain_db=domain_db
        self.cache_db=cache_db
        self.ttls=ttls
        self.timeout=timeout
        self.bcrypt_rounds=bcrypt_rounds
        self.session=requests.Session()

    def per_domain(self, dom):
        if dom in self.domain_db:
            try:
                # Already 4-value database format? Great!
                secret, url, queryDomain, extra = self.domain_db[dom].split('\t', 3)
            except ValueError:
                # No, fall back to 3-value format (and update DB)
                secret, url, extra = self.domain_db[dom].split('\t', 2)
                queryDomain = dom
                self.domain_db[dom] = '\t'.join((secret, url, queryDomain, extra))
            return secret, url, queryDomain
        else:
            return self.default_secret, self.default_url, dom

    def verbose_cloud_request(self, data, secret, url):
    #   logging.debug("Sending %s to %s" % (data, url))
        payload = urllib.urlencode(data)
        signature = hmac.new(secret, msg=payload, digestmod=hashlib.sha1).hexdigest();
        headers = {
            'X-JSXC-SIGNATURE': 'sha1=' + signature,
            'content-type':     'application/x-www-form-urlencoded'
        }
        try:
            r = self.session.post(url, data=payload, headers=headers,
                                  allow_redirects=False, timeout=self.timeout)
        except requests.exceptions.HTTPError as err:
            logging.warn(err)
            return False, None, err, None
        except requests.exceptions.RequestException as err:
            try:
                logging.warn('An error occured during the request to %s for domain %s: %s' % (url, data['domain'], err))
            except TypeError as err:
                logging.warn('An unknown error occured during the request to %s, probably an SSL error. Try updating your "requests" and "urllib" libraries.' % url)
            return False, None, err, None
        if r.status_code != requests.codes.ok:
            try:
                return False, r.status_code, r.json(), r.text
            except ValueError: # Not a valid JSON response
                return False, r.status_code, None, None
        try:
            # Return True only for HTTP 200 with JSON body, False for everything else
            return True, None, r.json(), r.text
        except ValueError: # Not a valid JSON response
            return False, r.status_code, None, None

    def cloud_request(self, data, secret, url):
        success, code, message, text = self.verbose_cloud_request(data, secret, url)
        if success:
            if code is not None and code != requests.codes.ok:
                return code
            else:
                return message
        else:
            return False

    # First try if it is a valid token
    # Failure may just indicate that we were passed a password
    def auth_token(self, username, domain, password, secret):
        try:
            token = b64decode(password.translate(usersafe_encoding) + '=======')
        except:
            logging.debug('Could not decode token (maybe not a token?)')
            return False

        jid = username + '@' + domain

        if len(token) != 23:
            logging.debug('Token is too short: %d != 23 (maybe not a token?)' % len(token))
            return False

        (version, mac, header) = unpack('> B 16s 6s', token)
        if version != 0:
            logging.debug('Wrong token version (maybe not a token?)')
            return False;

        (secretID, expiry) = unpack('> H I', header)
        if expiry < time():
            logging.debug('Token has expired')
            return False

        challenge = pack('> B 6s %ds' % len(jid), version, header, jid)
        response = hmac.new(secret, challenge, hashlib.sha256).digest()

        return hmac.compare_digest(mac, response[:16])

    def auth_cloud(self, username, domain, password, secret, url):
        response = self.cloud_request({
            'operation':'auth',
            'username': username,
            'domain':   domain,
            'password': password
        }, secret, url);
        if response:
            return response['result'] # 'error', 'success', 'noauth'
        return False

    def checkpw(self, pw, pwhash):
        if 'checkpw' in dir(bcrypt):
            return bcrypt.checkpw(pw, pwhash)
        else:
            ret = bcrypt.hashpw(pw, pwhash)
            return ret == pwhash

    def auth_cache(self, username, domain, password, unreach):
        key = username + ':' + domain
        if key in self.cache_db:
            now = int(time())
            (pwhash, ts1, tsv, tsa, rest) = self.cache_db[key].split("\t", 4)
            if ((int(tsa) + self.ttls['query'] > now and int(tsv) + self.ttls['verify'] > now)
               or (unreach and int(tsv) + self.ttls['unreach'] > now)):
                if self.checkpw(password, pwhash):
                    self.cache_db[key] = "\t".join((pwhash, ts1, tsv, str(now), rest))
                    return True
        return False

    def auth_update_cache(self, username, domain, password):
        if '' in self.cache_db: # Cache disabled?
            return
        key = username + ':' + domain
        now = int(time())
        snow = str(now)
        try:
            salt = bcrypt.gensalt(rounds=self.bcrypt_rounds)
        except TypeError:
            # Old versions of bcrypt() do not support the rounds option
            salt = bcrypt.gensalt()
        pwhash = bcrypt.hashpw(password, salt)
        if key in self.cache_db:
            (ignored, ts1, tsv, tsa, rest) = self.cache_db[key].split("\t", 4)
            self.cache_db[key] = "\t".join((pwhash, ts1, snow, snow, rest))
        else:
            self.cache_db[key] = "\t".join((pwhash, snow, snow, snow, ''))

    def auth(self, username, domain, password):
        secret, url, queryDomain = self.per_domain(domain)
        if self.auth_token(username, domain, password, secret):
            logging.info('SUCCESS: Token for %s@%s is valid' % (username, domain))
            self.try_roster(username, domain)
            return True
        if self.auth_cache(username, domain, password, False):
            logging.info('SUCCESS: Cache says password for %s@%s is valid' % (username, domain))
            self.try_roster(username, domain)
            return True
        r = self.auth_cloud(username, queryDomain, password, secret, url)
        if not r or r == 'error': # Request did not get through (connect, HTTP, signature check)
            cache = self.auth_cache(username, domain, password, True)
            logging.info('UNREACHABLE: Cache says password for %s@%s is %r' % (username, domain, cache))
            # The roster request would be futile
            return cache
        elif r == 'success':
            logging.info('SUCCESS: Cloud says password for %s@%s is valid' % (username, domain))
            self.auth_update_cache(username, domain, password)
            self.try_roster(username, domain)
            return True
        else: # 'noauth'
            logging.info('FAILURE: Could not authenticate user %s@%s: %s' % (username, domain, r))
            return False

    def isuser_cloud(self, username, domain, secret, url):
        response = self.cloud_request({
            'operation':'isuser',
            'username':  username,
            'domain':    domain
        }, secret, url);
        return response and response['result'] == 'success' and response['data']['isUser']

    def isuser(self, username, domain):
        secret, url, domain = self.per_domain(domain)
        if self.isuser_cloud(username, domain, secret, url):
            logging.info('Cloud says user %s@%s exists' % (username, domain))
            return True
        return False

    def ejabberdctl(self, args):
        logging.debug(self.ejabberdctl_path + str(args))
        try:
            return subprocess.check_output([self.ejabberdctl_path] + args)
        except subprocess.CalledProcessError, err:
            logging.warn('ejabberdctl %s failed with %s'
                % (self.ejabberdctl_path + str(args), str(err)))
            return None

    def ejabberdctl_set_fn(self, user, domain, name):
        fullname = self.ejabberdctl(['get_vcard', user, domain, 'FN'])
        # error_no_vcard is exitcode 1 is None
        if fullname is None or fullname == '' or fullname == '\n':
            self.ejabberdctl(['set_vcard', user, domain, 'FN', name])

    def ejabberdctl_members(self, group, domain):
        membership = self.ejabberdctl(['srg_get_members', group, domain]).split('\n')
        # Delete empty values (e.g. from empty output)
        mem = []
        for m in membership:
            if m != '':
                mem = mem + [m]
        return mem

    def jidsplit(self, jid, defaultDomain):
        (node, at, dom) = jid.partition('@')
        if at == '':
            return (node, defaultDomain)
        else:
            return (node, dom)

    # Ensure this is unique, has no problems with weird characters,
    # and does not conflict with other instances (identified by the secret)
    def hashname(self, secret, name):
        return hashlib.sha256(secret + '\t' + name).hexdigest()

    def sanitize(self, name):
        printable = set(('Lu', 'Ll', 'Lm', 'Lo', 'Nd', 'Nl', 'No', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 'Sm', 'Sc', 'Sk', 'So', 'Zs'))
        return ''.join(c for c in name if unicodedata.category(c) in printable and c != '@')

    def roster_groups(self, secret, domain, user, sr):
        # For all users we have information about:
        # - collect the shared roster groups they belong to
        # - set their full names if not yet defined
        groups = {}
        for u in sr:
            if 'groups' in sr[u]:
                for g in sr[u]['groups']:
                    if g in groups:
                            groups[g] += (u,)
                    else:
                            groups[g] = (u,)
            if 'name' in sr[u]:
                self.ejabberdctl_set_fn(u, domain, sr[u]['name'])
        # For all the groups we have information about:
        # - create the group (idempotent)
        # - delete the users that we do not know about anymore
        # - add the users we know about
        hashname = {}
        for g in groups:
            hashname[g] = self.sanitize(g)
            self.ejabberdctl(['srg_create', hashname[g], domain, hashname[g], hashname[g], hashname[g]])
            previous_users = self.ejabberdctl_members(hashname[g], domain)
            new_users = {}
            for u in groups[g]:
                (lhs, rhs) = self.jidsplit(u, domain)
                fulljid = '%s@%s' % (lhs, rhs)
                new_users[fulljid] = True
                if not fulljid in previous_users:
                    self.ejabberdctl(['srg_user_add', lhs, rhs, hashname[g], domain])
            for p in previous_users:
                (lhs, rhs) = self.jidsplit(p, domain) # Should always have a domain...
                if p not in new_users:
                    self.ejabberdctl(['srg_user_del', lhs, rhs, hashname[g], domain])
        # For all the groups the login user was previously a member of:
        # - delete her from the shared roster group if no longer a member
        key = '%s:%s' % (user, domain)
        if key in shared_roster_db:
            # Was previously there as well, need to be removed from one?
            previous = shared_roster_db[key].split('\t')
            for p in previous:
                if p not in hashname.values():
                    self.ejabberdctl(['srg_user_del', user, domain, p, domain])
            # Only update when necessary
            new = '\t'.join(sorted(hashname.values()))
            if previous != new:
                shared_roster_db[key] = new
        else: # New, always set
            shared_roster_db[key] = '\t'.join(sorted(hashname.values()))
        return groups

    def roster_cloud(self, username, domain):
        secret, url, domain = self.per_domain(domain)
        success, code, message, text = self.verbose_cloud_request({
            'operation':'sharedroster',
            'username':  username,
            'domain':    domain
        }, secret, url)
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

    def try_roster(self, username, domain):
        if (self.ejabberdctl_path is not None):
            try:
                secret, url, domain = self.per_domain(domain)
                response, text = self.roster_cloud(username, domain)
                if response is not None and response != False:
                    texthash = hashlib.sha256(text).hexdigest()
                    userhash = 'CACHE:' + username + ':' + domain
                    # Response changed or first response for that user?
                    if not userhash in shared_roster_db or shared_roster_db[userhash] != texthash:
                        shared_roster_db[userhash] = texthash
                        threading.Thread(target=self.roster_groups,
                            args=(secret, domain, username, response)).start()
            except Exception, err:
                (etype, value, tb) = sys.exc_info()
                traceback.print_exception(etype, value, tb)
                logging.warn('try_roster: ' + str(err) + traceback.format_tb(tb))

