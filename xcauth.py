#!/usr/bin/env python

import logging
import configargparse
import urllib
import requests
import hmac
import hashlib
import sys
import anydbm
from struct import *
from time import time
from base64 import b64decode
from string import maketrans

DEFAULT_LOG_DIR = '/var/log/xcauth'
FALLBACK_URL = ''
FALLBACK_SECRET = ''
VERSION = '0.2.2+'
DOMAINS = {}
DOMAIN_DB = None

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


### Handling requests to/responses from the cloud server

def cloud_request(s, data, secret, url):
    payload = urllib.urlencode(data)
    signature = hmac.new(secret, msg=payload, digestmod=hashlib.sha1).hexdigest();
    headers = {
        'X-JSXC-SIGNATURE': 'sha1=' + signature,
        'content-type':     'application/x-www-form-urlencoded'
    }
    try:
        r = s.post(url, data = payload, headers = headers, allow_redirects = False)
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
    return response and response['result'] == 'success'

def auth(s, username, domain, password):
    secret, url = per_domain(domain)
    if auth_token(username, domain, password, secret):
        logging.info('SUCCESS: Token for %s@%s is valid' % (username, domain))
        return True

    if auth_cloud(s, username, domain, password, secret, url):
        logging.info('SUCCESS: Cloud says password for %s@%s is valid' % (username, domain))
        return True

    logging.info('FAILURE: Neither token nor cloud approves user %s@%s' % (username, domain))
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
        default_config_files=['/etc/xcauth.conf', '/etc/external_cloud.conf', cfpath])

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
        choices=['generic', 'prosody', 'ejabberd'],
        default='generic',
        help='XMPP server type (prosody=generic); implies reading requests from stdin')
    parser.add_argument('-A', '--auth-test',
        nargs=3, metavar=("USER", "DOMAIN", "PASSWORD"),
        help='single, one-shot query of the user, domain, and password triple')
    parser.add_argument('-I', '--isuser-test',
        nargs=2, metavar=("USER", "DOMAIN"),
        help='single, one-shot query of the user and domain tuple')
    parser.add_argument('--version',
        action='version', version=VERSION)

    args = parser.parse_args()
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

def close_db(path):
    if path:
        DOMAIN_DB.close()


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

    logging.info('Start external auth script %s for %s with endpoint: %s', VERSION, args.type, FALLBACK_URL)

    read_pdc(args.per_domain_config)
    if args.domain_db:
        DOMAIN_DB = anydbm.open(args.domain_db, 'c', 0600)
    else:
        DOMAIN_DB = {}

    s = requests.Session()
    if args.isuser_test:
        success = isuser(s, args.isuser_test[0], args.isuser_test[1])
        print(success)
        close_db(args.domain_db)
        sys.exit(0)
    elif args.auth_test:
        success = auth(s, args.auth_test[0], args.auth_test[1], args.auth_test[2])
        print(success)
        close_db(args.domain_db)
        sys.exit(0)

    if args.type == "ejabberd":
        xmpp = ejabberd_io
    else:
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

    close_db(args.domain_db)
    logging.info('Shutting down...');

# vim: tabstop=8 softtabstop=0 expandtab shiftwidth=4
