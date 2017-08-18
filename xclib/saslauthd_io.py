import sys
import logging
from struct import pack, unpack

class saslauthd_io:
    @classmethod
    def read_request(cls):
        field_no = 0
        fields = [None, None, None, None]
        length_field = sys.stdin.read(2)
        while len(length_field) == 2:
            (size,) = unpack('>H', length_field)
            val = sys.stdin.read(size)
            if len(val) != size:
               logging.warn('premature EOF while reading field %d: %d != %d' % (field_no, len(val), size))
               return
            fields[field_no] = val
            field_no = (field_no + 1) % 4
            if field_no == 0:
                logging.debug('from_saslauthd got %s, %s, %s, %s' % tuple(fields))
                yield ('auth', fields[0], fields[3], fields[1])
            length_field = sys.stdin.read(2)

    @classmethod
    def write_response(cls, bool):
        answer = 'NO xcauth authentication failure'
        if bool:
            answer = 'OK success'
        token = pack('>H', len(answer)) + answer
        sys.stdout.write(token)
        sys.stdout.flush()
