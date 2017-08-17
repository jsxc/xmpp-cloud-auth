import configargparse
import sys

def parse_timespan(span):
    multipliers = {'s': 1, 'm': 60, 'h': 60*60, 'd': 60*60*24, 'w': 60*60*24*7}
    if span[-1] in multipliers:
        return int(span[:-1]) * multipliers[span[-1]]
    else:
        return int(span)

def get_args(version, logdir):
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
        default=logdir,
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
        action='version', version=version)

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
