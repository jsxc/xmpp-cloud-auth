#!/usr/bin/env python

import logging
import argparse
import urllib
import requests
import hmac
import hashlib
import sys
from struct import *

DEFAULT_LOG_DIR = '/var/log/ejabberd'
URL = ''
SECRET = ''

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

    r = requests.post(URL, data = payload, headers = headers, allow_redirects = False)

    if r.status_code != requests.codes.ok:
        return False

    json = r.json();

    if json['result'] == 'success':
        return True

    return False

def getArgs():
    # build command line argument parser
    desc = 'ejabberd authentication script'
    parser = argparse.ArgumentParser(description=desc)

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

    return args['url'], args['secret'], args['debug'], args['log']


if __name__ == '__main__':
    global URL, SECRET

    URL, SECRET, DEBUG, LOG = getArgs()

    LOGFILE = LOG + '/extauth.log'
    LEVEL = logging.DEBUG if DEBUG else logging.INFO

    # redirect stderr
    ERRFILE = LOG + '/extauth.err'
    sys.stderr = open(ERRFILE, 'a+')

    logging.basicConfig(filename=LOGFILE,level=LEVEL)

    logging.info('Start external auth script with endpoint: ' + URL)
    logging.info('Log level: ' + str(LEVEL))

    while True:
        data = from_ejabberd()
        logging.info('Receive operation ' + data[0]);

        success = False
        if data[0] == "auth":
            success = auth(data[1], data[2], data[3])

        to_ejabberd(success)

    logging.info('Shutting down...');

# vim: tabstop=8 softtabstop=0 expandtab shiftwidth=4 smarttab
