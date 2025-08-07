# 🪟 Windows Setup Guide for Test Accelerator

## Quick Start for Windows

### 1. Clone the Repository
```cmd
git clone <your-repo-url>
cd converterapp
```

### 2. Create Virtual Environment
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```cmd
pip install -r requirements.txt
```

> **⚠️ Important:** If you encounter an error about `email_validator`, make sure you have the latest version of `requirements.txt` which includes this dependency.

### 4. Database Configuration
The application now uses cross-platform database paths that work on Windows. The database will be created at:
```
converterapp\instance\app.db
```

### 5. Initialize Database
```cmd
flask db upgrade
```

### 6. Run the Application
```cmd
set FLASK_APP=run.py
flask run
```

Or use the provided script:
```cmd
python run.py
```

## 🔧 Windows-Specific Configuration

### Database Path
The application automatically detects the correct path for your Windows machine:

## 🚨 Troubleshooting

### Common Windows Issues

#### 1. Email Validator Error
**Error:** `Exception: Install 'email_validator' for email validation support.`

**Solution:**
```cmd
pip install email_validator==2.1.0
```

#### 2. JSON Schema Error
**Error:** `ModuleNotFoundError: No module named 'jsonschema'`

**Solution:**
```cmd
pip install jsonschema==4.21.1
```

#### 3. General Missing Dependencies
**Solution:** Update your requirements.txt and reinstall:
```cmd
pip install -r requirements.txt
```

#### 4. Database Path Issues
**Error:** `sqlite3.OperationalError: unable to open database file`

**Solution:**
- Make sure the `instance` folder exists in your project root
- Ensure you have write permissions to the project directory
- Try running as administrator if needed

#### 5. Virtual Environment Issues
**Error:** `'venv' is not recognized as an internal or external command`

**Solution:**
```cmd
python -m venv venv
venv\Scripts\activate
```
- **Database Location:** `converterapp\instance\app.db`
- **Backup Location:** `converterapp\instance\app.db.backup`

### Environment Variables (Optional)
If you need to override the default configuration, create a `.env` file in the project root:
```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
# Database path (optional - uses relative path by default)
SQLALCHEMY_DATABASE_URI=sqlite:///C:\Users\YourUsername\Projects\converterapp\instance\app.db
```

### Windows Path Examples
If you need to specify an absolute path manually:
```env
# For user in C:\Users\JohnDoe\Projects\converterapp
SQLALCHEMY_DATABASE_URI=sqlite:///C:\Users\JohnDoe\Projects\converterapp\instance\app.db

# For user in D:\Development\converterapp
SQLALCHEMY_DATABASE_URI=sqlite:///D:\Development\converterapp\instance\app.db
```

## 🚀 Startup Script for Windows

### Option 1: Use the Startup Script
```cmd
python start_app.py
```

### Option 2: Manual Startup
```cmd
# Activate virtual environment
venv\Scripts\activate

# Run migrations
python scripts\startup_migrate.py

# Start Flask app
flask run --port=8080
```

## 🔑 Login Credentials
- **Username:** `admin`
- **Password:** `admin123`

## 📱 Access the App
- **URL:** http://127.0.0.1:8080
- **Dashboard:** http://127.0.0.1:8080/dashboard

## 🛠️ Troubleshooting

### If you get "bad interpreter" error:
```cmd
# Remove old virtual environment
rmdir /s venv

# Create new virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### If you get permission errors:
```cmd
# Run Command Prompt as Administrator
# Then run your commands
```

### If database path issues occur:
```cmd
# Check if instance directory exists
dir instance

# Create instance directory if it doesn't exist
mkdir instance

# Run database initialization
flask db upgrade
```

### If you need to check database data:
```cmd
python scripts\check_data.py
```

## 📁 Directory Structure on Windows
```
converterapp\
├── app\                    # Main Flask app
├── instance\              # Instance config (database here)
│   └── app.db            # SQLite database file
├── migrations\            # Alembic migrations
├── resources\             # Static resources
├── scripts\              # Utility scripts
├── venv\                 # Virtual environment
├── .gitignore           # Git ignore file
├── requirements.txt     # Python dependencies
├── run.py              # Flask run script
├── start_app.py        # Startup script
└── README.md           # Main documentation
```

## 🔄 Migration Notes
- The application preserves all existing data during migrations
- Database backups are automatically created
- New tables and columns are added without dropping existing data

## 📊 Database Verification
To verify your database is working correctly:
```cmd
python scripts\check_data.py
```

This will show you all the data in your database tables.

---

## 🎯 Key Differences from macOS/Linux

1. **Virtual Environment Activation:**
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

2. **Path Separators:**
   - Windows: `\` (backslash)
   - macOS/Linux: `/` (forward slash)

3. **Environment Variables:**
   - Windows: `set VARIABLE=value`
   - macOS/Linux: `export VARIABLE=value`

4. **Command Line:**
   - Windows: `cmd` or PowerShell
   - macOS/Linux: Terminal

The application now handles all these differences automatically! 