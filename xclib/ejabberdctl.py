import subprocess

class ejabberdctl:
    def __init__(self, ctx):
        self.ctx = ctx

    def execute(args):
        logging.debug(self.ctx.ejabberdctl_path + str(args))
        try:
            return subprocess.check_output([self.ctx.ejabberdctl_path] + args)
        except subprocess.CalledProcessError, err:
            logging.warn('ejabberdctl %s failed with %s'
                % (self.ctx.ejabberdctl_path + str(args), str(err)))
            return None

    def ejabberdctl_set_fn(self, user, domain, name):
        fullname = self.execute(['get_vcard', user, domain, 'FN'])
        # 'error_no_vcard' is exitcode 1 is None
        if (fullname is None or fullname == '' or fullname == '\n'
            or fullname == user + '\n' or fullname == ('%s@%s\n' % (user, domain))):
            self.execute(['set_vcard', user, domain, 'FN', name])

    def members(self, group, domain):
        membership = self.execute(['srg_get_members', group, domain]).split('\n')
        # Delete empty values (e.g. from empty output)
        mem = []
        for m in membership:
            if m != '':
                mem = mem + [m]
        return mem

