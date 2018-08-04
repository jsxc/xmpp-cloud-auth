import configargparse
import sys
from xclib.version import VERSION
default_db = '/var/lib/xcauth/xcauth.sqlite3'

def parse_timespan(span):
    multipliers = {'s': 1, 'm': 60, 'h': 60*60, 'd': 60*60*24, 'w': 60*60*24*7}
    if span[-1] in multipliers:
        return int(span[:-1]) * multipliers[span[-1]]
    else:
        return int(span)

def add_maybe(*args, **kwargs):
    if app_name == 'xcdbm':
        kwargs['help'] = '(ignored for config file compatibility)'
    parser.add_argument(*args, **kwargs)

def get_args(logdir, desc, epilog, name, args=None, config_file_contents=None):
    # Config file in /etc or the program directory
    global parser, app_name
    app_name = name
    parser = configargparse.ArgumentParser(description=desc,
        epilog=epilog,
        default_config_files=['/etc/xcauth.conf'])

    parser.add_argument('--config-file', '-c',
        is_config_file=True,
        help='config file path')

    if name == 'xcdbm':
        parser.add_argument('--domain-db', '-b',
            required=True,
            help='persistent domain database; manipulated with -G, -P, -D, -L, -U')
        parser.add_argument('--get', '-G',
            help='retrieve (get) a database entry')
        parser.add_argument('--put', '-P',
            nargs=2, metavar=('KEY', 'VALUE'),
            help='store (put) a database entry (insert or update)')
        parser.add_argument('--delete', '-D',
            help='delete a database entry')
        parser.add_argument('--load', '-L',
            action='store_true',
            help='load multiple database entries from stdin')
        parser.add_argument('--unload', '-U',
            action='store_true',
            help='unload (dump) the database contents to stdout')
    else:
        parser.add_argument('--db',
            default=default_db,
            help='Path to the SQLite state database')
        parser.add_argument('--cache-storage',
            choices=['none', 'memory', 'db'],
            default='none',
            help='How to cache authentication information')
        parser.add_argument('--domain-db', '-b',
            help='''persistent domain database; manipulated with xcdbm.py.
                DEPRECATED, will only be used for migration purposes.''')
        parser.add_argument('--auth-test', '-A',
            nargs=3, metavar=("USER", "DOMAIN", "PASSWORD"),
            help='single, one-shot query of the user, domain, and password triple')
        parser.add_argument('--isuser-test', '-I',
            nargs=2, metavar=("USER", "DOMAIN"),
            help='single, one-shot query of the user and domain tuple')
        parser.add_argument('--roster-test', '-R',
            nargs=2, metavar=("USER", "DOMAIN"),
            help='single, one-shot query of the user\'s shared roster')
        parser.add_argument('--update-roster', '-T',
            action='store_true',
            help='DEPRECATED. Automatically activated when --ejabberdctl is set')

    add_maybe('--url', '-u',
        required=True,
        help='base URL')
    add_maybe('--secret', '-s',
        required=True,
        help='secure api token')
    add_maybe('--log', '-l',
        default=logdir,
        help='log directory (default: %(default)s)')
    add_maybe('--debug', '-d',
        action='store_true',
        help='enable debug mode')
    add_maybe('--interactive', '-i',
        action='store_true',
        help='log to stderr')
    add_maybe('--type', '-t',
        choices=['generic', 'prosody', 'ejabberd', 'saslauthd', 'postfix'],
        help='''XMPP server/query protocol type (prosody≘generic);
            implies reading requests from stdin. See doc/Installation.md
            and systemd/README.md for more information and overrides.''')
    add_maybe('--timeout',
        default='5,10',
        help='Timeout for connection setup, request processing')
    add_maybe('--cache-db',
        help='Database path for the user cache. DEPRECATED, only for conversion purposes')
    add_maybe('--cache-query-ttl',
        default='1h',
        help='Maximum time between queries')
    add_maybe('--cache-verification-ttl',
        default='1d',
        help='Maximum time between backend verifications')
    add_maybe('--cache-unreachable-ttl',
        default='1w',
        help='Maximum cache time when backend is unreachable (overrides the other TTLs)')
    add_maybe('--cache-bcrypt-rounds',
        type=int, default=12,
        help='''Encrypt passwords with 2^ROUNDS before storing
            (i.e., every increment of ROUNDS results in twice the
            computation time, both for us and an attacker).''')
    add_maybe('--ejabberdctl',
        metavar="PATH",
        help='''Enables shared roster updates on authentication;
            use ejabberdctl command at PATH to modify them''')
    add_maybe('--shared-roster-db',
        help='''Which groups a user has been added to (to ensure proper deletion).
            DEPRECATED, only for conversion purposes.''')

    parser.add_argument('--version',
        action='version', version=VERSION)

    args = parser.parse_args(args=args, config_file_contents=config_file_contents)
    if name != 'xcdbm':
        args.cache_query_ttl        = parse_timespan(args.cache_query_ttl)
        args.cache_verification_ttl = parse_timespan(args.cache_verification_ttl)
        args.cache_unreachable_ttl  = parse_timespan(args.cache_unreachable_ttl)
        if ',' in args.timeout:
            (a, b) = args.timeout.split(',', 1)
            args.timeout = (int(a), int(b))
        else:
            args.timeout = int(args.timeout)
        if (args.auth_test is None and args.isuser_test is None and args.roster_test is None
          and args.type is None): # No work to do
            parser.print_help(sys.stderr)
            sys.exit(1)
    else: # xcauth
        command_count = 0
        for i in (args.get, args.put, args.delete, args.load, args.unload):
            if i is not None and i != False:
                command_count += 1
        if command_count != 1:
            parser.print_help(sys.stderr)
            sys.exit(1)
    return args
