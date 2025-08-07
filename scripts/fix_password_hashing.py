from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

def fix_password_hashing():
    app = create_app()
    with app.app_context():
        # Get all users
        users = User.query.all()
        
        print(f"Found {len(users)} users in the database")
        
        # Update each user's password to use the compatible hashing method
        for user in users:
            print(f"Updating password for user: {user.username}")
            
            # For admin user, set the known password
            if user.username == 'admin':
                user.password = generate_password_hash('admin123', method='pbkdf2:sha256')
                print(f"  - Set admin password to 'admin123'")
            else:
                # For other users, we need to set a temporary password
                # You can change this to a known password or ask the user to reset it
                temp_password = 'temp123'  # Change this as needed
                user.password = generate_password_hash(temp_password, method='pbkdf2:sha256')
                print(f"  - Set temporary password '{temp_password}' for {user.username}")
                print(f"    (User should change this password after login)")
        
        # Commit the changes
        db.session.commit()
        print("\nPassword hashing fix completed!")
        print("All users now use pbkdf2:sha256 hashing method.")
        print("\nLogin credentials:")
        print("- admin/admin123")
        print("- Other users: username/temp123 (change after login)")

if __name__ == '__main__':
    fix_password_hashing() 