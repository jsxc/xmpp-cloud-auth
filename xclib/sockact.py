# systemd.daemon listen_fds_with_names() compatibility/abstraction library
# for socket activation
import os
import logging

def listen_fds_with_names():
    try:
        from systemd.daemon import listen_fds_with_names
        # We have the real McCoy
        return listen_fds_with_names()
    except ImportError:
        pass
    try:
        # Try to fall back to listen_fds(),
        # possbily emulating listen_fds_with_names() here
        from systemd.daemon import listen_fds
        fds = listen_fds()
        if fds:
            listeners = {}
            fdnames = os.getenv('LISTEN_FDNAMES')
            if fdnames:
                # Evil hack, should not be here!
                # Is here only because it seems unlikely
                # https://github.com/systemd/python-systemd/pull/60
                # will be merged and distributed anyting soon ;-(.
                # Diverges from original if not enough fdnames are provided
                # (but this should not happen anyway).
                names = fdnames.split(':')
            else:
                names = ()
            for i in range(0, len(fds)):
                if i < len(names):
                    listeners[fds[i]] = names[i]
                else:
                    listeners[fds[i]] = 'unknown'
            return listeners
        else:
            return None
    except ImportError:
        # No systemd.daemon found; try to fail appropriately:
        # - If $LISTEN_FDS is set, then insist on having systemd.daemon
        # - Else be lenient and remain compatible with pre-systemd users
        if os.getenv('LISTEN_FDS'):
            raise
        else:
            logging.info('Please `apt install python3-systemd` for future compatibility')
    return None
