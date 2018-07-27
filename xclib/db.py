import bsddb3
import sqlite3
from xclib.utf8 import unutf8

class connection:
    def __init__(self, paths):
        self.paths = paths

    def __enter__(self):
        self.conn = sqlite3.connect(self.paths.db, factory=sconn)
        self.conn.set_paths(self.paths)
        return self.conn

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()
        return False # Do not suppress exceptions

class sconn(sqlite3.Connection):
    def set_paths(self, paths):
        self.paths = paths
        self.upgrade = False

    def execute(self, *args, **kwargs):
        '''If the schema is not yet there, create it and fill the database first'''
        if self.upgrade:
            # Avoid recursion problems on upgrade errors (or after upgrading)
            return super().execute(*args, **kwargs)
        else:
            try:
                return super().execute(*args, **kwargs)
            except sqlite3.OperationalError as e:
                # Convert and try again
                self.upgrade = True
                self.db_upgrade()
                return super().execute(*args, **kwargs)

    def db_upgrade(self):
        self.db_upgrade_domain()
        self.db_upgrade_cache()
        self.db_upgrade_roster()

    def db_upgrade_domain(self):
        self.execute('''CREATE TABLE domains
                     (xmppdomain TEXT PRIMARY KEY,
                      authsecret TEXT,
                      authurl    TEXT,
                      authdomain TEXT,
                      regcontact TEXT,
                      regfirst   TEXT DEFAULT CURRENT_TIMESTAMP,
                      reglatest  TEXT DEFAULT CURRENT_TIMESTAMP)''')
        self.execute('BEGIN TRANSACTION')
        try:
            db = bsddb3.hashopen(self.paths.domain_db, 'r')
            for k,v in db.items():
                k = unutf8(k)
                v = unutf8(v)
                try:
                    (authsecret, authurl, authdomain, extra) = v.split("\t", 3)
                except ValueError:
                    (authsecret, authurl, authdomain) = v.split("\t", 2)
                    extra = None
                self.execute('''INSERT INTO domains (xmppdomain, authsecret, authurl, authdomain)
                     VALUES (?, ?, ?, ?)''', (k, authsecret, authurl, authdomain))
            db.close()
        except bsddb3.db.DBError as e:
            pass
        self.execute('COMMIT')

    def db_upgrade_cache(self):
        self.execute('''CREATE TABLE authcache
                       (jid        TEXT PRIMARY KEY,
                        pwhash     TEXT,
                        firstauth  TEXT DEFAULT CURRENT_TIMESTAMP,
                        anyauth    TEXT DEFAULT CURRENT_TIMESTAMP,
                        remoteauth TEXT DEFAULT CURRENT_TIMESTAMP)''')
        self.execute('BEGIN TRANSACTION')
        try:
            db = bsddb3.hashopen(self.paths.cache_db, 'r')
            for k,v in db.items():
                k = unutf8(k)
                v = unutf8(v)
                (pwhash, ts1, tsv, tsa, rest) = v.split("\t", 4)
                self.execute('''INSERT INTO authcache (jid, pwhash, firstauth, anyauth, remoteauth)
                     VALUES (?, ?,
                     datetime('unixepoch' || ?),
                     datetime('unixepoch' || ?),
                     datetime('unixepoch' || ?))''', (k, pwhash, ts1, tsv, tsa))
            db.close()
        except bsddb3.db.DBError as e:
            pass
        self.execute('COMMIT')

    def db_upgrade_roster(self):
        self.execute('''CREATE TABLE rosterinfo
                          (jid          TEXT PRIMARY KEY,
                           fullname     TEXT,
                           grouplist    TEXT,
                           responsehash TEXT)''')
        self.execute('''CREATE TABLE rostergroups
                          (groupname    TEXT PRIMARY KEY,
                           userlist     TEXT)''')
        rosterinfo_fn = {}
        rosterinfo_rh = {}
        rosterinfo_lg = {}
        rosterinfo_rg = {}
        rosterusers = set([])
        rostergroups = {}
        try:
            db = bsddb3.hashopen(self.paths.cache_db, 'r')
            for k,v in db.items():
                k = unutf8(k)
                v = unutf8(v)
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
        except bsddb3.db.DBError as e:
            pass

        rg = []
        for k,v in rostergroups.items():
            k = unutf8(k)
            v = unutf8(v)
            rg.append([k,v])
        self.executemany('INSERT INTO rostergroups (groupname, userlist) VALUES (?, ?)', rg)

        ri = []
        for k in rosterusers:
            ri.append([k,
                rosterinfo_fn[k] if k in rosterinfo_fn else None,
                rosterinfo_lg[k] if k in rosterinfo_lg else None,
                rosterinfo_rh[k] if k in rosterinfo_rh else None])
        self.executemany('INSERT INTO rosterinfo (jid, fullname, grouplist, responsehash) VALUES (?, ?, ?, ?)', ri)

