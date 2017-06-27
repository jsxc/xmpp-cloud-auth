#!/usr/bin/env python

import logging
import configargparse
import argparse
import urllib
import requests
import hmac
import hashlib
import sys
from struct import *
from time import time
import hmac, hashlib
from base64 import b64decode
from string import maketrans

DEFAULT_LOG_DIR = '/var/log/ejabberd'
FALLBACK_URL = ''
FALLBACK_SECRET = ''
VERSION = '0.2.2+'
DOMAINS = {}

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

    json = r.json();

    return json;

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

    if not response:
        return False

    if response['result'] == 'success':
        return True

    return False

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

    if not response:
        return False

    if response['result'] == 'success' and response['data']['isUser']:
        return True

    return False

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
        -A and -I imply -d.'''

    # Config file in /etc or the program directory
    cfpath = sys.argv[0][:-3] + ".conf"
    parser = configargparse.ArgumentParser(description=desc,
        epilog=epilog,
    default_config_files=['/etc/external_cloud.conf', cfpath])

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

    parser.add_argument('-d', '--debug',
        action='store_true',
        help='enable debug mode')

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

    parser.add_argument('-p', '--per-domain-config',
        help='name of file containing whitespace-separated (domain, secret, url) tuples')

    parser.add_argument('--version', action='version', version=VERSION)

    args = parser.parse_args()
    if args.type is None and args.auth_test is None and args.isuser_test is None:
        parser.print_help(sys.stderr)
        sys.exit(1)
    return args.type, args.url, args.secret, args.debug, args.log, args.auth_test, args.isuser_test, args.per_domain_config

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
    else:
        return FALLBACK_SECRET, FALLBACK_URL

if __name__ == '__main__':
    TYPE, FALLBACK_URL, FALLBACK_SECRET, DEBUG, LOGDIR, AUTH_TEST, ISUSER_TEST, PDC = get_args()

    LOGFILE = LOGDIR + '/extauth.log'
    LEVEL = logging.DEBUG if DEBUG or AUTH_TEST or ISUSER_TEST else logging.INFO

    if not AUTH_TEST and not ISUSER_TEST:
        logging.basicConfig(filename=LOGFILE,level=LEVEL,format='%(asctime)s %(levelname)s: %(message)s')

        # redirect stderr
        ERRFILE = LOGDIR + '/extauth.err'
        sys.stderr = open(ERRFILE, 'a+')
    else:
        logging.basicConfig(stream=sys.stdout,level=LEVEL,format='%(asctime)s %(levelname)s: %(message)s')

    logging.info('Start external auth script %s for %s with endpoint: %s', VERSION, TYPE, FALLBACK_URL)
    logging.debug('Log level: %s', 'DEBUG' if LEVEL == logging.DEBUG else 'INFO')

    read_pdc(PDC)

    s = requests.Session()
    if ISUSER_TEST:
        success = isuser(s, ISUSER_TEST[0], ISUSER_TEST[1])
        print(success)
        sys.exit(0)

    if AUTH_TEST:
        success = auth(s, AUTH_TEST[0], AUTH_TEST[1], AUTH_TEST[2])
        print(success)
        sys.exit(0)

    if TYPE == "ejabberd":
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

    logging.info('Shutting down...');

# vim: tabstop=8 softtabstop=0 expandtab shiftwidth=4
