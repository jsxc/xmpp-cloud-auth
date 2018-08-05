import sys
import bsddb3
from xclib.utf8 import utf8, unutf8

def perform(args):
    domain_db = bsddb3.hashopen(args.domain_db, 'c', 0o600)
    if args.get:
        print(unutf8(domain_db[utf8(args.get)], 'illegal'))
    elif args.put:
        domain_db[utf8(args.put[0])] = args.put[1]
    elif args.delete:
        del domain_db[utf8(args.delete)]
    elif args.unload:
        for k in list(domain_db.keys()):
            print('%s\t%s' % (unutf8(k, 'illegal'), unutf8(domain_db[k], 'illegal')))
        # Should work according to documentation, but doesn't
        # for k, v in DOMAIN_DB.iteritems():
        #     print k, '\t', v
    elif args.load:
        for line in sys.stdin:
            k, v = line.rstrip('\r\n').split('\t', 1)
            domain_db[utf8(k)] = v
    domain_db.close()

# vim: tabstop=8 softtabstop=0 expandtab shiftwidth=4
