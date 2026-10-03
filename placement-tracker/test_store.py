import csv
import io
import tempfile
import unittest
from pathlib import Path
from store import Store, Conflict

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.path=Path(self.directory.name)/'test.db'
        self.store=Store(self.path)
        self.data={'company':'Test Co','role':'Software placement'}
    def tearDown(self):
        self.store.close();self.directory.cleanup()
    def test_survives_restart(self):
        app=self.store.save(self.data)
        other=Store(self.path)
        try:self.assertEqual(other.get(app['id'])['company'],'Test Co')
        finally:other.close()
    def test_stale_edit_is_rejected(self):
        app=self.store.save(self.data)
        update={**app,'stage':'Interview'}
        self.store.save(update,app['id'])
        with self.assertRaises(Conflict):self.store.save({**app,'notes':'stale'},app['id'])
        self.assertEqual(self.store.get(app['id'])['stage'],'Interview')
    def test_history_only_records_stage_changes(self):
        app=self.store.save(self.data)
        app=self.store.save({**app,'notes':'first note'},app['id'])
        self.assertEqual(len(self.store.history(app['id'])),1)
        app=self.store.save({**app,'stage':'Applied'},app['id'])
        self.assertEqual([x['stage'] for x in self.store.history(app['id'])],['Applied','Saved'])
    def test_validation(self):
        for patch in [{'company':''},{'stage':'Invalid'},{'deadline':'2026-02-30'},{'url':'javascript:alert(1)'},{'notes':7},{'deadline':'20261002'}]:
            with self.subTest(patch=patch):
                with self.assertRaises(ValueError):self.store.save({**self.data,**patch})
        self.assertEqual(self.store.list(),[])
    def test_parameterised_sql(self):
        text="Robert'); DROP TABLE applications;--"
        self.store.save({**self.data,'company':text})
        self.assertEqual(self.store.list()[0]['company'],text)
    def test_csv_quotes_and_formula_guard(self):
        self.store.save({**self.data,'company':'=1+1','notes':'a, b\nsecond line'})
        row=next(csv.DictReader(io.StringIO(self.store.export())))
        self.assertEqual(row['company'],"'=1+1")
        self.assertEqual(row['notes'],'a, b\nsecond line')
    def test_missing_record(self):
        with self.assertRaises(KeyError):self.store.get(123)
    def test_failed_edit_adds_no_event(self):
        app=self.store.save(self.data)
        with self.assertRaises(Conflict):self.store.save({**app,'revision':0,'stage':'Offer'},app['id'])
        self.assertEqual(len(self.store.history(app['id'])),1)
