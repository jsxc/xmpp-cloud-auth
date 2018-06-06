import logging

def assertSimilar(a, b):
    if a != b:
        raise AssertionError('Assertion failed: Value mismatch: %r (%s) != %r (%s)' % (a, type(a), b, type(b)))

def assertEqual(a, b):
    if type(a) == type(b):
        assertSimilar(a, b)
    else:
        raise AssertionError('Assertion failed: Type mismatch %r (%s) != %r (%s)' % (a, type(a), b, type(b)))
