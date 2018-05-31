import logging
import sys
import atexit
import anydbm
from xclib import xcauth
from xclib.sigcloud import sigcloud
from xclib.version import VERSION

def perform(args):
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
        sc = sigcloud(xc, args.isuser_test[0], args.isuser_test[1])
        success = sc.isuser()
        print success
        return
    if args.roster_test:
        sc = sigcloud(xc, args.roster_test[0], args.roster_test[1])
        success, response = sc.roster_cloud()
        print str(response)
        if args.update_roster:
            sc.try_roster(async=False)
        return
    elif args.auth_test:
        sc = sigcloud(xc, args.auth_test[0], args.auth_test[1], args.auth_test[2])
        success = sc.auth()
        print success
        return

    if args.type == 'ejabberd':
        from xclib.ejabberd_io import ejabberd_io
        xmpp = ejabberd_io
    elif args.type == 'saslauthd':
        from xclib.saslauthd_io import saslauthd_io
        xmpp = saslauthd_io
    elif args.type == 'postfix':
        from xclib.postfix_io import postfix_io
        xmpp = postfix_io
    else: # 'generic' or 'prosody'
        from xclib.prosody_io import prosody_io
        xmpp = prosody_io

    for data in xmpp.read_request():
        logging.debug('Receive operation ' + data[0]);

        success = False
        if data[0] == "auth" and len(data) == 4:
            sc = sigcloud(xc, data[1], data[2], data[3])
            success = sc.auth()
        elif data[0] == "isuser" and len(data) == 3:
            sc = sigcloud(xc, data[1], data[2])
            success = sc.isuser()
        elif data[0] == "roster" and len(data) == 3:
            # Nonstandard extension, only useful with -t generic
            sc = sigcloud(xc, data[1], data[2])
            success, response = sc.roster_cloud()
            success = str(response) # Convert from unicode
        elif data[0] == "quit" or data[0] == "exit":
            break

        xmpp.write_response(success)

    logging.debug('Shutting down...');

# vim: tabstop=8 softtabstop=0 expandtab shiftwidth=4
