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
from struct import *
from time import time
from base64 import b64decode
from string import maketrans

DEFAULT_LOG_DIR = '/var/log/xcauth'
FALLBACK_URL = ''
FALLBACK_SECRET = ''
VERSION = '0.9.0+'
DOMAINS = {}
DOMAIN_DB = None
CACHE_DB = None

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
            logging.debug("from_prosody got %s" % line)
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
            (size,) = unpack('>h', length_field)
            if size == 0:
               logging.info("command length 0, treating as logical EOF")
               return
            cmd = sys.stdin.read(size)
            if len(cmd) != size:
               logging.warn("premature EOF while reading cmd: %d != %d" % (len(cmd), size))
               return
            logging.debug("from_ejabberd got %s" % cmd)
            x = cmd.split(':', 3)
            yield x
            length_field = sys.stdin.read(2)

    @classmethod
    def write_response(cls, bool):
        answer = 0
        if bool:
            answer = 1
        token = pack('>hh', 2, answer)
        sys.stdout.write(token)
        sys.stdout.flush()

class saslauthd_io:
    @classmethod
    def read_request(cls):
        field_no = 0
        fields = [None, None, None, None]
        length_field = sys.stdin.read(2)
        while len(length_field) == 2:
            (size,) = unpack('>h', length_field)
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
        token = pack('>h', len(answer)) + answer
        sys.stdout.write(token)
        sys.stdout.flush()


### Handling requests to/responses from the cloud server

def cloud_request(s, data, secret, url):
    payload = urllib.urlencode(data)
    signature = hmac.new(secret, msg=payload, digestmod=hashlib.sha1).hexdigest();
    headers = {
        'X-JSXC-SIGNATURE': 'sha1=' + signature,
        'content-type':     'application/x-www-form-urlencoded'
    }
    try:
        r = s['session'].post(url, data=payload, headers=headers,
                              allow_redirects=False, timeout=s['timeout'])
    except requests.exceptions.HTTPError as err:
        logging.warn(err)
        return False
    except requests.exceptions.RequestException as err:
        try:
            logging.warn('An error occured during the request: %s' % err)
        except TypeError as err:
            logging.warn('An unknown error occured during the request, probably an SSL error. Try updating your "requests" and "urllib" libraries.')
        return False
    if r.status_code != requests.codes.ok:
        return False
    return r.json();

# First try if it is a valid token
# Failure may just indicate that we were passed a password
def auth_token(username, domain, password, secret):
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

def auth_cloud(s, username, domain, password, secret, url):
    response = cloud_request(s, {
        'operation':'auth',
        'username': username,
        'domain':   domain,
        'password': password
    }, secret, url);
    if response:
        return response['result'] # 'error', 'success', 'noauth'
    return False

def checkpw(pw, pwhash):
    if 'checkpw' in dir(bcrypt):
        return bcrypt.checkpw(pw, pwhash)
    else:
        ret = bcrypt.hashpw(pw, pwhash)
        return ret == pwhash

def auth_cache(s, username, domain, password, unreach):
    key = username + ":" + domain
    if key in CACHE_DB:
        now = int(time())
        (pwhash, ts1, tsv, tsa, rest) = CACHE_DB[key].split("\t", 4)
        if ((int(tsa) + s['query_ttl'] > now and int(tsv) + s['verify_ttl'] > now)
           or (unreach and int(tsv) + s['unreach_ttl'] > now)):
            if checkpw(password, pwhash):
                CACHE_DB[key] = "\t".join((pwhash, ts1, tsv, str(now), rest))
                return True
    return False

def auth_update_cache(s, username, domain, password):
    if '' in CACHE_DB: # Cache disabled?
        return
    key = username + ":" + domain
    now = int(time())
    snow = str(now)
    pwhash = bcrypt.hashpw(password, bcrypt.gensalt(rounds=s['bcrypt_rounds']))
    if key in CACHE_DB:
        (ignored, ts1, tsv, tsa, rest) = CACHE_DB[key].split("\t", 4)
        CACHE_DB[key] = "\t".join((pwhash, ts1, snow, snow, rest))
    else:
        CACHE_DB[key] = "\t".join((pwhash, snow, snow, snow, ''))

def auth(s, username, domain, password):
    secret, url = per_domain(domain)
    if auth_token(username, domain, password, secret):
        logging.info('SUCCESS: Token for %s@%s is valid' % (username, domain))
        return True
    if auth_cache(s, username, domain, password, False):
        logging.info('SUCCESS: Cache says password for %s@%s is valid' % (username, domain))
        return True
    r = auth_cloud(s, username, domain, password, secret, url)
    if not r or r == 'error': # Request did not get through (connect, HTTP, signature check)
        cache = auth_cache(s, username, domain, password, True)
        logging.info('UNREACHABLE: Cache says password for %s@%s is %r' % (username, domain, cache))
        return cache
    elif r == 'success':
        logging.info('SUCCESS: Cloud says password for %s@%s is valid' % (username, domain))
        auth_update_cache(s, username, domain, password)
        return True
    else: # 'noauth'
        logging.info('FAILURE: Could not authenticate user %s@%s: %s' % (username, domain, r))
        return False

def isuser_cloud(s, username, domain, secret, url):
    response = cloud_request(s, {
        'operation':'isuser',
        'username':  username,
        'domain':    domain
    }, secret, url);
    return response and response['result'] == 'success' and response['data']['isUser']

def isuser(s, username, domain):
    secret, url = per_domain(domain)
    if isuser_cloud(s, username, domain, secret, url):
        logging.info('Cloud says user %s@%s exists' % (username, domain))
        return True
    return False


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
    epilog = '''-A takes precedence over -I over -t.
        -A and -I imply -d.
        -A, -I, -G, -P, -D, -L, and -U imply -i.
        The database operations require -b.'''

    # Config file in /etc or the program directory
    cfpath = sys.argv[0][:-3] + ".conf"
    parser = configargparse.ArgumentParser(description=desc,
        epilog=epilog,
        default_config_files=['/etc/xcauth.conf', '/etc/external_cloud.conf'])

    parser.add_argument('-c', '--config-file',
        is_config_file=True,
        help='config file path')
    parser.add_argument('-u', '--url',
        required=True,
        help='base URL')
    parser.add_argument('-s', '--secret',
        required=True,
        help='secure api token')
    parser.add_argument('-l', '--log',
        default=DEFAULT_LOG_DIR,
        help='log directory (default: %(default)s)')
    parser.add_argument('-p', '--per-domain-config',
        help='name of file containing whitespace-separated (domain, secret, url) tuples')
    parser.add_argument('-b', '--domain-db',
        help='persistent domain database; manipulated with -G, -P, -D, -L, -U')
    parser.add_argument('-d', '--debug',
        action='store_true',
        help='enable debug mode')
    parser.add_argument('-i', '--interactive',
        action='store_true',
        help='log to stdout')
    parser.add_argument('-t', '--type',
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
    parser.add_argument('-A', '--auth-test',
        nargs=3, metavar=("USER", "DOMAIN", "PASSWORD"),
        help='single, one-shot query of the user, domain, and password triple')
    parser.add_argument('-I', '--isuser-test',
        nargs=2, metavar=("USER", "DOMAIN"),
        help='single, one-shot query of the user and domain tuple')
    parser.add_argument('--version',
        action='version', version=VERSION)

    args = parser.parse_args()
    args.cache_query_ttl        = parse_timespan(args.cache_query_ttl)
    args.cache_verification_ttl = parse_timespan(args.cache_verification_ttl)
    args.cache_unreachable_ttl  = parse_timespan(args.cache_unreachable_ttl)
    if args.type is None and args.auth_test is None and args.isuser_test is None:
        parser.print_help(sys.stderr)
        sys.exit(1)
    return args

def read_pdc(filename):
    if not filename:
        return
    lines = 0
    with open(filename, "r") as f:
        for line in f:
            lines += 1
            line = line.rstrip("\r\n")
            if len(line) == 0 or line[0] == "#":
                continue
            try:
                dom, sec, url = line.split()
            except ValueError as err:
                logging.error('Missing fields in %s:%d: "%s"' % (filename, lines, line))
                raise
            DOMAINS[dom] = (sec, url)
    logging.info('Read %d lines, %d domains from %s' % (lines, len(dom), filename))

def per_domain(dom):
    if dom in DOMAINS:
        d = DOMAINS[dom]
        return d[0], d[1]
    elif dom in DOMAIN_DB:
        secret, url, extra = DOMAIN_DB[dom].split('\t', 2)
        return secret, url
    else:
        return FALLBACK_SECRET, FALLBACK_URL


if __name__ == '__main__':
    args = get_args()

    FALLBACK_SECRET = args.secret
    FALLBACK_URL = args.url

    logfile = args.log + '/xcauth.log'
    if (args.interactive or args.auth_test or args.isuser_test):
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

    logging.debug('Start external auth script %s for %s with endpoint: %s', VERSION, args.type, FALLBACK_URL)

    read_pdc(args.per_domain_config)
    if args.domain_db:
        DOMAIN_DB = anydbm.open(args.domain_db, 'c', 0600)
        atexit.register(DOMAIN_DB.close)
    else:
        DOMAIN_DB = {}
    if args.cache_db:
        import bcrypt
        CACHE_DB = anydbm.open(args.cache_db, 'c', 0600)
        atexit.register(CACHE_DB.close)
    else:
        CACHE_DB = {'': ''} # "Do not use" marker

    s = {'session': requests.Session(),
         'timeout': args.timeout,
         'query_ttl': args.cache_query_ttl,
         'verify_ttl': args.cache_verification_ttl,
         'unreach_ttl': args.cache_unreachable_ttl,
         'bcrypt_rounds': args.cache_bcrypt_rounds}
    if args.isuser_test:
        success = isuser(s, args.isuser_test[0], args.isuser_test[1])
        print(success)
        sys.exit(0)
    elif args.auth_test:
        success = auth(s, args.auth_test[0], args.auth_test[1], args.auth_test[2])
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
            success = auth(s, data[1], data[2], data[3])
        elif data[0] == "isuser" and len(data) == 3:
            success = isuser(s, data[1], data[2])
        elif data[0] == "quit" or data[0] == "exit":
            break

        xmpp.write_response(success)

    logging.info('Shutting down...');

# vim: tabstop=8 softtabstop=0 expandtab shiftwidth=4
