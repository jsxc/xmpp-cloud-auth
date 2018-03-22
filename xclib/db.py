import sqlite3


class connection:
    def __init__(self, paths):
        self.paths = paths

    def __enter__(self):
        self.conn = sqlite3.connect(self.paths.db)
        # Add bound method execute_check to this instance
        self.conn.execute_check = self.execute_check.__get__(self)
        return self.conn

    def __exit__(self):
        self.conn.close()

    def execute_check(self, *args, **kwargs):
        '''If the schema is not yet there, create it and fill the database first'''
        try:
            self.conn.execute(*args, **kwargs)
        except sqlite3.OperationalError, e:
            # Convert and try again
            self.db_upgrade()
            self.conn.execute(*args, **kwargs)

    def db_upgrade(self):
        self.db_upgrade_domain()
        self.db_upgrade_cache()
        self.db_upgrade_roster()

    def db_upgrade_domain():
        self.conn.execute('''CREATE TABLE domains (xmppdomain TEXT PRIMARY KEY,
                      authsecret TEXT,
                      authurl    TEXT,
                      authdomain TEXT,
                      regcontact TEXT,
                      regfirst   TEXT DEFAULT datetime('now'),
                      reglatest  TEXT DEFAULT datetime('now'))''')
        self.conn.execute('BEGIN TRANSACTION')
        try:
            db = anydbm.open(self.paths.domain_db, 'r')
            for k,v in db.iteritems():
                (authsecret, authurl, authdomain, extra) = v.split("\t", 3)
                self.conn.execute('''INSERT INTO domains (xmppdomain, authsecret, authurl, authdomain)
                     VALUES (?, ?, ?, ?)''', (k, authsecret, authurl, authdomain))
            db.close()
        except anydbm.error, e:
            pass
        self.conn.execute('COMMIT')

    def db_upgrade_cache():
        self.conn.execute('''CREATE TABLE authcache (jid        TEXT PRIMARY KEY,
                        pwhash     TEXT,
                        firstauth  TEXT DEFAULT datetime('now'),
                        anyauth    TEXT DEFAULT datetime('now'),
                        remoteauth TEXT DEFAULT datetime('now'))''')
        self.conn.execute('BEGIN TRANSACTION')
        try:
            db = anydbm.open(self.paths.cache_db, 'r')
            for k,v in db.iteritems():
                (pwhash, ts1, tsv, tsa, rest) = v.split("\t", 4)
                self.conn.execute('''INSERT INTO authcache (jid, pwhash, firstauth, anyauth, remoteauth)
                     VALUES (?, ?, ?, ?, ?)''', (k, pwhash, ts1, tsv, tsa))
            db.close()
        except anydbm.error, e:
            pass
        self.conn.execute('COMMIT')

    def db_upgrade_roster():
        self.conn.execute('''CREATE TABLE rosterinfo   (jid          TEXT PRIMARY KEY,
                           fullname     TEXT,
                           grouplist    TEXT,
                           responsehash TEXT)''')
        self.conn.execute('''CREATE TABLE rostergroups (groupname    TEXT PRIMARY KEY,
                           userlist     TEXT)''')
        rosterinfo_fn = {}
        rosterinfo_rh = {}
        rosterinfo_lg = {}
        rosterinfo_rg = {}
        rosterusers = set([])
        rostergroups = {}
        try:
            db = anydbm.open(self.paths.cache_db, 'r')
            for k,v in db.iteritems():
                if k[:4] == 'FNC:': # Full name (cache only)
                    jid = k[4:].replace(':', '@')
                    rosterusers = rosterusers + jid
                    if '@' in jid: # Do not copy malformed (old buggy) entries
                        rosterinfo_fn[jid] = v
                if k[:4] == 'LIG:': # Login In Group (state information)
                    jid = k[4:].replace(':', '@')
                    rosterusers = rosterusers + jid
                    rosterinfo_lg[jid] = v
                if k[:4] == 'RGC:': # Reverse Group Cache (state information)
                    gid = k[4:]
                    rosterinfo_rg[gid] = v
                elif k[:3] == 'RH:': # Response body hash (cache only)
                    jid = k[3:].replace(':', '@')
                    rosterusers = rosterusers + jid
                    rosterinfo_rc[jid] = v
            db.close()
        except anydbm.error, e:
            pass

        rg = []
        for k,v in rostergroups.iteritems():
            rg.append([k,v])
        self.conn.executemany('INSERT INTO rostergroups (groupname, userlist) VALUES (?, ?)', rg)

        ri = []
        for k in rosterusers:
            ri.append([k,
                rosterinfo_fn[k] if k in rosterinfo_fn else None,
                rosterinfo_lg[k] if k in rosterinfo_lg else None,
                rosterinfo_rh[k] if k in rosterinfo_rh else None])
        self.conn.executemany('INSERT INTO rosterinfo (jid, fullname, grouplist, responsehash) VALUES (?, ?, ?, ?)', ri)

