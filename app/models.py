from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Text, DateTime
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
    extraction_rules = db.Column(db.Text, nullable=True)
    file_mode = db.Column(db.String(10), default='text')  # 'xml' or 'text'

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(150))
    action = db.Column(db.String(50))
    filetype = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)

class Workflow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    stages = db.Column(db.Text, nullable=False)  # JSON list of converter config IDs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ConverterConfig(db.Model):
    __tablename__ = 'converter_config'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(256))
    source_type = db.Column(db.String(64), nullable=False)
    target_type = db.Column(db.String(64), nullable=False)
    rules = db.Column(db.Text, nullable=False)
    schema = db.Column(db.Text, nullable=True)

class WorkflowAuditLog(db.Model):
    __tablename__ = 'workflow_audit_log'
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflow.id'), nullable=False)
    user = db.Column(db.String(128), nullable=False)
    action = db.Column(db.String(64), nullable=False)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    workflow = db.relationship('Workflow', backref=db.backref('audit_logs', lazy=True)) 