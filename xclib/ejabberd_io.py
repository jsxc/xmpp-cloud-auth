import sys
import logging
from struct import pack, unpack

class ejabberd_io:
    @classmethod
    def read_request(cls):
        length_field = sys.stdin.read(2)
        while len(length_field) == 2:
            (size,) = unpack('>H', length_field)
            if size == 0:
               logging.info("command length 0, treating as logical EOF")
               return
            cmd = sys.stdin.read(size)
            if len(cmd) != size:
               logging.warn("premature EOF while reading cmd: %d != %d" % (len(cmd), size))
               return
            x = cmd.split(':', 3)
            yield x
            length_field = sys.stdin.read(2)

    @classmethod
    def write_response(cls, bool):
        answer = 0
        if bool:
            answer = 1
        token = pack('>HH', 2, answer)
        sys.stdout.write(token)
        sys.stdout.flush()

