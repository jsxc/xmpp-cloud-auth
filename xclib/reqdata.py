class reqdata:
    def __init__(self, ctx, username, domain, password=None):
        self.ctx = ctx
        self.username = username
        self.domain = domain
        self.password = password
        self.secret, self.url, self.queryDomain = ctx.per_domain(domain)
