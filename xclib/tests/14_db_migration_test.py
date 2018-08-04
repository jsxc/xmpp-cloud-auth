# Checks database migration functions
import sys
import os
import io
import bsddb3
import unittest
import tempfile
import logging
import shutil
from argparse import Namespace
from xclib.dbmops import perform
from xclib.tests.iostub import iostub
from xclib.utf8 import utf8
from xclib.check import assertEqual
from xclib.db import connection

class TestDBM(unittest.TestCase, iostub):

    @classmethod
    def setup_class(cls):
        global domname, cacname, rosname, sqlname, domfile, dirname, ucdname
        dirname = tempfile.mkdtemp()
        domname = dirname + "/domains.db"
        rosname = dirname + "/shared_roster.db"
        ucdname = dirname + "/user-cache.db"
        sqlname = dirname + "/xcauth.sqlite3"
        domfile = bsddb3.hashopen(domname, 'c', 0o600)

    @classmethod
    def teardown_class(cls):
        domfile.close()
#        shutil.rmtree(dirname)

    def mkns(self, **kwargs):
        params = {'domain_db': domname, 'get': None, 'put': None, 
            'delete': None, 'load': None, 'unload': None}
        params.update(**kwargs)
        return Namespace(**params)

    def mkpaths(self, **kwargs):
        paths = {'db': sqlname, 'domain_db': domname,
                'shared_roster_db': rosname,
                'cache_storage': 'memory', 'cache_db': ucdname}
        paths.update(**kwargs)
        return Namespace(**paths)

    def test_01_load(self):
        self.stub_stdin(u'example.ch\tXmplScrt\thttps://example.ch/index.php/apps/ojsxc/ajax/externalApi.php\texample.ch\t\n' +
            u'example.de\tNothrXampl\thttps://nothing\t\n')
        ns = self.mkns(load=True)
        perform(ns)
        assertEqual(domfile[b'example.ch'], b'XmplScrt\thttps://example.ch/index.php/apps/ojsxc/ajax/externalApi.php\texample.ch\t')
        assertEqual(domfile[b'example.de'], b'NothrXampl\thttps://nothing\t')
        assert b'example.net' not in domfile

    def test_02_execute(self):
        paths = self.mkpaths()
        sqlconn = connection(paths)
        r = set()
        for row in sqlconn.conn.execute('select * from domains'):
            r.add(row[0:4])
        logging.error('r = %r', r)
        assertEqual(len(r), 2)
        assert ('example.ch', 'XmplScrt', 'https://example.ch/index.php/apps/ojsxc/ajax/externalApi.php', 'example.ch') in r
        assert ('example.de', 'NothrXampl', 'https://nothing', '') in r
