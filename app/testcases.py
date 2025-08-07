from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response, abort, current_app
from flask_login import login_required, current_user
from .models import TestCase, TestRun, Workflow, AuditLog, GitRepository, TestFramework, Label, TestCaseLabel, TestExecutionQueue
from . import db
from datetime import datetime, timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField, SubmitField, FileField, FieldList
from wtforms.validators import DataRequired, Optional
from sqlalchemy.orm import joinedload
import random
import csv
from functools import wraps
from flask_wtf.file import FileAllowed, FileRequired
import os
import re
import json
from git import Repo
import tempfile
import shutil
import sys
import subprocess
import threading
import signal
import psutil
import time
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired, Optional
from functools import wraps
import logging

from app.models import db, TestCase, TestRun, Workflow, testcase_workflow, AuditLog, GitRepository, TestFramework, Label, TestCaseLabel, TestExecutionQueue

# Blueprint definition

testcases = Blueprint('testcases', __name__)

class TestCaseForm(FlaskForm):
    git_repository_id = SelectField('Git Repository', coerce=lambda x: int(x) if x and x != '' else None, validators=[Optional()])
    discovered_test_case = SelectField('Discovered Test Case', coerce=str, validators=[Optional()])
    name = StringField('Test Case Name', validators=[DataRequired()])
    description = StringField('Description', validators=[Optional()])
    test_type = SelectField('Test Type', choices=[('', 'Select Type'), ('UI', 'UI'), ('API', 'API'), ('Unit', 'Unit'), ('Integration', 'Integration')], validators=[Optional()])
    labels = SelectMultipleField('Labels', coerce=int, validators=[Optional()])
    workflows = SelectMultipleField('Workflows', coerce=int)
    schedule = SelectField('Schedule', choices=[('none', 'None'), ('daily', 'Daily'), ('weekly', 'Weekly')], default='none')
    submit = SubmitField('Save')

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if not current_user.role or not any(p.name == permission_name for p in current_user.role.permissions):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def discover_test_cases_from_repos():
    """Discover test cases from all active Git repositories."""
    discovered_tests = []
    
    for repo in GitRepository.query.filter_by(is_active=True).all():
        if not repo.local_path or not os.path.exists(repo.local_path):
            continue
            
        try:
            # Get framework configuration
            framework = repo.test_framework
            if not framework:
                continue
                
            # Get file extensions to match
            file_extensions = json.loads(framework.file_extensions) if framework.file_extensions else []
            
            # Walk through repository files
            for root, dirs, files in os.walk(repo.local_path):
                # Skip .git directory
                if '.git' in dirs:
                    dirs.remove('.git')
                    
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, repo.local_path)
                    
                    # Check if file has matching extension
                    file_extension = os.path.splitext(file)[1].lower()
                    if file_extension in [ext.lower() for ext in file_extensions]:
                        # Extract test cases from file
                        test_cases = extract_test_cases_from_file(file_path, framework)
                        for test_name in test_cases:
                            discovered_tests.append({
                                'name': test_name,
                                'file_path': rel_path,
                                'repository': repo.name,
                                'repository_id': repo.id,
                                'framework': framework.name,
                                'framework_id': framework.id,
                                'full_path': file_path
                            })
        except Exception as e:
            print(f"Error discovering tests from repository {repo.name}: {str(e)}")
            continue
    
    return discovered_tests

def discover_test_cases_from_repository(repo_id):
    """Discover test cases from a specific Git repository."""
    discovered_tests = []
    
    repo = GitRepository.query.get(repo_id)
    if not repo:
        return discovered_tests
    
    # Auto-clone repository if it doesn't exist locally
    if not repo.local_path or not os.path.exists(repo.local_path):
        try:
            # Create repos directory if it doesn't exist
            repos_dir = os.path.join(current_app.root_path, '..', 'repos')
            os.makedirs(repos_dir, exist_ok=True)
            
            # Set local path
            local_path = os.path.join(repos_dir, f"{repo.name}_{repo.id}")
            
            # Clone the repository
            if repo.username and repo.password:
                # Use credentials
                url_with_auth = repo.url.replace('https://', f'https://{repo.username}:{repo.password}@')
                git_repo = Repo.clone_from(url_with_auth, local_path, branch=repo.branch)
            else:
                git_repo = Repo.clone_from(repo.url, local_path, branch=repo.branch)
            
            # Update repository record with local path
            repo.local_path = local_path
            repo.last_sync = datetime.utcnow()
            db.session.commit()
            
            print(f"Repository {repo.name} cloned successfully to {local_path}")
            
        except Exception as e:
            print(f"Error cloning repository {repo.name}: {str(e)}")
            return discovered_tests
        
    try:
        # Get framework configuration
        framework = repo.test_framework
        if not framework:
            return discovered_tests
            
        # Get file extensions to match
        file_extensions = json.loads(framework.file_extensions) if framework.file_extensions else []
        
        # Walk through repository files
        for root, dirs, files in os.walk(repo.local_path):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
                
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo.local_path)
                
                # Check if file has matching extension
                file_extension = os.path.splitext(file)[1].lower()
                if file_extension in [ext.lower() for ext in file_extensions]:
                    # Extract test cases from file
                    test_cases = extract_test_cases_from_file(file_path, framework)
                    for test_name in test_cases:
                        discovered_tests.append({
                            'name': test_name,
                            'file_path': rel_path,
                            'repository': repo.name,
                            'repository_id': repo.id,
                            'framework': framework.name,
                            'framework_id': framework.id,
                            'full_path': file_path
                        })
    except Exception as e:
        print(f"Error discovering tests from repository {repo.name}: {str(e)}")
    
    return discovered_tests

def extract_test_cases_from_file(file_path, framework):
    """Extract test case names from a file based on framework patterns."""
    test_cases = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Get configurable patterns from framework
        test_patterns = json.loads(framework.test_patterns) if framework.test_patterns else []
        test_name_patterns = json.loads(framework.test_name_patterns) if framework.test_name_patterns else []
        settings = json.loads(framework.settings) if framework.settings else {}
        
        # Get framework-specific extraction method
        extraction_method = settings.get('extraction_method', 'pattern_based')
        
        if extraction_method == 'cucumber':
            # Cucumber-specific extraction using configurable patterns
            scenario_pattern = settings.get('scenario_pattern', r'Scenario:\s*(.+?)(?:\s*$|\s*\n)')
            scenario_outline_pattern = settings.get('scenario_outline_pattern', r'Scenario Outline:\s*(.+?)(?:\s*$|\s*\n)')
            
            # Extract Scenario names
            scenario_matches = re.findall(scenario_pattern, content, re.MULTILINE)
            for match in scenario_matches:
                test_name = match.strip()
                if test_name:
                    test_cases.append(test_name)
            
            # Extract Scenario Outline names
            outline_matches = re.findall(scenario_outline_pattern, content, re.MULTILINE)
            for match in outline_matches:
                test_name = match.strip()
                if test_name:
                    test_cases.append(test_name)
        
        elif extraction_method == 'robot_framework':
            # Robot Framework-specific extraction using configurable patterns
            test_cases_section_pattern = settings.get('test_cases_section_pattern', r'\*\*\*\s*Test Cases\s*\*\*\*')
            next_section_pattern = settings.get('next_section_pattern', r'\*\*\*\s*(?:Keywords|Settings|Variables|Documentation)\s*\*\*\*')
            test_case_name_pattern = settings.get('test_case_name_pattern', r'^[A-Za-z][A-Za-z0-9\s]*$')
            exclude_keywords = settings.get('exclude_keywords', ['open browser', 'input text', 'click button', 'input password', 'page should contain', 'library'])
            max_words = settings.get('max_words', 4)
            
            # Find the start of Test Cases section
            test_cases_start = re.search(test_cases_section_pattern, content, re.MULTILINE)
            if test_cases_start:
                # Get content from Test Cases section to the end or next section
                start_pos = test_cases_start.end()
                remaining_content = content[start_pos:]
                
                # Find the next section or end of file
                next_section = re.search(next_section_pattern, remaining_content, re.MULTILINE)
                if next_section:
                    test_section = remaining_content[:next_section.start()]
                else:
                    test_section = remaining_content
                
                # Extract test case names
                lines = test_section.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('[') and not line.startswith('#') and not line.startswith('***'):
                        # Check if line looks like a test case name
                        if re.match(test_case_name_pattern, line):
                            test_name = line.strip()
                            # Filter out common Robot keywords
                            if (test_name and len(test_name) > 2 and 
                                not any(keyword in test_name.lower() for keyword in exclude_keywords) and
                                len(test_name.split()) <= max_words):
                                test_cases.append(test_name)
        
        else:
            # Generic pattern-based extraction using configurable patterns
            for pattern in test_name_patterns:
                try:
                    matches = re.findall(pattern, content, re.MULTILINE)
                    for match in matches:
                        if isinstance(match, tuple):
                            # Handle multiple capture groups
                            test_name = match[0] if match[0] else match[1] if len(match) > 1 else str(match)
                        else:
                            test_name = match
                        
                        # Apply configurable name cleaning rules
                        if test_name:
                            test_name = test_name.strip()
                            
                            # Remove prefixes/suffixes based on settings
                            remove_prefixes = settings.get('remove_prefixes', ['test_', 'Test', '@Test'])
                            for prefix in remove_prefixes:
                                test_name = re.sub(f'^{re.escape(prefix)}\\s*', '', test_name)
                            
                            # Character filtering based on settings
                            allowed_chars = settings.get('allowed_chars', r'\w\s-')
                            test_name = re.sub(f'[^{allowed_chars}]', '', test_name)
                            test_name = test_name.strip()
                            
                            # Length validation based on settings
                            min_length = settings.get('min_length', 2)
                            if test_name and len(test_name) > min_length:
                                test_cases.append(test_name)
                                
                except re.error as e:
                    print(f"Invalid regex pattern '{pattern}': {e}")
                    continue
                
    except Exception as e:
        print(f"Error extracting tests from {file_path}: {e}")
        
    return list(set(test_cases))  # Remove duplicates

class TestExecutionManager:
    """CI/CD-style test execution manager with proper resource management and Docker support"""
    
    def __init__(self, app):
        self.app = app
        self.active_processes = {}  # queue_id -> process_info
        self.process_lock = threading.Lock()
        
        # Docker images for each framework
        self.docker_images = {
            'cucumber framework': 'maven:3.9.6-eclipse-temurin-17',  # Maven + Java 17 for Cucumber-JVM
            'pytest': 'python:3.9-slim',
            'playwright': 'mcr.microsoft.com/playwright:v1.40.0-focal',
            'selenium': 'openjdk:11-jdk-slim',
            'jest': 'node:18-slim',
            'cypress': 'cypress/included:12.17.4',
            'nunit': 'mcr.microsoft.com/dotnet/sdk:7.0',
            'robot framework': 'python:3.9-slim'
        }
        
        # Docker run commands for each framework
        self.docker_commands = {
            'cucumber framework': {
                'command_template': 'docker run --rm -v {workspace}:/workspace -w /workspace/repo/maven {image} bash -c "mvn test -Dcucumber.filter.name=\\"{test_name}\\" --batch-mode"',
                'setup_commands': [
                    'docker run --rm -v {workspace}:/workspace -w /workspace/repo/maven {image} bash -c "mvn clean compile --batch-mode"'
                ]
            },
            'pytest': {
                'command_template': 'docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} bash -c "pip install pytest pytest-json-report && pytest {file_path}::{test_function} -v --json-report --json-report-file=-"',
                'setup_commands': []
            },
            'playwright': {
                'command_template': 'docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} npx playwright test {file_path} --grep "{test_name}" --reporter=json',
                'setup_commands': [
                    'docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} npm install'
                ]
            },
            'selenium': {
                'command_template': 'docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} bash -c "mvn test -Dtest={class_name}#{method_name} -Dtestng.output.format=json"',
                'setup_commands': []
            },
            'jest': {
                'command_template': 'docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} npx jest {file_path} --testNamePattern "{test_name}" --json --outputFile=-',
                'setup_commands': [
                    'docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} npm install'
                ]
            },
            'cypress': {
                'command_template': 'docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} npx cypress run --spec {file_path} --reporter json --reporter-options output=-',
                'setup_commands': [
                    'docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} npm install'
                ]
            },
            'nunit': {
                'command_template': 'docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} dotnet test {file_path} --filter TestName="{test_name}" --logger json',
                'setup_commands': []
            },
            'robot framework': {
                'command_template': 'docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} bash -c "pip install robotframework && robot --test \\"{test_name}\\" --output - --report - --log - {file_path}"',
                'setup_commands': []
            }
        }
    
    def execute_test(self, queue_item_id, app):
        """Execute a test case with CI/CD best practices"""
        print(f"🔧 Starting CI/CD-style test execution for queue item {queue_item_id}")
        
        with app.app_context():
            try:
                # Get the queue item with retry logic
                queue_item = None
                for attempt in range(3):
                    queue_item = TestExecutionQueue.query.get(queue_item_id)
                    if queue_item:
                        break
                    print(f"⚠️  Queue item {queue_item_id} not found on attempt {attempt + 1}, retrying...")
                    time.sleep(1)
                
                if not queue_item:
                    print(f"❌ Queue item {queue_item_id} not found after 3 attempts")
                    return
                
                print(f"✅ Found queue item {queue_item_id}, status: {queue_item.status}")
                
                # Update status to running
                queue_item.status = 'running'
                queue_item.started_at = datetime.utcnow()
                db.session.commit()
                print(f"✅ Updated status to 'running'")
                
                # Get test case and repository info
                testcase = queue_item.test_case
                print(f"🔍 Test case details - ID: {testcase.id if testcase else 'None'}, Name: {testcase.name if testcase else 'None'}")
                print(f"🔍 Repository details - ID: {testcase.repository_id if testcase else 'None'}")
                
                if not testcase:
                    print(f"❌ Test case not found for queue item {queue_item_id}")
                    self._mark_failed(queue_item, 'Test case not found')
                    return
                
                if not testcase.repository:
                    print(f"❌ Repository not found for test case {testcase.name}")
                    self._mark_failed(queue_item, 'Repository not found for test case')
                    return
                
                print(f"✅ Found test case: {testcase.name}")
                print(f"✅ Found repository: {testcase.repository.name}")
                
                repo = testcase.repository
                framework = repo.test_framework
                
                print(f"🔍 Repository details - Name: {repo.name}, Framework ID: {repo.test_framework_id}")
                
                if not framework:
                    print(f"❌ No framework configured for repository {repo.name}")
                    self._mark_failed(queue_item, 'No framework configured for repository')
                    return
                
                print(f"✅ Found framework: {framework.name}")
                print(f"🔍 Framework execution commands: {framework.execution_commands}")
                
                # Create isolated workspace
                workspace = self._create_workspace(queue_item_id, repo)
                if not workspace:
                    self._mark_failed(queue_item, 'Failed to create workspace')
                    return
                
                print(f"✅ Created workspace: {workspace}")
                
                # Run Docker setup commands if needed
                setup_result = self._run_docker_setup(framework, workspace)
                
                # Build execution command
                command = self._build_execution_command(testcase, repo, framework, workspace)
                if not command:
                    print(f"❌ Could not build execution command for {testcase.name}")
                    self._mark_failed(queue_item, 'Could not build execution command')
                    return
                
                print(f"✅ Built command: {' '.join(command)}")
                
                # Get execution parameters
                execution_config = json.loads(framework.execution_commands)
                timeout = execution_config.get('timeout', 300)
                success_codes = execution_config.get('success_codes', [0])
                max_memory = execution_config.get('max_memory_mb', 1024)  # 1GB default
                
                print(f"✅ Execution parameters - timeout: {timeout}s, max_memory: {max_memory}MB")
                
                # Execute with resource monitoring
                result = self._execute_with_monitoring(command, workspace, timeout, max_memory, queue_item_id, setup_result)
                
                print(f"✅ Test execution completed - success: {result['success']}")
                
                # Update queue item with results
                queue_item.status = 'completed' if result['success'] else 'failed'
                queue_item.completed_at = datetime.utcnow()
                queue_item.execution_config = json.dumps(result)
                db.session.commit()
                print(f"✅ Updated queue item status to: {queue_item.status}")
                
                # Create test run record
                test_run = TestRun(
                    test_case_id=testcase.id,
                    status='passed' if result['success'] else 'failed',
                    output=result.get('output', ''),
                    duration=result.get('duration', 0),
                    execution_logs=result.get('logs', ''),
                    error_details=result.get('error', ''),
                    executed_at=datetime.utcnow()
                )
                db.session.add(test_run)
                db.session.commit()
                print(f"✅ Created test run record with ID: {test_run.id}")
                
                # Cleanup workspace
                self._cleanup_workspace(workspace)
                print(f"✅ Cleaned up workspace: {workspace}")
                
            except Exception as e:
                print(f"❌ Error in execute_test: {str(e)}")
                import traceback
                traceback.print_exc()
                
                # Handle any errors
                try:
                    if 'queue_item' in locals() and queue_item:
                        self._mark_failed(queue_item, str(e))
                    
                    # Create failed test run
                    if 'testcase' in locals() and testcase:
                        test_run = TestRun(
                            test_case_id=testcase.id,
                            status='error',
                            output='',
                            duration=0,
                            execution_logs='',
                            error_details=str(e),
                            executed_at=datetime.utcnow()
                        )
                        db.session.add(test_run)
                        db.session.commit()
                        
                    # Cleanup workspace
                    if 'workspace' in locals() and workspace:
                        self._cleanup_workspace(workspace)
                        
                except Exception as inner_e:
                    print(f"❌ Error handling error: {str(inner_e)}")
    
    def _create_workspace(self, queue_item_id, repo):
        """Create isolated workspace for test execution"""
        try:
            # Create temporary workspace
            workspace = tempfile.mkdtemp(prefix=f"test_exec_{queue_item_id}_")
            
            # Clone/copy repository to workspace
            if repo.local_path and os.path.exists(repo.local_path):
                # Copy existing repository
                shutil.copytree(repo.local_path, os.path.join(workspace, 'repo'))
            else:
                # Clone fresh repository
                import git
                git.Repo.clone_from(repo.url, os.path.join(workspace, 'repo'))
            
            print(f"✅ Created workspace at: {workspace}")
            return workspace
            
        except Exception as e:
            print(f"❌ Error creating workspace: {str(e)}")
            return None
    
    def _run_docker_setup(self, framework, workspace):
        """Run Docker setup commands for the framework"""
        framework_name = framework.name.lower()
        
        # Get setup commands and timeout from framework configuration
        setup_commands = []
        setup_timeout = 300  # Default 5 minutes
        try:
            if framework.execution_commands:
                execution_config = json.loads(framework.execution_commands)
                setup_commands = execution_config.get('setup_commands', [])
                setup_timeout = execution_config.get('timeout', 300)  # Use framework timeout
        except (json.JSONDecodeError, KeyError):
            pass
        
        # Fallback to hardcoded setup commands if not configured
        if not setup_commands and framework_name in self.docker_commands:
            docker_config = self.docker_commands[framework_name]
            setup_commands = docker_config.get('setup_commands', [])
        
        docker_image = self.docker_images.get(framework_name, 'ubuntu:latest')
        
        if not setup_commands:
            return True
        
        print(f"🔧 Running Docker setup commands for {framework_name}")
        
        setup_errors = []
        
        for setup_cmd in setup_commands:
            try:
                # Format the setup command
                formatted_cmd = setup_cmd.format(
                    workspace=workspace,
                    image=docker_image
                )
                
                print(f"   Running: {formatted_cmd}")
                
                # Execute setup command with framework timeout
                result = subprocess.run(
                    formatted_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=setup_timeout  # Use framework timeout
                )
                
                if result.returncode != 0:
                    error_msg = f"Setup command failed (exit code {result.returncode}):\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
                    print(f"⚠️  {error_msg}")
                    setup_errors.append(error_msg)
                else:
                    print(f"✅ Setup command completed")
                    
            except subprocess.TimeoutExpired:
                error_msg = f"Setup command timed out after {setup_timeout} seconds"
                print(f"⚠️  {error_msg}")
                setup_errors.append(error_msg)
            except Exception as e:
                error_msg = f"Error running setup command: {str(e)}"
                print(f"⚠️  {error_msg}")
                setup_errors.append(error_msg)
        
        # Return setup errors if any occurred
        if setup_errors:
            return '\n'.join(setup_errors)
        
        return True
    
    def _build_execution_command(self, testcase, repo, framework, workspace):
        """Build execution command with workspace path and Docker fallback"""
        if not framework.execution_commands:
            return None
        
        try:
            execution_config = json.loads(framework.execution_commands)
            command_template = execution_config.get('command_template')
            use_docker = execution_config.get('use_docker', True)  # Default to Docker
            working_dir = execution_config.get('working_dir', '{repo_path}')
            
            if not command_template:
                return None
            
            # Prepare variables for template substitution
            repo_path = os.path.join(workspace, 'repo')
            variables = {
                'file_path': testcase.file_path or '',
                'test_name': testcase.name or '',
                'repo_path': repo_path,
                'test_function': testcase.name.replace(' ', '_').lower().replace('(', '').replace(')', ''),
                'class_name': os.path.splitext(os.path.basename(testcase.file_path or ''))[0] if testcase.file_path else '',
                'method_name': testcase.name.replace(' ', '').replace('(', '').replace(')', '') if testcase.name else ''
            }
            
            # Ensure test_function starts with 'test_' for pytest
            if not variables['test_function'].startswith('test_'):
                variables['test_function'] = f"test_{variables['test_function']}"
            
            # Try local command first if Docker is not preferred
            if not use_docker:
                command_str = command_template
                for var_name, var_value in variables.items():
                    command_str = command_str.replace(f'{{{var_name}}}', str(var_value))
                
                command = command_str.split()
                
                # Test if local command exists
                if self._test_command_exists(command[0]):
                    return command
            
            # Use Docker command - build from framework configuration
            framework_name = framework.name.lower()
            docker_image = self.docker_images.get(framework_name, 'ubuntu:latest')
            
            # Build Docker command using framework's command template
            # First replace variables in the command template
            formatted_template = command_template
            for var_name, var_value in variables.items():
                if var_name == 'test_name':
                    # For test names, we need to handle quotes properly
                    # The template should have {test_name} without quotes, we'll add them
                    formatted_template = formatted_template.replace(f'{{{var_name}}}', var_value)
                else:
                    formatted_template = formatted_template.replace(f'{{{var_name}}}', str(var_value))
            
            # Now build the Docker command with proper quoting
            # Use the working_dir from framework configuration
            docker_working_dir = f'/workspace{working_dir.replace("{repo_path}", "/repo")}'
            docker_command = f'docker run --rm -v {workspace}:/workspace -w {docker_working_dir} {docker_image} bash -c "{formatted_template}"'
            
            # Return the command as a single string for shell execution
            return docker_command
            
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            print(f"Error building execution command: {e}")
            return None
    
    def _test_command_exists(self, command):
        """Test if a command exists on the system"""
        try:
            result = subprocess.run(['which', command], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def _execute_with_monitoring(self, command, workspace, timeout, max_memory, queue_item_id, setup_result=None):
        """Execute command with resource monitoring and timeout handling"""
        start_time = datetime.utcnow()
        process = None
        
        try:
            print(f"🚀 Executing command with monitoring...")
            
            # Start process with resource limits
            # Handle both string and list commands
            if isinstance(command, str):
                # For string commands, use shell=True
                process = subprocess.Popen(
                    command,
                    cwd=workspace,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=True,
                    preexec_fn=os.setsid  # Create new process group
                )
            else:
                # For list commands, use shell=False
                process = subprocess.Popen(
                    command,
                    cwd=workspace,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    preexec_fn=os.setsid  # Create new process group
                )
            
            # Register process for monitoring
            with self.process_lock:
                self.active_processes[queue_item_id] = {
                    'process': process,
                    'start_time': start_time,
                    'command': command,
                    'workspace': workspace
                }
            
            print(f"✅ Command started with PID: {process.pid}")
            
            # Monitor process with timeout and memory limits
            stdout, stderr = self._monitor_process(process, timeout, max_memory, queue_item_id)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            print(f"✅ Command completed with exit code: {process.returncode}")
            print(f"✅ Duration: {duration} seconds")
            print(f"✅ STDOUT length: {len(stdout)} characters")
            print(f"✅ STDERR length: {len(stderr)} characters")
            
            # Include setup errors in stderr if any occurred
            if setup_result and setup_result is not True:
                stderr = f"SETUP ERRORS:\n{setup_result}\n\nEXECUTION ERRORS:\n{stderr}"
                print(f"⚠️  Including setup errors in execution logs")
            
            # Determine success
            success = process.returncode == 0
            
            return {
                'success': success,
                'output': stdout,
                'error': stderr,
                'duration': duration,
                'logs': self._format_logs(command, workspace, process.returncode, stdout, stderr, duration),
                'command': command if isinstance(command, str) else ' '.join(command),
                'pid': process.pid,
                'workspace': workspace
            }
            
        except subprocess.TimeoutExpired:
            print(f"❌ Command timed out after {timeout} seconds")
            self._terminate_process(process, queue_item_id)
            error_msg = f'Test execution timed out after {timeout} seconds'
            if setup_result and setup_result is not True:
                error_msg = f"SETUP ERRORS:\n{setup_result}\n\nEXECUTION ERROR:\n{error_msg}"
            return {
                'success': False,
                'output': '',
                'error': error_msg,
                'duration': timeout,
                'logs': self._format_logs(command, workspace, -1, '', error_msg, timeout),
                'command': command if isinstance(command, str) else ' '.join(command),
                'timeout': True
            }
        except Exception as e:
            print(f"❌ Error executing command: {str(e)}")
            if process:
                self._terminate_process(process, queue_item_id)
            error_msg = str(e)
            if setup_result and setup_result is not True:
                error_msg = f"SETUP ERRORS:\n{setup_result}\n\nEXECUTION ERROR:\n{error_msg}"
            return {
                'success': False,
                'output': '',
                'error': error_msg,
                'duration': (datetime.utcnow() - start_time).total_seconds(),
                'logs': self._format_logs(command, workspace, -1, '', error_msg, 0),
                'command': command if isinstance(command, str) else ' '.join(command)
            }
        finally:
            # Cleanup process registration
            with self.process_lock:
                if queue_item_id in self.active_processes:
                    del self.active_processes[queue_item_id]
    
    def _monitor_process(self, process, timeout, max_memory, queue_item_id):
        """Monitor process with timeout and memory limits"""
        start_time = time.time()
        
        while process.poll() is None:
            # Check timeout
            if time.time() - start_time > timeout:
                raise subprocess.TimeoutExpired(' '.join(process.args), timeout)
            
            # Check memory usage
            try:
                process_info = psutil.Process(process.pid)
                memory_mb = process_info.memory_info().rss / 1024 / 1024
                
                if memory_mb > max_memory:
                    print(f"⚠️  Memory limit exceeded: {memory_mb:.1f}MB > {max_memory}MB")
                    self._terminate_process(process, queue_item_id)
                    raise subprocess.TimeoutExpired('Memory limit exceeded', timeout)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass  # Process may have terminated
            
            time.sleep(0.1)  # Check every 100ms
        
        # Process completed, get output
        stdout, stderr = process.communicate()
        return stdout, stderr
    
    def _terminate_process(self, process, queue_item_id):
        """Terminate process and its children gracefully"""
        if not process:
            return
        
        try:
            # Kill process group
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            
            # Wait for graceful termination
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if not responding
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                process.wait()
                
        except (OSError, subprocess.TimeoutExpired) as e:
            print(f"⚠️  Error terminating process: {e}")
    
    def _format_logs(self, command, workspace, exit_code, stdout, stderr, duration):
        """Format execution logs in structured format"""
        return f"""=== TEST EXECUTION LOG ===
Timestamp: {datetime.utcnow().isoformat()}
Command: {command if isinstance(command, str) else ' '.join(command)}
Working Directory: {workspace}
Exit Code: {exit_code}
Duration: {duration:.2f} seconds

=== STDOUT ===
{stdout}

=== STDERR ===
{stderr}

=== EXECUTION SUMMARY ===
Status: {'SUCCESS' if exit_code == 0 else 'FAILED'}
Duration: {duration:.2f}s
Output Size: {len(stdout)} chars
Error Size: {len(stderr)} chars
"""
    
    def _mark_failed(self, queue_item, error_message):
        """Mark queue item as failed with error message"""
        print(f"❌ Marking queue item {queue_item.id} as failed: {error_message}")
        queue_item.status = 'failed'
        queue_item.completed_at = datetime.utcnow()
        queue_item.execution_config = json.dumps({'error': error_message})
        db.session.commit()
        print(f"✅ Queue item {queue_item.id} marked as failed")
    
    def _cleanup_workspace(self, workspace):
        """Clean up temporary workspace"""
        try:
            if os.path.exists(workspace):
                shutil.rmtree(workspace)
                print(f"✅ Cleaned up workspace: {workspace}")
        except Exception as e:
            print(f"⚠️  Error cleaning up workspace: {e}")
    
    def get_active_processes(self):
        """Get information about active processes"""
        with self.process_lock:
            return {
                queue_id: {
                    'pid': info['process'].pid,
                    'start_time': info['start_time'].isoformat(),
                    'command': info['command'] if isinstance(info['command'], str) else ' '.join(info['command']),
                    'workspace': info['workspace']
                }
                for queue_id, info in self.active_processes.items()
            }

# Global execution manager
execution_manager = None

def get_execution_manager(app):
    """Get or create execution manager instance"""
    global execution_manager
    if execution_manager is None:
        execution_manager = TestExecutionManager(app)
    return execution_manager

def cleanup_old_queue_items():
    """Clean up old queue items that are older than 24 hours"""
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Delete old completed/failed items
        old_items = TestExecutionQueue.query.filter(
            TestExecutionQueue.queued_at < cutoff_time,
            TestExecutionQueue.status.in_(['completed', 'failed'])
        ).all()
        
        for item in old_items:
            db.session.delete(item)
        
        # Mark stuck pending items as failed (older than 1 hour)
        stuck_cutoff = datetime.utcnow() - timedelta(hours=1)
        stuck_items = TestExecutionQueue.query.filter(
            TestExecutionQueue.queued_at < stuck_cutoff,
            TestExecutionQueue.status == 'pending'
        ).all()
        
        for item in stuck_items:
            item.status = 'failed'
            item.completed_at = datetime.utcnow()
            item.execution_config = json.dumps({'error': 'Stuck in queue for more than 1 hour - marked as failed'})
        
        if old_items or stuck_items:
            db.session.commit()
            print(f"🧹 Cleaned up {len(old_items)} old items and marked {len(stuck_items)} stuck items as failed")
        
    except Exception as e:
        print(f"⚠️  Error during queue cleanup: {e}")
        db.session.rollback()

@testcases.route('/testcases', methods=['GET'])
@login_required
def list_testcases():
    testcases = TestCase.query.options(
        joinedload(TestCase.workflows),
        joinedload(TestCase.labels),
        joinedload(TestCase.test_runs),
        joinedload(TestCase.repository).joinedload(GitRepository.test_framework)
    ).order_by(TestCase.created_at.desc()).all()
    
    # Get additional data for display
    git_repos = GitRepository.query.all()
    
    return render_template('testcases.html', testcases=testcases, git_repos=git_repos)

@testcases.route('/testcases/discover/<int:repo_id>', methods=['GET'])
@login_required
def discover_tests_for_repository(repo_id):
    """Fetch discovered test cases for a specific repository."""
    discovered_tests = discover_test_cases_from_repository(repo_id)
    
    # Format for dropdown - value should be the test name, display should include file path
    choices = [(tc['name'], f"{tc['name']} (File: {tc['file_path']})") for tc in discovered_tests]
    
    return jsonify({
        'success': True,
        'choices': choices,
        'test_cases': discovered_tests
    })

@testcases.route('/testcases/new', methods=['GET', 'POST'])
@login_required
@permission_required('testcase_create')
def create_testcase():
    form = TestCaseForm()
    
    # Populate form choices
    form.workflows.choices = [(w.id, w.name) for w in Workflow.query.order_by(Workflow.name).all()]
    form.git_repository_id.choices = [(None, 'Select Repository')] + [(r.id, f"{r.name} ({r.url})") for r in GitRepository.query.all()]
    form.labels.choices = [(l.id, l.name) for l in Label.query.all()]
    
    # Initialize discovered test case choices as empty
    form.discovered_test_case.choices = [(None, 'Select a repository first')]

    if request.method == 'POST':
        # Handle form submission manually to bypass choice validation
        form_data = request.form.to_dict()
        
        # Validate required fields manually
        errors = {}
        
        # Check required fields
        if not form_data.get('name'):
            errors['name'] = ['This field is required.']
        
        # Check for duplicate workflows (if any are selected)
        workflow_ids = []
        i = 0
        while True:
            wf_key = f'workflow_{i}'
            if wf_key not in form_data:
                break
            wf_id = form_data.get(wf_key)
            if wf_id:
                workflow_ids.append(wf_id)
            i += 1
        
        if len(set(workflow_ids)) != len(workflow_ids):
            errors['workflows'] = ['Duplicate workflows are not allowed.']
        
        # If no validation errors, process the form
        if not errors:
            # Handle discovered test case selection
            discovered_test_data = None
            discovered_test_case = form_data.get('discovered_test_case', '').strip()
            if discovered_test_case:
                # Get the selected repository
                repo_id = form_data.get('git_repository_id')
                if repo_id:
                    discovered_test_cases = discover_test_cases_from_repository(int(repo_id))
                    for tc in discovered_test_cases:
                        if tc['name'] == discovered_test_case:
                            discovered_test_data = tc
                            break
            
            testcase = TestCase(
                name=form_data.get('name'),
                description=form_data.get('description', ''),
                repository_id=discovered_test_data['repository_id'] if discovered_test_data else (int(form_data.get('git_repository_id')) if form_data.get('git_repository_id') else None),
                test_type=form_data.get('test_type') if form_data.get('test_type') else None,
                file_path=discovered_test_data['file_path'] if discovered_test_data else None,
                last_modified=datetime.utcnow(),
                is_discovered=bool(discovered_test_data),
                schedule=form_data.get('schedule') if form_data.get('schedule') != 'none' else None,
                next_run_at=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(testcase)
            db.session.flush()  # Get testcase.id
            
            # Handle labels
            labels = request.form.getlist('labels')
            if labels:
                for label_id in labels:
                    testcase_label = TestCaseLabel(test_case_id=testcase.id, label_id=int(label_id))
                    db.session.add(testcase_label)
            
            # Ensure uploads directory exists
            os.makedirs('uploads', exist_ok=True)
            # Handle dynamic workflow associations and file uploads
            i = 0
            while True:
                wf_key = f'workflow_{i}'
                file_key = f'sample_file_{i}'
                if wf_key not in form_data:
                    break
                wf_id = form_data.get(wf_key)
                if not wf_id:
                    i += 1
                    continue
                file_field = request.files.get(file_key)
                sample_file_path = None
                if file_field and file_field.filename:
                    filename = f"testcase_{testcase.id}_workflow_{wf_id}_" + file_field.filename
                    file_path = f"uploads/{filename}"
                    file_field.save(file_path)
                    sample_file_path = file_path
                assoc = db.session.execute(
                    testcase_workflow.insert().values(
                        test_case_id=testcase.id,
                        workflow_id=int(wf_id),
                        sample_file=sample_file_path
                    )
                )
                db.session.add(assoc)
                i += 1
            db.session.commit()
            db.session.add(AuditLog(
                user=current_user.username,
                action='create',
                filetype='testcase',
                details=f"Created test case: {testcase.name} (ID: {testcase.id})"
            ))
            db.session.commit()
            flash('Test case created successfully!', 'success')
            return redirect(url_for('testcases.list_testcases'))
        else:
            # Set form errors
            for field, field_errors in errors.items():
                if hasattr(form, field):
                    getattr(form, field).errors = field_errors
    
    return render_template('testcase_form.html', form=form, action='Create')

@testcases.route('/testcases/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('testcase_edit')
def edit_testcase(id):
    testcase = TestCase.query.get_or_404(id)
    form = TestCaseForm(obj=testcase)
    
    # Populate form choices
    form.workflows.choices = [(w.id, w.name) for w in Workflow.query.order_by(Workflow.name).all()]
    form.git_repository_id.choices = [(None, 'Select Repository')] + [(r.id, f"{r.name} ({r.url})") for r in GitRepository.query.all()]
    form.labels.choices = [(l.id, l.name) for l in Label.query.all()]
    
    if request.method == 'GET':
        # Get workflow IDs from the many-to-many relationship
        if hasattr(testcase, 'workflows'):
            form.workflows.data = [w.id for w in testcase.workflows]
        else:
            form.workflows.data = []
        form.schedule.data = testcase.schedule or 'none'
        
        # Get label IDs from the many-to-many relationship
        if hasattr(testcase, 'labels'):
            form.labels.data = [l.id for l in testcase.labels]
        else:
            form.labels.data = []
    
    if form.validate_on_submit():
        # Custom validation for dynamic workflows
        workflow_ids = []
        i = 0
        while True:
            wf_key = f'workflow_{i}'
            if wf_key not in request.form:
                break
            wf_id = request.form.get(wf_key)
            if wf_id:
                workflow_ids.append(wf_id)
            i += 1
        if not workflow_ids:
            flash('At least one workflow must be added.', 'danger')
            return render_template('testcase_form.html', form=form, action='Edit')
        if len(set(workflow_ids)) != len(workflow_ids):
            flash('Duplicate workflows are not allowed.', 'danger')
            return render_template('testcase_form.html', form=form, action='Edit')
        
        testcase.name = form.name.data
        testcase.description = form.description.data
        testcase.repository_id = form.git_repository_id.data if form.git_repository_id.data else None
        testcase.schedule = form.schedule.data if form.schedule.data != 'none' else None
        testcase.updated_at = datetime.utcnow()
        
        # Handle labels
        TestCaseLabel.query.filter_by(test_case_id=testcase.id).delete()
        if form.labels.data:
            for label_id in form.labels.data:
                testcase_label = TestCaseLabel(test_case_id=testcase.id, label_id=label_id)
                db.session.add(testcase_label)
        
        # Remove old associations
        db.session.execute(testcase_workflow.delete().where(testcase_workflow.c.test_case_id == testcase.id))
        # Ensure uploads directory exists
        os.makedirs('uploads', exist_ok=True)
        # Add new associations and handle file uploads
        i = 0
        while True:
            wf_key = f'workflow_{i}'
            file_key = f'sample_file_{i}'
            if wf_key not in request.form:
                break
            wf_id = request.form.get(wf_key)
            if not wf_id:
                i += 1
                continue
            file_field = request.files.get(file_key)
            sample_file_path = None
            if file_field and file_field.filename:
                filename = f"testcase_{testcase.id}_workflow_{wf_id}_" + file_field.filename
                file_path = f"uploads/{filename}"
                file_field.save(file_path)
                sample_file_path = file_path
            assoc = db.session.execute(
                testcase_workflow.insert().values(
                    test_case_id=testcase.id,
                    workflow_id=int(wf_id),
                    sample_file=sample_file_path
                )
            )
            db.session.add(assoc)
            i += 1
        db.session.commit()
        db.session.add(AuditLog(
            user=current_user.username,
            action='edit',
            filetype='testcase',
            details=f"Edited test case: {testcase.name} (ID: {testcase.id})"
        ))
        db.session.commit()
        flash('Test case updated successfully!', 'success')
        return redirect(url_for('testcases.list_testcases'))
    return render_template('testcase_form.html', form=form, action='Edit')

@testcases.route('/testcases/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('testcase_delete')
def delete_testcase(id):
    testcase = TestCase.query.get_or_404(id)
    # Delete all associated test runs
    TestRun.query.filter_by(test_case_id=testcase.id).delete()
    db.session.delete(testcase)
    db.session.commit()
    db.session.add(AuditLog(
        user=current_user.username,
        action='delete',
        filetype='testcase',
        details=f"Deleted test case: {testcase.name} (ID: {testcase.id})"
    ))
    db.session.commit()
    flash('Test case deleted successfully!', 'success')
    return redirect(url_for('testcases.list_testcases'))

@testcases.route('/testcases/execute', methods=['GET', 'POST'])
@login_required
@permission_required('testcase_execute')
def execute_testcases():
    """Test execution page with filtering and real-time execution."""
    if request.method == 'GET':
        # Get filter parameters
        label_filter = request.args.get('label', type=int)
        test_type_filter = request.args.get('test_type')
        repo_filter = request.args.get('repository', type=int)
        framework_filter = request.args.get('framework', type=int)
        
        # Build query with filters
        query = TestCase.query
        
        if label_filter:
            query = query.join(TestCaseLabel).filter(TestCaseLabel.label_id == label_filter)
        if test_type_filter:
            query = query.filter(TestCase.test_type == test_type_filter)
        if repo_filter:
            query = query.filter(TestCase.repository_id == repo_filter)
            
        testcases = query.order_by(TestCase.created_at.desc()).all()
        
        # Get filter options
        labels = Label.query.all()
        repositories = GitRepository.query.all()
        frameworks = TestFramework.query.all()
        
        return render_template('testcases_execute.html', 
                             testcases=testcases,
                             labels=labels,
                             repositories=repositories,
                             frameworks=frameworks,
                             current_filters={
                                 'label': label_filter,
                                 'test_type': test_type_filter,
                                 'repository': repo_filter,
                                 'framework': framework_filter
                             })
    
    # Handle POST - Execute selected test cases
    testcase_ids = request.form.getlist('testcase_ids')
    if not testcase_ids:
        flash('No test cases selected for execution.', 'warning')
        return redirect(url_for('testcases.execute_testcases'))
    
    # Add test cases to execution queue
    for tc_id in testcase_ids:
        testcase = TestCase.query.get(tc_id)
        if testcase:
            # Create new queue item (allow multiple executions)
            queue_item = TestExecutionQueue(
                test_case_id=testcase.id,
                status='pending',
                queued_at=datetime.utcnow()
            )
            db.session.add(queue_item)
            db.session.commit()  # Commit immediately to ensure the item is available
            
            print(f"🔧 Creating execution queue item {queue_item.id} for test case {testcase.name}")
            
            # Start background worker to execute the test
            execution_manager = get_execution_manager(current_app._get_current_object())
            thread = threading.Thread(target=execution_manager.execute_test, args=(queue_item.id, current_app._get_current_object()))
            thread.daemon = True
            thread.start()
            
            print(f"✅ Started background thread for queue item {queue_item.id}")
    flash(f'Added {len(testcase_ids)} test case(s) to execution queue.', 'success')
    return redirect(url_for('testcases.execute_testcases'))

@testcases.route('/testcases/execute/status', methods=['GET'])
@login_required
def execution_status():
    """Get real-time execution status."""
    # Run cleanup periodically (every 10th request to avoid too frequent cleanup)
    import random
    if random.randint(1, 10) == 1:
        cleanup_old_queue_items()
    
    queue_items = TestExecutionQueue.query.order_by(TestExecutionQueue.queued_at.desc()).limit(50).all()
    
    status_data = []
    for item in queue_items:
        testcase = item.test_case
        
        # Get execution details
        execution_details = {}
        if item.execution_config:
            try:
                execution_details = json.loads(item.execution_config)
            except:
                execution_details = {'error': 'Invalid execution config'}
        
        status_data.append({
            'id': item.id,
            'test_case_name': testcase.name if testcase else 'Unknown',
            'status': item.status,
            'queued_at': item.queued_at.strftime('%Y-%m-%d %H:%M:%S') if item.queued_at else None,
            'scheduled_at': item.scheduled_at.strftime('%Y-%m-%d %H:%M:%S') if item.scheduled_at else None,
            'priority': item.priority,
            'execution_details': execution_details
        })
    
    return jsonify(status_data)

@testcases.route('/testcases/execute/report', methods=['GET'])
@login_required
def download_execution_report():
    """Download execution report as CSV."""
    # Get execution data
    queue_items = TestExecutionQueue.query.order_by(TestExecutionQueue.queued_at.desc()).all()
    
    def generate():
        data = csv.writer([])
        header = ['Test Case', 'Repository', 'Framework', 'Type', 'Status', 'Queued At', 'Scheduled At', 'Priority']
        yield ','.join(header) + '\n'
        
        for item in queue_items:
            testcase = item.test_case
            if testcase:
                repo_name = testcase.repository.name if testcase.repository else 'N/A'
                framework_name = testcase.repository.test_framework.name if testcase.repository and testcase.repository.test_framework else 'N/A'
                test_type = testcase.test_type or 'N/A'
                
                row = [
                    testcase.name,
                    repo_name,
                    framework_name,
                    test_type,
                    item.status,
                    item.queued_at.strftime('%Y-%m-%d %H:%M:%S') if item.queued_at else '',
                    item.scheduled_at.strftime('%Y-%m-%d %H:%M:%S') if item.scheduled_at else '',
                    str(item.priority)
                ]
                yield ','.join(row) + '\n'
    
    return Response(generate(), mimetype='text/csv', headers={
        'Content-Disposition': 'attachment; filename=test_execution_report.csv'
    })

@testcases.route('/testruns/<int:id>', methods=['GET'])
@login_required
def testrun_detail(id):
    testrun = TestRun.query.get_or_404(id)
    testcase = TestCase.query.get(testrun.test_case_id)
    # Get workflows through the many-to-many relationship
    workflows = []
    if testcase and hasattr(testcase, 'workflows'):
        workflows = testcase.workflows
    return render_template('testrun_detail.html', testrun=testrun, testcase=testcase, workflows=workflows)

@testcases.route('/testruns', methods=['GET'])
@login_required
def list_testruns():
    query = TestRun.query
    status = request.args.get('status')
    date = request.args.get('date')
    test_case_id = request.args.get('test_case_id', type=int)
    if status:
        query = query.filter_by(status=status)
    if date:
        try:
            dt = datetime.strptime(date, '%Y-%m-%d')
            next_day = dt + timedelta(days=1)
            query = query.filter(TestRun.executed_at >= dt, TestRun.executed_at < next_day)
        except Exception:
            pass
    if test_case_id:
        query = query.filter_by(test_case_id=test_case_id)
    runs = query.order_by(TestRun.executed_at.desc()).limit(100).all()
    return render_template('testruns_list.html', runs=runs, status=status, date=date, test_case_id=test_case_id)

@testcases.route('/testruns/export', methods=['GET'])
@login_required
def export_testruns():
    query = TestRun.query
    status = request.args.get('status')
    date = request.args.get('date')
    test_case_id = request.args.get('test_case_id', type=int)
    if status:
        query = query.filter_by(status=status)
    if date:
        try:
            dt = datetime.strptime(date, '%Y-%m-%d')
            next_day = dt + timedelta(days=1)
            query = query.filter(TestRun.executed_at >= dt, TestRun.executed_at < next_day)
        except Exception:
            pass
    if test_case_id:
        query = query.filter_by(test_case_id=test_case_id)
    runs = query.order_by(TestRun.executed_at.desc()).all()
    def generate():
        data = csv.writer([])
        header = ['Test Case', 'Workflows', 'Status', 'Executed At', 'Duration', 'Output']
        yield ','.join(header) + '\n'
        for run in runs:
            # Get workflow names from the many-to-many relationship
            workflow_names = []
            if run.test_case and hasattr(run.test_case, 'workflows'):
                workflow_names = [w.name for w in run.test_case.workflows]
            workflow_str = '; '.join(workflow_names) if workflow_names else ''
            
            row = [
                run.test_case.name if run.test_case else '',
                workflow_str,
                run.status,
                run.executed_at.strftime('%Y-%m-%d %H:%M:%S'),
                str(run.duration),
                '"' + (run.output.replace('"', '""') if run.output else '') + '"'
            ]
            yield ','.join(row) + '\n'
    return Response(generate(), mimetype='text/csv', headers={
        'Content-Disposition': 'attachment; filename=testruns.csv'
    })

@testcases.route('/testcases/auditlog', methods=['GET'])
@login_required
def testcases_auditlog():
    query = AuditLog.query.filter_by(filetype='testcase')
    user = request.args.get('user')
    action = request.args.get('action')
    date = request.args.get('date')
    if user:
        query = query.filter_by(user=user)
    if action:
        query = query.filter_by(action=action)
    if date:
        try:
            dt = datetime.strptime(date, '%Y-%m-%d')
            next_day = dt + timedelta(days=1)
            query = query.filter(AuditLog.timestamp >= dt, AuditLog.timestamp < next_day)
        except Exception:
            pass
    logs = query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return render_template('testcases_auditlog.html', logs=logs, user=user, action=action, date=date)

@testcases.route('/testcases/<int:id>', methods=['GET'])
@login_required
def testcase_detail(id):
    testcase = TestCase.query.get_or_404(id)
    runs = TestRun.query.filter_by(test_case_id=id).order_by(TestRun.executed_at.desc()).all()
    # Get workflows through the many-to-many relationship
    workflows = testcase.workflows if hasattr(testcase, 'workflows') else []
    
    # Get related information
    git_repo = GitRepository.query.get(testcase.repository_id) if testcase.repository_id else None
    framework = git_repo.test_framework if git_repo else None
    labels = testcase.labels if hasattr(testcase, 'labels') else []
    
    return render_template('testcases_detail.html', 
                         testcase=testcase, 
                         runs=runs, 
                         workflows=workflows,
                         git_repo=git_repo,
                         framework=framework,
                         labels=labels)

@testcases.route('/testcases/<int:id>/clone', methods=['POST'])
@login_required
@permission_required('testcase_create')
def clone_testcase(id):
    orig = TestCase.query.get_or_404(id)
    new_tc = TestCase(
        name=orig.name + ' (Clone)',
        description=orig.description,
        schedule=orig.schedule,
        next_run_at=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.session.add(new_tc)
    db.session.commit()
    db.session.add(AuditLog(
        user=current_user.username,
        action='clone',
        filetype='testcase',
        details=f"Cloned test case: {orig.name} (ID: {orig.id}) to {new_tc.name} (ID: {new_tc.id})"
    ))
    db.session.commit()
    flash('Test case cloned successfully!', 'success')
    return redirect(url_for('testcases.edit_testcase', id=new_tc.id)) 

@testcases.route('/testcases/execute/logs/<int:queue_id>', methods=['GET'])
@login_required
def execution_logs(queue_id):
    """Get detailed execution logs for a queue item."""
    queue_item = TestExecutionQueue.query.get_or_404(queue_id)
    
    execution_details = {}
    if queue_item.execution_config:
        try:
            execution_details = json.loads(queue_item.execution_config)
        except:
            execution_details = {'error': 'Invalid execution config'}
    
    return jsonify({
        'id': queue_item.id,
        'test_case_name': queue_item.test_case.name if queue_item.test_case else 'Unknown',
        'status': queue_item.status,
        'queued_at': queue_item.queued_at.strftime('%Y-%m-%d %H:%M:%S') if queue_item.queued_at else None,
        'execution_details': execution_details
    })

@testcases.route('/testcases/execute/cleanup', methods=['POST'])
@login_required
@permission_required('testcase_execute')
def cleanup_queue():
    """Manually clean up old queue items"""
    try:
        cleanup_old_queue_items()
        flash('Queue cleanup completed successfully.', 'success')
    except Exception as e:
        flash(f'Error during cleanup: {str(e)}', 'error')
    
    return redirect(url_for('testcases.execute_testcases'))

@testcases.route('/testcases/execute/monitor', methods=['GET'])
@login_required
def execution_monitor():
    """Monitor active processes and system resources (CI/CD style)"""
    try:
        # Get active processes from execution manager
        execution_manager = get_execution_manager(current_app._get_current_object())
        active_processes = execution_manager.get_active_processes()
        
        # Get system resource usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get queue statistics
        pending_count = TestExecutionQueue.query.filter_by(status='pending').count()
        running_count = TestExecutionQueue.query.filter_by(status='running').count()
        completed_count = TestExecutionQueue.query.filter_by(status='completed').count()
        failed_count = TestExecutionQueue.query.filter_by(status='failed').count()
        
        return jsonify({
            'active_processes': active_processes,
            'system_resources': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3)
            },
            'queue_stats': {
                'pending': pending_count,
                'running': running_count,
                'completed': completed_count,
                'failed': failed_count,
                'total': pending_count + running_count + completed_count + failed_count
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500 