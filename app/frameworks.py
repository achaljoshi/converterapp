from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from .models import TestFramework, GitRepository
from . import db
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional
from functools import wraps
import json
import re

frameworks = Blueprint('frameworks', __name__)

def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if getattr(current_user, 'role', None) and (current_user.role.name == 'admin' or any(p.name == permission_name for p in current_user.role.permissions)):
                return f(*args, **kwargs)
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        return decorated_function
    return decorator

class TestFrameworkForm(FlaskForm):
    name = StringField('Framework Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    language = SelectField('Language', choices=[
        ('Python', 'Python'),
        ('Java', 'Java'),
        ('JavaScript', 'JavaScript'),
        ('TypeScript', 'TypeScript'),
        ('C#', 'C#'),
        ('Ruby', 'Ruby'),
        ('Go', 'Go'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    file_extensions = TextAreaField('File Extensions (JSON)', 
        default='[".py", ".java", ".js", ".ts"]',
        description='JSON array of file extensions to scan for tests (e.g., [".py", ".java"])')
    test_patterns = TextAreaField('Test Patterns (JSON)', 
        default='["def test_", "@Test", "test(", "Scenario:"]',
        description='JSON array of patterns to identify test files (legacy field)')
    test_name_patterns = TextAreaField('Test Name Patterns (JSON)', 
        default='["def (test_\\w+)", "@Test\\s+public\\s+void\\s+(\\w+)", "test\\(\\s*[\'\"]([^\'\"]+)[\'\"]", "Scenario:\\s*(\\w+)"]',
        description='JSON array of regex patterns to extract test names from files')
    settings = TextAreaField('Framework Settings (JSON)', 
        default='{"extraction_method": "pattern_based", "remove_prefixes": ["test_"], "allowed_chars": "\\\\w\\\\s-", "min_length": 2}',
        description='JSON object with extraction settings (method, prefixes to remove, character filters, etc.)')
    execution_commands = TextAreaField('Execution Commands (JSON)', 
        default='{"command_template": "command {file_path} --name \\"{test_name}\\"", "working_dir": "{repo_path}", "timeout": 300, "success_codes": [0], "max_memory_mb": 1024, "use_docker": true}',
        description='JSON object with execution command template, working directory, timeout, success codes, memory limits, and Docker preference')
    setup_commands = TextAreaField('Setup Commands (JSON)', 
        default='[]',
        description='JSON array of Docker setup commands to run before test execution (e.g., ["docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} bash -c \\"npm install\\""])')
    is_active = BooleanField('Active')
    submit = SubmitField('Save')

@frameworks.route('/frameworks')
@login_required
def list_frameworks():
    frameworks = TestFramework.query.order_by(TestFramework.name).all()
    return render_template('frameworks.html', frameworks=frameworks)

@frameworks.route('/frameworks/new', methods=['GET', 'POST'])
@login_required
@permission_required('framework_manage')
def create_framework():
    form = TestFrameworkForm()
    if form.validate_on_submit():
        # Validate JSON fields
        try:
            file_extensions = json.loads(form.file_extensions.data)
            test_patterns = json.loads(form.test_patterns.data)
            test_name_patterns = json.loads(form.test_name_patterns.data)
            settings = json.loads(form.settings.data)
            execution_commands = json.loads(form.execution_commands.data)
            setup_commands = json.loads(form.setup_commands.data)
        except json.JSONDecodeError as e:
            flash(f'Invalid JSON format: {str(e)}', 'danger')
            return render_template('framework_form.html', form=form, action='Create')
        
        framework = TestFramework(
            name=form.name.data,
            description=form.description.data,
            language=form.language.data,
            file_extensions=form.file_extensions.data,
            test_patterns=form.test_patterns.data,
            test_name_patterns=form.test_name_patterns.data,
            settings=form.settings.data,
            execution_commands=form.execution_commands.data,
            setup_commands=form.setup_commands.data,
            is_active=form.is_active.data
        )
        
        db.session.add(framework)
        db.session.commit()
        
        flash('Test framework created successfully!', 'success')
        return redirect(url_for('frameworks.list_frameworks'))
    
    return render_template('framework_form.html', form=form, action='Create')

@frameworks.route('/frameworks/<int:framework_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('framework_manage')
def edit_framework(framework_id):
    framework = TestFramework.query.get_or_404(framework_id)
    form = TestFrameworkForm(obj=framework)
    
    if form.validate_on_submit():
        # Validate JSON fields
        try:
            file_extensions = json.loads(form.file_extensions.data)
            test_patterns = json.loads(form.test_patterns.data)
            test_name_patterns = json.loads(form.test_name_patterns.data)
            settings = json.loads(form.settings.data)
            execution_commands = json.loads(form.execution_commands.data)
            setup_commands = json.loads(form.setup_commands.data)
        except json.JSONDecodeError as e:
            flash(f'Invalid JSON format: {str(e)}', 'danger')
            return render_template('framework_form.html', form=form, action='Edit')
        
        framework.name = form.name.data
        framework.description = form.description.data
        framework.language = form.language.data
        framework.file_extensions = form.file_extensions.data
        framework.test_patterns = form.test_patterns.data
        framework.test_name_patterns = form.test_name_patterns.data
        framework.settings = form.settings.data
        framework.execution_commands = form.execution_commands.data
        framework.setup_commands = form.setup_commands.data
        framework.is_active = form.is_active.data
        
        db.session.commit()
        flash('Test framework updated successfully!', 'success')
        return redirect(url_for('frameworks.list_frameworks'))
    
    return render_template('framework_form.html', form=form, action='Edit')

@frameworks.route('/frameworks/<int:framework_id>/delete', methods=['POST'])
@login_required
@permission_required('framework_manage')
def delete_framework(framework_id):
    framework = TestFramework.query.get_or_404(framework_id)
    
    # Check if framework is used by any repositories
    repositories = GitRepository.query.filter_by(test_framework_id=framework_id).count()
    if repositories > 0:
        flash(f'Cannot delete framework. It is used by {repositories} repository(ies).', 'danger')
        return redirect(url_for('frameworks.list_frameworks'))
    
    db.session.delete(framework)
    db.session.commit()
    flash('Test framework deleted successfully!', 'success')
    return redirect(url_for('frameworks.list_frameworks'))

@frameworks.route('/frameworks/<int:framework_id>/test', methods=['POST'])
@login_required
@permission_required('framework_manage')
def test_framework(framework_id):
    framework = TestFramework.query.get_or_404(framework_id)
    test_code = request.form.get('test_code', '')
    
    if not test_code:
        return jsonify({'error': 'No test code provided'}), 400
    
    try:
        # Parse framework configuration
        test_patterns = json.loads(framework.test_patterns)
        test_name_patterns = json.loads(framework.test_name_patterns)
        
        # Test the patterns
        results = []
        for pattern in test_patterns:
            matches = re.findall(pattern, test_code, re.MULTILINE)
            if matches:
                results.append({
                    'pattern': pattern,
                    'matches': matches
                })
        
        # Extract test names
        extracted_tests = []
        for name_pattern in test_name_patterns:
            matches = re.findall(name_pattern, test_code, re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    extracted_tests.extend([name for name in match if name])
                else:
                    extracted_tests.append(match)
        
        return jsonify({
            'success': True,
            'pattern_matches': results,
            'extracted_tests': list(set(extracted_tests))  # Remove duplicates
        })
        
    except Exception as e:
        return jsonify({'error': f'Error testing framework: {str(e)}'}), 500

@frameworks.route('/api/frameworks')
@login_required
def api_frameworks():
    """API endpoint to get all frameworks for dropdowns"""
    frameworks = TestFramework.query.filter_by(is_active=True).order_by(TestFramework.name).all()
    return jsonify([{
        'id': f.id,
        'name': f.name,
        'language': f.language,
        'description': f.description
    } for f in frameworks])

@frameworks.route('/api/frameworks/<int:framework_id>')
@login_required
def api_framework_details(framework_id):
    """API endpoint to get framework details"""
    framework = TestFramework.query.get_or_404(framework_id)
    return jsonify({
        'id': framework.id,
        'name': framework.name,
        'language': framework.language,
        'file_extensions': json.loads(framework.file_extensions),
        'test_patterns': json.loads(framework.test_patterns),
        'test_name_patterns': json.loads(framework.test_name_patterns),
        'settings': json.loads(framework.settings)
    }) 