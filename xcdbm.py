#!/usr/bin/python3 -tt

from xclib.configuration import get_args
from xclib.dbmops import perform

DESC = '''XMPP server authentication against JSXC>=3.2.0 on Nextcloud: Database manipulation.
    See https://jsxc.org or https://github.com/jsxc/xmpp-cloud-auth.'''
EPILOG = '''Exactly one of -G, -P, -D, -L, and -U is required.'''

if __name__ == '__main__':
    args = get_args(None, DESC, EPILOG, 'xcdbm')
    perform(args)

# vim: tabstop=8 softtabstop=0 expandtab shiftwidth=4
