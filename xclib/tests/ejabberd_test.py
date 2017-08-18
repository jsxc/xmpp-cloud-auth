import sys
import io
import unittest
from xclib.ejabberd_io import ejabberd_io
from xclib.tests.iostub import iostub

class TestEjabberd(unittest.TestCase, iostub):

  def test_input(self):
    self.stub_stdin('\000\015isuser:login:' +
      '\000\021auth:log:dom:pass')
    tester = iter(ejabberd_io.read_request())
    output = tester.next()
    assert output == ('isuser', 'login', '')
    output = tester.next()
    assert output == ('auth', 'log', 'dom', 'pass')
    try:
      output = tester.next()
      assert False # Should raise StopIteration
    except StopIteration:
      pass

  def test_input_fake_eof(self):
    self.stub_stdin('\000\000')
    tester = iter(ejabberd_io.read_request())
    try:
      output = tester.next()
      assert False # Should raise StopIteration
    except StopIteration:
      pass

  def test_input_short(self):
    self.stub_stdin('\001\000')
    tester = iter(ejabberd_io.read_request())
    try:
      output = tester.next()
      assert False # Should raise StopIteration
    except StopIteration:
      pass

  def test_input_negative(self):
    self.stub_stdin('\377\377')
    tester = iter(ejabberd_io.read_request())
    try:
      output = tester.next()
      assert False # Should raise StopIteration
    except StopIteration:
      pass

  def test_output_false(self):
    self.stub_stdout()
    ejabberd_io.write_response(False)
    self.assertEqual(sys.stdout.getvalue(), '\000\002\000\000')

  # Cannot be merged, as getvalue() returns the aggregate value
  def test_output_true(self):
    self.stub_stdout()
    ejabberd_io.write_response(True)
    self.assertEqual(sys.stdout.getvalue(), '\000\002\000\001')
