# Only supports isuser request for Postfix virtual mailbox maps
import sys
import re
import logging

# Message formats described in `../doc/Protocol.md`

class postfix_io:
    @classmethod
    def read_request(cls, infd, outfd):
        # "for line in sys.stdin:" would be more concise but adds unwanted buffering
        while True:
            line = infd.readline()
            if not line:
                break
            match = re.match('^get ([^\000- @%]+)@([^\000- @%]+)\r?\n$', line)
            if match:
                yield ('isuser',) + match.group(1,2)
            else:
                logging.error('Illegal request format: ' + line)
                outfd.write('500 Illegal request format\n')
                outfd.flush()

    @classmethod
    def write_response(cls, flag, outfd):
        if flag == None:
            outfd.write('400 Trouble connecting to backend\n')
        elif flag:
            outfd.write('200 OK\n')
        else:
            outfd.write('500 No such user\n')
        outfd.flush()
