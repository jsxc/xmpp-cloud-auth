import sys

# Message formats described in `../doc/Protocol.md`

class prosody_io:
    @classmethod
    def read_request(cls, infd, outfd):
        # "for line in sys.stdin:" would be more concise but adds unwanted buffering
        while True:
            line = infd.readline()
            if not line:
                break
            line = line.rstrip("\r\n")
            yield tuple(line.split(':', 3))

    @classmethod
    def write_response(cls, flag, outfd):
        if isinstance(flag, str):
            # Hack for interactive 'roster' command used by tests/online_test.py
            answer = flag
        else:
            answer = '0'
            if flag:
                answer = '1'
        outfd.write(answer+"\n")
        outfd.flush()
