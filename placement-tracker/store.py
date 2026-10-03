"""Application persistence and validation, independent of HTTP and UI."""
import csv
import io
import sqlite3
from datetime import date, datetime, timezone
from urllib.parse import urlsplit

STAGES = ('Saved', 'Applied', 'Assessment', 'Interview', 'Offer', 'Rejected', 'Withdrawn')
class Conflict(Exception):
    """A newer revision exists; the caller should reload rather than overwrite."""

def validate(data):
    if not isinstance(data, dict):
        raise ValueError('An application must be an object')
    result = {}
    for field, limit in [('company',100),('role',150),('location',100),('url',1000),('notes',5000)]:
        value = data.get(field, '')
        if not isinstance(value,str) or len(value)>limit or '\x00' in value:
            raise ValueError(f'{field} must be text, at most {limit} characters')
        result[field] = value.strip()
    if not result['company'] or not result['role']:
        raise ValueError('Company and role are required')
    result['stage'] = data.get('stage','Saved')
    if result['stage'] not in STAGES:
        raise ValueError('Unknown application stage')
    deadline = data.get('deadline','')
    if not isinstance(deadline,str):
        raise ValueError('Deadline must be a date or empty')
    if deadline:
        parsed = date.fromisoformat(deadline)
        if parsed.isoformat() != deadline:
            raise ValueError('Deadline must use YYYY-MM-DD')
    result['deadline'] = deadline
    if result['url']:
        url = urlsplit(result['url'])
        if url.scheme not in ('https','http') or not url.hostname or url.username or url.password:
            raise ValueError('Job URL must be an HTTP(S) address without credentials')
    return result

class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS applications(
          id INTEGER PRIMARY KEY, company TEXT NOT NULL, role TEXT NOT NULL,
          location TEXT NOT NULL, url TEXT NOT NULL, notes TEXT NOT NULL,
          stage TEXT NOT NULL, deadline TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(
          id INTEGER PRIMARY KEY, application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
          stage TEXT NOT NULL, happened_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS application_stage ON applications(stage);
        """)
    def close(self):
        self.db.close()
    def list(self):
        return [dict(x) for x in self.db.execute('SELECT * FROM applications ORDER BY updated_at DESC,id DESC')]
    def get(self, identifier):
        row = self.db.execute('SELECT * FROM applications WHERE id=?',(identifier,)).fetchone()
        if row is None:
            raise KeyError('Application not found')
        return dict(row)
    def save(self, data, identifier=None):
        values = validate(data)
        now = datetime.now(timezone.utc).isoformat()
        with self.db:
            if identifier is None:
                fields = list(values)
                cursor = self.db.execute('INSERT INTO applications('+','.join(fields)+',created_at,updated_at) VALUES ('+','.join('?' for _ in range(len(fields)+2))+')',list(values.values())+[now,now])
                identifier = cursor.lastrowid
                changed_stage = True
            else:
                previous = self.get(identifier)
                revision = data.get('revision')
                if type(revision) is not int:
                    raise ValueError('A numeric revision is required for updates')
                assignment = ','.join(f'{field}=?' for field in values)
                cursor = self.db.execute('UPDATE applications SET '+assignment+',updated_at=?,revision=revision+1 WHERE id=? AND revision=?',list(values.values())+[now,identifier,revision])
                if cursor.rowcount != 1:
                    raise Conflict('This application changed in another tab. Reload before editing.')
                changed_stage = previous['stage'] != values['stage']
            if changed_stage:
                self.db.execute('INSERT INTO events(application_id,stage,happened_at) VALUES (?,?,?)',(identifier,values['stage'],now))
        return self.get(identifier)
    def history(self, identifier):
        self.get(identifier)
        return [dict(x) for x in self.db.execute('SELECT stage,happened_at FROM events WHERE application_id=? ORDER BY id DESC',(identifier,))]
    def export(self):
        buffer = io.StringIO(newline='')
        fields = ['company','role','stage','location','deadline','url','notes']
        writer = csv.DictWriter(buffer,fieldnames=fields)
        writer.writeheader()
        for application in self.list():
            row = {}
            for field in fields:
                value = application[field]
                # Mitigate formula injection when opened in spreadsheet software.
                row[field] = "'"+value if value.lstrip().startswith(('=','+','-','@')) or value.startswith(('\t','\r','\n')) else value
            writer.writerow(row)
        return buffer.getvalue()
