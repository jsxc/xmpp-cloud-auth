import sys
import io
import unittest
from xclib.prosody_io import prosody_io
from xclib.tests.iostub import iostub

class TestProsody(unittest.TestCase, iostub):

    def test_input(self):
        self.stub_stdin('isuser:login:\n' +
            'auth:log:dom:pass\n')
        tester = iter(prosody_io.read_request())
        output = tester.next()
        assert output == ('isuser', 'login', '')
        output = tester.next()
        assert output == ('auth', 'log', 'dom', 'pass')
        try:
            output = tester.next()
            assert False # Should raise StopIteration
        except StopIteration:
            pass

    def test_output_false(self):
        self.stub_stdout()
        prosody_io.write_response(False)
        self.assertEqual(sys.stdout.getvalue(), '0\n')

    # Cannot be merged, as getvalue() returns the aggregate value
    def test_output_true(self):
        self.stub_stdout()
        prosody_io.write_response(True)
        self.assertEqual(sys.stdout.getvalue(), '1\n')
