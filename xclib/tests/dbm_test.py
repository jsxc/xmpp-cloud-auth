import sys
import os
import io
import bsddb3
import unittest
import tempfile
import logging
import subprocess
from argparse import Namespace
from xclib.dbmops import perform
from xclib.tests.iostub import iostub
from xclib.utf8 import utf8

class TestDBM(unittest.TestCase, iostub):

    @classmethod
    def setup_class(cls):
        global dbname, dbfile, dirname
        dirname = tempfile.mkdtemp()
        dbname = dirname + "/domains.db"
        dbfile = bsddb3.hashopen(dbname, 'c', 0o600)

    @classmethod
    def teardown_class(cls):
        dbfile.close()
        os.remove(dbname)
        os.rmdir(dirname)

    def mkns(self, **kwargs):
        params = {'domain_db': dbname, 'get': None, 'put': None, 
            'delete': None, 'load': None, 'unload': None}
        params.update(**kwargs)
        return Namespace(**params)

    def test_01_load(self):
        self.stub_stdin(u'example.ch\tXmplScrt\thttps://example.ch/index.php/apps/ojsxc/ajax/externalApi.php\texample.ch\t\n' +
            u'example.de\tNothrXampl\thttps://nothing\t\n')
        ns = self.mkns(load=True)
        perform(ns)
        assert dbfile[b'example.ch'] == b'XmplScrt\thttps://example.ch/index.php/apps/ojsxc/ajax/externalApi.php\texample.ch\t'
        assert dbfile[b'example.de'] == b'NothrXampl\thttps://nothing\t'
        assert b'example.net' not in dbfile

    def test_02_put(self):
        ns = self.mkns(put=[u'example.net', u'dummy'])
        perform(ns)
        ns = self.mkns(get=u'example.net')
        perform(ns)
        dbfile = bsddb3.hashopen(dbname, 'c', 0o600)
        assert b'example.net' in dbfile
        assert dbfile[b'example.net'] == b'dummy'
        dbfile.close()

    def test_03_get(self):
        self.stub_stdout(ioclass=io.StringIO)
        ns = self.mkns(get=u'example.net')
        perform(ns)
        self.assertEqual(sys.stdout.getvalue(), u'dummy\n')

    def test_04_delete(self):
        ns = self.mkns(delete=u'example.de')
        perform(ns)

    def test_05_unload(self):
        expected = [b'example.net', b'example.ch']
        self.stub_stdout(ioclass=io.StringIO)
        ns = self.mkns(unload=True)
        perform(ns)
        v = sys.stdout.getvalue()
        for line in v.split('\n'):
            if line != '':
               (k, delim, v) = line.partition('\t')
               expected.remove(utf8(k))
        assert expected == []
