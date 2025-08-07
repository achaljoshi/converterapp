#!/usr/bin/env python3
"""
Script to update test frameworks with configurable extraction settings
"""

import os
import sys
import json

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app import create_app, db
from app.models import TestFramework

def update_framework_settings():
    """Update test frameworks with configurable extraction settings"""
    
    app = create_app()
    with app.app_context():
        
        # Framework configurations with configurable settings
        framework_configs = {
            'Pytest': {
                'test_name_patterns': [
                    r'def\s+(test_\w+)',
                    r'class\s+Test\w+:\s*\n(?:[^\n]*\n)*?\s*def\s+(test_\w+)'
                ],
                'settings': {
                    'extraction_method': 'pattern_based',
                    'remove_prefixes': ['test_'],
                    'allowed_chars': r'\w\s-',
                    'min_length': 2
                }
            },
            
            'Selenium TestNG': {
                'test_name_patterns': [
                    r'@Test\s*\n\s*public\s+void\s+(test\w+)'
                ],
                'settings': {
                    'extraction_method': 'pattern_based',
                    'remove_prefixes': ['test'],
                    'allowed_chars': r'\w\s-',
                    'min_length': 2
                }
            },
            
            'Playwright': {
                'test_name_patterns': [
                    r'test\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
                    r'it\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
                ],
                'settings': {
                    'extraction_method': 'pattern_based',
                    'remove_prefixes': [],
                    'allowed_chars': r'\w\s-',
                    'min_length': 2
                }
            },
            
            'Cucumber': {
                'test_name_patterns': [
                    r'Scenario:\s*(.+?)(?:\s*$|\s*\n)',
                    r'Scenario Outline:\s*(.+?)(?:\s*$|\s*\n)'
                ],
                'settings': {
                    'extraction_method': 'cucumber',
                    'scenario_pattern': r'Scenario:\s*(.+?)(?:\s*$|\s*\n)',
                    'scenario_outline_pattern': r'Scenario Outline:\s*(.+?)(?:\s*$|\s*\n)'
                }
            },
            
            'Jest': {
                'test_name_patterns': [
                    r'test\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
                    r'it\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
                ],
                'settings': {
                    'extraction_method': 'pattern_based',
                    'remove_prefixes': [],
                    'allowed_chars': r'\w\s-',
                    'min_length': 2
                }
            },
            
            'Cypress': {
                'test_name_patterns': [
                    r'it\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
                ],
                'settings': {
                    'extraction_method': 'pattern_based',
                    'remove_prefixes': [],
                    'allowed_chars': r'\w\s-',
                    'min_length': 2
                }
            },
            
            'NUnit': {
                'test_name_patterns': [
                    r'\[Test\]\s*\n\s*public\s+void\s+(Test\w+)',
                    r'\[TestMethod\]\s*\n\s*public\s+void\s+(Test\w+)'
                ],
                'settings': {
                    'extraction_method': 'pattern_based',
                    'remove_prefixes': ['Test'],
                    'allowed_chars': r'\w\s-',
                    'min_length': 2
                }
            },
            
            'Robot Framework': {
                'test_name_patterns': [
                    r'^[A-Za-z][A-Za-z0-9\s]*$'
                ],
                'settings': {
                    'extraction_method': 'robot_framework',
                    'test_cases_section_pattern': r'\*\*\*\s*Test Cases\s*\*\*\*',
                    'next_section_pattern': r'\*\*\*\s*(?:Keywords|Settings|Variables|Documentation)\s*\*\*\*',
                    'test_case_name_pattern': r'^[A-Za-z][A-Za-z0-9\s]*$',
                    'exclude_keywords': ['open browser', 'input text', 'click button', 'input password', 'page should contain', 'library'],
                    'max_words': 4
                }
            }
        }
        
        # Update each framework
        for framework_name, config in framework_configs.items():
            framework = TestFramework.query.filter_by(name=framework_name).first()
            if framework:
                print(f"Updating {framework_name}...")
                
                # Update test_name_patterns
                framework.test_name_patterns = json.dumps(config['test_name_patterns'])
                
                # Update settings
                framework.settings = json.dumps(config['settings'])
                
                print(f"  - Test name patterns: {len(config['test_name_patterns'])} patterns")
                print(f"  - Extraction method: {config['settings']['extraction_method']}")
                
            else:
                print(f"Framework '{framework_name}' not found in database")
        
        # Commit changes
        db.session.commit()
        print("\n✅ All frameworks updated successfully!")
        
        # Display updated frameworks
        print("\nUpdated Framework Configurations:")
        print("=" * 50)
        
        frameworks = TestFramework.query.all()
        for framework in frameworks:
            print(f"\n{framework.name}:")
            print(f"  Language: {framework.language}")
            print(f"  File Extensions: {framework.file_extensions}")
            print(f"  Test Patterns: {framework.test_patterns}")
            print(f"  Test Name Patterns: {framework.test_name_patterns}")
            print(f"  Settings: {framework.settings}")

if __name__ == "__main__":
    update_framework_settings() 