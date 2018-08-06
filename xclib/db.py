import bsddb3
import sqlite3
import os
import time
import logging
from datetime import datetime
from xclib.utf8 import unutf8

class sq3c_debugger(sqlite3.Connection):
#    def execute(self, sql, *args, **kwargs):
#        logging.debug('EXECUTE: %s' % sql)
#        return super().execute(sql, *args, **kwargs)

    def begin(self, mode = ''):
        self.execute('BEGIN %s' % mode)

    def dump(self, tbl):
        logging.debug('DUMP %s START' % tbl)
        for row in self.execute('SELECT * from %s' % tbl):
            out = map(str, row)
            logging.debug(' | '.join(out))
        logging.debug('DUMP %s STOP' % tbl)

class connection:
    def __init__(self, args):
        logging.debug('Opening database connections')
        db_was_there = (args.db != ':memory:'
                and os.access(args.db, os.R_OK|os.W_OK))
        # PySQLite by default does a weird
        # auto-start-transaction-but-don't-stop mode,
        # causing so much pain. Reset back to
        # SQLite default of 'autocommit'.
        self.conn = sqlite3.connect(args.db,
                factory=sq3c_debugger,
                check_same_thread=False,
                isolation_level = None,
                detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = sqlite3.Row

        if args.cache_storage == 'memory':
            self.cache = sqlite3.connect(':memory:',
                    factory=sq3c_debugger,
                    check_same_thread=False,
                    isolation_level = None,
                    detect_types=sqlite3.PARSE_DECLTYPES)
            self.cache.row_factory = sqlite3.Row
            # Create in-memory structure on every creation (db is empty)
            self.db_create_cache(self.cache)
        elif args.cache_storage == 'db':
            self.cache = self.conn
        else: # 'none'
            self.cache = fake_db()
        self.cache_storage = args.cache_storage

        if not db_was_there: # First-time opening of the SQLite3 db
            # Ensure persistent cache table is always created
            # on upgrade, independent of the --cache-storage mode
            # (so that a later mode change will not require any changes)
            logging.info('Initializing %s from %s, %s, and %s'
                    % (args.db, args.domain_db,
                        args.shared_roster_db, args.cache_db))
            self.db_create_cache(self.conn)
            self.db_upgrade_domain(args.domain_db)
            self.db_upgrade_roster(args.shared_roster_db)
            if self.cache == self.conn: # Persistent?
                self.db_upgrade_cache(args.cache_db)

    def db_upgrade_domain(self, olddb):
        logging.debug('Upgrading domain from %s' % olddb)
        try:
            self.conn.execute('''CREATE TABLE domains
                     (xmppdomain TEXT PRIMARY KEY,
                      authsecret TEXT,
                      authurl    TEXT,
                      authdomain TEXT,
                      regcontact TEXT,
                      regfirst   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      reglatest  TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        except sqlite3.OperationalError as e:
            logging.warning('Cannot create `domains` table; maybe multiple processes started in parallel? %s' % str(e))
            # Try to get out of the way of a parallel updater
            time.sleep(1)
            # Someone else already created the table; he probably also
            # migrated it
            return
        try:
            if olddb is None:
                return
            elif isinstance(olddb, str):
                db = bsddb3.hashopen(olddb, 'r')
            else: # dict
                db = olddb
            for k,v in db.items():
                k = unutf8(k, 'illegal')
                v = unutf8(v, 'illegal')
                try:
                    (authsecret, authurl, authdomain, extra) = v.split("\t", 3)
                except ValueError:
                    (authsecret, authurl, authdomain) = v.split("\t", 2)
                    extra = None
                self.conn.execute('''INSERT INTO domains (xmppdomain, authsecret, authurl, authdomain) VALUES (?, ?, ?, ?)''', (k, authsecret, authurl, authdomain))
            if isinstance(olddb, str):
                db.close()
        except bsddb3.db.DBError as e:
            logging.error('Trouble converting %s: %s' % (olddb, e))

    def db_create_cache(self, conn):
        logging.debug('Creating cache table in %s' % str(conn))
        try:
            conn.execute('''CREATE TABLE authcache
                       (jid        TEXT PRIMARY KEY,
                        pwhash     TEXT,
                        firstauth  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        remoteauth TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        anyauth    TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        except sqlite3.OperationalError as e:
            logging.warning('Cannot create `domains` table; maybe multiple processes started in parallel? %s' % str(e))
            # Try to get out of the way of a parallel updater
            time.sleep(1)

    def db_upgrade_cache(self, olddb):
        logging.debug('Upgrading cache from %s' % olddb)
        try:
            if olddb is None:
                return
            elif isinstance(olddb, str):
                db = bsddb3.hashopen(olddb, 'r')
            else: # dict
                db = olddb
            for k,v in db.items():
                k = unutf8(k, 'illegal')
                v = unutf8(v, 'illegal')
                (pwhash, ts1, tsv, tsa, rest) = v.split("\t", 4)
                ts1 = datetime.utcfromtimestamp(ts1)
                tsv = datetime.utcfromtimestamp(tsv)
                tsa = datetime.utcfromtimestamp(tsa)
                self.cache.execute('''INSERT INTO authcache (jid, pwhash, firstauth, remoteauth, anyauth)
                     VALUES (?, ?, ?, ?, ?)''', (k, pwhash, ts1, tsv, tsa))
            if isinstance(olddb, str):
                db.close()
        except bsddb3.db.DBError as e:
            logging.error('Trouble converting %s: %s' % (olddb, e))

    def db_upgrade_roster(self, olddb):
        logging.debug('Upgrading roster from %s' % olddb)
        try:
            self.conn.execute('''CREATE TABLE rosterinfo
                          (jid          TEXT PRIMARY KEY,
                           fullname     TEXT,
                           grouplist    TEXT,
                           responsehash TEXT,
                           last_update  TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        except sqlite3.OperationalError as e:
            logging.warning('Cannot create `domains` table; maybe multiple processes started in parallel? %s' % str(e))
            # Try to get out of the way of a parallel updater
            time.sleep(1)
            # Continue, in case a previous table creation was aborted
        try:
            self.conn.execute('''CREATE TABLE rostergroups
                          (groupname    TEXT PRIMARY KEY,
                           userlist     TEXT)''')
        except sqlite3.OperationalError as e:
            logging.warning('Cannot create `domains` table; maybe multiple processes started in parallel? %s' % str(e))
            # Try to get out of the way of a parallel updater
            time.sleep(1)
            # Someone else already created the table; he probably also
            # migrated it
            return

        rosterinfo_fn = {}
        rosterinfo_rh = {}
        rosterinfo_lg = {}
        rosterusers = set([])
        rostergroups = {}
        try:
            if olddb is None:
                return
            elif isinstance(olddb, str):
                db = bsddb3.hashopen(olddb, 'r')
            else: # dict
                db = olddb
            for k,v in db.items():
                k = unutf8(k, 'illegal')
                v = unutf8(v, 'illegal')
                if k.startswith('FNC:'): # Full name (cache only)
                    jid = k[4:].replace(':', '@')
                    rosterusers.add(jid)
                    if '@' in jid: # Do not copy malformed (old buggy) entries
                        rosterinfo_fn[jid] = v
                if k.startswith('LIG:'): # Login In Group (state information)
                    jid = k[4:].replace(':', '@')
                    rosterusers.add(jid)
                    rosterinfo_lg[jid] = v
                if k.startswith('RGC:'): # Reverse Group Cache (state information)
                    gid = k[4:].replace(':', '@')
                    rostergroups[gid] = v
                elif k.startswith('RH:'): # Response body hash (cache only)
                    jid = k[3:].replace(':', '@')
                    rosterusers.add(jid)
                    rosterinfo_rh[jid] = v
            if isinstance(olddb, str):
                db.close()
        except bsddb3.db.DBError as e:
            logging.error('Trouble converting %s: %s' % (olddb, e))

        rg = []
        for k,v in rostergroups.items():
            rg.append([k,v])
        self.conn.executemany('INSERT INTO rostergroups (groupname, userlist) VALUES (?, ?)', rg)

        ri = []
        for k in rosterusers:
            ri.append([k,
                rosterinfo_fn[k] if k in rosterinfo_fn else None,
                rosterinfo_lg[k] if k in rosterinfo_lg else None,
                rosterinfo_rh[k] if k in rosterinfo_rh else None])
        self.conn.executemany('INSERT INTO rosterinfo (jid, fullname, grouplist, responsehash) VALUES (?, ?, ?, ?)', ri)

class fake_db:
    def execute(self, cmd, args=None):
        return None
    def close(self):
        return None
