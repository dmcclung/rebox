from datetime import datetime, timezone
from db import db
import random
import string

class EmailAlias(db.Model):
    __tablename__ = 'email_alias'
    
    id = db.Column(db.Integer, primary_key=True)
    alias_title = db.Column(db.String(120), nullable=False)
    alias_random = db.Column(db.String(120), nullable=False)
    alias_domain = db.Column(db.String(120), nullable=False, default='rebox.sh')
    description = db.Column(db.String(500), nullable=True)
    forwarding_email = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('email_aliases', lazy=True))
    
    @property
    def full_alias(self):
        """Return the full email alias in the format title.random@domain"""
        return f"{self.alias_title}.{self.alias_random}@{self.alias_domain}"
    
    @classmethod
    def generate_alias(cls):
        """Generate a random dictionary word with 3-4 numbers"""
        words = [
            'apple', 'banana', 'cherry', 'date', 'elderberry', 'fig', 'grape', 'honeydew',
            'kiwi', 'lemon', 'mango', 'nectarine', 'orange', 'pear', 'quince', 'raspberry',
            'strawberry', 'tangerine', 'ugli', 'vanilla', 'watermelon', 'xigua', 'yam', 'zucchini'
        ]
        
        word = random.choice(words)
        numbers = ''.join(random.choices(string.digits, k=random.randint(3, 4)))
        return f"{word}{numbers}"
    
    def to_dict(self):
        """Convert the alias to a dictionary for JSON serialization"""
        return {
            'id': self.id,
            'alias_title': self.alias_title,
            'alias_random': self.alias_random,
            'alias_domain': self.alias_domain,
            'full_alias': self.full_alias,
            'description': self.description,
            'forwarding_email': self.forwarding_email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_id': self.user_id
        }
