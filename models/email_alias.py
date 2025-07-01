from datetime import datetime, timezone
from db import db
import random
import string

class EmailAlias(db.Model):
    __tablename__ = 'email_aliases'
    
    id = db.Column(db.Integer, primary_key=True)
    alias_prefix = db.Column(db.String(120), nullable=False)
    alias_domain = db.Column(db.String(120), nullable=False, default='rebox.sh')
    description = db.Column(db.String(500), nullable=True)
    forwarding_email = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('email_aliases', lazy=True))
    
    @classmethod
    def generate_alias_prefix(cls, length=8):
        """Generate a random string of letters and digits"""
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    @property
    def full_alias(self):
        return f"{self.alias_prefix}@{self.alias_domain}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'alias_prefix': self.alias_prefix,
            'alias_domain': self.alias_domain,
            'full_alias': self.full_alias,
            'description': self.description,
            'forwarding_email': self.forwarding_email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_id': self.user_id
        }
