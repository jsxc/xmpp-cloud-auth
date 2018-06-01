import sys
import requests
import unittest
import logging
import shutil
import tempfile
import json
from xclib.sigcloud import sigcloud
from xclib import xcauth
from xclib.tests.iostub import iostub
from xclib.configuration import get_args
from xclib.authops import perform

def setup_module():
    global dirname
    dirname = tempfile.mkdtemp()

def teardown_module():
    shutil.rmtree(dirname)

class TestOnline(unittest.TestCase, iostub):
    # Run this (connection-error) online test even when /etc/xcauth.accounts does not exist
    def test_postfix_connection_error(self):
        self.stub_stdin('get user@example.org\n')
        self.stub_stdout()
        args = get_args(None, None, None, 'xcauth',
           args=['-t', 'postfix', '-u', 'https://no-connection.jsxc.org/', '-s', '0', '-l', dirname],
           config_file_contents='#')
        perform(args)
        output = sys.stdout.getvalue().rstrip('\n')
        logging.debug(output)
        assert output[0:4] == '400 '
