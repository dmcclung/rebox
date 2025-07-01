from flask_login import UserMixin
from db import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    credential_id = db.Column(db.String(255), unique=True, nullable=False)
    public_key = db.Column(db.String(255), nullable=False)
    emails = db.relationship('Email', backref='user', lazy=True)
    is_active = db.Column(db.Boolean, default=True)

    def get_id(self):
        return str(self.id)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'credential_id': self.credential_id,
            'public_key': self.public_key
        }
