import sys

# Message formats described in `../doc/Protocol.md`

class prosody_io:
    @classmethod
    def read_request(cls):
        # "for line in sys.stdin:" would be more concise but adds unwanted buffering
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.rstrip("\r\n")
            yield tuple(line.split(':', 3))

    @classmethod
    def write_response(cls, flag):
        if isinstance(flag, str):
            # Hack for interactive 'roster' command used by tests/online_test.py
            answer = flag
        else:
            answer = '0'
            if flag:
                answer = '1'
        sys.stdout.write(answer+"\n")
        sys.stdout.flush()
