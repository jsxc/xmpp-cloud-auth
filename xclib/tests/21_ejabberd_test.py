# Checks that ejabberd_io works as designed
import sys
import io
import unittest
from xclib.ejabberd_io import ejabberd_io
from xclib.tests.iostub import iostub

class TestEjabberd(unittest.TestCase, iostub):

    def test_input(self):
        self.stub_stdin(b'\000\015isuser:login:' +
            b'\000\021auth:log:dom:pass', ioclass=io.BytesIO)
        tester = iter(ejabberd_io.read_request())
        output = next(tester)
        self.assertEqual(output, ('isuser', 'login', ''))
        output = next(tester)
        self.assertEqual(output, ('auth', 'log', 'dom', 'pass'))
        self.assertRaises(StopIteration, next, tester)

    def test_input_fake_eof(self):
        self.stub_stdin(b'\000\000', ioclass=io.BytesIO)
        tester = iter(ejabberd_io.read_request())
        self.assertRaises(StopIteration, next, tester)

    def test_input_short(self):
        self.stub_stdin(b'\001\000', ioclass=io.BytesIO)
        tester = iter(ejabberd_io.read_request())
        self.assertRaises(StopIteration, next, tester)

    def test_input_negative(self):
        self.stub_stdin(b'\377\377', ioclass=io.BytesIO)
        tester = iter(ejabberd_io.read_request())
        self.assertRaises(StopIteration, next, tester)

    def test_output_false(self):
        self.stub_stdout(ioclass=io.BytesIO)
        ejabberd_io.write_response(False)
        self.assertEqual(sys.stdout.getvalue(), b'\000\002\000\000')

    # Cannot be merged, as getvalue() returns the aggregate value
    def test_output_true(self):
        self.stub_stdout(ioclass=io.BytesIO)
        ejabberd_io.write_response(True)
        self.assertEqual(sys.stdout.getvalue(), b'\000\002\000\001')
