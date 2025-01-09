import os
import sqlite3
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_database():
    """Initialize the SQLite database with the required schema."""
    conn = sqlite3.connect('pomchat.db')
    c = conn.cursor()
    
    # Create messages table
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TIMESTAMP NOT NULL,
            author TEXT NOT NULL,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            signature TEXT NOT NULL,
            original_file TEXT
        )
    ''')
    
    # Create indexes
    c.execute('CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_messages_author ON messages(author)')
    
    conn.commit()
    return conn

def migrate_messages():
    """Migrate messages from text files to SQLite database."""
    conn = init_database()
    c = conn.cursor()
    
    # Get messages directory from env
    messages_dir = Path(os.getenv('MESSAGES_DIRECTORY', 'messages'))
    
    if not messages_dir.exists():
        print(f"No messages directory found at {messages_dir}")
        return
    
    # Process each message file
    for message_file in messages_dir.glob('*.txt'):
        try:
            # Parse filename for timestamp
            filename = message_file.stem  # Remove .txt extension
            timestamp_str = filename.split('_')[0] + '_' + filename.split('_')[1]
            timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            
            # Read message content
            with open(message_file, 'r') as f:
                content = {}
                headers_done = False
                message_content = []
                
                for line in f:
                    line = line.strip()
                    if not headers_done:
                        if line == '':
                            headers_done = True
                            continue
                        key, value = line.split(': ', 1)
                        content[key.lower()] = value
                    else:
                        message_content.append(line)
                
                # Insert into SQLite
                c.execute('''
                    INSERT INTO messages 
                    (date, author, type, content, signature, original_file)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp,
                    content.get('author', 'anonymous'),
                    content.get('type', 'message'),
                    '\n'.join(message_content),
                    content.get('signature', ''),
                    message_file.name
                ))
                
                print(f"Migrated {message_file.name}")
        
        except Exception as e:
            print(f"Error migrating {message_file}: {e}")
    
    conn.commit()
    
    # Print statistics
    c.execute('SELECT COUNT(*) FROM messages')
    count = c.fetchone()[0]
    print(f"\nMigration completed!")
    print(f"Total messages in SQLite: {count}")
    
    conn.close()

if __name__ == '__main__':
    migrate_messages()
