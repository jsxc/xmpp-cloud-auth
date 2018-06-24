import sys
import logging
from struct import pack, unpack
from xclib.utf8 import unutf8

# Message formats described in `../doc/Protocol.md`

class ejabberd_io:
    @classmethod
    def read_request(cls, infd, outfd):
        try:
            infd = infd.buffer
        except AttributeError:
            pass
        length_field = infd.read(2)
        while len(length_field) == 2:
            (size,) = unpack('>H', length_field)
            if size == 0:
               logging.info('command length 0, treating as logical EOF')
               return
            cmd = infd.read(size)
            if len(cmd) != size:
               logging.warn('premature EOF while reading cmd: %d != %d' % (len(cmd), size))
               return
            x = unutf8(cmd).split(':', 3)
            yield tuple(x)
            length_field = infd.read(2)

    @classmethod
    def write_response(cls, flag, outfd):
        try:
            outfd = outfd.buffer
        except AttributeError:
            pass
        answer = 0
        if flag:
            answer = 1
        token = pack('>HH', 2, answer)
        outfd.write(token)
        outfd.flush()

