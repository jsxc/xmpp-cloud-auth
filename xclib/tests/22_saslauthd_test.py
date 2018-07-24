# Checks that saslauthd_io works as it should
import sys
import io
import unittest
from xclib.saslauthd_io import saslauthd_io
from xclib.tests.iostub import iostub
class TestSaslAuthD(unittest.TestCase, iostub):

    def test_input(self):
        self.stub_stdin(b'\000\005login\000\004pass\000\000\000\006domain' +
                        b'\000\005login\000\004pass\000\006ignore\000\006domain',
                        ioclass=io.BytesIO)
        tester = iter(saslauthd_io.read_request(sys.stdin, sys.stdout))
        output = next(tester)
        self.assertEqual(output, ('auth', 'login', 'domain', 'pass'))
        output = next(tester)
        self.assertEqual(output, ('auth', 'login', 'domain', 'pass'))
        self.assertRaises(StopIteration, next, tester)

    def test_input_short(self):
        self.stub_stdin(b'\001\005login\000\004pass\000\000\000\006domain',
                        ioclass=io.BytesIO)
        tester = iter(saslauthd_io.read_request(sys.stdin, sys.stdout))
        self.assertRaises(StopIteration, next, tester)

    def test_output_false(self):
        self.stub_stdout(ioclass=io.BytesIO)
        saslauthd_io.write_response(False, sys.stdout)
        v = sys.stdout.getvalue()
        self.assertEqual(sys.stdout.getvalue(), b'\000\040NO xcauth authentication failure')

    # Cannot be merged, as getvalue() returns the aggregate value
    def test_output_true(self):
        self.stub_stdout(ioclass=io.BytesIO)
        saslauthd_io.write_response(True, sys.stdout)
        self.assertEqual(sys.stdout.getvalue(), b'\000\012OK success')
