#!/usr/bin/python -tt

import configargparse
import sys
import anydbm

VERSION = '0.9.0+'

def get_args():
    # build command line argument parser
    desc = '''XMPP server authentication against JSXC>=3.2.0 on Nextcloud: Database manipulation.
        See https://jsxc.org or https://github.com/jsxc/xmpp-cloud-auth.'''

    # Config file in /etc or the program directory
    cfpath = sys.argv[0][:-3] + ".conf"
    parser = configargparse.ArgumentParser(description=desc,
        default_config_files=['/etc/xcauth.conf', '/etc/external_cloud.conf', cfpath])

    parser.add_argument('-c', '--config-file',
        is_config_file=True,
        help='config file path')
    parser.add_argument('-u', '--url',
        required=True,
        help='(ignored for compatibility)')
    parser.add_argument('-s', '--secret',
        required=True,
        help='(ignored for compatibility)')
    parser.add_argument('-l', '--log',
        help='(ignored for compatibility)')
    parser.add_argument('-b', '--domain-db',
        required=True,
        help='persistent domain database; manipulated with -G, -P, -D, -L, -U')
    parser.add_argument('-d', '--debug',
        action='store_true',
        help='(ignored for compatibility)')
    parser.add_argument('-i', '--interactive',
        action='store_true',
        help='(ignored for compatibility)')
    parser.add_argument('-t', '--type',
        help='(ignored for compatibility)')
    parser.add_argument('--timeout',
        help='(ignored for compatibility)')
    parser.add_argument('--cache-db',
        help='(ignored for compatibility)')
    parser.add_argument('--cache-query-ttl',
        help='(ignored for compatibility)')
    parser.add_argument('--cache-verification-ttl',
        help='(ignored for compatibility)')
    parser.add_argument('--cache-unreachable-ttl',
        help='(ignored for compatibility)')
    parser.add_argument('--cache-bcrypt-rounds',
        help='(ignored for compatibility)')
    parser.add_argument('--ejabberdctl',
        help='(ignored for compatibility)')
    parser.add_argument('--shared-roster-domain',
        help='(ignored for compatibility)')
    parser.add_argument('-G', '--get',
        help='retrieve (get) a database entry')
    parser.add_argument('-P', '--put',
        nargs=2, metavar=('KEY', 'VALUE'),
        help='store (put) a database entry (insert or update)')
    parser.add_argument('-D', '--delete',
        help='delete a database entry')
    parser.add_argument('-L', '--load',
        action='store_true',
        help='load multiple database entries from stdin')
    parser.add_argument('-U', '--unload',
        action='store_true',
        help='unload (dump) the database contents to stdout')
    parser.add_argument('--version',
        action='version', version=VERSION)
    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()

    DOMAIN_DB = anydbm.open(args.domain_db, 'c', 0600)
    if args.get:
        print(DOMAIN_DB[args.get])
    elif args.put:
        DOMAIN_DB[args.put[0]] = args.put[1]
    elif args.delete:
        del DOMAIN_DB[args.delete]
    elif args.unload:
        for k in DOMAIN_DB.keys():
            print k, '\t', DOMAIN_DB[k]
        # Should work according to documentation, but doesn't
        # for k, v in DOMAIN_DB.iteritems():
        #     print k, '\t', v
    elif args.load:
        for line in sys.stdin:
            k, v = line.rstrip().split('\t', 1)
            DOMAIN_DB[k] = v
    DOMAIN_DB.close()

# vim: tabstop=8 softtabstop=0 expandtab shiftwidth=4
