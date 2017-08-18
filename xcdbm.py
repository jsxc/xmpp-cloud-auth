#!/usr/bin/python -tt

import configargparse
import sys
import anydbm
from xclib.configuration import get_args

VERSION = '0.9.0+'
DESC = '''XMPP server authentication against JSXC>=3.2.0 on Nextcloud: Database manipulation.
    See https://jsxc.org or https://github.com/jsxc/xmpp-cloud-auth.'''
EPILOG = '''Exactly one of -G, -P, -D, -L, and -U is required.'''

if __name__ == '__main__':
    args = get_args(VERSION, None, DESC, EPILOG, 'xcdbm')

    domain_db = anydbm.open(args.domain_db, 'c', 0600)
    if args.get:
        print(domain_db[args.get])
    elif args.put:
        domain_db[args.put[0]] = args.put[1]
    elif args.delete:
        del domain_db[args.delete]
    elif args.unload:
        for k in domain_db.keys():
            print k, '\t', domain_db[k]
        # Should work according to documentation, but doesn't
        # for k, v in DOMAIN_DB.iteritems():
        #     print k, '\t', v
    elif args.load:
        for line in sys.stdin:
            k, v = line.rstrip().split('\t', 1)
            domain_db[k] = v
    domain_db.close()

# vim: tabstop=8 softtabstop=0 expandtab shiftwidth=4
