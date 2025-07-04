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

## 6. Final Verification

After applying all configurations, restart Postfix and check its status.

```bash
# Restart the service to apply all changes
systemctl restart postfix

# Check that the service is active and running
systemctl status postfix

# Check the mail log for errors and successful deliveries
tail -f /var/log/mail.log
```
