# Check whether calling `ejabberdctl` would work
# Uses `echo`, `true`, and `false` as external programs;
# thus does not require in installation of *ejabberd*
from xclib.ejabberdctl import ejabberdctl
from xclib import xcauth
from xclib.check import assertEqual

def test_echo():
    xc = xcauth(ejabberdctl='/bin/echo')
    e = ejabberdctl(xc)
    assertEqual(e.execute(['Hello', 'world']), 'Hello world\n')

def test_true():
    xc = xcauth(ejabberdctl='/bin/true')
    e = ejabberdctl(xc)
    assertEqual(e.execute(['Hello', 'world']), '')

def test_false():
    xc = xcauth(ejabberdctl='/bin/false')
    e = ejabberdctl(xc)
    assertEqual(e.execute(['Hello', 'world']), None)
