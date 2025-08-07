# 🚀 Converter App Startup Guide

## Quick Start

### Option 1: Use the Startup Script (Recommended)
```bash
# Make sure you're in the project directory
cd /Users/storezadeveloper/Projects/converterapp

# Activate virtual environment
source venv/bin/activate

# Run the startup script
python start_app.py
```

### Option 2: Manual Start
```bash
# Make sure you're in the project directory
cd /Users/storezadeveloper/Projects/converterapp

# Activate virtual environment
source venv/bin/activate

# Run migrations (preserves existing data)
PYTHONPATH=/Users/storezadeveloper/Projects/converterapp python scripts/startup_migrate.py

# Start Flask app
flask run --port=5001
```

## 🔑 Login Credentials
- **Username:** `admin`
- **Password:** `admin123`

## 📱 Access the App
- **URL:** http://127.0.0.1:5001
- **Dashboard:** http://127.0.0.1:5001/dashboard

## 💾 Data Persistence

### ✅ What's Preserved
- All your existing data (file types, configurations, workflows, etc.)
- User accounts and permissions
- Test cases and test runs
- Git repositories and frameworks

### 🔄 Migration Process
The startup script automatically:
1. Checks if database exists
2. Adds missing columns to existing tables
3. Creates new tables if needed
4. Seeds default data only if tables are empty
5. **NEVER drops or recreates existing data**

### 📊 Database Location
- **File:** `instance/app.db`
- **Backup:** `instance/app.db.backup` (created automatically)

## 🛠️ Troubleshooting

### If you get "bad interpreter" error:
```bash
# Remove old virtual environment
rm -rf venv

# Create new virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### If you get permission errors:
```bash
# Make startup script executable
chmod +x start_app.py
```

### If you need to check database data:
```bash
PYTHONPATH=/Users/storezadeveloper/Projects/converterapp python scripts/check_data.py
```

## 📋 Available Features

### Original Features (All Working)
- ✅ **Payments Section:**
  - File Types Management
  - Configuration Management  
  - Test Workflow Management
  - Manual Execution (Converter Testing)
  - Data Generator
- ✅ Audit Logs

### New Features (All Working)
- ✅ **Test Management Section:**
  - Test Cases
  - Git Repository Management
  - Test Framework Configuration
  - Test Case Labels
- ✅ Framework-Aware Test Discovery
- ✅ Test Execution Queue

## 🔧 Development

### Adding New Features
1. Update models in `app/models.py`
2. Run `python scripts/startup_migrate.py` to add new fields/tables
3. Your existing data will be preserved!

### Database Schema Changes
- Use `scripts/startup_migrate.py` for safe migrations
- **NEVER use `scripts/fix_database_schema.py`** (it recreates the database)

## 📞 Support
If you encounter any issues:
1. Check the logs in the terminal
2. Verify your virtual environment is activated
3. Ensure you're in the correct directory
4. Try running the startup migration manually

---

**🎉 Your data is now safe and will persist between server restarts!** 