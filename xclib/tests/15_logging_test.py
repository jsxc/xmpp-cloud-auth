import sys
import unittest
from xclib.tests.iostub import iostub
from xclib.configuration import get_args
from xclib.authops import perform

class TestLogging(unittest.TestCase, iostub):

    def permission_denied_test(self):
        self.stub_stdin('isuser:john.doe:example.com')
        self.stub_stdout()
        args = get_args(None, None, None, 'xcauth',
                args=('-l', '/etc',
                    '-t', 'generic',
                    '-u', 'https://localhost:58193/doesnotexist',
                    '-s', 'secret'))
        perform(args)
        output = sys.stdout.getvalue().rstrip('\n')
        self.assertEqual(output, '0')

    def file_not_found_test(self):
        self.stub_stdin('isuser:john.doe:example.com')
        self.stub_stdout()
        args = get_args(None, None, None, 'xcauth',
                args=('-l', '/non/ex/ist/ant',
                    '-t', 'generic',
                    '-u', 'https://localhost:58193/doesnotexist',
                    '-s', 'secret'))
        perform(args)
        output = sys.stdout.getvalue().rstrip('\n')
        self.assertEqual(output, '0')
