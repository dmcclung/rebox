from flask import Blueprint, render_template, redirect, url_for, send_from_directory, current_app, flash, request
from flask_login import login_required, current_user, logout_user
import os
import re
from models import Email, Attachment
import bleach

bp = Blueprint('ui', __name__)

@bp.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('ui.login_page'))
    return render_template("emails.html")

@bp.route('/aliases')
@login_required
def aliases():
    return render_template('aliases.html')

@bp.route('/login', methods=['GET'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('ui.index'))
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('ui.login_page'))

@bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'images'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

@bp.route('/email/<int:email_id>')
@login_required
def view_email(email_id):
    email = Email.query.get_or_404(email_id)
    if email.user_id != current_user.id:
        flash('You do not have permission to access this email.', 'danger')
        return redirect(url_for('ui.index'))

    view_mode = request.args.get('view', 'html')
    sanitized_html = ""
    if email.body_html:
        # Define allowed tags and attributes for bleach
        allowed_tags = list(bleach.ALLOWED_TAGS) + ['html', 'body', 'head', 'title', 'style', 'img']
        allowed_attrs = {
            '*': ['class', 'style'],
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'width', 'height']
        }
        
        # Allow 'cid' protocol for inline images
        allowed_protocols = list(bleach.ALLOWED_PROTOCOLS) + ['cid']
        
        # Sanitize first, keeping cid links
        temp_sanitized_html = bleach.clean(
            email.body_html, 
            tags=allowed_tags, 
            attributes=allowed_attrs, 
            protocols=allowed_protocols,
            strip=True
        )

        # Handle inline images with CIDs
        if email.attachments:
            cid_map = {
                att.content_id: url_for('ui.download_attachment', attachment_id=att.id)
                for att in email.attachments if att.content_id
            }

            def replace_cid(match):
                cid = match.group(1)
                url = cid_map.get(cid)
                if url:
                    return f'src="{url}"'
                return match.group(0) # Return original if no mapping found

            sanitized_html = re.sub(r'src="cid:([^"]+)"', replace_cid, temp_sanitized_html)
        else:
            sanitized_html = temp_sanitized_html

    return render_template('view_email.html', email=email, sanitized_html=sanitized_html, view_mode=view_mode)

@bp.route('/attachment/<int:attachment_id>/download')
@login_required
def download_attachment(attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    if attachment.email.user_id != current_user.id:
        flash('You do not have permission to access this attachment.', 'danger')
        return redirect(url_for('ui.index'))
    
    try:
        directory, filename = os.path.split(attachment.file_path)
        
        # Serve images inline, other attachments for download
        as_attachment = not (attachment.content_type and attachment.content_type.startswith('image/'))
        
        return send_from_directory(directory, filename, as_attachment=as_attachment)
    except FileNotFoundError:
        flash('Attachment file not found.', 'danger')
        return redirect(url_for('ui.view_email', email_id=attachment.email_id))

@bp.route('/send-email', methods=['GET'])
@login_required
def send_email_form():
    return render_template('send_email.html')
