import logging
import subprocess
import os
import smtplib
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from typing import cast

bp = Blueprint('send_email', __name__, url_prefix='/api')

@bp.route('/send', methods=['GET', 'POST'])
def send_email():
    if request.method == 'POST':
        # Logic to send email will go here
        recipient = request.form.get('recipient')
        subject = request.form.get('subject')
        body = request.form.get('body')

        email_domain = os.environ.get('EMAIL_DOMAIN', 'rebox.sh')
        from_address = f"{current_user.username}@{email_domain}"

        if not recipient or not subject or not body:
            return jsonify({'success': False, 'message': 'Recipient, subject, and body are required.'}), 400

        try:
            msg = MIMEMultipart()
            msg['From'] = from_address
            msg['To'] = recipient
            msg['Subject'] = subject
            msg['Date'] = formatdate()
            msg['Message-ID'] = make_msgid(domain=email_domain)
            msg.attach(MIMEText(body, 'plain'))

            smtp_server = cast(str, current_app.config.get('SMTP_SERVER'))
            smtp_port = cast(int, current_app.config.get('SMTP_PORT'))
            smtp_username = cast(str, current_app.config.get('SMTP_USERNAME'))
            smtp_password = cast(str, current_app.config.get('SMTP_PASSWORD'))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)

            return jsonify({'success': True, 'message': f'Email successfully sent to {recipient}!'}), 200
        except Exception as e:
            logging.error(f"Failed to send email: {e}")
            return jsonify({'success': False, 'message': 'Failed to send email. Please check the logs.'}), 500

    return render_template('send_email.html')
