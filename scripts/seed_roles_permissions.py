from app import create_app, db
from app.models import Role, Permission, User
from werkzeug.security import generate_password_hash

def seed():
    app = create_app()
    with app.app_context():
        db.create_all()
        # Define permissions
        permissions = [
            'dashboard_view',
            'testcase_create', 'testcase_edit', 'testcase_delete', 'testcase_execute',
            'testrun_view', 'testrun_export',
            'auditlog_view',
            'filetype_manage',
            'workflow_manage',
            'config_manage',
        ]
        perm_objs = {}
        for perm in permissions:
            p = Permission.query.filter_by(name=perm).first()
            if not p:
                p = Permission(name=perm, description=perm.replace('_', ' ').capitalize())
                db.session.add(p)
            perm_objs[perm] = p
        db.session.commit()
        # Define roles and their permissions
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
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name, description=role_name.capitalize())
                db.session.add(role)
            role.permissions = [perm_objs[p] for p in perms]
        db.session.commit()
        # Create an admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin:
            admin = User(username='admin', password=generate_password_hash('admin123'), role=admin_role)
            db.session.add(admin)
        db.session.commit()
        print('Seeded roles, permissions, and admin user (admin/admin123)')

if __name__ == '__main__':
    seed() 