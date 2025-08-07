from app import create_app, db
from app.models import GitRepository, Label, TestCaseLabel, TestExecutionQueue
from sqlalchemy import text

def create_git_integration_tables():
    app = create_app()
    with app.app_context():
        # Create new tables
        db.create_all()
        
        # Add default labels
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
            existing = Label.query.filter_by(name=label_data['name']).first()
            if not existing:
                label = Label(**label_data)
                db.session.add(label)
        
        db.session.commit()
        print("Git integration tables created successfully!")
        print("Default labels added:")
        for label_data in default_labels:
            print(f"  - {label_data['name']} ({label_data['color']})")

if __name__ == '__main__':
    create_git_integration_tables() 