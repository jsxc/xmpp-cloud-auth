from xclib.utf8 import utf8, unutf8, utf8l
from xclib.check import assertEqual

def test_utf8_ascii():
    assertEqual(b'hallo', utf8(u'hallo'))

def test_utf8_valid():
    assertEqual(b'Hall\xc3\xb6chen', utf8(u'Hallöchen'))

def test_unutf8_ascii():
    assertEqual(unutf8(b'Hallo'), u'Hallo')

def test_unutf8_valid():
    assertEqual(unutf8(b'Hall\xc3\xb6chen'), u'Hallöchen')

def test_unutf8_invalid_ignore():
    assertEqual(unutf8(b'Hall\xffchen', 'ignore'), u'Hallchen')

def test_unutf8_invalid_ignore2():
    assertEqual(unutf8(b'Hall\x80\x80chen', 'ignore'), u'Hallchen')

def test_unutf8_invalid_ignore3():
    assertEqual(unutf8(b'Hall\x80chen', 'ignore'), u'Hallchen')

def test_unutf8_invalid_strict():
    try:
        assertEqual(unutf8(b'Hall\x80chen', 'strict'), u'Hallchen')
    except UnicodeError:
        return
    raise AssertionError('Illegal UTF-8 sequence accepted under "strict"')

def test_unutf8_invalid_illegal():
    assertEqual(unutf8(b'Hall\x80chen', 'illegal'), u'illegal-utf8-sequence-Hallchen')

def test_utf8l_match():
    assertEqual([b'b', b'\xc3\xb6', b's', b'e'], utf8l(['b', 'ö', 's', 'e']))
