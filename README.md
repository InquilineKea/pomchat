# PomChat - Secure Chat System

A secure chat system with message signing, username management, and SQLite storage. Messages are stored in a SQLite database, and usernames are verified cryptographically.

## Features

- Message signing with RSA keys
- Secure username changes with cryptographic verification
- Message persistence in SQLite database
- Works with and without JavaScript
- Clean, simple interface

## Installation and Deployment Options

### Option 1: Local Development

1. Clone the repository:
```bash
git clone https://github.com/InquilineKea/pomchat.git
cd pomchat
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the environment file and configure it:
```bash
cp .env.example .env
```

5. Run the server:
```bash
python server.py
```

The server will create necessary directories (`keys/`) and database on first run.

### Option 2: Docker (Recommended for Production)

1. Using Docker Compose (easiest):
```bash
docker-compose up -d
```

2. Or using Docker directly:
```bash
docker build -t pomchat .
docker run -p 8000:8000 -v pomchat_data:/app/data pomchat
```

The application will be available at http://localhost:8000

## Usage

1. Open http://localhost:8000 in your browser
2. Start with default username 'anonymous'
3. Send messages using the form at the bottom
4. Change username using the button at the top

## Data Storage

Messages are stored in a SQLite database with the following schema:
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    author TEXT NOT NULL,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    signature TEXT NOT NULL,
    original_file TEXT
);
```

## Security Notes

- All messages are cryptographically signed
- Username changes require signature verification
- Messages are stored in a SQLite database with proper escaping
- The application runs as a non-root user in Docker
- Persistent data is stored in a Docker volume for production deployments

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
