# Checks that prosody_io works as designed
import sys
import unittest
from xclib.prosody_io import prosody_io
from xclib.tests.iostub import iostub
from xclib.check import assertEqual

class TestProsody(unittest.TestCase, iostub):

    def test_input(self):
        self.stub_stdin('isuser:login:\n' +
            'auth:log:dom:pass\n')
        tester = iter(prosody_io.read_request(sys.stdin, sys.stdout))
        output = next(tester)
        assertEqual(output, ('isuser', 'login', ''))
        output = next(tester)
        assertEqual(output, ('auth', 'log', 'dom', 'pass'))
        self.assertRaises(StopIteration, next, tester)

    def test_output_false(self):
        self.stub_stdout()
        prosody_io.write_response(False, sys.stdout)
        self.assertEqual(sys.stdout.getvalue(), '0\n')

    # Cannot be merged, as getvalue() returns the aggregate value
    def test_output_true(self):
        self.stub_stdout()
        prosody_io.write_response(True, sys.stdout)
        self.assertEqual(sys.stdout.getvalue(), '1\n')
