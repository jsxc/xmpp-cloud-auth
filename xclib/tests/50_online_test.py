# Performs the online auth(), isuser(), and roster() functions
# if `/etc/xcauth.accounts` exists and the machine is online.
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
    # Skip online tests if /etc/xcauth.accounts does not exist
    # The overall operation is modeled after ../../tests/run-online.pl
    def test_online(self):
        has_run = []
        try:
            file = open('/etc/xcauth.accounts', 'r');
        except IOError:
            return
        u = None
        d = None
        p = None
        for line in file:
            line = line.rstrip('\r\n')
            fields = line.split('\t', 2)
            if fields[0] == '':
                # Line with test command
                if fields[1] == 'isuser':
                    option = '-I'
                    params = [u, d]
                elif fields[1] == 'roster':
                    option = '-R'
                    params = [u, d]
                elif fields[1] == 'auth':
                    option = '-A'
                    params = [u, d, p]
                else:
                    raise ValueError('Invalid /etc/xcauth.accounts command %s' % fields[1])
                # To get maximum coverage with minimum duplicate requests:
                # The first time, use command line; afterward, use -t generic
                if fields[1] in has_run:
                    self.generic_io([fields[1]] + params, fields[2])
                else:
                    # Test some more options on the first run
                    if len(has_run) == 0:
                        params += ['-b', dirname + '/domain.db',
                            '-l', dirname,
                            '--cache-db', dirname + '/cache.db',
                            '--shared-roster-db', dirname + '/roster.db',
                            '--ejabberdctl', '/bin/true']
                    self.command_line([option] + params, fields[2])
                    has_run += [fields[1]]
            else:
                # Line with account values
                (u, d, p) = fields
        file.close()

    def command_line(self, options, expected):
        logging.info('command_line ' + str(options) + ' =? ' + expected)
        self.stub_stdout()
        args = get_args(None, None, None, 'xcauth', args=options)
        perform(args)
        output = sys.stdout.getvalue().rstrip('\n')
        self.assertEqual(output, expected)

    def generic_io(self, command, expected):
        logging.info('generic_io ' + str(command) + ' =? ' + expected)
        self.stub_stdin(':'.join(command) + '\n')
        self.stub_stdout()
        args = get_args(None, None, None, 'xcauth', args=['-t', 'generic'])
        perform(args)
        output = sys.stdout.getvalue().rstrip('\n')
        logging.debug(output)
        logging.debug(expected)
        if output == '0' or output == 'None':
            assert str(expected) == 'False' or str(expected), 'None'
        elif output == '1':
            self.assertEqual(str(expected), 'True')
        else:
            # Only "roster" command will get here.
            # Convert both strs to dicts to avoid
            # problems with formatting (whitespace) and order.
            output = json.loads(output)
            expected = json.loads(expected)
            self.assertEqual(output, expected)
