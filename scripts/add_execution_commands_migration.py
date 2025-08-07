#!/usr/bin/env python3
"""
Migration script to add execution_commands field to TestFramework table
"""

import os
import sys
import json

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app import create_app, db
from app.models import TestFramework
from sqlalchemy import text

def add_execution_commands_field():
    """Add execution_commands field to TestFramework table"""
    
    app = create_app()
    with app.app_context():
        
        # Check if the column already exists
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('test_framework')]
        
        if 'execution_commands' in columns:
            print("✅ execution_commands column already exists")
            return
        
        # Add the new column
        try:
            db.session.execute(text('ALTER TABLE test_framework ADD COLUMN execution_commands TEXT'))
            db.session.commit()
            print("✅ Added execution_commands column to test_framework table")
        except Exception as e:
            print(f"❌ Error adding column: {e}")
            return
        
        # Update existing frameworks with default execution commands
        frameworks = TestFramework.query.all()
        
        default_commands = {
            'cucumber': {
                'command_template': 'cucumber {file_path} --name "{test_name}" --format json --out -',
                'working_dir': '{repo_path}',
                'timeout': 300,
                'success_codes': [0]
            },
            'pytest': {
                'command_template': 'pytest {file_path}::{test_function} -v --json-report --json-report-file=-',
                'working_dir': '{repo_path}',
                'timeout': 300,
                'success_codes': [0]
            },
            'playwright': {
                'command_template': 'npx playwright test {file_path} --grep "{test_name}" --reporter=json',
                'working_dir': '{repo_path}',
                'timeout': 300,
                'success_codes': [0]
            },
            'selenium': {
                'command_template': 'mvn test -Dtest={class_name}#{method_name} -Dtestng.output.format=json',
                'working_dir': '{repo_path}',
                'timeout': 300,
                'success_codes': [0]
            },
            'jest': {
                'command_template': 'npx jest {file_path} --testNamePattern "{test_name}" --json --outputFile=-',
                'working_dir': '{repo_path}',
                'timeout': 300,
                'success_codes': [0]
            },
            'cypress': {
                'command_template': 'npx cypress run --spec {file_path} --reporter json --reporter-options output=-',
                'working_dir': '{repo_path}',
                'timeout': 300,
                'success_codes': [0]
            },
            'nunit': {
                'command_template': 'dotnet test {file_path} --filter TestName="{test_name}" --logger json',
                'working_dir': '{repo_path}',
                'timeout': 300,
                'success_codes': [0]
            },
            'robot': {
                'command_template': 'robot --test "{test_name}" --output - --report - --log - {file_path}',
                'working_dir': '{repo_path}',
                'timeout': 300,
                'success_codes': [0]
            }
        }
        
        for framework in frameworks:
            framework_name = framework.name.lower()
            if framework_name in default_commands:
                framework.execution_commands = json.dumps(default_commands[framework_name])
                print(f"✅ Updated {framework.name} with execution commands")
        
        db.session.commit()
        print("✅ Migration completed successfully!")

if __name__ == "__main__":
    add_execution_commands_field() 