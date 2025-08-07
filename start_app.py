#!/usr/bin/env python3
"""
Startup script for the converter app
Runs migrations and starts the Flask application
"""

import os
import sys
import subprocess

def main():
    print("🚀 Starting Converter App...")
    
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    # Set environment variable for Python path
    os.environ['PYTHONPATH'] = project_root
    
    try:
        # Run startup migration
        print("📊 Running database migrations...")
        result = subprocess.run([
            sys.executable, 'scripts/startup_migrate.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migrations completed successfully!")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ Migration failed:")
            print(result.stderr)
            return 1
        
        # Start Flask app
        print("🌐 Starting Flask application...")
        print("📱 Access the app at: http://127.0.0.1:8080")
        print("🔑 Login with: admin / admin123")
        print("⏹️  Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Start Flask with proper environment
        subprocess.run([
            sys.executable, '-m', 'flask', 'run', '--port=8080'
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main()) 