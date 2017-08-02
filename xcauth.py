#!/usr/bin/python -tt

import logging
import configargparse
import urllib
import requests
import hmac
import hashlib
import sys
import atexit
import anydbm
import subprocess
import traceback
from struct import *
from time import time
from base64 import b64decode
from string import maketrans

DEFAULT_LOG_DIR = '/var/log/xcauth'
VERSION = '0.9.0+'

usersafe_encoding = maketrans('-$%', 'OIl')


### Handling requests from/responses to XMPP server

class prosody_io:
    @classmethod
    def read_request(cls):
        # "for line in sys.stdin:" would be more concise but adds unwanted buffering
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.rstrip("\r\n")
            yield line.split(':', 3)

    @classmethod
    def write_response(cls, bool):
        answer = '0'
        if bool:
            answer = '1'
        sys.stdout.write(answer+"\n")
        sys.stdout.flush()

class ejabberd_io:
    @classmethod
    def read_request(cls):
        length_field = sys.stdin.read(2)
        while len(length_field) == 2:
            (size,) = unpack('>H', length_field)
            if size == 0:
               logging.info("command length 0, treating as logical EOF")
               return
            cmd = sys.stdin.read(size)
            if len(cmd) != size:
               logging.warn("premature EOF while reading cmd: %d != %d" % (len(cmd), size))
               return
            x = cmd.split(':', 3)
            yield x
            length_field = sys.stdin.read(2)

    @classmethod
    def write_response(cls, bool):
        answer = 0
        if bool:
            answer = 1
        token = pack('>HH', 2, answer)
        sys.stdout.write(token)
        sys.stdout.flush()

class saslauthd_io:
    @classmethod
    def read_request(cls):
        field_no = 0
        fields = [None, None, None, None]
        length_field = sys.stdin.read(2)
        while len(length_field) == 2:
            (size,) = unpack('>H', length_field)
            val = sys.stdin.read(size)
            if len(val) != size:
               logging.warn("premature EOF while reading field %d: %d != %d" % (field_no, len(cmd), size))
               return
            fields[field_no] = val
            field_no = (field_no + 1) % 4
            if field_no == 0:
                logging.debug("from_saslauthd got %s, %s, %s, %s" % tuple(fields))
                yield ('auth', fields[0], fields[3], fields[1])
            length_field = sys.stdin.read(2)

    @classmethod
    def write_response(cls, bool):
        answer = 'NO xcauth authentication failure'
        if bool:
            answer = 'OK success'
        token = pack('>H', len(answer)) + answer
        sys.stdout.write(token)
        sys.stdout.flush()


### Handling requests to/responses from the cloud server
class xcauth:
    def __init__(self, default_url=None, default_secret=None,
                ejabberdctl=None,
                shared_roster_db=None, shared_roster_domain=None,
                domain_db=None, cache_db=None,
                ttls={'query': 3600, 'verify': 86400, 'unreach': 7*86400},
                bcrypt_rounds=12, timeout=5):
        self.default_url=default_url
        self.default_secret=default_secret
        self.shared_roster_domain=shared_roster_domain
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
            token = b64decode(password.translate(usersafe_encoding) + "=======")
        except:
            logging.debug('Could not decode token (maybe not a token?)')
            return False

        jid = username + '@' + domain

        if len(token) != 23:
            logging.debug('Token is too short: %d != 23 (maybe not a token?)' % len(token))
            return False

        (version, mac, header) = unpack("> B 16s 6s", token)
        if version != 0:
            logging.debug('Wrong token version (maybe not a token?)')
            return False;

        (secretID, expiry) = unpack("> H I", header)
        if expiry < time():
            logging.debug('Token has expired')
            return False

        challenge = pack("> B 6s %ds" % len(jid), version, header, jid)
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
        key = username + ":" + domain
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
        key = username + ":" + domain
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
            logging.warn("ejabberdctl %s failed with %s"
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

    def roster_domain(self, domain):
        if self.shared_roster_domain is None:
            return domain
        else:
            return self.shared_roster_domain

    # Ensure this is unique, has no problems with weird characters,
    # and does not conflict with other instances (identified by the secret)
    def hashname(self, secret, name):
        return hashlib.sha256(secret + '\t' + name).hexdigest()

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
        hashdomain = domain if self.shared_roster_domain is None else self.shared_roster_domain
        for g in groups:
            hashname[g] = self.hashname(secret, g)
            self.ejabberdctl(['srg_create', hashname[g], hashdomain, g, g, hashname[g]])
            previous_users = self.ejabberdctl_members(hashname[g], hashdomain)
            new_users = {}
            for u in groups[g]:
                (lhs, rhs) = self.jidsplit(u, domain)
                new_users['%s@%s' % (lhs, rhs)] = True
                self.ejabberdctl(['srg_user_add', lhs, rhs, hashname[g], hashdomain])
            for p in previous_users:
                (lhs, rhs) = self.jidsplit(p, domain) # Should always have a domain...
                if p not in new_users:
                    self.ejabberdctl(['srg_user_del', lhs, rhs, hashname[g], hashdomain])
        # For all the groups the login user was previously a member of:
        # - delete her from the shared roster group if no longer a member
        key = '%s:%s' % (user, domain)
        if key in shared_roster_db:
            # Was previously there as well, need to be removed from one?
            previous = shared_roster_db[key].split('\t')
            for p in previous:
                if p not in hashname.values():
                    self.ejabberdctl(['srg_user_del', user, domain, p, hashdomain])
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
                    logging.warn("Weird response: " + str(e))
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
                    userhash = self.hashname(secret, username)
                    # Response changed or first response for that user?
                    if not userhash in shared_roster_db or shared_roster_db[userhash] != texthash:
                        shared_roster_db[userhash] = texthash
                        self.roster_groups(secret, domain, username, response)
            except Exception, err:
                (etype, value, tb) = sys.exc_info()
                traceback.print_exception(etype, value, tb)
                logging.warn('try_roster: ' + str(err) + traceback.format_tb(tb))

def verify_with_isuser(url, secret, domain, user, timeout):
    xc = xcauth(default_url=url, default_secret=secret, timeout=timeout)
    success, code, response = xc.verbose_cloud_request({
        'operation': 'isuser',
        'username':  user,
        'domain':    domain
    }, secret, url);
    return success, code, response

### Configuration-related functions

def parse_timespan(span):
    multipliers = {'s': 1, 'm': 60, 'h': 60*60, 'd': 60*60*24, 'w': 60*60*24*7}
    if span[-1] in multipliers:
        return int(span[:-1]) * multipliers[span[-1]]
    else:
        return int(span)

def get_args():
    # build command line argument parser
    desc = '''XMPP server authentication against JSXC>=3.2.0 on Nextcloud.
        See https://jsxc.org or https://github.com/jsxc/xmpp-cloud-auth.'''
    epilog = '''-I, -R, and -A take precedence over -t. One of them is required.
        -I, -R, and -A imply -i and -d.'''

    # Config file in /etc or the program directory
    cfpath = sys.argv[0][:-3] + ".conf"
    parser = configargparse.ArgumentParser(description=desc,
        epilog=epilog,
        default_config_files=['/etc/xcauth.conf', '/etc/external_cloud.conf'])

    parser.add_argument('--config-file', '-c',
        is_config_file=True,
        help='config file path')
    parser.add_argument('--url', '-u',
        required=True,
        help='base URL')
    parser.add_argument('--secret', '-s',
        required=True,
        help='secure api token')
    parser.add_argument('--log', '-l',
        default=DEFAULT_LOG_DIR,
        help='log directory (default: %(default)s)')
    parser.add_argument('--domain-db', '-b',
        help='persistent domain database; manipulated with xcdbm.py')
    parser.add_argument('--debug', '-d',
        action='store_true',
        help='enable debug mode')
    parser.add_argument('--interactive', '-i',
        action='store_true',
        help='log to stdout')
    parser.add_argument('--type', '-t',
        choices=['generic', 'prosody', 'ejabberd', 'saslauthd'],
        default='generic',
        help='XMPP server type (prosody=generic); implies reading requests from stdin')
    parser.add_argument('--timeout',
        type=int, default=5,
        help='Timeout for each of connection setup and request processing')
    parser.add_argument('--cache-db',
        help='Database path for the user cache; enables cache if set')
    parser.add_argument('--cache-query-ttl',
        default='1h',
        help='Maximum time between queries')
    parser.add_argument('--cache-verification-ttl',
        default='1d',
        help='Maximum time between backend verifications')
    parser.add_argument('--cache-unreachable-ttl',
        default='1w',
        help='Maximum cache time when backend is unreachable (overrides the other TTLs)')
    parser.add_argument('--cache-bcrypt-rounds',
        type=int, default=12,
        help='''Encrypt passwords with 2^ROUNDS before storing
            (i.e., every increasing ROUNDS takes twice as much
            computation time)''')
    parser.add_argument('--ejabberdctl',
        metavar="PATH",
        help='Enables shared roster updates on authentication; use ejabberdctl command at PATH to modify them')
    parser.add_argument('--shared-roster-domain',
        help='Put all shared rosters to DOMAIN instead of the authentication user\'s domain (necessary for virtual domain configurations)')
    parser.add_argument('--shared-roster-db',
        help='Which groups a user has been added to (to ensure proper deletion)')
    parser.add_argument('--auth-test', '-A',
        nargs=3, metavar=("USER", "DOMAIN", "PASSWORD"),
        help='single, one-shot query of the user, domain, and password triple')
    parser.add_argument('--isuser-test', '-I',
        nargs=2, metavar=("USER", "DOMAIN"),
        help='single, one-shot query of the user and domain tuple')
    parser.add_argument('--roster-test', '-R',
        nargs=2, metavar=("USER", "DOMAIN"),
        help='single, one-shot query of the user\'s shared roster')
    parser.add_argument('--version',
        action='version', version=VERSION)

    args = parser.parse_args()
    args.cache_query_ttl        = parse_timespan(args.cache_query_ttl)
    args.cache_verification_ttl = parse_timespan(args.cache_verification_ttl)
    args.cache_unreachable_ttl  = parse_timespan(args.cache_unreachable_ttl)
    # There is no logical XOR in Python
    if ('ejabberdctl' in args)*1 + ('shared_roster_db' in args)*1 == 1:
        sys.stderr.write('Define either both --ejabberdctl and --shared-roster-db, or neither\n')
        sys.exit(1)
    if (args.auth_test is None and args.isuser_test is None and args.roster_test is None):
        if args.type is None: # No work to do
            parser.print_help(sys.stderr)
            sys.exit(1)
    return args



if __name__ == '__main__':
    args = get_args()

    logfile = args.log + '/xcauth.log'
    if (args.interactive or args.auth_test or args.isuser_test or args.roster_test):
        logging.basicConfig(stream=sys.stderr,
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(message)s')
    else:
        logging.basicConfig(filename=logfile,
            level=logging.DEBUG if args.debug else logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s')

        # redirect stderr
        errfile = args.log + '/xcauth.err'
        sys.stderr = open(errfile, 'a+')

    logging.debug('Start external auth script %s for %s with endpoint: %s', VERSION, args.type, args.url)

    if args.domain_db:
        domain_db = anydbm.open(args.domain_db, 'c', 0600)
        atexit.register(domain_db.close)
    else:
        domain_db = {}
    if args.cache_db:
        import bcrypt
        cache_db = anydbm.open(args.cache_db, 'c', 0600)
        atexit.register(cache_db.close)
    else:
        cache_db = {'': ''} # "Do not use" marker
    if args.shared_roster_db:
        shared_roster_db = anydbm.open(args.shared_roster_db, 'c', 0600)
        atexit.register(shared_roster_db.close)
    else:
        # Will never be accessed, as `ejabberdctl` will not be set
        shared_roster_db = None

    ttls = {'query': args.cache_query_ttl,
            'verify': args.cache_verification_ttl,
            'unreach': args.cache_unreachable_ttl}
    xc = xcauth(default_url = args.url, default_secret = args.secret,
            ejabberdctl = args.ejabberdctl if 'ejabberdctl' in args else None,
            shared_roster_domain = args.shared_roster_domain if 'shared_roster_domain' in args else None,
            shared_roster_db = shared_roster_db,
            domain_db = domain_db, cache_db = cache_db,
            timeout = args.timeout, ttls = ttls,
            bcrypt_rounds = args.cache_bcrypt_rounds)

    if args.isuser_test:
        success = xc.isuser(args.isuser_test[0], args.isuser_test[1])
        print(success)
        sys.exit(0)
    if args.roster_test:
        response, text = xc.roster_cloud(args.roster_test[0], args.roster_test[1])
        print(response)
        sys.exit(0)
    elif args.auth_test:
        success = xc.auth(args.auth_test[0], args.auth_test[1], args.auth_test[2])
        print(success)
        sys.exit(0)

    if args.type == 'ejabberd':
        xmpp = ejabberd_io
    elif args.type == 'saslauthd':
        xmpp = saslauthd_io
    else: # 'generic' or 'prosody'
        xmpp = prosody_io

    for data in xmpp.read_request():
        logging.debug('Receive operation ' + data[0]);

        success = False
        if data[0] == "auth" and len(data) == 4:
            success = xc.auth(data[1], data[2], data[3])
        elif data[0] == "isuser" and len(data) == 3:
            success = xc.isuser(data[1], data[2])
        elif data[0] == "quit" or data[0] == "exit":
            break

        xmpp.write_response(success)

    logging.debug('Shutting down...');

# vim: tabstop=8 softtabstop=0 expandtab shiftwidth=4
