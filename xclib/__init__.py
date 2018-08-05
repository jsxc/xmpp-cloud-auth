import logging
import sys
import requests
from argparse import Namespace
from xclib.sigcloud import sigcloud
import xclib.isuser
from xclib.utf8 import utf8, unutf8
from xclib.db import connection

def verify_with_isuser(url, secret, domain, user, timeout, hook=None):
    xc = xcauth(default_url=url, default_secret=secret, timeout=timeout)
    sc = sigcloud(xc, user, domain)
    if hook != None: hook(sc) # For automated testing only
    return sc.isuser_verbose()

class xcauth:
    def __init__(self, default_url=None, default_secret=None,
                ejabberdctl=None,
                sql_db=None, cache_storage='none',
                domain_db = None, cache_db = None, shared_roster_db = None,
                ttls={'query': 3600, 'verify': 86400, 'unreach': 7*86400},
                bcrypt_rounds=12, timeout=5):
        '''Argument notes:
- `sql_db`: Path to SQLite3 db or ':memory:' (`None` is ':memory:')
- `cache_storage`: Whether cache is disabled ('none'),
  is in-memory ('memory'),
  or in the `sql_db` above ('db', i.e., generally persistent)
- `[domain|cache|shared_roster]_db`: Legacy database for imports into `sql_db`
  (`None`, `str` (path to bsddb3), or a `dict`
'''
        self.default_url=default_url
        self.default_secret=default_secret
        self.ejabberdctl_path=ejabberdctl
        self.ttls=ttls
        self.timeout=timeout
        self.bcrypt_rounds=bcrypt_rounds
        self.session=requests.Session()
        h = {'db': sql_db or ':memory:',
            'domain_db': domain_db,
            'cache_db': cache_db,
            'shared_roster_db': shared_roster_db,
            'cache_storage': cache_storage}
        self.db = connection(Namespace(**h))

    def per_domain(self, dom):
        for row in self.db.conn.execute('SELECT authsecret, authurl, authdomain FROM domains WHERE xmppdomain = ?', (dom,)):
            return utf8(row[0]), row[1], row[2]
        return utf8(self.default_secret), self.default_url, dom
