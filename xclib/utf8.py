import logging
import sys
import traceback

def utf8(u, opts='strict'):
    return u.encode('utf-8', opts)

def unutf8(u, opts='strict'):
    if opts == 'illegal':
        try:
            return u.decode('utf-8', 'strict')
        except UnicodeError:
            dec = u.decode('utf-8', 'ignore')
            logging.error('Illegal UTF-8 sequence: %r' % dec)
            sys.stderr.write('Illegal UTF-8 sequence: %r\n' % dec)
            traceback.print_exc()
            return 'illegal-utf8-sequence-' + dec
    else:
        try:
            return u.decode('utf-8', opts)
        except AttributeError:
            pass
        
def utf8l(l):
    '''Encode a copy of the list, converted to UTF-8'''
    return list(map(utf8, l))
