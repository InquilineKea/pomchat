# PomChat - Secure Chat System

A secure chat system with message signing, username management, and SQLite storage. Messages are stored in a SQLite database, and usernames are verified cryptographically.

## Features

- Message signing with RSA keys
- Secure username changes with cryptographic verification
- Message persistence in SQLite database
- Works with and without JavaScript
- Clean, simple interface

## Deployment Options

### Option 1: One-Click Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template/pomchat?referralCode=cascade)

1. Click the "Deploy on Railway" button above
2. Create a Railway account if you don't have one (free tier available)
3. Your app will be automatically deployed with HTTPS and a public URL
4. The deployment process takes about 2-3 minutes
5. Once deployed, you can access your app at the provided URL

### Option 2: Deploy to DigitalOcean

[![Deploy to DigitalOcean](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/InquilineKea/pomchat/tree/main)

1. Click the "Deploy to DigitalOcean" button above
2. Create a DigitalOcean account if you don't have one
3. Your app will be deployed with HTTPS and a public URL

### Option 3: Manual Cloud Deployment

1. Clone the repository:
```bash
git clone https://github.com/InquilineKea/pomchat.git
cd pomchat
```

2. Deploy to any cloud platform that supports Docker:
```bash
# Using Docker Compose
docker-compose up -d

# Or using plain Docker
docker build -t pomchat .
docker run -p 80:8000 -v pomchat_data:/app/data pomchat
```

#### Cloud Platform Quick-Start Guides:

**Heroku:**
```bash
heroku create
git push heroku main
```

**Google Cloud Run:**
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT/pomchat
gcloud run deploy --image gcr.io/YOUR_PROJECT/pomchat --platform managed
```

**AWS Elastic Beanstalk:**
```bash
eb init -p docker pomchat
eb create pomchat-env
```

### Option 4: Local Development

1. Clone and set up:
```bash
git clone https://github.com/InquilineKea/pomchat.git
cd pomchat
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
```

3. Run the server:
```bash
python server.py
```

## Security Notes

- All messages are cryptographically signed
- Username changes require signature verification
- Messages are stored in a SQLite database with proper escaping
- The application runs as a non-root user in Docker
- Persistent data is stored in a Docker volume for production deployments

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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
