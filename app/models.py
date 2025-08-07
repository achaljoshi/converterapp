from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.orm import relationship

# Association table for many-to-many relationship between test cases and workflows
testcase_workflow = db.Table('testcase_workflow',
    db.Column('test_case_id', db.Integer, db.ForeignKey('test_case.id'), primary_key=True),
    db.Column('workflow_id', db.Integer, db.ForeignKey('workflow.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password = db.Column(db.String(120), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)

    role = relationship('Role', backref='users')

class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))
    permissions = relationship('Permission', secondary='role_permission', back_populates='roles')

class Permission(db.Model):
    __tablename__ = 'permission'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))
    roles = relationship('Role', secondary='role_permission', back_populates='permissions')

role_permission = db.Table('role_permission',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True)
)

# Original models for existing functionality
class Configuration(db.Model):
    __tablename__ = 'configuration'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(255))
    file_type = db.Column(db.String(50))
    rules = db.Column(db.Text)  # Store rules as JSON or plain text for now
    schema = db.Column(db.Text)  # Store JSON schema for rules (optional)

class FileType(db.Model):
    __tablename__ = 'file_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    active = db.Column(db.Boolean, default=True)
    extraction_rules = db.Column(db.Text, nullable=True)
    file_mode = db.Column(db.String(10), default='text')  # 'xml' or 'text'

class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(150))
    action = db.Column(db.String(50))
    filetype = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)

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

    workflow = relationship('Workflow', backref=db.backref('audit_logs', lazy=True))

class Workflow(db.Model):
    __tablename__ = 'workflow'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    stages = db.Column(db.Text, nullable=False)  # JSON list of converter config IDs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships with overlaps parameter to silence warnings
    testcases = relationship('TestCase', secondary='testcase_workflow', back_populates='workflows')

class TestCase(db.Model):
    __tablename__ = 'test_case'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    schedule = db.Column(db.String(64), nullable=True)  # e.g., 'daily', 'weekly', cron, or None
    next_run_at = db.Column(db.DateTime, nullable=True)
    
    # New fields for Git integration
    repository_id = db.Column(db.Integer, db.ForeignKey('git_repository.id'), nullable=True)
    file_path = db.Column(db.String(500), nullable=True)  # Path to test file in repo
    test_type = db.Column(db.String(50), nullable=True)  # 'UI', 'API', etc.
    last_modified = db.Column(db.DateTime, nullable=True)  # Last modified in Git
    is_discovered = db.Column(db.Boolean, default=False)  # Whether this was auto-discovered
    
    # Relationships
    workflows = relationship('Workflow', secondary='testcase_workflow', back_populates='testcases')
    repository = relationship('GitRepository', backref='test_cases')
    labels = relationship('TestCaseLabel', back_populates='test_case', cascade='all, delete-orphan')

class TestRun(db.Model):
    __tablename__ = 'test_run'
    id = db.Column(db.Integer, primary_key=True)
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_case.id'), nullable=False)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(32), nullable=False)  # e.g., 'passed', 'failed', 'error'
    output = db.Column(db.Text)  # Store output, logs, or error messages
    duration = db.Column(db.Float)  # Duration in seconds
    
    # New fields for enhanced execution
    execution_logs = db.Column(db.Text)  # Real-time execution logs
    error_details = db.Column(db.Text)  # Detailed error information
    environment = db.Column(db.String(100))  # Test environment
    browser = db.Column(db.String(50), nullable=True)  # For UI tests
    api_endpoint = db.Column(db.String(200), nullable=True)  # For API tests

    test_case = relationship('TestCase', backref=db.backref('test_runs', lazy=True))

# New models for Git integration and enhanced features

class GitRepository(db.Model):
    __tablename__ = 'git_repository'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    branch = db.Column(db.String(100), default='main')
    repo_type = db.Column(db.String(50), nullable=False)  # 'UI', 'API', 'Mixed'
    local_path = db.Column(db.String(500), nullable=True)  # Local clone path
    last_sync = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Git credentials (encrypted)
    username = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(500), nullable=True)  # Should be encrypted
    ssh_key_path = db.Column(db.String(500), nullable=True)
    
    # Test discovery settings
    test_patterns = db.Column(db.Text)  # JSON array of test file patterns
    ignore_patterns = db.Column(db.Text)  # JSON array of ignore patterns
    
    # Framework configuration
    test_framework_id = db.Column(db.Integer, db.ForeignKey('test_framework.id'), nullable=True)
    custom_extraction_rules = db.Column(db.Text)  # JSON for custom rules
    
    # Relationships
    test_framework = relationship('TestFramework', backref='repositories')

class TestFramework(db.Model):
    __tablename__ = 'test_framework'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    language = db.Column(db.String(50))  # Python, Java, JavaScript, etc.
    file_extensions = db.Column(db.Text)  # JSON array of file extensions
    test_patterns = db.Column(db.Text)  # JSON array of regex patterns
    test_name_patterns = db.Column(db.Text)  # JSON array of patterns to extract test names
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Framework-specific settings
    settings = db.Column(db.Text)  # JSON for framework-specific settings
    
    # Execution command templates
    execution_commands = db.Column(db.Text)  # JSON for configurable execution commands
    
    # Setup commands for Docker execution
    setup_commands = db.Column(db.Text)  # JSON array for Docker setup commands

class Label(db.Model):
    __tablename__ = 'label'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(7), default='#007bff')  # Hex color code
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TestCaseLabel(db.Model):
    __tablename__ = 'testcase_label'
    id = db.Column(db.Integer, primary_key=True)
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_case.id'), nullable=False)
    label_id = db.Column(db.Integer, db.ForeignKey('label.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    test_case = relationship('TestCase', back_populates='labels')
    label = relationship('Label')

class TestExecutionQueue(db.Model):
    __tablename__ = 'test_execution_queue'
    
    id = db.Column(db.Integer, primary_key=True)
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_case.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    queued_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_at = db.Column(db.DateTime)
    priority = db.Column(db.Integer, default=0)
    execution_config = db.Column(db.Text)  # JSON for execution details
    started_at = db.Column(db.DateTime)  # When execution started
    completed_at = db.Column(db.DateTime)  # When execution completed
    
    # Relationships
    test_case = db.relationship('TestCase', backref='execution_queue_items') 