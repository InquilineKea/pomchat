#!/usr/bin/env python3

import json
import os
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs
import re
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from dotenv import load_dotenv
import sqlite3
from contextlib import contextmanager

# Load environment variables
load_dotenv()

# Environment variables with defaults
PORT = int(os.getenv('PORT', 8000))
HOST = os.getenv('HOST', 'localhost')
KEYS_DIR = os.getenv('KEYS_DIRECTORY', 'keys')
DB_PATH = os.getenv('DB_PATH', 'pomchat.db')
PRIVATE_KEY_PASSWORD = os.getenv('PRIVATE_KEY_PASSWORD', None)
if PRIVATE_KEY_PASSWORD:
    PRIVATE_KEY_PASSWORD = PRIVATE_KEY_PASSWORD.encode()
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize the database schema."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TIMESTAMP NOT NULL,
                author TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                signature TEXT NOT NULL
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_messages_author ON messages(author)')
        conn.commit()

class KeyManager:
    def __init__(self, keys_dir):
        self.keys_dir = Path(keys_dir)
        self.keys_dir.mkdir(exist_ok=True)
        self.public_keys_dir = self.keys_dir / 'public_keys'
        self.public_keys_dir.mkdir(exist_ok=True)
        self.private_key_path = self.keys_dir / 'private.pem'
        self._ensure_keypair()
    
    def _ensure_keypair(self):
        if not self.private_key_path.exists():
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Save private key
            with open(self.private_key_path, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
    
    def get_private_key(self):
        with open(self.private_key_path, 'rb') as f:
            return serialization.load_pem_private_key(f.read(), password=None)
    
    def get_public_key(self, username):
        key_path = self.public_keys_dir / f'{username}.pub'
        if not key_path.exists():
            return None
        with open(key_path, 'rb') as f:
            return serialization.load_pem_public_key(f.read())
    
    def save_public_key(self, username, key_pem):
        key_path = self.public_keys_dir / f'{username}.pub'
        with open(key_path, 'wb') as f:
            f.write(key_pem)
    
    def rename_public_key(self, old_username, new_username):
        old_path = self.public_keys_dir / f'{old_username}.pub'
        new_path = self.public_keys_dir / f'{new_username}.pub'
        if old_path.exists():
            old_path.rename(new_path)

    def sign_message(self, message):
        private_key = self.get_private_key()
        signature = private_key.sign(
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature.hex()
    
    def verify_signature(self, message, signature_hex, username):
        public_key = self.get_public_key(username)
        if not public_key:
            return False
        
        try:
            signature = bytes.fromhex(signature_hex)
            public_key.verify(
                signature,
                message.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except:
            return False

class MessageManager:
    def __init__(self, key_manager):
        self.key_manager = key_manager
        init_db()

    def save_message(self, content, author, msg_type='message'):
        # Create message document
        timestamp = datetime.now()
        signature = self.key_manager.sign_message(content)
        
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO messages (date, author, type, content, signature)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, author, msg_type, content, signature))
            conn.commit()
            
            # Return the inserted message
            c.execute('''
                SELECT * FROM messages WHERE id = last_insert_rowid()
            ''')
            row = c.fetchone()
            return dict(row)

    def get_messages(self):
        with get_db() as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM messages ORDER BY date ASC')
            return [dict(row) for row in c.fetchall()]

class ChatRequestHandler(SimpleHTTPRequestHandler):
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,20}$')
    
    def do_GET(self):
        if self.path == '/messages':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            messages = self.server.message_manager.get_messages()
            self.wfile.write(json.dumps(messages, default=str).encode())
            return
        elif self.path == '/verify_username':
            self._send_json({'username': self._get_current_username()})
        else:
            super().do_GET()
    
    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len).decode() if content_len > 0 else ''
        
        if self.path == '/messages':
            try:
                data = json.loads(body)
                if not data.get('content'):
                    self.send_error(400, 'Content required')
                    return
                
                message = self.server.message_manager.save_message(
                    content=data['content'],
                    author=data.get('author', 'anonymous'),
                    msg_type=data.get('type', 'message')
                )
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'message': message}, default=str).encode())
                return
            except json.JSONDecodeError:
                self.send_error(400, 'Invalid JSON')
                return
            except Exception as e:
                self.send_error(500, str(e))
                return
        
        self.send_error(404)

    def _get_current_username(self):
        return 'anonymous'  # For now, we'll implement proper session management later
    
    def _send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def main():
    server = HTTPServer(
        ('', int(os.getenv('PORT', 8000))),
        ChatRequestHandler
    )
    server.message_manager = MessageManager(KeyManager('keys'))
    print(f"Server running on port {server.server_port}")
    server.serve_forever()

if __name__ == '__main__':
    main()
