import sys
import email
import psycopg2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
import email.utils

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the path to the .env file in that directory
dotenv_path = os.path.join(script_dir, '.env')
# Load the .env file from the explicit path
load_dotenv(dotenv_path=dotenv_path)
db_url = os.getenv('DATABASE_URL')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'localhost')
SMTP_PORT = int(os.getenv('SMTP_PORT', 1025))  # Default to local testing port
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
EMAIL_DOMAIN = os.getenv('EMAIL_DOMAIN', 'rebox.sh')

class EmailProcessor:
    def __init__(self):
        self.conn = psycopg2.connect(db_url)
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.smtp_username = SMTP_USERNAME
        self.smtp_password = SMTP_PASSWORD
        self.email_domain = EMAIL_DOMAIN

    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    def get_forwarding_email(self, alias):
        """Get the forwarding email for a given alias"""
        # Split alias into title and random parts
        if '.' in alias:
            alias_parts = alias.split('.')
            if len(alias_parts) == 2:
                alias_title, alias_random = alias_parts
                with self.conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT ea.forwarding_email, u.username 
                        FROM email_alias ea
                        JOIN "user" u ON ea.user_id = u.id
                        WHERE ea.alias_title = %s 
                        AND ea.alias_random = %s 
                        AND ea.alias_domain = %s
                        """,
                        (alias_title, alias_random, self.email_domain)
                    )
                    result = cur.fetchone()
                    return result if result else (None, None)
        return (None, None)

    def get_user_id_from_alias(self, alias):
        """Get user_id from email alias (format: alias_title.alias_random@domain)"""
        try:
            # Extract alias parts (format: alias_title.alias_random@domain)
            local_part = alias.split('@')[0]
            if '.' in local_part:
                alias_title, alias_random = local_part.split('.', 1)
                with self.conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT user_id FROM email_alias
                        WHERE alias_title = %s 
                        AND alias_random = %s 
                        AND alias_domain = %s
                        """,
                        (alias_title, alias_random, self.email_domain)
                    )
                    result = cur.fetchone()
                    return result[0] if result else None
            return None
        except Exception as e:
            print(f"Error looking up user from alias: {e}", file=sys.stderr)
            return None

    def get_user_id_from_username(self, username):
        """Get user_id from a username."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id FROM "user" WHERE username = %s
                    """,
                    (username,)
                )
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Error looking up user from username: {e}", file=sys.stderr)
            return None

    def store_email(self, user_id, sender, sender_name, recipient, subject, body, alias_used=None):
        """Store the email in the database for a given user_id."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO email (user_id, sender, sender_name, recipient, subject, body, alias_used)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (user_id, sender, sender_name, recipient, subject, body, alias_used)
                )
                self.conn.commit()
                return cur.fetchone()[0]
        except Exception as e:
            self.conn.rollback()
            print(f"Error storing email: {e}", file=sys.stderr)
            raise

    def forward_email(self, to_email, from_email, subject, body, original_msg=None):
        """Forward an email to the specified address"""
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = f"Fwd: {subject}"
        
        # Preserve the original Date header if it exists
        if original_msg and 'Date' in original_msg:
            msg['Date'] = original_msg['Date']
        else:
            msg['Date'] = email.utils.formatdate()
        
        # Add Message-ID header (required for email delivery)
        domain = self.email_domain or 'rebox.sh'  # Fallback domain if not set
        msg['Message-ID'] = email.utils.make_msgid(domain=domain)
        
        # Add the original email as an attachment or in the body
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_username and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            return True
        except Exception as e:
            raise e

    def process_email(self, raw_email, recipient_arg=None):
        """Process an incoming email by identifying the recipient and storing or forwarding it."""
        msg = email.message_from_string(raw_email)

        # Determine recipient
        to = recipient_arg or email.utils.parseaddr(msg['to'])[1] or msg['to']
        if not to:
            print("Could not determine recipient. Dropping email.", file=sys.stderr)
            return False

        recipient_local = to.split('@')[0].lower()
        user_id = None
        is_alias = False
        owner_username = None

        # Check if recipient is an alias
        forwarding_email, owner_username = self.get_forwarding_email(recipient_local)

        if owner_username:
            is_alias = True
            user_id = self.get_user_id_from_username(owner_username)
        else:
            # Not an alias, check if it's a primary user email
            user_id = self.get_user_id_from_username(recipient_local)

        if not user_id:
            print(f"Recipient address {to} not found. Dropping email.", file=sys.stderr)
            return False

        # Now that we have a user, parse the rest of the email
        sender_name, sender_addr = email.utils.parseaddr(msg['from'])
        sender = sender_addr or msg['from']
        subject = msg['subject']
        
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode(errors='replace')
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors='replace')

        # Store the email
        try:
            alias_to_store = recipient_local if is_alias else None
            self.store_email(user_id, sender, sender_name, to, subject, body, alias_used=alias_to_store)
        except Exception as e:
            print(f"Failed to store email for {to}. Reason: {e}", file=sys.stderr)
            return False

        # If it was an alias with a forwarding address, forward it
        if is_alias and forwarding_email:
            try:
                self.forward_email(
                    forwarding_email,
                    f"{owner_username}@{self.email_domain}",
                    subject, body, msg
                )
                print(f"Email forwarded to {forwarding_email}")
            except Exception as e:
                print(f"Failed to forward email to {forwarding_email}. Reason: {e}", file=sys.stderr)

        return True

def main():
    # Read email from stdin
    raw_email = sys.stdin.read()

    # Get recipient from command-line argument if provided by Postfix (from master.cf)
    recipient = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Process the email
    processor = EmailProcessor()
    processor.process_email(raw_email, recipient_arg=recipient)

if __name__ == '__main__':
    main()