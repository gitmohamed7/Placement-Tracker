import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path
from server import make_server

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.server=make_server(Path(self.tmp.name)/'api.db',0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
    def request(self,method,path,payload=None,authorised=True,host=None):
        connection=HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        headers={'Content-Type':'application/json'}
        if authorised:headers['X-CSRF-Token']=self.server.token
        if host:headers['Host']=host
        body=json.dumps(payload) if payload is not None else None
        connection.request(method,path,body,headers)
        response=connection.getresponse();status=response.status;body=response.read();connection.close()
        return status,body
    def test_create_read_update(self):
        status,body=self.request('POST','/api/applications',{'company':'Demo','role':'Intern'})
        self.assertEqual(status,201);app=json.loads(body)
        status,body=self.request('POST','/api/applications/'+str(app['id']),{**app,'stage':'Interview'})
        self.assertEqual(status,200);self.assertEqual(json.loads(body)['revision'],2)
        status,body=self.request('GET','/api/applications');self.assertEqual(len(json.loads(body)),1)
    def test_conflict_returns_409(self):
        _,body=self.request('POST','/api/applications',{'company':'Demo','role':'Intern'})
        app=json.loads(body);path='/api/applications/'+str(app['id'])
        self.request('POST',path,{**app,'stage':'Interview'})
        self.assertEqual(self.request('POST',path,app)[0],409)
    def test_missing_token_rejected(self):
        self.assertEqual(self.request('POST','/api/applications',{'company':'x','role':'y'},False)[0],403)
    def test_foreign_host_rejected(self):
        self.assertEqual(self.request('GET','/api/session',host='foreign.example')[0],403)
    def test_invalid_input(self):
        self.assertEqual(self.request('POST','/api/applications',{'company':''})[0],400)
    def test_static_and_csv(self):
        for path in ['/','/app.js','/style.css','/api/export']:
            self.assertEqual(self.request('GET',path)[0],200)
        self.assertEqual(self.request('GET','/missing')[0],404)
