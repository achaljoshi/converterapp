from app import create_app, db
from app.models import TestCase, TestRun, GitRepository, TestFramework, Label, TestCaseLabel, TestExecutionQueue
from sqlalchemy import text
import sqlite3
import os

def fix_database_schema():
    app = create_app()
    with app.app_context():
        # Get the database file path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Create a backup
        backup_path = db_path + '.backup'
        if os.path.exists(db_path):
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"Database backed up to: {backup_path}")
        
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        
        print("Database schema updated successfully!")
        
        # Re-seed the data
        seed_default_data()
        
        print("Default data re-seeded!")

def seed_default_data():
    """Re-seed default data after schema update"""
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
    
    # Create default labels
    default_labels = [
        {'name': 'Smoke', 'color': '#28a745', 'description': 'Smoke tests'},
        {'name': 'Regression', 'color': '#dc3545', 'description': 'Regression tests'},
        {'name': 'UI', 'color': '#007bff', 'description': 'UI tests'},
        {'name': 'API', 'color': '#6f42c1', 'description': 'API tests'},
        {'name': 'Critical', 'color': '#fd7e14', 'description': 'Critical path tests'},
        {'name': 'Performance', 'color': '#e83e8c', 'description': 'Performance tests'},
        {'name': 'Security', 'color': '#6c757d', 'description': 'Security tests'},
        {'name': 'Integration', 'color': '#20c997', 'description': 'Integration tests'}
    ]
    
    for label_data in default_labels:
        label = Label(**label_data)
        db.session.add(label)
    
    # Create test frameworks
    frameworks = [
        {
            'name': 'Pytest',
            'description': 'Python testing framework',
            'language': 'Python',
            'file_extensions': ['.py'],
            'test_patterns': ['def test_', '@pytest.mark', 'class Test'],
            'test_name_patterns': [
                'def (test_\\w+)',
                'class (Test\\w+)',
                '@pytest\\.mark\\.(\\w+)'
            ],
            'settings': {
                'conftest_support': True,
                'fixture_support': True
            }
        },
        {
            'name': 'Selenium TestNG',
            'description': 'Java testing framework with TestNG',
            'language': 'Java',
            'file_extensions': ['.java'],
            'test_patterns': ['@Test', 'public void test', 'class Test'],
            'test_name_patterns': [
                '@Test\\s+public\\s+void\\s+(\\w+)',
                'public\\s+void\\s+(test\\w+)',
                'class (Test\\w+)'
            ],
            'settings': {
                'annotation_support': True,
                'parallel_execution': True
            }
        },
        {
            'name': 'Playwright',
            'description': 'Microsoft Playwright testing framework',
            'language': 'JavaScript',
            'file_extensions': ['.js', '.ts'],
            'test_patterns': ['test(', 'describe(', 'it('],
            'test_name_patterns': [
                'test\\(\\s*[\'\"]([^\'\"]+)[\'\"]',
                'it\\(\\s*[\'\"]([^\'\"]+)[\'\"]',
                'describe\\(\\s*[\'\"]([^\'\"]+)[\'\"]'
            ],
            'settings': {
                'browser_support': ['chromium', 'firefox', 'webkit'],
                'async_support': True
            }
        },
        {
            'name': 'Cucumber',
            'description': 'BDD testing framework',
            'language': 'Ruby',
            'file_extensions': ['.feature', '.rb'],
            'test_patterns': ['Scenario:', 'Feature:', 'Given ', 'When ', 'Then '],
            'test_name_patterns': [
                'Scenario:\\s*(\\w+)',
                'Feature:\\s*(\\w+)',
                'def (\\w+)'
            ],
            'settings': {
                'gherkin_support': True,
                'step_definitions': True
            }
        },
        {
            'name': 'Jest',
            'description': 'JavaScript testing framework',
            'language': 'JavaScript',
            'file_extensions': ['.js', '.ts', '.jsx', '.tsx'],
            'test_patterns': ['test(', 'describe(', 'it('],
            'test_name_patterns': [
                'test\\(\\s*[\'\"]([^\'\"]+)[\'\"]',
                'it\\(\\s*[\'\"]([^\'\"]+)[\'\"]',
                'describe\\(\\s*[\'\"]([^\'\"]+)[\'\"]'
            ],
            'settings': {
                'mock_support': True,
                'coverage_support': True
            }
        },
        {
            'name': 'Cypress',
            'description': 'End-to-end testing framework',
            'language': 'JavaScript',
            'file_extensions': ['.js', '.ts'],
            'test_patterns': ['describe(', 'it(', 'cy.'],
            'test_name_patterns': [
                'describe\\(\\s*[\'\"]([^\'\"]+)[\'\"]',
                'it\\(\\s*[\'\"]([^\'\"]+)[\'\"]'
            ],
            'settings': {
                'browser_automation': True,
                'real_time_reload': True
            }
        },
        {
            'name': 'NUnit',
            'description': '.NET testing framework',
            'language': 'C#',
            'file_extensions': ['.cs'],
            'test_patterns': ['[Test]', '[TestMethod]', 'public void Test'],
            'test_name_patterns': [
                '\\[Test\\]\\s*public\\s+void\\s+(\\w+)',
                '\\[TestMethod\\]\\s*public\\s+void\\s+(\\w+)',
                'public\\s+void\\s+(Test\\w+)'
            ],
            'settings': {
                'attribute_support': True,
                'parallel_execution': True
            }
        },
        {
            'name': 'Robot Framework',
            'description': 'Python-based automation framework',
            'language': 'Python',
            'file_extensions': ['.robot'],
            'test_patterns': ['*** Test Cases ***', '*** Keywords ***'],
            'test_name_patterns': [
                '([A-Za-z0-9_]+)\\s*\\[Documentation\\]',
                '([A-Za-z0-9_]+)\\s*\\[Tags\\]'
            ],
            'settings': {
                'keyword_driven': True,
                'data_driven': True
            }
        }
    ]
    
    import json
    for framework_data in frameworks:
        framework = TestFramework(
            name=framework_data['name'],
            description=framework_data['description'],
            language=framework_data['language'],
            file_extensions=json.dumps(framework_data['file_extensions']),
            test_patterns=json.dumps(framework_data['test_patterns']),
            test_name_patterns=json.dumps(framework_data['test_name_patterns']),
            settings=json.dumps(framework_data['settings']),
            is_active=True
        )
        db.session.add(framework)
    
    db.session.commit()
    print("Database schema and data updated successfully!")

if __name__ == '__main__':
    fix_database_schema() 