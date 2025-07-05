from db import db

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(1024), nullable=False) # Path where the file is stored
    content_id = db.Column(db.String(255), nullable=True) # For inline images (CID)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    email = db.relationship('Email', back_populates='attachments')

    def to_dict(self):
        return {
            'id': self.id,
            'email_id': self.email_id,
            'filename': self.filename,
            'content_type': self.content_type,
            'content_id': self.content_id
        }
