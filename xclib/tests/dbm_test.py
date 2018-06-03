import sys
import os
import dbm
import unittest
import tempfile
from argparse import Namespace
from xclib.dbmops import perform
from xclib.tests.iostub import iostub

class TestDBM(unittest.TestCase, iostub):

    @classmethod
    def setup_class(cls):
        global dbname, dbfile, dirname
        dirname = tempfile.mkdtemp()
        dbname = dirname + "/domains.db"
        dbfile = dbm.open(dbname, 'c', 0o600)

    @classmethod
    def teardown_class(cls):
        pass
        dbfile.close()
        os.remove(dbname)
        os.rmdir(dirname)

    def mkns(self, **kwargs):
        params = {'domain_db': dbname, 'get': None, 'put': None, 
            'delete': None, 'load': None, 'unload': None}
        params.update(**kwargs)
        return Namespace(**params)

    def test_01_load(self):
        self.stub_stdin('example.ch\tXmplScrt\thttps://example.ch/index.php/apps/ojsxc/ajax/externalApi.php\texample.ch\t\n' +
            'example.de\tNothrXampl\thttps://nothing\t\n')
        ns = self.mkns(load=True)
        perform(ns)
        assert dbfile['example.ch'] == 'XmplScrt\thttps://example.ch/index.php/apps/ojsxc/ajax/externalApi.php\texample.ch\t'
        assert dbfile['example.de'] == 'NothrXampl\thttps://nothing\t'
        assert 'example.net' not in dbfile

    def test_02_put(self):
        ns = self.mkns(put=['example.net', 'dummy'])
        perform(ns)
        ns = self.mkns(get='example.net')
        perform(ns)
        dbfile = dbm.open(dbname, 'c', 0o600)
        assert 'example.net' in dbfile
        assert dbfile['example.net'] == 'dummy'
        dbfile.close()

    def test_03_get(self):
        self.stub_stdout()
        ns = self.mkns(get='example.net')
        perform(ns)
        self.assertEqual(sys.stdout.getvalue(), 'dummy\n')

    def test_04_delete(self):
        ns = self.mkns(delete='example.de')
        perform(ns)

    def test_05_unload(self):
        expected = ['example.net', 'example.ch']
        self.stub_stdout()
        ns = self.mkns(unload=True)
        perform(ns)
        v = sys.stdout.getvalue()
	for line in v.split('\n'):
            if line != '':
               (k, delim, v) = line.partition('\t')
               expected.remove(k)
        assert expected == []
