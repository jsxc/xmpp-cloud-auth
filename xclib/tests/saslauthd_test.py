import sys
import io
import unittest
from xclib.saslauthd_io import saslauthd_io
from xclib.tests.iostub import iostub

class TestSaslAuthD(unittest.TestCase, iostub):

    def test_input(self):
        self.stub_stdin('\000\005login\000\004pass\000\000\000\006domain' +
                        '\000\005login\000\004pass\000\006ignore\000\006domain')
        tester = iter(saslauthd_io.read_request())
        output = tester.next()
        assert output == ('auth', 'login', 'domain', 'pass')
        output = tester.next()
        assert output == ('auth', 'login', 'domain', 'pass')
        try:
            output = tester.next()
            assert False # Should raise StopIteration
        except StopIteration:
            pass

    def test_input_short(self):
        self.stub_stdin('\001\005login\000\004pass\000\000\000\006domain')
        tester = iter(saslauthd_io.read_request())
        try:
            output = tester.next()
            assert False # Should raise StopIteration
        except StopIteration:
            pass

    def test_output_false(self):
        self.stub_stdout()
        saslauthd_io.write_response(False)
        v = sys.stdout.getvalue()
        self.assertEqual(sys.stdout.getvalue(), '\000\040NO xcauth authentication failure')

    # Cannot be merged, as getvalue() returns the aggregate value
    def test_output_true(self):
        self.stub_stdout()
        saslauthd_io.write_response(True)
        self.assertEqual(sys.stdout.getvalue(), '\000\012OK success')
