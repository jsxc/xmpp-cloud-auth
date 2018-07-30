import logging
import sys
import atexit
import bsddb3
import select
import threading
import socket
import io
from xclib import xcauth
from xclib.sigcloud import sigcloud
from xclib.version import VERSION
from xclib.sockact import listen_fds_with_names

def perform(args):
    # Read configuration
    logfile = args.log + '/xcauth.log'
    if (args.interactive or args.auth_test or args.isuser_test or args.roster_test):
        logging.basicConfig(stream=sys.stderr,
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(message)s')
    else:
        errfile = args.log + '/xcauth.err'
        try:
            # redirect stderr
            sys.stderr = open(errfile, 'a+')
        except OSError as e:
            logging.warning('Cannot redirect stderr to %s: %s' % (errfile, str(e)))
        try:
            logging.basicConfig(filename=logfile,
                level=logging.DEBUG if args.debug else logging.INFO,
                format='%(asctime)s %(levelname)s: %(message)s')
        except OSError as e:
            logging.basicConfig(stream=sys.stderr)
            logging.warning('Cannot log to %s: %s' % (logfile, str(e)))

    logging.debug('Start external auth script %s for %s with endpoint: %s', VERSION, args.type, args.url)

    # Open databases
    if args.domain_db:
        domain_db = bsddb3.hashopen(args.domain_db, 'c', 0o600)
        atexit.register(domain_db.close)
    else:
        domain_db = {}
    if args.cache_db:
        try:
            import bcrypt
            cache_db = bsddb3.hashopen(args.cache_db, 'c', 0o600)
            atexit.register(cache_db.close)
        except ImportError as e:
            logging.warn('Cannot import bcrypt (%s); caching disabled' % e)
            cache_db = {b'': b''} # "Do not use" marker
        except bsddb3.db.DBError as e:
            # Fall back to in-memory DB; use faster password hashing, as
            # it is not persistent, so an attacker must have live access
            # (and then, there are easier ways, unfortunately)
            cache_db = {}
            args.cache_bcrypt_rounds = max(6, args.cache_bcrypt_rounds-2)
            logging.warn('Trouble opening cache-db=%s (%s); falling back to in-memory caching with reduced cache-bcrypt-rounds=%d' % (args.cache_db, e, args.cache_bcrypt_rounds))
    else:
        cache_db = {b'': b''} # Magic "do not use" marker
    if args.shared_roster_db:
        shared_roster_db = bsddb3.hashopen(args.shared_roster_db, 'c', 0o600)
        atexit.register(shared_roster_db.close)
    else:
        # Will never be accessed, as `ejabberdctl` will not be set
        shared_roster_db = None

    # Set up environment
    ttls = {'query': args.cache_query_ttl,
            'verify': args.cache_verification_ttl,
            'unreach': args.cache_unreachable_ttl}
    xc = xcauth(default_url = args.url, default_secret = args.secret,
            ejabberdctl = args.ejabberdctl if 'ejabberdctl' in args else None,
            shared_roster_db = shared_roster_db,
            domain_db = domain_db, cache_db = cache_db,
            timeout = args.timeout, ttls = ttls,
            bcrypt_rounds = args.cache_bcrypt_rounds)

    # Check for one-shot commands
    if args.isuser_test:
        sc = sigcloud(xc, args.isuser_test[0], args.isuser_test[1])
        success = sc.isuser()
        print(success)
        return
    if args.roster_test:
        sc = sigcloud(xc, args.roster_test[0], args.roster_test[1])
        success, response = sc.roster_cloud()
        print(str(response))
        if args.update_roster:
            sc.try_roster(async=False)
        return
    elif args.auth_test:
        sc = sigcloud(xc, args.auth_test[0], args.auth_test[1], args.auth_test[2])
        success = sc.auth()
        print(success)
        return

    # Read commands from file descriptors
    # Acceptor socket?
    listeners = listen_fds_with_names()
    if listeners is None:
        # Single socket; unclear whether it is connected or an acceptor
        try:
            stdinfd = sys.stdin.fileno()
        except io.UnsupportedOperation:
            stdinfd = None
        if stdinfd is None:
            # Not a real socket, assume stdio communication
            perform_from_fd(sys.stdin, sys.stdout, xc, args.type)
        else:
            s = socket.socket(fileno=stdinfd)
            try:
                # Is it an acceptor socket?
                s.listen()
                # Yes, accept connections (fake systemd context)
                perform_from_listeners({0: args.type}, xc, args.type)
            except OSError:
                # Not an acceptor socket, use for stdio
                perform_from_fd(sys.stdin, sys.stdout, xc, args.type, closefds=(sys.stdin,sys.stdout,s))
    else:
        # Uses systemd socket activation
        perform_from_listeners(listeners, xc, args.type)

# Handle possibly multiple listening sockets
def perform_from_listeners(listeners, xc, proto):
    sockets = {}
    while listeners:
        inputs = listeners.keys()
        r, w, x = select.select(inputs, (), inputs)
        for sfd in r:
            logging.debug('Read %r, sockets=%r' % (r, sockets))
            if sfd not in sockets:
                s = socket.socket(fileno=sfd)
                sockets[sfd] = s
            s = sockets[sfd]
            conn, remote_addr = s.accept()
            lproto = listeners[sfd]
            if lproto in ('generic', 'prosody', 'ejabberd', 'saslauthd', 'postfix'):
                fdproto = lproto
            else:
                fdproto = proto
                lproto = "%s/%s" % (lproto, fdproto)
            threading.Thread(target=perform_from_fd,
                    name='worker-%s(%d)-%r' % (lproto, sfd, remote_addr),
                    args=(conn, conn, xc, fdproto),
                    kwargs={'closefds': (conn,)}).start()
        for sfd in x:
            logging.warn("Socket %d logged a complaint, dropping" % sfd)
            del listeners[sfd]

# Handle a single I/O stream (stdin/stdout or acepted socket)
def perform_from_fd(infd, outfd, xc, proto, closefds=()):
    if proto == 'ejabberd':
        from xclib.ejabberd_io import ejabberd_io
        xmpp = ejabberd_io
        if infd == outfd:
            infd = infd.makefile("rb")
            outfd = outfd.makefile("wb")
            closefds = closefds + (infd, outfd)
    elif proto == 'saslauthd':
        from xclib.saslauthd_io import saslauthd_io
        xmpp = saslauthd_io
        if infd == outfd:
            infd = infd.makefile("rb")
            outfd = outfd.makefile("wb")
            closefds = closefds + (infd, outfd)
    elif proto == 'postfix':
        from xclib.postfix_io import postfix_io
        xmpp = postfix_io
        if infd == outfd:
            infd = infd.makefile("r")
            outfd = outfd.makefile("w")
            closefds = closefds + (infd, outfd)
    else: # 'generic' or 'prosody'
        from xclib.prosody_io import prosody_io
        xmpp = prosody_io
        if infd == outfd:
            infd = infd.makefile("r")
            outfd = outfd.makefile("w")
            closefds = closefds + (infd, outfd)

    for data in xmpp.read_request(infd, outfd):
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

        xmpp.write_response(success, outfd)

    logging.debug('Closing connection')
    for c in closefds:
        c.close()
