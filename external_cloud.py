#!/usr/bin/env python

import logging
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
URL = ''
SECRET = ''

usersafe_encoding = maketrans('-$%', 'OIl')

def send_request(data):
    payload = urllib.urlencode(data)
    signature = hmac.new(SECRET, msg=payload, digestmod=hashlib.sha1).hexdigest();
    headers = {
        'X-JSXC-SIGNATURE': 'sha1=' + signature,
        'content-type': 'application/x-www-form-urlencoded'
    }

    try:
        r = requests.post(URL, data = payload, headers = headers, allow_redirects = False)
    except requests.exceptions.HTTPError as err:
        logging.warn(err)
        return False
    except requests.exceptions.RequestException as err:
        logging.warn('An error occured during the request: %s' % err)
        return False

    if r.status_code != requests.codes.ok:
        return False

    json = r.json();

    return json;

# First try if it is a valid token
# Failure may just indicate that we were passed a password
def verify_token(username, server, password):
    try:
        token = b64decode(password.translate(usersafe_encoding) + "=======")
    except:
        logging.debug('Could not decode token (maybe not a token?)')
        return False

    jid = username + '@' + server

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
    response = hmac.new(SECRET, challenge, hashlib.sha256).digest()

    return hmac.compare_digest(mac, response[:16])

def verify_cloud(username, server, password):
    response = send_request({
        'operation':'auth',
        'username':username,
        'password':password
    });

    if not response:
        return False

    if response['result'] == 'success':
        return True

    return False

def is_user_cloud(username, server):
    response = send_request({
        'operation':'isuser',
        'username':username
    });

    if not response:
        return False

    if response['result'] == 'success' and response['data']['isUser']:
        return True

    return False

def from_server(type):
    if type == 'ejabberd':
        return from_ejabberd();
    elif type == 'prosody':
        return from_prosody();

def to_server(type, bool):
    if type == 'ejabberd':
        return to_ejabberd(bool);
    elif type == 'prosody':
        return to_prosody(bool);

def from_prosody():
    line = sys.stdin.readline().rstrip("\n")
    return line.split(':')

def to_prosody(bool):
    answer = '0'
    if bool:
        answer = '1'
    sys.stdout.write(answer+"\n")
    sys.stdout.flush()

def from_ejabberd():
    input_length = sys.stdin.read(2)
    (size,) = unpack('>h', input_length)
    return sys.stdin.read(size).split(':')

def to_ejabberd(bool):
    answer = 0
    if bool:
        answer = 1
    token = pack('>hh', 2, answer)
    sys.stdout.write(token)
    sys.stdout.flush()

def auth(username, server, password):
    if verify_token(username, server, password):
        logging.info('SUCCESS: Token is valid')
        return True

    if verify_cloud(username, server, password):
        logging.info('SUCCESS: Cloud says this password is valid')
        return True

    logging.info('FAILURE: Neither token nor cloud approves')
    return False

def is_user(username, server):
    if is_user_cloud(username, server):
        logging.info('Cloud says this user exists')
        return True

    return False

def getArgs():
    # build command line argument parser
    desc = 'XMPP server authentication script'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-t', '--type',
        required=True,
        choices=['prosody', 'ejabberd'],
        help='XMPP server')

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

    parser.add_argument('-A', '--auth-test',
	nargs=3,
        help='one-shot query of the user, domain, and password triple')

    args = vars(parser.parse_args())
    return args['type'], args['url'], args['secret'], args['debug'], args['log'], args['auth_test']


if __name__ == '__main__':
    TYPE, URL, SECRET, DEBUG, LOG, AUTH_TEST = getArgs()

    LOGFILE = LOG + '/extauth.log'
    LEVEL = logging.DEBUG if DEBUG or AUTH_TEST else logging.INFO

    if not AUTH_TEST:
        logging.basicConfig(filename=LOGFILE,level=LEVEL,format='%(asctime)s %(levelname)s: %(message)s')

        # redirect stderr
        ERRFILE = LOG + '/extauth.err'
        sys.stderr = open(ERRFILE, 'a+')
    else:
        logging.basicConfig(stream=sys.stdout,level=LEVEL,format='%(asctime)s %(levelname)s: %(message)s')

    logging.info('Start external auth script for %s with endpoint: %s', TYPE, URL)
    logging.info('Log location: %s', LOG)
    logging.info('Log level: %s', 'DEBUG' if DEBUG else 'INFO')

    if AUTH_TEST:
        success = auth(AUTH_TEST[0], AUTH_TEST[1], AUTH_TEST[2])
        print(success)
        sys.exit(0)

    while True:
        data = from_server(TYPE)
        logging.info('Receive operation ' + data[0]);

        success = False
        if data[0] == "auth" and len(data) == 4:
            success = auth(data[1], data[2], data[3])
        if data[0] == "isuser" and len(data) == 3:
            success = is_user(data[1], data[2])

        to_server(TYPE, success)

    logging.info('Shutting down...');

# vim: tabstop=8 softtabstop=0 expandtab shiftwidth=4 smarttab
