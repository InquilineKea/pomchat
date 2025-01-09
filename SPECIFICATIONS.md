# PomChat Minimal Implementation Spec

Create a secure chat system with message signing and username management. Messages are stored as text files, and usernames are verified cryptographically.

## Core Requirements

### Message Storage
- Store each message as a text file: `YYYYMMDD_HHMMSS_username.txt`
- Message format:
  ```
  Date: ISO-8601 timestamp
  Author: username
  Type: message|username_change|system|error
  [Signature: hex_encoded_signature]

  message content
  ```

### Security
- Each user has RSA public/private keypair
- Store public keys as `public_keys/username.pub`
- Sign messages with private key
- Verify username changes with signatures

### API Endpoints
```
GET /messages
  Returns: Array of message objects

POST /messages
  Body: { content, type, author }
  Signs and saves message

GET /verify_username
  Returns: Current verified username
```

### Username Changes
1. Client sends username change message:
   ```json
   {
     "type": "username_change",
     "content": {
       "old_username": "old",
       "new_username": "new"
     }
   }
   ```
2. Server verifies signature with old username's public key
3. Moves public key file to new username
4. Returns success/error

### Validation
- Usernames: `/^[a-zA-Z0-9_]{3,20}$/`
- Required message fields: date, author, type, content
- Valid message types: message, username_change, system, error

## Example Message File
```
Date: 2025-01-08T13:52:18-05:00
Author: alice
Type: message
Signature: a1b2c3...

Hello, world!
```

## Frontend Implementation

### HTML Structure
```html
<!DOCTYPE html>
<html>
<head>
    <title>BookChat</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <noscript>
        <link rel="stylesheet" href="/static/css/noscript.css">
    </noscript>
</head>
<body>
    <div class="container">
        <div class="header">
            <span id="current-username">Current username: anonymous</span>
            <!-- No-JS username form -->
            <form method="POST" action="/username" class="nojs-only">
                <input name="new_username" required>
                <button type="submit">Change Username</button>
            </form>
            <!-- JS-only button -->
            <button id="change-username-btn" class="js-only">Change Username</button>
        </div>
        
        <div id="messages">
            <!-- No-JS refresh -->
            <form method="GET" action="/" class="nojs-only">
                <button type="submit">Refresh</button>
            </form>
            <div id="messages-container"></div>
        </div>
        
        <!-- Message form works with/without JS -->
        <form method="POST" action="/messages" class="message-form">
            <textarea name="content" required></textarea>
            <button type="submit">Send</button>
        </form>
    </div>
    <script src="/static/js/main.js"></script>
</body>
</html>
```

### JavaScript Core Functions
```javascript
// Core state
let currentUsername = 'anonymous';

// Main functions
async function loadMessages() {
    const messages = await fetch('/messages').then(r => r.json());
    displayMessages(messages);
}

async function sendMessage(content, type = 'message') {
    await fetch('/messages', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ content, type, author: currentUsername })
    });
    await loadMessages();
}

async function changeUsername(newUsername) {
    if (!/^[a-zA-Z0-9_]{3,20}$/.test(newUsername)) return false;
    const content = JSON.stringify({
        old_username: currentUsername,
        new_username: newUsername
    });
    const success = await sendMessage(content, 'username_change');
    if (success) {
        currentUsername = newUsername;
        localStorage.setItem('username', newUsername);
    }
    return success;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadMessages();
    setupEventListeners();
});
```

## Python Server Implementation

### Core Classes
```python
class KeyManager:
    def __init__(self, keys_dir):
        self.keys_dir = Path(keys_dir)
        self.private_key_path = self.keys_dir / 'local.pem'
        self.public_key_path = self.keys_dir / 'local.pub'
        self._ensure_keypair()
    
    def sign_message(self, message):
        return subprocess.run(
            ['openssl', 'dgst', '-sha256', '-sign', str(self.private_key_path)],
            input=message.encode(),
            capture_output=True
        ).stdout.hex()
    
    def verify_signature(self, message, signature_hex, public_key_pem):
        # Convert hex signature to bytes and verify with OpenSSL
        return self._verify_with_openssl(message, signature_hex, public_key_pem)

class MessageManager:
    def __init__(self, messages_dir, key_manager):
        self.messages_dir = Path(messages_dir)
        self.key_manager = key_manager
    
    def save_message(self, content, author, type='message'):
        timestamp = datetime.now().isoformat()
        filename = f"{timestamp:%Y%m%d_%H%M%S}_{author}.txt"
        signature = self.key_manager.sign_message(content)
        
        message = f"""Date: {timestamp}
Author: {author}
Type: {type}
Signature: {signature}

{content}"""
        
        (self.messages_dir / filename).write_text(message)
        return filename
    
    def read_messages(self):
        messages = []
        for file in sorted(self.messages_dir.glob('*.txt')):
            content = file.read_text()
            messages.append(self._parse_message(content))
        return messages

class ChatServer(HTTPServer):
    def __init__(self, messages_dir, keys_dir):
        self.message_manager = MessageManager(messages_dir, KeyManager(keys_dir))
        super().__init__(('', 8000), ChatRequestHandler)
```

### Request Handler
```python
class ChatRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/messages':
            self._send_json(self.server.message_manager.read_messages())
        elif self.path == '/verify_username':
            self._send_json(self._verify_username())
        else:
            super().do_GET()  # Serve static files
    
    def do_POST(self):
        content_len = int(self.headers['Content-Length'])
        body = self.rfile.read(content_len).decode()
        
        if self.path == '/messages':
            if self.headers.get('Content-Type') == 'application/json':
                data = json.loads(body)
            else:
                data = parse_qs(body)
                data = {
                    'content': data.get('content', [''])[0],
                    'author': 'anonymous',
                    'type': 'message'
                }
            
            filename = self.server.message_manager.save_message(**data)
            self._send_json({'status': 'success', 'id': filename})
```

## Implementation Notes
1. Default to 'anonymous' user if no username set
2. Verify signatures before username changes
3. Sort messages by timestamp when displaying
4. Sanitize all user inputs
5. Handle both JSON and form-data POST requests

# PomChat Specifications

## Overview

PomChat is a Pomodoro-integrated chat application that combines focused work sessions with collaborative communication. It helps users maintain productivity while staying connected with their team or study group.

## Core Features

### 1. Pomodoro Timer Integration
- Standard 25/5 minute work/break cycles
- Customizable timer durations
- Visual and audio notifications
- Sync timer status with chat status

### 2. Chat System
- Real-time messaging
- Message persistence
- User presence indicators
- Chat rooms/channels
- Direct messaging

### 3. Focus States
```
States:
- FOCUSING: During Pomodoro work session
- BREAK: During short break
- LONG_BREAK: During long break (after 4 cycles)
- IDLE: Timer not running
```

### 4. Message Types
```json
{
  "type": "message|status|timer|system",
  "content": "string",
  "author": "username",
  "timestamp": "ISO-8601",
  "focus_state": "FOCUSING|BREAK|LONG_BREAK|IDLE"
}
```

### 5. User Management
- Username-based authentication
- User profiles with:
  - Current focus state
  - Total focus time
  - Pomodoro completion stats
- Status indicators (online/focusing/break)

## Technical Requirements

### Backend
- Flask-based REST API
- SQLite database for message and user data
- WebSocket support for real-time updates
- Timer synchronization across clients

### Database Schema
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_focus_time INTEGER DEFAULT 0,
    pomodoros_completed INTEGER DEFAULT 0
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    author_id INTEGER,
    type TEXT NOT NULL,
    focus_state TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES users (id)
);

CREATE TABLE rooms (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE room_members (
    room_id INTEGER,
    user_id INTEGER,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms (id),
    FOREIGN KEY (user_id) REFERENCES users (id),
    PRIMARY KEY (room_id, user_id)
);
```

### API Endpoints
```
GET /api/timer
  Returns: Current timer state and time remaining

POST /api/timer/start
  Body: { duration: int }
  Starts a new timer

GET /api/messages
  Query: { room_id: int, before: timestamp }
  Returns: Array of messages

POST /api/messages
  Body: { content: string, room_id: int }
  Creates a new message

GET /api/users/me
  Returns: Current user's profile and stats

GET /api/rooms
  Returns: List of available chat rooms

POST /api/rooms
  Body: { name: string }
  Creates a new chat room
```

### WebSocket Events
```
client -> server:
  join_room: { room_id: int }
  leave_room: { room_id: int }
  message: { content: string, room_id: int }
  timer_sync: { state: string, remaining: int }

server -> client:
  message: { message object }
  timer_update: { state: string, remaining: int }
  user_status: { username: string, status: string }
  focus_change: { username: string, focus_state: string }
```

## Frontend Implementation

### Components
1. Timer Display
   - Current time remaining
   - Session type indicator
   - Start/pause/reset controls
   - Progress visualization

2. Chat Interface
   - Message list with infinite scroll
   - Input box with send button
   - User list with status indicators
   - Room list and selection

3. Stats Dashboard
   - Daily focus time
   - Pomodoros completed
   - Productivity trends
   - Team/room activity

### User Interface Requirements
- Clean, distraction-free design
- Dark/light theme support
- Mobile-responsive layout
- Keyboard shortcuts for common actions
- Accessibility compliance (WCAG 2.1)

### Local Storage
```javascript
{
  "username": string,
  "theme": "light|dark",
  "timerSettings": {
    "workDuration": number,
    "shortBreakDuration": number,
    "longBreakDuration": number,
    "autostart": boolean
  },
  "notifications": {
    "sound": boolean,
    "desktop": boolean
  }
}
```

## Deployment Requirements

### Environment Variables
```
DATABASE_URL=sqlite:///pomchat.db
SECRET_KEY=your-secret-key
WEBSOCKET_URL=ws://localhost:8000/ws
PORT=8000
DEBUG=False
```

### Dependencies
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-SocketIO==5.3.6
python-dotenv==1.0.0
SQLAlchemy==2.0.23
```

### Development Setup
1. Create virtual environment
2. Install dependencies
3. Initialize database
4. Run development server

### Production Considerations
- Use production-grade WSGI server (Gunicorn)
- Enable SSL/TLS
- Implement rate limiting
- Add request logging
- Set up monitoring
- Configure backup system
