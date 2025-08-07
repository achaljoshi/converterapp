#!/usr/bin/env python3
"""
Startup migration script - only adds missing fields and tables
DOES NOT drop or recreate existing data
"""

from app import create_app, db
from app.models import *
import sqlite3
import os

def startup_migrate():
    """Run migrations only if needed, preserving all existing data"""
    app = create_app()
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Check if database exists
        if not os.path.exists(db_path):
            print(f"Database not found at {db_path}, creating new database...")
            db.create_all()
            seed_initial_data()
            return
        
        print(f"Database exists at {db_path}, checking for missing fields...")
        
        # Connect to SQLite database directly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check and add missing columns to existing tables
            add_missing_columns(cursor)
            
            # Create new tables if they don't exist
            create_missing_tables(cursor)
            
            # Seed default data only if tables are empty
            seed_default_data_if_needed(cursor)
            
            conn.commit()
            print("Startup migration completed successfully!")
            
        except Exception as e:
            print(f"Error during startup migration: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

def add_missing_columns(cursor):
    """Add missing columns to existing tables"""
    
    # Check workflow table
    try:
        cursor.execute("PRAGMA table_info(workflow)")
        workflow_columns = [col[1] for col in cursor.fetchall()]
        
        if 'stages' not in workflow_columns:
            print("Adding 'stages' column to workflow table...")
            cursor.execute("ALTER TABLE workflow ADD COLUMN stages TEXT")
        
        if 'description' not in workflow_columns:
            print("Adding 'description' column to workflow table...")
            cursor.execute("ALTER TABLE workflow ADD COLUMN description TEXT")
        
        if 'is_active' not in workflow_columns:
            print("Adding 'is_active' column to workflow table...")
            cursor.execute("ALTER TABLE workflow ADD COLUMN is_active BOOLEAN DEFAULT 1")
    except:
        print("Workflow table doesn't exist yet")
    
    # Check test_case table
    try:
        cursor.execute("PRAGMA table_info(test_case)")
        testcase_columns = [col[1] for col in cursor.fetchall()]
        
        missing_testcase_columns = [
            ('repository_id', 'INTEGER'),
            ('file_path', 'VARCHAR(500)'),
            ('test_type', 'VARCHAR(50)'),
            ('last_modified', 'DATETIME'),
            ('is_discovered', 'BOOLEAN DEFAULT 0')
        ]
        
        for col_name, col_type in missing_testcase_columns:
            if col_name not in testcase_columns:
                print(f"Adding '{col_name}' column to test_case table...")
                cursor.execute(f"ALTER TABLE test_case ADD COLUMN {col_name} {col_type}")
    except:
        print("Test_case table doesn't exist yet")
    
    # Check test_run table
    try:
        cursor.execute("PRAGMA table_info(test_run)")
        testrun_columns = [col[1] for col in cursor.fetchall()]
        
        missing_testrun_columns = [
            ('execution_logs', 'TEXT'),
            ('error_details', 'TEXT'),
            ('environment', 'VARCHAR(100)'),
            ('browser', 'VARCHAR(50)'),
            ('api_endpoint', 'VARCHAR(200)')
        ]
        
        for col_name, col_type in missing_testrun_columns:
            if col_name not in testrun_columns:
                print(f"Adding '{col_name}' column to test_run table...")
                cursor.execute(f"ALTER TABLE test_run ADD COLUMN {col_name} {col_type}")
    except:
        print("Test_run table doesn't exist yet")

def create_missing_tables(cursor):
    """Create new tables if they don't exist"""
    
    new_tables = [
        ('git_repository', '''
            CREATE TABLE IF NOT EXISTS git_repository (
                id INTEGER PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                url VARCHAR(500) NOT NULL,
                branch VARCHAR(100) DEFAULT 'main',
                repo_type VARCHAR(50) NOT NULL,
                local_path VARCHAR(500),
                last_sync DATETIME,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                username VARCHAR(100),
                password VARCHAR(500),
                ssh_key_path VARCHAR(500),
                test_patterns TEXT,
                ignore_patterns TEXT,
                test_framework_id INTEGER,
                custom_extraction_rules TEXT
            )
        '''),
        ('test_framework', '''
            CREATE TABLE IF NOT EXISTS test_framework (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                description VARCHAR(255),
                language VARCHAR(50),
                file_extensions TEXT,
                test_patterns TEXT,
                test_name_patterns TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                settings TEXT
            )
        '''),
        ('label', '''
            CREATE TABLE IF NOT EXISTS label (
                id INTEGER PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                color VARCHAR(7) DEFAULT '#007bff',
                description VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        '''),
        ('testcase_label', '''
            CREATE TABLE IF NOT EXISTS testcase_label (
                id INTEGER PRIMARY KEY,
                test_case_id INTEGER NOT NULL,
                label_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_case_id) REFERENCES test_case (id),
                FOREIGN KEY (label_id) REFERENCES label (id)
            )
        '''),
        ('test_execution_queue', '''
            CREATE TABLE IF NOT EXISTS test_execution_queue (
                id INTEGER PRIMARY KEY,
                test_case_id INTEGER NOT NULL,
                priority INTEGER DEFAULT 0,
                scheduled_at DATETIME,
                queued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(32) DEFAULT 'pending',
                execution_config TEXT,
                FOREIGN KEY (test_case_id) REFERENCES test_case (id)
            )
        ''')
    ]
    
    for table_name, create_sql in new_tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not cursor.fetchone():
            print(f"Creating table: {table_name}")
            cursor.execute(create_sql)

def seed_default_data_if_needed(cursor):
    """Seed default data only if tables are empty"""
    
    # Check if test_framework table is empty
    cursor.execute("SELECT COUNT(*) FROM test_framework")
    if cursor.fetchone()[0] == 0:
        print("Seeding test frameworks...")
        
        frameworks = [
            ('Pytest', 'Python testing framework', 'Python', '["py"]', '["def test_", "@pytest.mark", "class Test"]', '["def (test_\\\\w+)", "class (Test\\\\w+)", "@pytest\\\\.mark\\\\.(\\\\w+)"]', '{"conftest_support": true, "fixture_support": true}'),
            ('Selenium TestNG', 'Java testing framework with TestNG', 'Java', '["java"]', '["@Test", "public void test", "class Test"]', '["@Test\\\\s+public\\\\s+void\\\\s+(\\\\w+)", "public\\\\s+void\\\\s+(test\\\\w+)", "class (Test\\\\w+)"]', '{"annotation_support": true, "parallel_execution": true}'),
            ('Playwright', 'Microsoft Playwright testing framework', 'JavaScript', '["js", "ts"]', '["test(", "describe(", "it("]', '["test\\\\(\\\\s*[\'\"]([^\'\"]+)[\'\"]", "it\\\\(\\\\s*[\'\"]([^\'\"]+)[\'\"]", "describe\\\\(\\\\s*[\'\"]([^\'\"]+)[\'\"]"]', '{"browser_support": ["chromium", "firefox", "webkit"], "async_support": true}'),
            ('Cucumber', 'BDD testing framework', 'Ruby', '["feature", "rb"]', '["Scenario:", "Feature:", "Given ", "When ", "Then "]', '["Scenario:\\\\s*(\\\\w+)", "Feature:\\\\s*(\\\\w+)", "def (\\\\w+)"]', '{"gherkin_support": true, "step_definitions": true}'),
            ('Jest', 'JavaScript testing framework', 'JavaScript', '["js", "ts", "jsx", "tsx"]', '["test(", "describe(", "it("]', '["test\\\\(\\\\s*[\'\"]([^\'\"]+)[\'\"]", "it\\\\(\\\\s*[\'\"]([^\'\"]+)[\'\"]", "describe\\\\(\\\\s*[\'\"]([^\'\"]+)[\'\"]"]', '{"mock_support": true, "coverage_support": true}'),
            ('Cypress', 'End-to-end testing framework', 'JavaScript', '["js", "ts"]', '["describe(", "it(", "cy."]', '["describe\\\\(\\\\s*[\'\"]([^\'\"]+)[\'\"]", "it\\\\(\\\\s*[\'\"]([^\'\"]+)[\'\"]"]', '{"browser_automation": true, "real_time_reload": true}'),
            ('NUnit', '.NET testing framework', 'C#', '["cs"]', '["[Test]", "[TestMethod]", "public void Test"]', '["\\\\[Test\\\\]\\\\s*public\\\\s+void\\\\s+(\\\\w+)", "\\\\[TestMethod\\\\]\\\\s*public\\\\s+void\\\\s+(\\\\w+)", "public\\\\s+void\\\\s+(Test\\\\w+)"]', '{"attribute_support": true, "parallel_execution": true}'),
            ('Robot Framework', 'Python-based automation framework', 'Python', '["robot"]', '["*** Test Cases ***", "*** Keywords ***"]', '["([A-Za-z0-9_]+)\\\\s*\\\\[Documentation\\\\]", "([A-Za-z0-9_]+)\\\\s*\\\\[Tags\\\\]"]', '{"keyword_driven": true, "data_driven": true}')
        ]
        
        for framework in frameworks:
            cursor.execute('''
                INSERT INTO test_framework (name, description, language, file_extensions, test_patterns, test_name_patterns, settings)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', framework)
    
    # Check if label table is empty
    cursor.execute("SELECT COUNT(*) FROM label")
    if cursor.fetchone()[0] == 0:
        print("Seeding labels...")
        
        labels = [
            ('Smoke', '#28a745', 'Smoke tests'),
            ('Regression', '#dc3545', 'Regression tests'),
            ('UI', '#007bff', 'UI tests'),
            ('API', '#6f42c1', 'API tests'),
            ('Critical', '#fd7e14', 'Critical path tests'),
            ('Performance', '#e83e8c', 'Performance tests'),
            ('Security', '#6c757d', 'Security tests'),
            ('Integration', '#20c997', 'Integration tests')
        ]
        
        for label in labels:
            cursor.execute('''
                INSERT INTO label (name, color, description)
                VALUES (?, ?, ?)
            ''', label)

def seed_initial_data():
    """Seed initial data for new database"""
    from werkzeug.security import generate_password_hash
    from app.models import User, Role, Permission
    
    # Create permissions
    permissions = [
        'dashboard_view',
        'testcase_create', 'testcase_edit', 'testcase_delete', 'testcase_execute',
        'testrun_view', 'testrun_export',
        'auditlog_view',
        'filetype_manage',
        'workflow_manage',
        'config_manage',
        'repo_manage',
        'framework_manage',
        'label_manage'
    ]
    
    perm_objs = {}
    for perm in permissions:
        p = Permission(name=perm, description=perm.replace('_', ' ').capitalize())
        db.session.add(p)
        perm_objs[perm] = p
    
    db.session.commit()
    
    # Create roles
    roles = {
        'admin': permissions,
        'tester': [
            'dashboard_view', 'testcase_execute', 'testrun_view', 'testrun_export'
        ],
        'analyst': [
            'dashboard_view', 'testrun_view', 'testrun_export'
        ],
        'developer': [
            'dashboard_view', 'testrun_view', 'testrun_export'
        ],
    }
    
    for role_name, perms in roles.items():
        role = Role(name=role_name, description=role_name.capitalize())
        db.session.add(role)
        role.permissions = [perm_objs[p] for p in perms]
    
    db.session.commit()
    
    # Create admin user
    admin_role = Role.query.filter_by(name='admin').first()
    admin = User(
        username='admin',
        password=generate_password_hash('admin123', method='pbkdf2:sha256'),
        role=admin_role
    )
    db.session.add(admin)
    db.session.commit()
    
    print("Initial data seeded successfully!")

if __name__ == '__main__':
    startup_migrate() 