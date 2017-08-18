#!/usr/bin/python -tt

import logging
import sys
import atexit
import anydbm
from xclib import xcauth
from xclib.configuration import get_args

DEFAULT_LOG_DIR = '/var/log/xcauth'
VERSION = '0.9.0+'
DESC = '''XMPP server authentication against JSXC>=3.2.0 on Nextcloud.
    See https://jsxc.org or https://github.com/jsxc/xmpp-cloud-auth.'''
EPILOG = '''-I, -R, and -A take precedence over -t. One of them is required.
    -I, -R, and -A imply -i and -d.'''

if __name__ == '__main__':
    args = get_args(VERSION, DEFAULT_LOG_DIR, DESC, EPILOG, 'xcauth')

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
