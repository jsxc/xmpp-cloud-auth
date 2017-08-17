#!/usr/bin/python -tt

import logging
import configargparse
import sys
import atexit
import anydbm
from xclib import xcauth

DEFAULT_LOG_DIR = '/var/log/xcauth'
VERSION = '0.9.0+'

def parse_timespan(span):
    multipliers = {'s': 1, 'm': 60, 'h': 60*60, 'd': 60*60*24, 'w': 60*60*24*7}
    if span[-1] in multipliers:
        return int(span[:-1]) * multipliers[span[-1]]
    else:
        return int(span)

def get_args():
    # build command line argument parser
    desc = '''XMPP server authentication against JSXC>=3.2.0 on Nextcloud.
        See https://jsxc.org or https://github.com/jsxc/xmpp-cloud-auth.'''
    epilog = '''-I, -R, and -A take precedence over -t. One of them is required.
        -I, -R, and -A imply -i and -d.'''

    # Config file in /etc or the program directory
    cfpath = sys.argv[0][:-3] + ".conf"
    parser = configargparse.ArgumentParser(description=desc,
        epilog=epilog,
        default_config_files=['/etc/xcauth.conf', '/etc/external_cloud.conf'])

    parser.add_argument('--config-file', '-c',
        is_config_file=True,
        help='config file path')
    parser.add_argument('--url', '-u',
        required=True,
        help='base URL')
    parser.add_argument('--secret', '-s',
        required=True,
        help='secure api token')
    parser.add_argument('--log', '-l',
        default=DEFAULT_LOG_DIR,
        help='log directory (default: %(default)s)')
    parser.add_argument('--domain-db', '-b',
        help='persistent domain database; manipulated with xcdbm.py')
    parser.add_argument('--debug', '-d',
        action='store_true',
        help='enable debug mode')
    parser.add_argument('--interactive', '-i',
        action='store_true',
        help='log to stdout')
    parser.add_argument('--type', '-t',
        choices=['generic', 'prosody', 'ejabberd', 'saslauthd'],
        default='generic',
        help='XMPP server type (prosody=generic); implies reading requests from stdin')
    parser.add_argument('--timeout',
        type=int, default=5,
        help='Timeout for each of connection setup and request processing')
    parser.add_argument('--cache-db',
        help='Database path for the user cache; enables cache if set')
    parser.add_argument('--cache-query-ttl',
        default='1h',
        help='Maximum time between queries')
    parser.add_argument('--cache-verification-ttl',
        default='1d',
        help='Maximum time between backend verifications')
    parser.add_argument('--cache-unreachable-ttl',
        default='1w',
        help='Maximum cache time when backend is unreachable (overrides the other TTLs)')
    parser.add_argument('--cache-bcrypt-rounds',
        type=int, default=12,
        help='''Encrypt passwords with 2^ROUNDS before storing
            (i.e., every increasing ROUNDS takes twice as much
            computation time)''')
    parser.add_argument('--ejabberdctl',
        metavar="PATH",
        help='Enables shared roster updates on authentication; use ejabberdctl command at PATH to modify them')
    parser.add_argument('--shared-roster-db',
        help='Which groups a user has been added to (to ensure proper deletion)')
    parser.add_argument('--auth-test', '-A',
        nargs=3, metavar=("USER", "DOMAIN", "PASSWORD"),
        help='single, one-shot query of the user, domain, and password triple')
    parser.add_argument('--isuser-test', '-I',
        nargs=2, metavar=("USER", "DOMAIN"),
        help='single, one-shot query of the user and domain tuple')
    parser.add_argument('--roster-test', '-R',
        nargs=2, metavar=("USER", "DOMAIN"),
        help='single, one-shot query of the user\'s shared roster')
    parser.add_argument('--version',
        action='version', version=VERSION)

    args = parser.parse_args()
    args.cache_query_ttl        = parse_timespan(args.cache_query_ttl)
    args.cache_verification_ttl = parse_timespan(args.cache_verification_ttl)
    args.cache_unreachable_ttl  = parse_timespan(args.cache_unreachable_ttl)
    if ('ejabberdctl' in args) != ('shared_roster_db' in args):
        sys.stderr.write('Define either both --ejabberdctl and --shared-roster-db, or neither\n')
        sys.exit(1)
    if (args.auth_test is None and args.isuser_test is None and args.roster_test is None):
        if args.type is None: # No work to do
            parser.print_help(sys.stderr)
            sys.exit(1)
    return args



if __name__ == '__main__':
    args = get_args()

    logfile = args.log + '/xcauth.log'
    if (args.interactive or args.auth_test or args.isuser_test or args.roster_test):
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

    logging.debug('Start external auth script %s for %s with endpoint: %s', VERSION, args.type, args.url)

    if args.domain_db:
        domain_db = anydbm.open(args.domain_db, 'c', 0600)
        atexit.register(domain_db.close)
    else:
        domain_db = {}
    if args.cache_db:
        import bcrypt
        cache_db = anydbm.open(args.cache_db, 'c', 0600)
        atexit.register(cache_db.close)
    else:
        cache_db = {'': ''} # "Do not use" marker
    if args.shared_roster_db:
        shared_roster_db = anydbm.open(args.shared_roster_db, 'c', 0600)
        atexit.register(shared_roster_db.close)
    else:
        # Will never be accessed, as `ejabberdctl` will not be set
        shared_roster_db = None

    ttls = {'query': args.cache_query_ttl,
            'verify': args.cache_verification_ttl,
            'unreach': args.cache_unreachable_ttl}
    xc = xcauth(default_url = args.url, default_secret = args.secret,
            ejabberdctl = args.ejabberdctl if 'ejabberdctl' in args else None,
            shared_roster_db = shared_roster_db,
            domain_db = domain_db, cache_db = cache_db,
            timeout = args.timeout, ttls = ttls,
            bcrypt_rounds = args.cache_bcrypt_rounds)

    if args.isuser_test:
        success = xc.isuser(args.isuser_test[0], args.isuser_test[1])
        print(success)
        sys.exit(0)
    if args.roster_test:
        response, text = xc.roster_cloud(args.roster_test[0], args.roster_test[1])
        print(response)
        sys.exit(0)
    elif args.auth_test:
        success = xc.auth(args.auth_test[0], args.auth_test[1], args.auth_test[2])
        print(success)
        sys.exit(0)

    if args.type == 'ejabberd':
        from xclib.ejabberd_io import ejabberd_io
        xmpp = ejabberd_io
    elif args.type == 'saslauthd':
        from xclib.saslauthd_io import saslauthd_io
        xmpp = saslauthd_io
    else: # 'generic' or 'prosody'
        from xclib.prosody_io import prosody_io
        xmpp = prosody_io

    for data in xmpp.read_request():
        logging.debug('Receive operation ' + data[0]);

        success = False
        if data[0] == "auth" and len(data) == 4:
            success = xc.auth(data[1], data[2], data[3])
        elif data[0] == "isuser" and len(data) == 3:
            success = xc.isuser(data[1], data[2])
        elif data[0] == "quit" or data[0] == "exit":
            break

        xmpp.write_response(success)

    logging.debug('Shutting down...');

# vim: tabstop=8 softtabstop=0 expandtab shiftwidth=4
