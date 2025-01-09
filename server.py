#!/usr/bin/env python3

import json
import os
import subprocess
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs
import re
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

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
    def __init__(self, messages_dir, key_manager):
        self.messages_dir = Path(messages_dir)
        self.messages_dir.mkdir(exist_ok=True)
        self.key_manager = key_manager
    
    def save_message(self, content, author, type='message'):
        timestamp = datetime.now().isoformat()
        filename = f"{datetime.now():%Y%m%d_%H%M%S}_{author}.txt"
        signature = self.key_manager.sign_message(content)
        
        message = f"""Date: {timestamp}
Author: {author}
Type: {type}
Signature: {signature}

{content}"""
        
        with open(self.messages_dir / filename, 'w') as f:
            f.write(message)
        return filename
    
    def read_messages(self):
        messages = []
        for file in sorted(self.messages_dir.glob('*.txt')):
            with open(file) as f:
                content = f.read()
                messages.append(self._parse_message(content))
        return messages
    
    def _parse_message(self, content):
        lines = content.split('\n')
        headers = {}
        message_content = []
        in_headers = True
        
        for line in lines:
            if in_headers:
                if line == '':
                    in_headers = False
                    continue
                key, value = line.split(': ', 1)
                headers[key.lower()] = value
            else:
                message_content.append(line)
        
        return {
            'date': headers.get('date'),
            'author': headers.get('author'),
            'type': headers.get('type', 'message'),
            'signature': headers.get('signature'),
            'content': '\n'.join(message_content)
        }

class ChatRequestHandler(SimpleHTTPRequestHandler):
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,20}$')
    
    def do_GET(self):
        if self.path == '/messages':
            self._send_json(self.server.message_manager.read_messages())
        elif self.path == '/verify_username':
            self._send_json({'username': self._get_current_username()})
        else:
            super().do_GET()
    
    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len).decode() if content_len > 0 else ''
        
        if self.path == '/messages':
            self._handle_message(body)
        elif self.path == '/username':
            self._handle_username_change(body)
        else:
            self.send_error(404)
    
    def _handle_message(self, body):
        if self.headers.get('Content-Type') == 'application/json':
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_error(400, 'Invalid JSON')
                return
        else:
            data = parse_qs(body)
            data = {
                'content': data.get('content', [''])[0],
                'author': self._get_current_username(),
                'type': 'message'
            }
        
        if not data.get('content'):
            self.send_error(400, 'Content required')
            return
        
        filename = self.server.message_manager.save_message(**data)
        self._send_json({'status': 'success', 'id': filename})
    
    def _handle_username_change(self, body):
        try:
            data = json.loads(body)
            old_username = data['old_username']
            new_username = data['new_username']
        except (json.JSONDecodeError, KeyError):
            self.send_error(400, 'Invalid request')
            return
        
        if not self.USERNAME_PATTERN.match(new_username):
            self.send_error(400, 'Invalid username format')
            return
        
        if not self.server.key_manager.verify_signature(
            json.dumps({'old_username': old_username, 'new_username': new_username}),
            data.get('signature', ''),
            old_username
        ):
            self.send_error(401, 'Invalid signature')
            return
        
        self.server.key_manager.rename_public_key(old_username, new_username)
        self._send_json({'status': 'success', 'username': new_username})
    
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
    server.message_manager = MessageManager('messages', KeyManager('keys'))
    print(f"Server running on port {server.server_port}")
    server.serve_forever()

if __name__ == '__main__':
    main()
