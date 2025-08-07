from app import create_app, db
from app.models import TestFramework
import json

def seed_test_frameworks():
    app = create_app()
    with app.app_context():
        # Define common test frameworks
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
        
        for framework_data in frameworks:
            existing = TestFramework.query.filter_by(name=framework_data['name']).first()
            if not existing:
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
                print(f"Added framework: {framework_data['name']}")
            else:
                print(f"Framework already exists: {framework_data['name']}")
        
        db.session.commit()
        print("\nTest frameworks seeded successfully!")
        print(f"Total frameworks: {TestFramework.query.count()}")

if __name__ == '__main__':
    seed_test_frameworks() 