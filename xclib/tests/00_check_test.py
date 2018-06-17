# Test whether our own assertEqual works as it should
from xclib.check import assertEqual, assertSimilar

def test_assert_equal_type_success():
    assertEqual(u'Hallo', u'Hallo')

def test_assert_equal_type_fail():
    try:
        assertEqual(b'Hallo', u'Hallo')
    except AssertionError:
        return
    raise AssertionError('Should have raised an exception')

def test_assert_equal_type_fail2():
    try:
        assertEqual(int(3), float(3))
    except AssertionError:
        return
    raise AssertionError('Should have raised an exception')

def test_assert_equal_value_fail():
    try:
        assertEqual(u'Hallo', u'Tschüss')
    except AssertionError:
        return
    raise AssertionError('Should have raised an exception')

def test_assert_similar_type_success():
    assertSimilar(u'Hallo', u'Hallo')

def test_assert_similar_type_mismatch():
    assertSimilar(int(3), float(3))

def test_assert_equal_value_fail():
    try:
        assertSimilar(int(3), float(4))
    except AssertionError:
        return
    raise AssertionError('Should have raised an exception')

