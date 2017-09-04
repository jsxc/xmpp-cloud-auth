from xclib.ejabberdctl import ejabberdctl
from xclib import xcauth

def test_echo():
    xc = xcauth(ejabberdctl='/bin/echo')
    e = ejabberdctl(xc)
    assert e.execute(['Hello', 'world']) == 'Hello world\n'

def test_true():
    xc = xcauth(ejabberdctl='/bin/true')
    e = ejabberdctl(xc)
    assert e.execute(['Hello', 'world']) == ''

def test_false():
    xc = xcauth(ejabberdctl='/bin/false')
    e = ejabberdctl(xc)
    assert e.execute(['Hello', 'world']) == None
