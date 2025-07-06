# Postfix Configuration Guide for Rebox

This document outlines the necessary steps to configure Postfix on a Debian-based server (like a DigitalOcean droplet) to receive all emails for a domain and pipe them to the `email_processor.py` script for processing.

## 1. Initial Setup

Ensure Postfix is installed. If it was reinstalled, choose **"Internet Site"** during the setup prompt. The mail name should be your domain (e.g., `rebox.sh`).

## 2. Configure `main.cf`

These settings tell Postfix to handle `rebox.sh` as a "virtual" domain and pass all mail for it to a custom transport service we will create called `rebox`.

Use the `postconf` command to apply these settings safely:

```bash
# Tell Postfix which domain to handle virtually
postconf -e "virtual_mailbox_domains = rebox.sh"

# Tell Postfix to use our custom "rebox" service for that domain
postconf -e "virtual_transport = rebox:"

# IMPORTANT: Stop Postfix from rejecting mail for non-existent local users
postconf -e "local_recipient_maps ="

# CRITICAL: Ensure the domain is NOT in `mydestination` to avoid conflicts
postconf -e "mydestination = \$myhostname, localhost.\$mydomain, localhost"
```

## 3. Configure `master.cf`

This step defines the custom `rebox` transport service. We append this configuration to the end of the `/etc/postfix/master.cf` file.

```bash
# Append the custom transport definition to master.cf
echo '
# ==========================================================================
# Custom Rebox transport to pipe email to the processor script
# ==========================================================================
rebox     unix  -       n       n       -       -       pipe
  flags=R user=www-data
  argv=/app/venv/bin/python3 /app/email_processor.py ${recipient}' >> /etc/postfix/master.cf
```

**Explanation of options:**
- `pipe`: Specifies that Postfix should stream the email to a command.
- `user=www-data`: Runs the command as the `www-data` user for security.
- `argv`: The command to execute. `${recipient}` is crucial as it passes the recipient's email address to our script as a command-line argument.

## 4. Set Script Permissions

The `email_processor.py` script must be executable by the `www-data` user.

```bash
# Make the script executable
chmod 755 /app/email_processor.py

# Change the owner to www-data (recommended)
chown www-data:www-data /app/email_processor.py
```

## 5. Firewall Configuration (DigitalOcean)

To allow the `email_processor.py` script to forward emails via an external SMTP service (like Mailtrap or SendGrid), you must allow outgoing traffic on the correct port.

1.  In the DigitalOcean Control Panel, go to **Networking -> Firewalls**.
2.  Select the firewall attached to your droplet.
3.  Go to the **Outbound Rules** tab.
4.  Add a new **TCP** rule:
    -   **Port Range:** The port your SMTP service uses (e.g., `587` or `2525`).
    -   **Destination:** Leave as default (`All IPv4` and `All IPv6`).
5.  Save the rule.

## 6. Configure an SMTP Relay for Outbound Mail (Crucial for Cloud Hosts)

### The Problem

Most cloud providers, including DigitalOcean, block **outbound** connections on port 25 to prevent spam. This will cause your server to fail when it tries to send emails, such as bounce messages (Non-Delivery Reports) or notifications. You will see errors like `Connection timed out` in your Postfix logs when it tries to connect to other mail servers.

### The Solution

The solution is to configure Postfix to send all outbound mail through a dedicated SMTP relay service (like Mailtrap, SendGrid, or Mailgun). These services listen on alternative, unblocked ports (like 587, 465, or 2525) and handle the final delivery for you.

**Important:** This change only affects **outbound** mail. Your server will continue to **receive** inbound mail from the internet on port 25 as normal.

### Step-by-Step Configuration (using Mailtrap)

1.  **Get Relay Credentials:**
    Log in to your Mailtrap account and get your SMTP credentials (Host, Port, Username, and Password).

2.  **Edit Postfix Configuration (`/etc/postfix/main.cf`):**
    Add the following lines to the end of the file. Use port `587` or `2525` if `587` is also blocked.

    ```bash
    sudo nano /etc/postfix/main.cf
    ```

    ```ini
    # SMTP Relay Configuration
    relayhost = [smtp.mailtrap.io]:587

    # Enable SASL authentication for the relay
    smtp_sasl_auth_enable = yes
    smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
    smtp_sasl_security_options = noanonymous

    # Force TLS encryption for security
    smtp_tls_security_level = encrypt
    ```

3.  **Create SASL Password File:**
    Create a file to store your relay credentials.

    ```bash
    sudo nano /etc/postfix/sasl_passwd
    ```

    Add your credentials in this specific format:
    `[smtp.mailtrap.io]:587 YOUR_USERNAME:YOUR_PASSWORD`

4.  **Secure and Process the Password File:**
    Set secure permissions and create the Postfix lookup table (`.db` file).

    ```bash
    # Set permissions so only root can read/write
    sudo chmod 600 /etc/postfix/sasl_passwd

    # Create the Postfix database file
    sudo postmap /etc/postfix/sasl_passwd
    ```

5.  **Reload Postfix:**
    Apply the new configuration.

    ```bash
    sudo systemctl reload postfix
    ```

Your server will now correctly route all outbound mail through the relay, bypassing the port blocks.

#### A Note on Bounce Messages and Cloud Relays

By default, Postfix sends bounce messages with a **null sender** (`MAIL FROM:<>`). This is a critical security feature of the email standard, designed to prevent infinite mail loops. However, **many commercial SMTP relays and cloud providers block null senders** for their own security and anti-spam policies. You may encounter an error like `550 5.7.1 Sending from domain is not allowed` when trying to send a bounce message to a relay.

### General Tip: Rewriting Sender Addresses
Postfix can rewrite sender addresses before they are sent to the relay. The two main tools for this are `sender_canonical_maps` and `smtp_generic_maps`.

*   **`sender_canonical_maps`**: A general-purpose tool that rewrites addresses early in the mail processing chain. It's good for standardizing addresses system-wide.
*   **`smtp_generic_maps`**: A more targeted tool applied by the SMTP client *just before* sending mail to a relay. This is the most reliable method for fixing addresses to meet a relay's specific requirements.

#### Recommended Implementation

For maximum reliability, using `smtp_generic_maps` with a regular expression table is the best approach.

1.  **Configure `main.cf`:**
    Edit `/etc/postfix/main.cf` to use a `regexp` map.

    ```ini
    # Rewrite sender addresses just before sending to the relay
    smtp_generic_maps = regexp:/etc/postfix/generic_maps
    ```

2.  **Create the Map File (`/etc/postfix/generic_maps`):**
    Create a file with the rewrite rules. The first column is a regular expression to match the sender.

    ```
    # /etc/postfix/generic_maps

    # Match local system users
    /^root$/         noreply@rebox.sh
    /^www-data$/    noreply@rebox.sh

    # Match the internal empty sender for bounce messages
    /^$/            noreply@rebox.sh
    ```

3.  **Reload Postfix:**
    Regexp maps do not use the `postmap` command. Just reload the service.

    ```bash
    sudo systemctl reload postfix
    ```

## 7. Final Verification

After applying all configurations, restart Postfix and check its status.

```bash
# Restart the service to apply all changes
systemctl restart postfix

# Check that the service is active and running
systemctl status postfix

# Check the mail log for errors and successful deliveries
tail -f /var/log/mail.log
