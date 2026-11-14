"""Small SQLite-backed Kanban server."""
import argparse
import hashlib
import hmac
import json
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent
SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), expires TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS boards(id INTEGER PRIMARY KEY, name TEXT NOT NULL, owner_id INTEGER NOT NULL REFERENCES users(id));
CREATE TABLE IF NOT EXISTS members(board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE, user_id INTEGER NOT NULL REFERENCES users(id), UNIQUE(board_id,user_id));
CREATE TABLE IF NOT EXISTS columns(id INTEGER PRIMARY KEY, board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE, name TEXT NOT NULL, position INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS cards(id INTEGER PRIMARY KEY, column_id INTEGER NOT NULL REFERENCES columns(id), title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', due_date TEXT, position INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS labels(id INTEGER PRIMARY KEY, board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE, name TEXT NOT NULL, color TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS card_labels(card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE, label_id INTEGER NOT NULL REFERENCES labels(id) ON DELETE CASCADE, UNIQUE(card_id,label_id));
"""

def connect(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript(SCHEMA)
    return db

class Problem(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message

def required(value, label):
    if not isinstance(value, str) or not value.strip():
        raise Problem(400, f'{label} is required')
    return value.strip()

def board_access(db, board_id, user_id, owner=False):
    row = db.execute('SELECT * FROM boards WHERE id=? AND (owner_id=? OR EXISTS (SELECT 1 FROM members WHERE board_id=boards.id AND user_id=?))', (board_id,user_id,user_id)).fetchone()
    if not row: raise Problem(404, 'Board not found')
    if owner and row['owner_id'] != user_id: raise Problem(403, 'Only the board owner can do that')
    return row

def parent(db, table, item_id):
    sql = {'columns':'SELECT board_id FROM columns WHERE id=?', 'cards':'SELECT columns.board_id FROM cards JOIN columns ON columns.id=cards.column_id WHERE cards.id=?', 'labels':'SELECT board_id FROM labels WHERE id=?'}[table]
    row = db.execute(sql,(item_id,)).fetchone()
    if not row: raise Problem(404, 'Item not found')
    return row['board_id']

def positions(db, table, parent_field, parent_id, ids):
    actual = [r['id'] for r in db.execute(f'SELECT id FROM {table} WHERE {parent_field}=?',(parent_id,))]
    if len(ids) != len(actual) or set(ids) != set(actual): raise Problem(400,'Order must contain every item exactly once')
    for index, item_id in enumerate(ids): db.execute(f'UPDATE {table} SET position=? WHERE id=?',(index,item_id))

def snapshot(db, board_id, user_id):
    b = dict(board_access(db,board_id,user_id))
    b['owner'] = b['owner_id'] == user_id
    b['members'] = [dict(r) for r in db.execute('SELECT users.id,users.email FROM members JOIN users ON users.id=members.user_id WHERE board_id=?',(board_id,))]
    b['labels'] = [dict(r) for r in db.execute('SELECT * FROM labels WHERE board_id=? ORDER BY id',(board_id,))]
    b['columns'] = []
    for c in db.execute('SELECT * FROM columns WHERE board_id=? ORDER BY position,id',(board_id,)):
        col = dict(c)
        col['cards'] = []
        for card in db.execute('SELECT * FROM cards WHERE column_id=? ORDER BY position,id',(c['id'],)):
            item = dict(card)
            item['label_ids'] = [r['label_id'] for r in db.execute('SELECT label_id FROM card_labels WHERE card_id=?',(card['id'],))]
            col['cards'].append(item)
        b['columns'].append(col)
    return b

def operate(db, user, method, parts, data):
    if parts == ['boards'] and method == 'GET':
        return [dict(r) for r in db.execute('SELECT boards.id,boards.name,boards.owner_id FROM boards WHERE owner_id=? OR EXISTS(SELECT 1 FROM members WHERE board_id=boards.id AND user_id=?) ORDER BY boards.id DESC',(user,user))]
    if parts == ['boards'] and method == 'POST':
        name = required(data.get('name'),'Board name')
        cur = db.execute('INSERT INTO boards(name,owner_id) VALUES(?,?)',(name,user)); bid=cur.lastrowid
        for i, name in enumerate(('To Do','In Progress','Done')): db.execute('INSERT INTO columns(board_id,name,position) VALUES(?,?,?)',(bid,name,i))
        return snapshot(db,bid,user)
    if not parts or parts[0] != 'boards' or len(parts)<2: raise Problem(404,'Not found')
    try: bid=int(parts[1])
    except ValueError: raise Problem(404,'Not found')
    if len(parts)==2:
        if method=='GET': return snapshot(db,bid,user)
        board_access(db,bid,user,True)
        if method=='PATCH':
            db.execute('UPDATE boards SET name=? WHERE id=?',(required(data.get('name'),'Board name'),bid)); return snapshot(db,bid,user)
        if method=='DELETE':
            db.execute('DELETE FROM cards WHERE column_id IN (SELECT id FROM columns WHERE board_id=?)',(bid,))
            db.execute('DELETE FROM boards WHERE id=?',(bid,))
            return {'ok':True}
    board_access(db,bid,user)
    kind=parts[2] if len(parts)>2 else ''
    if kind=='members':
        board_access(db,bid,user,True)
        if method=='POST' and len(parts)==3:
            email=required(data.get('email'),'Email').lower()
            member=db.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone()
            if not member: raise Problem(404,'User not found')
            if member['id']==user: raise Problem(400,'Owner is already on this board')
            db.execute('INSERT OR IGNORE INTO members(board_id,user_id) VALUES(?,?)',(bid,member['id'])); return snapshot(db,bid,user)
        if method=='DELETE' and len(parts)==4:
            db.execute('DELETE FROM members WHERE board_id=? AND user_id=?',(bid,int(parts[3]))); return snapshot(db,bid,user)
    if kind=='columns':
        board_access(db,bid,user,True)
        if len(parts)==3 and method=='POST':
            pos=db.execute('SELECT COUNT(*) FROM columns WHERE board_id=?',(bid,)).fetchone()[0]
            db.execute('INSERT INTO columns(board_id,name,position) VALUES(?,?,?)',(bid,required(data.get('name'),'Column name'),pos)); return snapshot(db,bid,user)
        if len(parts)==4 and parts[3]=='order' and method=='PATCH':
            positions(db,'columns','board_id',bid,data.get('ids',[])); return snapshot(db,bid,user)
        if len(parts)==4:
            cid=int(parts[3]);
            if parent(db,'columns',cid)!=bid: raise Problem(404,'Column not found')
            if method=='PATCH': db.execute('UPDATE columns SET name=? WHERE id=?',(required(data.get('name'),'Column name'),cid)); return snapshot(db,bid,user)
            if method=='DELETE':
                if db.execute('SELECT 1 FROM cards WHERE column_id=?',(cid,)).fetchone(): raise Problem(409,'Move the cards before deleting this column')
                db.execute('DELETE FROM columns WHERE id=?',(cid,)); return snapshot(db,bid,user)
    if kind=='labels':
        board_access(db,bid,user,True)
        if len(parts)==3 and method=='POST':
            color=data.get('color')
            if color not in ('red','blue','green','purple','amber'): raise Problem(400,'Choose a valid label color')
            db.execute('INSERT INTO labels(board_id,name,color) VALUES(?,?,?)',(bid,required(data.get('name'),'Label name'),color)); return snapshot(db,bid,user)
        if len(parts)==4 and method=='DELETE':
            lid=int(parts[3]);
            if parent(db,'labels',lid)!=bid: raise Problem(404,'Label not found')
            db.execute('DELETE FROM labels WHERE id=?',(lid,)); return snapshot(db,bid,user)
    if kind=='cards':
        if len(parts)==4 and parts[3]=='move' and method=='PATCH':
            card_id=int(data.get('card_id',0)); target=int(data.get('column_id',0)); index=data.get('index',0)
            if parent(db,'cards',card_id)!=bid or parent(db,'columns',target)!=bid: raise Problem(404,'Item not found')
            if not isinstance(index,int): raise Problem(400,'Invalid position')
            source=db.execute('SELECT column_id FROM cards WHERE id=?',(card_id,)).fetchone()[0]
            db.execute('UPDATE cards SET column_id=? WHERE id=?',(target,card_id))
            for col_id in {source,target}:
                ids=[r['id'] for r in db.execute('SELECT id FROM cards WHERE column_id=? AND id!=? ORDER BY position,id',(col_id,card_id))]
                if col_id==target: ids.insert(max(0,min(index,len(ids))),card_id)
                positions(db,'cards','column_id',col_id,ids)
            return snapshot(db,bid,user)
        if len(parts)==3 and method=='POST':
            cid=int(data.get('column_id',0))
            if parent(db,'columns',cid)!=bid: raise Problem(404,'Column not found')
            title=required(data.get('title'),'Card title'); desc=data.get('description','')
            if not isinstance(desc,str): raise Problem(400,'Invalid description')
            pos=db.execute('SELECT COUNT(*) FROM cards WHERE column_id=?',(cid,)).fetchone()[0]
            cur=db.execute('INSERT INTO cards(column_id,title,description,position) VALUES(?,?,?,?)',(cid,title,desc,pos))
            return snapshot(db,bid,user)
        if len(parts)==4:
            card_id=int(parts[3]);
            if parent(db,'cards',card_id)!=bid: raise Problem(404,'Card not found')
            if method=='DELETE': db.execute('DELETE FROM cards WHERE id=?',(card_id,)); return snapshot(db,bid,user)
            if method=='PATCH':
                card=db.execute('SELECT * FROM cards WHERE id=?',(card_id,)).fetchone()
                title=required(data.get('title',card['title']),'Card title')
                desc=data.get('description',card['description'])
                due=data.get('due_date',card['due_date'])
                if not isinstance(desc,str): raise Problem(400,'Invalid description')
                if due:
                    try: datetime.strptime(due,'%Y-%m-%d')
                    except (ValueError,TypeError): raise Problem(400,'Invalid due date')
                ids=data.get('label_ids',[r['label_id'] for r in db.execute('SELECT label_id FROM card_labels WHERE card_id=?',(card_id,))])
                if not isinstance(ids,list) or len(ids)!=len(set(ids)) or any(parent(db,'labels',int(i))!=bid for i in ids): raise Problem(400,'Invalid labels')
                db.execute('UPDATE cards SET title=?,description=?,due_date=? WHERE id=?',(title,desc,due or None,card_id))
                db.execute('DELETE FROM card_labels WHERE card_id=?',(card_id,))
                db.executemany('INSERT INTO card_labels(card_id,label_id) VALUES(?,?)',[(card_id,i) for i in ids]); return snapshot(db,bid,user)
    raise Problem(404,'Not found')

def handler(db_path):
    class Handler(BaseHTTPRequestHandler):
        def reply(self,status,obj):
            raw=json.dumps(obj).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(raw))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(raw)
        def do_GET(self): self.handle_request('GET')
        def do_POST(self): self.handle_request('POST')
        def do_PATCH(self): self.handle_request('PATCH')
        def do_DELETE(self): self.handle_request('DELETE')
        def handle_request(self,method):
            path=urlparse(self.path).path
            if method=='GET' and path in ('/','/app.js','/style.css','/theme.css'):
                file=ROOT / {'/':'index.html','/app.js':'app.js','/style.css':'style.css','/theme.css':'theme.css'}[path]
                raw=file.read_bytes(); self.send_response(200); self.send_header('Content-Type',{'/':'text/html','/app.js':'text/javascript','/style.css':'text/css','/theme.css':'text/css'}[path]); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw); return
            db=connect(db_path)
            try:
                length=int(self.headers.get('Content-Length','0'))
                if length>100000: raise Problem(413,'Request too large')
                data=json.loads(self.rfile.read(length)) if length else {}
                if not isinstance(data,dict): raise Problem(400,'Invalid request')
                if path in ('/api/signup','/api/login') and method=='POST':
                    email=required(data.get('email'),'Email').lower(); password=data.get('password','')
                    if '@' not in email or len(password)<8: raise Problem(400,'Enter a valid email and a password of at least 8 characters')
                    if path.endswith('signup'):
                        salt=secrets.token_hex(16); digest=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),200000).hex()
                        try: user=db.execute('INSERT INTO users(email,password) VALUES(?,?)',(email,salt+':'+digest)).lastrowid
                        except sqlite3.IntegrityError: raise Problem(409,'Email already registered')
                    else:
                        row=db.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
                        if not row: raise Problem(401,'Invalid credentials')
                        salt,digest=row['password'].split(':'); actual=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),200000).hex()
                        if not hmac.compare_digest(actual,digest): raise Problem(401,'Invalid credentials')
                        user=row['id']
                    token=secrets.token_urlsafe(32); db.execute('INSERT INTO sessions VALUES(?,?,?)',(token,user,(datetime.now(timezone.utc)+timedelta(days=7)).isoformat()))
                    db.commit(); raw=json.dumps({'email':email}).encode(); self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Set-Cookie',f'session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=604800'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw); return
                jar=cookies.SimpleCookie(); jar.load(self.headers.get('Cookie','')); token=jar['session'].value if 'session' in jar else ''
                row=db.execute('SELECT user_id,email FROM sessions JOIN users ON users.id=sessions.user_id WHERE token=? AND expires>?',(token,datetime.now(timezone.utc).isoformat())).fetchone()
                if not row: raise Problem(401,'Sign in required')
                if method!='GET' and self.headers.get('Origin') and self.headers['Origin'] != f'http://{self.headers.get("Host")}': raise Problem(403,'Invalid origin')
                if path=='/api/me' and method=='GET': result={'email':row['email']}
                elif path=='/api/logout' and method=='POST': db.execute('DELETE FROM sessions WHERE token=?',(token,)); result={'ok':True}
                elif path.startswith('/api/'): result=operate(db,row['user_id'],method,[p for p in path[5:].split('/') if p],data)
                else: raise Problem(404,'Not found')
                db.commit(); self.reply(200,result)
            except Problem as e: db.rollback(); self.reply(e.status,{'error':e.message})
            except (ValueError,TypeError,json.JSONDecodeError): db.rollback(); self.reply(400,{'error':'Invalid request'})
            finally: db.close()
    return Handler

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=8000); parser.add_argument('--db',default=str(ROOT/'kanban.sqlite3')); args=parser.parse_args()
    with connect(args.db): pass
    print(f'Kanban running at http://localhost:{args.port}')
    ThreadingHTTPServer(('127.0.0.1',args.port),handler(args.db)).serve_forever()
