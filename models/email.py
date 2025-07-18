from db import db

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(255), nullable=False)
    sender_name = db.Column(db.String(255), nullable=True)
    recipient = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255))
    body = db.Column(db.Text, nullable=True)
    body_html = db.Column(db.Text, nullable=True)
    raw = db.Column(db.Text, nullable=True)
    alias_used = db.Column(db.String(255), nullable=True)  # Stores the alias prefix that was used
    received_at = db.Column(db.DateTime, server_default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    attachments = db.relationship('Attachment', back_populates='email', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'sender': self.sender,
            'sender_name': self.sender_name,
            'recipient': self.recipient,
            'subject': self.subject,
            'body': self.body,
            'body_html': self.body_html,
            'raw': self.raw,
            'alias_used': self.alias_used,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'user_id': self.user_id
        }
