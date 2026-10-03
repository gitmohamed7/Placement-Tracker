"""Loopback-only HTTP server for the single-user portfolio demo."""
import argparse
import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from store import Store, Conflict

class Handler(BaseHTTPRequestHandler):
    def reply(self,status,body,mime='application/json'):
        if mime=='application/json':
            body=json.dumps(body).encode()
        elif isinstance(body,str):
            body=body.encode()
        self.send_response(status)
        self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        if mime.startswith('text/csv'):
            self.send_header('Content-Disposition','attachment; filename="applications.csv"')
        self.end_headers()
        self.wfile.write(body)
    def authorised_host(self):
        return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'
    def do_GET(self):
        if not self.authorised_host():
            self.reply(403,{'error':'Use the printed loopback URL'});return
        path=urlsplit(self.path).path
        if path in ('/','/app.js','/style.css'):
            filename={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}[path]
            mime={'/':'text/html; charset=utf-8','/app.js':'text/javascript; charset=utf-8','/style.css':'text/css; charset=utf-8'}[path]
            self.reply(200,Path(__file__).with_name(filename).read_bytes(),mime);return
        if path=='/api/session':
            self.reply(200,{'token':self.server.token});return
        store=Store(self.server.database)
        try:
            if path=='/api/applications':self.reply(200,store.list())
            elif path=='/api/export':self.reply(200,store.export(),'text/csv; charset=utf-8')
            elif path.startswith('/api/history/'):
                self.reply(200,store.history(int(path.rsplit('/',1)[-1])))
            else:self.reply(404,{'error':'Not found'})
        except (ValueError,KeyError):self.reply(404,{'error':'Application not found'})
        finally:store.close()
    def do_POST(self):
        if not self.authorised_host() or self.headers.get('X-CSRF-Token')!=self.server.token:
            self.reply(403,{'error':'Invalid session. Reload the page.'});return
        store=None
        try:
            if self.headers.get('Content-Type')!='application/json':
                raise ValueError('Use application/json')
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=40000:raise ValueError('Request body too large or empty')
            payload=json.loads(self.rfile.read(size))
            path=urlsplit(self.path).path
            if path=='/api/applications':identifier=None
            elif path.startswith('/api/applications/'):
                identifier=int(path.rsplit('/',1)[-1])
            else:self.reply(404,{'error':'Not found'});return
            store=Store(self.server.database)
            self.reply(201 if identifier is None else 200,store.save(payload,identifier))
        except Conflict as error:self.reply(409,{'error':str(error)})
        except KeyError:self.reply(404,{'error':'Application not found'})
        except (ValueError,TypeError) as error:self.reply(400,{'error':str(error) or 'Invalid input'})
        finally:
            if store:store.close()

def make_server(database,port=8001):
    Store(database).close()
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.database=database
    server.token=secrets.token_urlsafe(32)
    return server
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',default=str(Path(__file__).with_name('applications.db')))
    parser.add_argument('--port',type=int,default=8001)
    args=parser.parse_args()
    server=make_server(args.db,args.port)
    print(f'Placement tracker: http://127.0.0.1:{server.server_port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
