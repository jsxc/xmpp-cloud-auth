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
