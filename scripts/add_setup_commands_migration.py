#!/usr/bin/env python3
"""
Migration script to add setup_commands column to test_framework table.
This makes Docker setup commands configurable through the UI.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import TestFramework
from sqlalchemy import text

def migrate():
    """Add setup_commands column to test_framework table"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Adding setup_commands column to test_framework table...")
        
        try:
            # Add the column using raw SQL
            db.session.execute(text('ALTER TABLE test_framework ADD COLUMN setup_commands TEXT'))
            db.session.commit()
            print("✅ Successfully added setup_commands column")
            
            # Update existing frameworks with default setup commands
            frameworks = TestFramework.query.all()
            for framework in frameworks:
                if not framework.setup_commands:
                    # Set default setup commands based on framework type
                    if 'cucumber' in framework.name.lower():
                        framework.setup_commands = '["docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} bash -c \\"mvn clean compile --batch-mode\\""]'
                    elif 'pytest' in framework.name.lower():
                        framework.setup_commands = '["docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} bash -c \\"pip install -r requirements.txt\\""]'
                    elif 'playwright' in framework.name.lower():
                        framework.setup_commands = '["docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} bash -c \\"npm install\\"", "docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} bash -c \\"npx playwright install\\""]'
                    elif 'selenium' in framework.name.lower():
                        framework.setup_commands = '["docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} bash -c \\"mvn clean compile --batch-mode\\""]'
                    elif 'jest' in framework.name.lower():
                        framework.setup_commands = '["docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} bash -c \\"npm install\\""]'
                    elif 'cypress' in framework.name.lower():
                        framework.setup_commands = '["docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} bash -c \\"npm install\\""]'
                    elif 'nunit' in framework.name.lower():
                        framework.setup_commands = '["docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} bash -c \\"dotnet restore\\""]'
                    elif 'robot' in framework.name.lower():
                        framework.setup_commands = '["docker run --rm -v {workspace}:/workspace -w /workspace/repo {image} bash -c \\"pip install -r requirements.txt\\""]'
                    else:
                        framework.setup_commands = '[]'
            
            db.session.commit()
            print(f"✅ Updated {len(frameworks)} frameworks with default setup commands")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            db.session.rollback()
            return False
        
        return True

if __name__ == '__main__':
    success = migrate()
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
        sys.exit(1) 