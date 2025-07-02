import subprocess
import argparse
from faker import Faker
from email.mime.text import MIMEText

# Set up argument parsing
parser = argparse.ArgumentParser(description='Send a mock email to the email processor')
parser.add_argument('recipient', help='Recipient email address (must be a valid user in the system)')
args = parser.parse_args()

# Initialize Faker
fake = Faker()

# Generate mock email data
sender = fake.email()
recipient = args.recipient  # Use the provided recipient, ex shopping.apple123@rebox.sh
subject = fake.sentence()
body = fake.paragraph()

# Create the email message
msg = MIMEText(body)
msg['From'] = sender
msg['To'] = recipient
msg['Subject'] = subject

raw_email = msg.as_string()

print("--- Mock Email ---")
print(raw_email)
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

except FileNotFoundError:
    print("Error: 'python3' command not found. Make sure Python 3 is installed and in your PATH.")
except subprocess.CalledProcessError as e:
    print(f"Error executing email_processor.py: {e}")
    print("--- stdout ---")
    print(e.stdout)
    print("--- stderr ---")
    print(e.stderr)
    print("--------------")
