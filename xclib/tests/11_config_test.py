# Test whether the configuration parser works as it should
import sys
import unittest
from xclib.tests.iostub import iostub
from xclib.configuration import get_args

def setup_module():
    global arg_save
    arg_save = sys.argv
    sys.argv = [arg_save[0]]

def teardown_module():
    sys.argv = arg_save

class TestConfiguration(unittest.TestCase, iostub):

    def test_xcauth(self):
        args = get_args('/var/log/xcauth', None, None, 'xcauth',
            config_file_contents='#',
            args=['-b', '/tmp/domdb.db',
                  '--secret', '012345678',
                  '--url', 'https://unconfigured.example.ch',
                  '--type', 'generic',
                  '--timeout', '5',
                  '--cache-unreachable-ttl', '1w',
                  '--cache-query-ttl', '3600'])
        print(args.timeout)
        self.assertEqual(args.timeout, 5)

    def test_xcauth_timeout(self):
        args = get_args('/var/log/xcauth', None, None, 'xcauth',
            config_file_contents='#',
            args=['-b', '/tmp/domdb.db',
                  '--secret', '012345678',
                  '--url', 'https://unconfigured.example.ch',
                  '--type', 'generic',
                  '--timeout', '1,2',
                  '--cache-unreachable-ttl', '1w',
                  '--cache-query-ttl', '3600'])
        print(args.timeout)
        self.assertEqual(args.timeout, (1, 2))

    def test_xcauth_crash_timeout(self):
        self.stub_stdouts()
        self.assertRaises(ValueError, get_args, 
                '/var/log/xcauth', None, None, 'xcauth',
                config_file_contents='#',
                args=['-b', '/tmp/domdb.db',
                      '--secret', '012345678',
                      '--ejabberdctl', '012345678',
                      '--url', 'https://unconfigured.example.ch',
                      '--type', 'generic',
                      '--timeout', '1,2,3',
                      '--cache-unreachable-ttl', '1w',
                      '--cache-query-ttl', '3600'])

    def test_xcauth_exit_a(self):
        self.stub_stdouts()
        self.assertRaises(SystemExit, get_args,
                '/var/log/xcauth', None, None, 'xcauth',
                config_file_contents='#',
                args=['-b', '/tmp/domdb.db',
                      '--secret', '012345678',
                      '--ejabberdctl', '012345678',
                      '--url', 'https://unconfigured.example.ch',
                      '--type', 'generic',
                      '--cache-unreachable-ttl', '1w',
                      '--cache-query-ttl', '3600'])

    def test_xcauth_exit_b(self):
        self.stub_stdouts()
        self.assertRaises(SystemExit, get_args,
                '/var/log/xcauth', None, None, 'xcauth',
                config_file_contents='#',
                args=['-b', '/tmp/domdb.db',
                      '--secret', '012345678',
                      '--url', 'https://unconfigured.example.ch',
                      '--cache-query-ttl', '3600'])

    def test_xcdbm(self):
        args = get_args('/var/log/xcauth', None, None, 'xcdbm',
            config_file_contents='#',
            args=['-b', '/tmp/domdb.db',
                  '--secret', '012345678',
                  '--url', 'https://unconfigured.example.ch',
                  '--unload'])
