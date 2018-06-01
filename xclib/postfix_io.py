# Only supports isuser request for Postfix virtual mailbox maps
import sys
import re
import logging

class postfix_io:
    @classmethod
    def read_request(cls):
        # "for line in sys.stdin:" would be more concise but adds unwanted buffering
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            match = re.match('^get ([^ @%]+)@([^ @%]+)\r?\n$', line)
            if match:
                yield ('isuser',) + match.group(1,2)
            else:
                logging.error('Illegal request format: ' + line)
                sys.stdout.write('500 Illegal request format\n')
                sys.stdout.flush()

    @classmethod
    def write_response(cls, flag):
        if flag == None:
            sys.stdout.write('400 Trouble connecting to backend\n')
        elif flag:
            sys.stdout.write('200 OK\n')
        else:
            sys.stdout.write('500 No such user\n')
        sys.stdout.flush()
