import sys
import email
import psycopg2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()
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

    def store_email(self, sender, recipient, subject, body, alias=None):
        """Store the email in the database"""
        try:
            # Get user_id from the email alias
            user_id = self.get_user_id_from_alias(recipient)
            if user_id is None:
                raise ValueError(f"No user found for email alias: {recipient}")
                
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO email (sender, recipient, subject, body, alias_used, user_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (sender, recipient, subject, body, alias, user_id)
                )
                self.conn.commit()
                return cur.fetchone()[0]
        except Exception as e:
            self.conn.rollback()
            print(f"Error storing email: {e}", file=sys.stderr)
            raise

    def forward_email(self, to_email, from_email, subject, body):
        """Forward an email to the specified address"""
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = f"Fwd: {subject}"
        
        # Add the original email as an attachment or in the body
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Error forwarding email: {e}", file=sys.stderr)
            return False

    def process_email(self, raw_email):
        """Process an incoming email"""
        msg = email.message_from_string(raw_email)
        
        sender = msg['from']
        to = msg['to']
        subject = msg['subject']
        
        # Extract body (text/plain)
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode(errors='replace')
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors='replace')
        
        # Extract the local part from the recipient email
        recipient_local = to.split('@')[0].lower()
        
        # Check if this is an alias
        forwarding_email, username = self.get_forwarding_email(recipient_local)
        
        if forwarding_email:
            # This is an alias, forward the email
            try:
                # Store the original email
                email_id = self.store_email(sender, to, subject, body, recipient_local)
                
                # Forward the email
                success = self.forward_email(
                    to_email=forwarding_email,
                    from_email=f"{recipient_local}@{self.email_domain}",
                    subject=subject,
                    body=body
                )
                
                if not success:
                    print(f"Failed to forward email to {forwarding_email}", file=sys.stderr)
                
                return True
                
            except Exception as e:
                print(f"Error processing email: {e}", file=sys.stderr)
                return False
        else:
            # Not an alias, just store it
            try:
                self.store_email(sender, to, subject, body)
                return True
            except Exception as e:
                print(f"Error storing email: {e}", file=sys.stderr)
                return False

def main():
    # Read email from stdin
    raw_email = sys.stdin.read()
    
    # Process the email
    processor = EmailProcessor()
    processor.process_email(raw_email)

if __name__ == '__main__':
    main()