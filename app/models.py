from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Text
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # e.g., admin, analyst, tester, developer 

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Configuration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(255))
    file_type = db.Column(db.String(50))
    rules = db.Column(Text)  # Store rules as JSON or plain text for now
    schema = db.Column(Text)  # Store JSON schema for rules (optional)

class FileType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    active = db.Column(db.Boolean, default=True)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(150))
    action = db.Column(db.String(50))
    filetype = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text) 