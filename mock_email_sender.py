import subprocess
import argparse
import psycopg2
import os
import sys
import email.utils
from faker import Faker
from email.mime.text import MIMEText

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def get_db_connection():
    """Create a database connection"""
    return psycopg2.connect(os.getenv('DATABASE_URL'))

def get_random_email_alias():
    """Get a random email alias from the database"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT CONCAT(alias_title, '.', alias_random, '@', alias_domain) as email
                FROM email_alias
                ORDER BY RANDOM()
                LIMIT 1
                """
            )
            result = cur.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"Error fetching random email alias: {e}", file=sys.stderr)
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Send a mock email to the email processor')
    parser.add_argument('recipient', nargs='?', help='Recipient email address (optional)')
    args = parser.parse_args()

    # Initialize Faker
    fake = Faker()

    # Generate mock email data
    sender = fake.email()
    
    # Use provided recipient or get a random one from the database
    recipient = args.recipient
    if not recipient:
        recipient = get_random_email_alias()
        if not recipient:
            print("Error: No recipient provided and no email aliases found in the database.")
            print("Please provide a recipient or ensure there are email aliases in the database.")
            return 1
    
    subject = fake.sentence()
    body = fake.paragraph()

    # Create the email message
    msg = MIMEText(body)
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject
    msg['Date'] = email.utils.formatdate()
    # Add Message-ID header (required for email delivery)
    domain = os.getenv('EMAIL_DOMAIN', 'rebox.sh')  # Fallback domain if not set
    msg['Message-ID'] = email.utils.make_msgid(domain=domain)

    raw_email = msg.as_string()

    print(f"--- Mock Email ---")
    print(f"From: {sender}")
    print(f"To: {recipient}")
    print(f"Subject: {subject}")
    print(f"\n{body}")
    print("--------------------\n")

    # Call email_processor.py and pass the raw email via stdin
    try:
        print("Calling email_processor.py...")
        process = subprocess.run(
            ['python3', 'email_processor.py'],
            input=raw_email,
            text=True,
            capture_output=True,
            check=True
        )
        print("--- email_processor.py stdout ---")
        print(process.stdout)
        print("-----------------------------------")
        if process.stderr:
            print("--- email_processor.py stderr ---")
            print(process.stderr)
            print("-----------------------------------")
        print("\nScript finished successfully.")
        return 0
    except FileNotFoundError:
        print("Error: 'python3' command not found. Make sure Python 3 is installed and in your PATH.")
        return 1
    except subprocess.CalledProcessError as e:
        print(f"Error executing email_processor.py: {e}")
        print("--- stdout ---")
        print(e.stdout)
        print("--- stderr ---")
        print(e.stderr)
        print("--------------")
        return 1

if __name__ == '__main__':
    sys.exit(main())
