# Checks that postfix_io (tcp_table) works as it should
import sys
import unittest
from xclib.postfix_io import postfix_io
from xclib.tests.iostub import iostub

class TestPostfix(unittest.TestCase, iostub):

    def test_input(self):
        self.stub_stdin('get success@jsxc.ch\n' +
            'get succ2@jsxc.org\n')
        tester = iter(postfix_io.read_request(sys.stdin, sys.stdout))
        output = next(tester)
        self.assertEqual(output, ('isuser', 'success', 'jsxc.ch'))
        output = next(tester)
        self.assertEqual(output, ('isuser', 'succ2', 'jsxc.org'))
        self.assertRaises(StopIteration, next, tester)

    def test_input_ignore(self):
        self.stub_stdin('get success@jsxc.ch\n' +
            'get ignore@@jsxc.ch\n' +
            'get succ2@jsxc.org\n')
        self.stub_stdouts()
        tester = iter(postfix_io.read_request(sys.stdin, sys.stdout))
        output = next(tester)
        self.assertEqual(output, ('isuser', 'success', 'jsxc.ch'))
        output = next(tester)
        self.assertEqual(sys.stdout.getvalue()[0:4], '500 ')
        self.assertEqual(output, ('isuser', 'succ2', 'jsxc.org'))
        self.assertRaises(StopIteration, next, tester)

    def test_output_false(self):
        self.stub_stdout()
        postfix_io.write_response(False, sys.stdout)
        self.assertEqual(sys.stdout.getvalue()[0:4], '500 ')

    def test_output_true(self):
        self.stub_stdout()
        postfix_io.write_response(True, sys.stdout)
        self.assertEqual(sys.stdout.getvalue()[0:4], '200 ')

    def test_output_none(self):
        self.stub_stdout()
        postfix_io.write_response(None, sys.stdout)
        self.assertEqual(sys.stdout.getvalue()[0:4], '400 ')
