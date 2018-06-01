import sys
import unittest
from xclib.postfix_io import postfix_io
from xclib.tests.iostub import iostub

class TestPostfix(unittest.TestCase, iostub):

    def test_input(self):
        self.stub_stdin('get success@jsxc.ch\n' +
            'get succ2@jsxc.org\n')
        tester = iter(postfix_io.read_request())
        output = tester.next()
        assert output == ('isuser', 'success', 'jsxc.ch')
        output = tester.next()
        assert output == ('isuser', 'succ2', 'jsxc.org')
        try:
            output = tester.next()
            assert False # Should raise StopIteration
        except StopIteration:
            pass

    def test_input_ignore(self):
        self.stub_stdin('get success@jsxc.ch\n' +
            'get ignore@@jsxc.ch\n' +
            'get succ2@jsxc.org\n')
        self.stub_stdouts()
        tester = iter(postfix_io.read_request())
        output = tester.next()
        assert output == ('isuser', 'success', 'jsxc.ch')
        output = tester.next()
        self.assertEqual(sys.stdout.getvalue()[0:4], '500 ')
        assert output == ('isuser', 'succ2', 'jsxc.org')
        try:
            output = tester.next()
            assert False # Should raise StopIteration
        except StopIteration:
            pass

    def test_output_false(self):
        self.stub_stdout()
        postfix_io.write_response(False)
        self.assertEqual(sys.stdout.getvalue()[0:4], '500 ')

    def test_output_true(self):
        self.stub_stdout()
        postfix_io.write_response(True)
        self.assertEqual(sys.stdout.getvalue()[0:4], '200 ')

    def test_output_none(self):
        self.stub_stdout()
        postfix_io.write_response(None)
        self.assertEqual(sys.stdout.getvalue()[0:4], '400 ')
