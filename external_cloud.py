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

def verify_token(username, server, password):
    token = b64decode(password.translate(usersafe_encoding) + "=======")
    jid = username + '@' + server

    if len(token) != 23:
        logging.debug('Token is too short')
        return False

    (version, mac, header) = unpack("> B 16s 6s", token)
    if version != 0:
        logging.debug('Wrong token version')
        return False;

    (secretID, expiry) = unpack("> H I", header)
    if expiry < time():
        logging.debug('Token is expired')
        return False

    challenge = pack("> B 6s %ds" % len(jid), version, header, jid)
    response = hmac.new(SECRET, challenge, hashlib.sha256).digest()

    return hmac.compare_digest(mac, response[:16])

def verify_cloud(username, server, password):
    payload = urllib.urlencode({
        'operation':'auth',
        'username':username,
        'password':password
    })
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
        logging.warn('An error occured during the request')
        return False

    if r.status_code != requests.codes.ok:
        return False

    json = r.json();

    if json['result'] == 'success':
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
        logging.info('Token is valid')
        return True

    if verify_cloud(username, server, password):
        logging.info('Cloud says this password is valid')
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
        action='store_const', const=True,
        help='toggle debug mode')

    args = vars(parser.parse_args())

    return args['type'], args['url'], args['secret'], args['debug'], args['log']


if __name__ == '__main__':
    TYPE, URL, SECRET, DEBUG, LOG = getArgs()

    LOGFILE = LOG + '/extauth.log'
    LEVEL = logging.DEBUG if DEBUG else logging.INFO

    # redirect stderr
    ERRFILE = LOG + '/extauth.err'
    sys.stderr = open(ERRFILE, 'a+')

    logging.basicConfig(filename=LOGFILE,level=LEVEL,format='%(asctime)s %(levelname)s: %(message)s')

    logging.info('Start external auth script for %s with endpoint: %s', TYPE, URL)
    logging.info('Log location: %s', LOG)
    logging.info('Log level: %s', 'DEBUG' if DEBUG else 'INFO')

    while True:
        data = from_server(TYPE)
        logging.info('Receive operation ' + data[0]);

        success = False
        if data[0] == "auth" and len(data) == 4:
            success = auth(data[1], data[2], data[3])

        to_server(TYPE, success)

    logging.info('Shutting down...');

# vim: tabstop=8 softtabstop=0 expandtab shiftwidth=4 smarttab
