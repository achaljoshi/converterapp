from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, session
from flask_login import login_required, current_user
from .models import GitRepository, TestCase, Label, TestCaseLabel, TestFramework
from . import db
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired, URL, Optional
from functools import wraps
import os
import json
import subprocess
import re
from pathlib import Path
import git
from git import Repo, GitCommandError

git_repos = Blueprint('git_repos', __name__)

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

class GitRepositoryForm(FlaskForm):
    name = StringField('Repository Name', validators=[DataRequired()])
    url = StringField('Git URL', validators=[DataRequired(), URL()])
    branch = StringField('Branch', default='main')
    repo_type = SelectField('Repository Type', choices=[
        ('UI', 'UI Tests'),
        ('API', 'API Tests'),
        ('Mixed', 'Mixed (UI + API)')
    ], validators=[DataRequired()])
    username = StringField('Username (Optional)')
    password = StringField('Password/Token (Optional)')
    test_framework = SelectField('Test Framework', coerce=int, validators=[Optional()])
    submit = SubmitField('Save')

class TestCaseDiscoveryForm(FlaskForm):
    repository_id = SelectField('Repository', coerce=int, validators=[DataRequired()])
    labels = SelectField('Labels', coerce=int, validators=[Optional()])
    submit = SubmitField('Discover Tests')

@git_repos.route('/repositories')
@login_required
@permission_required('repo_manage')
def list_repositories():
    repositories = GitRepository.query.order_by(GitRepository.created_at.desc()).all()
    return render_template('git_repositories.html', repositories=repositories)

@git_repos.route('/repositories/new', methods=['GET', 'POST'])
@login_required
@permission_required('repo_manage')
def create_repository():
    form = GitRepositoryForm()
    # Populate framework choices
    form.test_framework.choices = [(0, '-- Select Framework --')] + [
        (f.id, f"{f.name} ({f.language})") 
        for f in TestFramework.query.filter_by(is_active=True).order_by(TestFramework.name).all()
    ]
    
    if form.validate_on_submit():
        # Use default patterns
        default_test_patterns = '["**/test_*.py", "**/*_test.py", "**/tests/**/*.py"]'
        default_ignore_patterns = '["**/__pycache__/**", "**/.git/**", "**/node_modules/**"]'
        default_custom_rules = '{}'
        
        repo = GitRepository(
            name=form.name.data,
            url=form.url.data,
            branch=form.branch.data,
            repo_type=form.repo_type.data,
            username=form.username.data if form.username.data else None,
            password=form.password.data if form.password.data else None,
            test_framework_id=form.test_framework.data if form.test_framework.data != 0 else None,
            test_patterns=default_test_patterns,
            ignore_patterns=default_ignore_patterns,
            custom_extraction_rules=default_custom_rules
        )
        
        db.session.add(repo)
        db.session.commit()
        
        flash('Repository added successfully!', 'success')
        return redirect(url_for('git_repos.list_repositories'))
    
    return render_template('git_repository_form.html', form=form, action='Create')

@git_repos.route('/repositories/test-connection', methods=['POST'])
@login_required
@permission_required('repo_manage')
def test_connection():
    """Test Git repository connection"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    
    url = data.get('url')
    branch = data.get('branch', 'main')
    username = data.get('username')
    password = data.get('password')
    
    if not url:
        return jsonify({'success': False, 'message': 'Git URL is required'}), 400
    
    try:
        # Test the connection by trying to get repository info
        if username and password:
            # Use credentials
            url_with_auth = url.replace('https://', f'https://{username}:{password}@')
            # Try to get repository info without cloning
            result = git.cmd.Git().ls_remote(url_with_auth)
        else:
            # Try to get repository info without cloning
            result = git.cmd.Git().ls_remote(url)
        
        # Check if the specified branch exists in the result
        if branch and branch not in ['main', 'master']:
            # For specific branches, check if they exist in the ls-remote output
            if branch not in result:
                return jsonify({'success': False, 'message': f'Branch "{branch}" not found in the repository.'}), 400
        
        return jsonify({
            'success': True, 
            'message': f'Successfully connected to repository. Branch "{branch}" is accessible.'
        })
        
    except GitCommandError as e:
        error_msg = str(e)
        if 'Authentication failed' in error_msg or 'fatal: Authentication failed' in error_msg:
            return jsonify({'success': False, 'message': 'Authentication failed. Please check your username and password/token.'}), 400
        elif 'Repository not found' in error_msg or 'fatal: repository' in error_msg.lower():
            return jsonify({'success': False, 'message': 'Repository not found. Please check the URL.'}), 400
        elif 'Branch not found' in error_msg:
            return jsonify({'success': False, 'message': f'Branch "{branch}" not found in the repository.'}), 400
        else:
            return jsonify({'success': False, 'message': f'Connection failed: {error_msg}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Unexpected error: {str(e)}'}), 500

@git_repos.route('/repositories/<int:repo_id>/clone', methods=['POST'])
@login_required
@permission_required('repo_manage')
def clone_repository(repo_id):
    repo = GitRepository.query.get_or_404(repo_id)
    
    try:
        # Create repos directory if it doesn't exist
        repos_dir = os.path.join(current_app.root_path, '..', 'repos')
        os.makedirs(repos_dir, exist_ok=True)
        
        # Clone the repository
        local_path = os.path.join(repos_dir, f"{repo.name}_{repo.id}")
        
        if os.path.exists(local_path):
            # Pull latest changes
            git_repo = Repo(local_path)
            origin = git_repo.remotes.origin
            origin.pull()
            flash('Repository updated successfully!', 'success')
        else:
            # Clone new repository
            if repo.username and repo.password:
                # Use credentials
                url_with_auth = repo.url.replace('https://', f'https://{repo.username}:{repo.password}@')
                git_repo = Repo.clone_from(url_with_auth, local_path, branch=repo.branch)
            else:
                git_repo = Repo.clone_from(repo.url, local_path, branch=repo.branch)
            flash('Repository cloned successfully!', 'success')
        
        # Update repository record
        repo.local_path = local_path
        repo.last_sync = datetime.utcnow()
        db.session.commit()
        
        # Log the action
        audit_log = AuditLog(
            user=current_user.username,
            action='clone_repository',
            filetype=repo.repo_type,
            details=f"Cloned/updated repository: {repo.name}"
        )
        db.session.add(audit_log)
        db.session.commit()
        
    except GitCommandError as e:
        flash(f'Git operation failed: {str(e)}', 'danger')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('git_repos.list_repositories'))

@git_repos.route('/repositories/<int:repo_id>/discover', methods=['GET', 'POST'])
@login_required
@permission_required('testcase_create')
def discover_test_cases(repo_id):
    repo = GitRepository.query.get_or_404(repo_id)
    form = TestCaseDiscoveryForm()
    form.repository_id.data = repo_id
    form.labels.choices = [(l.id, l.name) for l in Label.query.all()]
    
    if not repo.local_path or not os.path.exists(repo.local_path):
        flash('Repository not cloned. Please clone the repository first.', 'warning')
        return redirect(url_for('git_repos.list_repositories'))
    
    # Use the new test discovery logic from testcases.py
    from app.testcases import discover_test_cases_from_repository
    discovered_tests = discover_test_cases_from_repository(repo_id)
    
    if request.method == 'POST' and form.validate_on_submit():
        if discovered_tests:
            # Store discovered tests in session for selection
            session['discovered_tests'] = discovered_tests
            return render_template('test_case_discovery.html', 
                                 tests=discovered_tests, 
                                 repository=repo, 
                                 form=form)
        else:
            flash('No test cases found in the repository.', 'info')
    
    return render_template('test_case_discovery.html', 
                         tests=discovered_tests, 
                         repository=repo, 
                         form=form)

@git_repos.route('/repositories/<int:repo_id>/discover/import', methods=['POST'])
@login_required
@permission_required('testcase_create')
def import_discovered_tests(repo_id):
    repo = GitRepository.query.get_or_404(repo_id)
    selected_tests = request.form.getlist('selected_tests')
    
    if not selected_tests:
        flash('No test cases selected.', 'warning')
        return redirect(url_for('git_repos.discover_test_cases', repo_id=repo_id))
    
    imported_count = 0
    for test_data in selected_tests:
        test_info = None
        try:
            test_info = json.loads(test_data)
            
            # Create test case with available data
            test_case = TestCase(
                name=test_info['name'],
                description=f"Auto-discovered from {repo.name} repository\nFile: {test_info['file_path']}\nFramework: {test_info['framework']}",
                repository_id=repo.id,
                file_path=test_info['file_path'],
                test_type=repo.repo_type,
                last_modified=datetime.utcnow(),
                is_discovered=True
            )
            
            db.session.add(test_case)
            db.session.flush()  # Get the ID
            
            # Add label if selected
            label_id = request.form.get('label_id')
            if label_id and label_id.strip():
                test_case_label = TestCaseLabel(
                    test_case_id=test_case.id,
                    label_id=int(label_id)
                )
                db.session.add(test_case_label)
            
            imported_count += 1
            
        except json.JSONDecodeError as e:
            flash(f'Error parsing test data: {str(e)}', 'danger')
        except Exception as e:
            test_name = test_info.get("name", "unknown") if test_info else "unknown"
            flash(f'Error importing test case {test_name}: {str(e)}', 'danger')
    
    db.session.commit()
    flash(f'Successfully imported {imported_count} test cases.', 'success')
    
    return redirect(url_for('testcases.list_testcases'))

def discover_tests_in_repository(repo):
    """Discover test cases in the repository based on patterns and framework."""
    discovered_tests = []
    
    try:
        test_patterns = json.loads(repo.test_patterns)
        ignore_patterns = json.loads(repo.ignore_patterns)
        custom_rules = json.loads(repo.custom_extraction_rules) if repo.custom_extraction_rules else {}
        
        repo_path = Path(repo.local_path)
        
        # Get framework if specified
        framework = repo.test_framework
        
        for pattern in test_patterns:
            for test_file in repo_path.rglob(pattern.replace('**/', '')):
                # Check if file should be ignored
                should_ignore = False
                for ignore_pattern in ignore_patterns:
                    if test_file.match(ignore_pattern):
                        should_ignore = True
                        break
                
                if should_ignore:
                    continue
                
                # Check file extension if framework is specified
                if framework:
                    framework_extensions = json.loads(framework.file_extensions)
                    if not any(test_file.suffix in framework_extensions):
                        continue
                
                # Extract test case names from the file
                test_cases = extract_test_cases_from_file(test_file, framework, custom_rules)
                
                for test_name in test_cases:
                    # Get file modification time
                    mtime = datetime.fromtimestamp(test_file.stat().st_mtime)
                    
                    discovered_tests.append({
                        'name': test_name,
                        'file_path': str(test_file.relative_to(repo_path)),
                        'full_path': str(test_file),
                        'last_modified': mtime.isoformat(),
                        'repository': repo.name,
                        'framework': framework.name if framework else 'Default'
                    })
        
        return discovered_tests
        
    except Exception as e:
        current_app.logger.error(f"Error discovering tests: {str(e)}")
        return []

def extract_test_cases_from_file(file_path, framework=None, custom_rules=None):
    """Extract test case names from a file using framework-specific patterns."""
    test_cases = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if framework:
            # Use framework-specific patterns
            test_patterns = json.loads(framework.test_patterns)
            test_name_patterns = json.loads(framework.test_name_patterns)
            
            # First, check if file contains any test patterns
            has_tests = False
            for pattern in test_patterns:
                if re.search(pattern, content, re.MULTILINE):
                    has_tests = True
                    break
            
            if has_tests:
                # Extract test names using framework patterns
                for name_pattern in test_name_patterns:
                    matches = re.findall(name_pattern, content, re.MULTILINE)
                    for match in matches:
                        if isinstance(match, tuple):
                            test_cases.extend([name for name in match if name])
                        else:
                            test_cases.append(match)
        else:
            # Fallback to default Python pattern
            test_pattern = r'def\s+(test_\w+)\s*\('
            matches = re.findall(test_pattern, content)
            test_cases.extend(matches)
        
        # Apply custom rules if provided
        if custom_rules:
            test_cases = apply_custom_extraction_rules(test_cases, content, custom_rules)
            
    except Exception as e:
        current_app.logger.error(f"Error reading file {file_path}: {str(e)}")
    
    return list(set(test_cases))  # Remove duplicates

def apply_custom_extraction_rules(test_cases, content, custom_rules):
    """Apply custom extraction rules to refine test case discovery."""
    try:
        rules = json.loads(custom_rules) if isinstance(custom_rules, str) else custom_rules
        
        # Apply include patterns
        if 'include_patterns' in rules:
            included_cases = []
            for pattern in rules['include_patterns']:
                matches = re.findall(pattern, content, re.MULTILINE)
                for match in matches:
                    if isinstance(match, tuple):
                        included_cases.extend([name for name in match if name])
                    else:
                        included_cases.append(match)
            test_cases.extend(included_cases)
        
        # Apply exclude patterns
        if 'exclude_patterns' in rules:
            for pattern in rules['exclude_patterns']:
                test_cases = [case for case in test_cases if not re.search(pattern, case)]
        
        # Apply name transformations
        if 'name_transformations' in rules:
            for transformation in rules['name_transformations']:
                if transformation.get('type') == 'replace':
                    pattern = transformation.get('pattern', '')
                    replacement = transformation.get('replacement', '')
                    test_cases = [re.sub(pattern, replacement, case) for case in test_cases]
        
        return test_cases
        
    except Exception as e:
        current_app.logger.error(f"Error applying custom rules: {str(e)}")
        return test_cases

@git_repos.route('/repositories/<int:repo_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('repo_manage')
def edit_repository(repo_id):
    repo = GitRepository.query.get_or_404(repo_id)
    form = GitRepositoryForm(obj=repo)
    
    # Populate framework choices
    form.test_framework.choices = [(0, '-- Select Framework --')] + [
        (f.id, f"{f.name} ({f.language})") 
        for f in TestFramework.query.filter_by(is_active=True).order_by(TestFramework.name).all()
    ]
    
    if form.validate_on_submit():
        repo.name = form.name.data
        repo.url = form.url.data
        repo.branch = form.branch.data
        repo.repo_type = form.repo_type.data
        repo.username = form.username.data if form.username.data else None
        repo.password = form.password.data if form.password.data else None
        repo.test_framework_id = form.test_framework.data if form.test_framework.data != 0 else None
        repo.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Repository updated successfully!', 'success')
        return redirect(url_for('git_repos.list_repositories'))
    else:
        # Set current values for the form (for GET requests and validation errors)
        form.name.data = repo.name
        form.url.data = repo.url
        form.branch.data = repo.branch
        form.repo_type.data = repo.repo_type
        form.username.data = repo.username
        form.password.data = repo.password
        form.test_framework.data = repo.test_framework_id if repo.test_framework_id else 0
    
    return render_template('git_repository_form.html', form=form, action='Edit')

@git_repos.route('/repositories/<int:repo_id>/delete', methods=['POST'])
@login_required
@permission_required('repo_manage')
def delete_repository(repo_id):
    repo = GitRepository.query.get_or_404(repo_id)
    
    # Delete local clone if it exists
    if repo.local_path and os.path.exists(repo.local_path):
        try:
            import shutil
            shutil.rmtree(repo.local_path)
        except Exception as e:
            flash(f'Warning: Could not delete local repository: {str(e)}', 'warning')
    
    db.session.delete(repo)
    db.session.commit()
    
    flash('Repository deleted successfully!', 'success')
    return redirect(url_for('git_repos.list_repositories')) 

@git_repos.route('/repositories/<int:repo_id>/pull', methods=['POST'])
@login_required
@permission_required('repo_manage')
def pull_repository(repo_id):
    """Pull latest changes from Git repository and update test case count"""
    repo = GitRepository.query.get_or_404(repo_id)
    
    try:
        if not repo.local_path or not os.path.exists(repo.local_path):
            # If repository doesn't exist locally, clone it
            repos_dir = os.path.join(current_app.root_path, '..', 'repos')
            os.makedirs(repos_dir, exist_ok=True)
            local_path = os.path.join(repos_dir, f"{repo.name}_{repo.id}")
            
            if repo.username and repo.password:
                url_with_auth = repo.url.replace('https://', f'https://{repo.username}:{repo.password}@')
                git_repo = Repo.clone_from(url_with_auth, local_path, branch=repo.branch)
            else:
                git_repo = Repo.clone_from(repo.url, local_path, branch=repo.branch)
            
            repo.local_path = local_path
            flash('Repository cloned successfully!', 'success')
        else:
            # Pull latest changes
            git_repo = Repo(repo.local_path)
            origin = git_repo.remotes.origin
            origin.pull()
            flash('Repository updated successfully!', 'success')
        
        # Update last sync timestamp
        repo.last_sync = datetime.utcnow()
        
        # Discover and count test cases
        test_case_count = 0
        if repo.test_framework:
            from app.testcases import discover_test_cases_from_repository
            discovered_tests = discover_test_cases_from_repository(repo.id)
            test_case_count = len(discovered_tests)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Repository updated successfully! Found {test_case_count} test cases.',
            'test_case_count': test_case_count,
            'last_sync': repo.last_sync.isoformat() if repo.last_sync else None
        })
        
    except Exception as e:
        db.session.rollback()
        error_msg = str(e)
        if 'Authentication failed' in error_msg:
            return jsonify({'success': False, 'message': 'Authentication failed. Please check your credentials.'}), 400
        elif 'Repository not found' in error_msg:
            return jsonify({'success': False, 'message': 'Repository not found. Please check the URL.'}), 400
        else:
            return jsonify({'success': False, 'message': f'Error updating repository: {error_msg}'}), 500

@git_repos.route('/repositories/<int:repo_id>/test-count', methods=['GET'])
@login_required
def get_test_case_count(repo_id):
    """Get the current test case count for a repository"""
    repo = GitRepository.query.get_or_404(repo_id)
    
    try:
        test_case_count = 0
        if repo.test_framework and repo.local_path and os.path.exists(repo.local_path):
            from app.testcases import discover_test_cases_from_repository
            discovered_tests = discover_test_cases_from_repository(repo.id)
            test_case_count = len(discovered_tests)
        
        return jsonify({
            'success': True,
            'test_case_count': test_case_count,
            'last_sync': repo.last_sync.isoformat() if repo.last_sync else None
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error counting test cases: {str(e)}'}), 500 