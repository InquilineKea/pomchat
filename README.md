# PomChat - Minimal Implementation

A secure chat system with message signing and username management. Messages are stored as text files, and usernames are verified cryptographically.

## Features

- Message signing with RSA keys
- Secure username changes with cryptographic verification
- Message persistence in text files
- Works with and without JavaScript
- Clean, simple interface

## Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
python server.py
```

The server will create necessary directories (`messages/` and `keys/`) on first run.

## Usage

1. Open http://localhost:8000 in your browser
2. Start with default username 'anonymous'
3. Send messages using the form at the bottom
4. Change username using the button at the top

## Message Format

Messages are stored as text files with the format:
```
Date: ISO-8601 timestamp
Author: username
Type: message|username_change|system|error
Signature: hex_encoded_signature

message content
```

## Security

- Each user has an RSA public/private keypair
- Messages are signed with the sender's private key
- Username changes require signature verification
- Public keys are stored in `keys/public_keys/`

## Development

- `server.py`: Main server implementation
- `static/`: Frontend files
  - `index.html`: Main page
  - `css/`: Stylesheets
  - `js/`: JavaScript files

## License

MIT
