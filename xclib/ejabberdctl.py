import logging
import subprocess
from xclib.utf8 import unutf8

class ejabberdctl:
    def __init__(self, ctx):
        self.ctx = ctx

    def execute(self, args):
        logging.debug(self.ctx.ejabberdctl_path + str(args))
        try:
            return unutf8(subprocess.check_output([self.ctx.ejabberdctl_path] + args))
        except subprocess.CalledProcessError as err:
            return None
            logging.warn('ejabberdctl failed with %s'
                % str(err))
            return None

    def members(self, group, domain):
        membership = self.execute(['srg_get_members', group, domain])
        if membership is None:
            membership = ()
        else:
            membership = membership.split('\n')
        # Delete empty values (e.g. from empty output)
        mem = []
        for m in membership:
            if m != '':
                mem.append(m)
        logging.debug('%s@%s members: %s' % (group, domain, mem))
        return mem
