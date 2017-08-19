#!/usr/bin/python -tt

from xclib.configuration import get_args
from xclib.authops import perform
import sys

DEFAULT_LOG_DIR = '/var/log/xcauth'
DESC = '''XMPP server authentication against JSXC>=3.2.0 on Nextcloud.
    See https://jsxc.org or https://github.com/jsxc/xmpp-cloud-auth.'''
EPILOG = '''-I, -R, and -A take precedence over -t. One of them is required.
    -I, -R, and -A imply -i and -d.'''

if __name__ == '__main__':
    args = get_args(DEFAULT_LOG_DIR, DESC, EPILOG, 'xcauth')
    perform(args)

# vim: tabstop=8 softtabstop=0 expandtab shiftwidth=4
