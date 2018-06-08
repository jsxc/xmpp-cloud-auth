import sys
import logging
from struct import pack, unpack
from xclib.utf8 import unutf8

class ejabberd_io:
    @classmethod
    def read_request(cls):
        length_field = sys.stdin.buffer.read(2)
        while len(length_field) == 2:
            (size,) = unpack('>H', length_field)
            if size == 0:
               logging.info('command length 0, treating as logical EOF')
               return
            cmd = sys.stdin.buffer.read(size)
            if len(cmd) != size:
               logging.warn('premature EOF while reading cmd: %d != %d' % (len(cmd), size))
               return
            x = unutf8(cmd).split(':', 3)
            yield tuple(x)
            length_field = sys.stdin.buffer.read(2)

    @classmethod
    def write_response(cls, flag):
        answer = 0
        if flag:
            answer = 1
        token = pack('>HH', 2, answer)
        sys.stdout.buffer.write(token)
        sys.stdout.flush()

