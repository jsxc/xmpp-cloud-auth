import os
import unittest
from xclib.sockact import listen_fds_with_names

have_systemd = None

def systemd_present():
    global have_systemd
    if have_systemd is None:
        try:
            from systemd.daemon import listen_fds
            have_systemd = True
        except ImportError:
            have_systemd = False
    return have_systemd

@unittest.skipUnless(systemd_present(), 'systemd.daemon not available')
class TestSystemdAvailable(unittest.TestCase):
    def setUp(self):
        # Make sure the first three fds (after std???) are valid
        # during test executions
        self.placeholderfds = []
        for i in range(3):
            self.placeholderfds.append(open('/dev/null'))

    def test_listen_no_fds(self):
        os.unsetenv('LISTEN_FDS')
        os.unsetenv('LISTEN_PID')
        self.assertEqual(listen_fds_with_names(), None)

    def test_listen_1_fd_no_names(self):
        os.environ['LISTEN_FDS'] = '1'
        os.environ['LISTEN_PID'] = str(os.getpid())
        os.unsetenv('LISTEN_FDNAMES')
        self.assertEqual(listen_fds_with_names(),
            {3: 'unknown'})

    def test_listen_3_fds_no_names(self):
        os.environ['LISTEN_FDS'] = '3'
        os.environ['LISTEN_PID'] = str(os.getpid())
        os.unsetenv('LISTEN_FDNAMES')
        self.assertEqual(listen_fds_with_names(),
            {3: 'unknown', 4: 'unknown', 5: 'unknown'})

    def test_listen_3_fds_with_names(self):
        os.environ['LISTEN_FDS'] = '3'
        os.environ['LISTEN_PID'] = str(os.getpid())
        os.environ['LISTEN_FDNAMES'] = 'one:two:three'
        self.assertEqual(listen_fds_with_names(),
            {3: 'one', 4: 'two', 5: 'three'})

@unittest.skipIf(systemd_present(), 'systemd.daemon available')
class TestSystemdUnavailable(unittest.TestCase):
    def test_no_systemd_at_all(self):
        os.unsetenv('LISTEN_FDS')
        os.unsetenv('LISTEN_PID')
        self.assertEqual(listen_fds_with_names(), None)

    def test_no_systemd_module_only(self):
        os.environ['LISTEN_FDS'] = '5'
        os.environ['LISTEN_PID'] = str(os.getpid())
        with self.assertRaises(ImportError):
            listen_fds_with_names()
