from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Text, DateTime
from datetime import datetime

role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True)
)

class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    permissions = db.relationship('Permission', secondary=role_permissions, backref=db.backref('roles', lazy='dynamic'))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    password = db.Column(db.String(256), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', backref=db.backref('users', lazy=True))
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

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

    testcases_assoc = db.relationship('TestCaseWorkflow', back_populates='workflow', cascade='all, delete-orphan')
    testcases = db.relationship('TestCase', secondary='testcase_workflow', back_populates='workflows')

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

# Association table for many-to-many TestCase <-> Workflow with sample file
class TestCaseWorkflow(db.Model):
    __tablename__ = 'testcase_workflow'
    id = db.Column(db.Integer, primary_key=True)
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_case.id'), nullable=False)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflow.id'), nullable=False)
    sample_file = db.Column(db.String(255), nullable=True)  # Path to uploaded sample file

    test_case = db.relationship('TestCase', back_populates='workflows_assoc')
    workflow = db.relationship('Workflow', back_populates='testcases_assoc')

class TestCase(db.Model):
    __tablename__ = 'test_case'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    schedule = db.Column(db.String(64), nullable=True)  # e.g., 'daily', 'weekly', cron, or None
    next_run_at = db.Column(db.DateTime, nullable=True)

    workflows_assoc = db.relationship('TestCaseWorkflow', back_populates='test_case', cascade='all, delete-orphan')
    workflows = db.relationship('Workflow', secondary='testcase_workflow', back_populates='testcases')

class TestRun(db.Model):
    __tablename__ = 'test_run'
    id = db.Column(db.Integer, primary_key=True)
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_case.id'), nullable=False)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(32), nullable=False)  # e.g., 'passed', 'failed', 'error'
    output = db.Column(db.Text)  # Store output, logs, or error messages
    duration = db.Column(db.Float)  # Duration in seconds

    test_case = db.relationship('TestCase', backref=db.backref('test_runs', lazy=True)) 