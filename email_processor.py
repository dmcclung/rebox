import sys
import email
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
db_url = os.getenv('DATABASE_URL')

def store_email(sender, recipient, subject, body):
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO emails (sender, recipient, subject, body) VALUES (%s, %s, %s, %s)",
                (sender, recipient, subject, body)
            )
        conn.commit()
    finally:
        conn.close()

def main():
    # Read email from stdin
    raw_email = sys.stdin.read()
    msg = email.message_from_string(raw_email)
    
    sender = msg['from']
    recipient = msg['to']
    subject = msg['subject']
    
    # Extract body (text/plain)
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True).decode()
                break
    else:
        body = msg.get_payload(decode=True).decode()

    store_email(sender, recipient, subject, body)

if __name__ == '__main__':
    main()