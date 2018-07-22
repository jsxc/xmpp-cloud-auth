# systemd.daemon listen_fds_with_names() compatibility/abstraction library
# for socket activation
import os
import logging

def listen_fds_with_names():
    try:
        from systemd.daemon import listen_fds_with_names
        # We have the real McCoy
        return listen_fds_with_names()
    except ModuleNotFoundError: # Inherits from ImportError, needs thus to be first
        # Not yet there in Python 3.5
        # No systemd.daemon found; try to fail appropriately:
        # - If $LISTEN_FDS is set, then insist on having systemd.daemon
        # - Else be lenient and remain compatible with pre-systemd users
        if os.path.exists('/run/systemd/system') and 'LISTEN_FDS' in os.environ:
            logging.error('Software from https://github.com/systemd/python-systemd/ missing; do `apt install python3-systemd` or `pip3 install systemd-python` (please note the similarly-named `pip3 install python-systemd` does not provide the interfaces needed)')
            raise
        else:
            logging.info('Please `apt install python3-systemd` for future compatibility')
    except ImportError:
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
