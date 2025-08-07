from app import create_app, db
from app.models import *
import sqlite3
import json

def migrate_preserve_data():
    app = create_app()
    with app.app_context():
        # Get the database file path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        print(f"Migrating database: {db_path}")
        
        # Connect to SQLite database directly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if tables exist and add missing columns
            cursor.execute("PRAGMA table_info(workflow)")
            workflow_columns = [col[1] for col in cursor.fetchall()]
            
            # Add missing columns to workflow table
            if 'stages' not in workflow_columns:
                print("Adding 'stages' column to workflow table...")
                cursor.execute("ALTER TABLE workflow ADD COLUMN stages TEXT")
            
            if 'description' not in workflow_columns:
                print("Adding 'description' column to workflow table...")
                cursor.execute("ALTER TABLE workflow ADD COLUMN description TEXT")
            
            if 'is_active' not in workflow_columns:
                print("Adding 'is_active' column to workflow table...")
                cursor.execute("ALTER TABLE workflow ADD COLUMN is_active BOOLEAN DEFAULT 1")
            
            # Check test_case table
            cursor.execute("PRAGMA table_info(test_case)")
            testcase_columns = [col[1] for col in cursor.fetchall()]
            
            # Add missing columns to test_case table
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
            
            # Check test_run table
            cursor.execute("PRAGMA table_info(test_run)")
            testrun_columns = [col[1] for col in cursor.fetchall()]
            
            # Add missing columns to test_run table
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
            
            # Create new tables if they don't exist
            new_tables = [
                ('git_repository', '''
                    CREATE TABLE git_repository (
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
                    CREATE TABLE test_framework (
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
                    CREATE TABLE label (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(50) UNIQUE NOT NULL,
                        color VARCHAR(7) DEFAULT '#007bff',
                        description VARCHAR(255),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                '''),
                ('testcase_label', '''
                    CREATE TABLE testcase_label (
                        id INTEGER PRIMARY KEY,
                        test_case_id INTEGER NOT NULL,
                        label_id INTEGER NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (test_case_id) REFERENCES test_case (id),
                        FOREIGN KEY (label_id) REFERENCES label (id)
                    )
                '''),
                ('test_execution_queue', '''
                    CREATE TABLE test_execution_queue (
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
            
            # Seed default data only if tables are empty
            seed_default_data_if_needed(cursor)
            
            # Commit all changes
            conn.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

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

if __name__ == '__main__':
    migrate_preserve_data() 