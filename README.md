# Test Accelerator

A comprehensive test case, workflow, and configuration management platform with analytics, scheduling, and universal permissions.

## Features
- Test case, workflow, converter config, file type, and configuration management
- **Test Cases can have multiple workflows, each with its own sample file upload**
- Dynamic UI: Add Workflow button, workflow dropdown, file upload per workflow, remove row
- Bulk execution, scheduling, and analytics dashboards
- Universal, fine-grained permission and role system
- User management (create, edit, deactivate, assign roles)
- Cloning for all major entities
- Audit logging for all actions
- Extensible, modular architecture
- **Git repository integration with framework-aware test discovery**
- **Test framework configuration and custom extraction rules**
- **Test case labeling and categorization**
- **Real-time test execution with detailed logging**
- **Configurable execution commands for all test frameworks**
- **Organized navigation with Payments and Test Management sections**

## Quickstart

1. **Clone the repo:**
   ```sh
   git clone <repo-url>
   cd converterapp
   ```
2. **Create and activate a virtual environment:**
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Set up the database:**
   ```sh
   flask db upgrade
   ```
5. **Run the app:**
   ```sh
   flask run
   ```

## Directory Structure

```
converterapp/
  app/           # Main Flask app (blueprints, models, templates)
  instance/      # Instance config
  migrations/    # Alembic migrations
  resources/     # Static resources
  scripts/       # Utility scripts
  venv/          # Virtual environment
  DESIGN.md      # Technical design
  WORKFLOW.md    # Business/technical workflows
  API_REFERENCE.md # API endpoints
  README.md      # This file
  requirements.txt
  run.py
  start_app.py   # Startup script with migrations
  STARTUP.md     # Detailed startup guide
```

## Documentation
- [DESIGN.md](DESIGN.md) — Technical architecture, ERD, DFD
- [WORKFLOW.md](WORKFLOW.md) — Business and technical workflows
- [API_REFERENCE.md](API_REFERENCE.md) — API endpoints
- [STARTUP.md](STARTUP.md) — Detailed startup and migration guide

---
For contributing, see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Requirements
- **Python 3.8+** (recommended: Python 3.10 or newer)
- Git

---

## Setup Instructions

### 1. Clone the Repository
```sh
git clone <your-repo-url>
cd converterapp
```

### 2. Create a Virtual Environment
**On Windows:**
```sh
python -m venv venv
venv\Scripts\activate
```
**On Linux/Mac:**
```sh
python3 -m venv venv
source venv/bin/activate
```

> **Note:**  
> The `venv/` folder (your virtual environment) is excluded from version control via `.gitignore`.  
> Each developer should create their own virtual environment locally after cloning the repository.

### 3. Install Dependencies
```sh
pip install -r requirements.txt
```

### 4. Configuration
- Default configuration values (such as `SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`, etc.) are set in `app/config/__init__.py` in the `DefaultConfig` class.
- You **do not need a `.env` file** for local development unless you want to override these defaults.
- To override any config (for production or secrets), set environment variables or create a `.env` file as needed:
  ```
  FLASK_APP=run.py
  FLASK_ENV=production
  SECRET_KEY=your-production-secret
  SQLALCHEMY_DATABASE_URI=sqlite:///instance/app.db
  ```
- **Important:**
  - On **Linux/Mac**, the default `sqlite:///instance/app.db` usually works if you run the app from the project root.
  - On **Windows**, you may need to use an absolute path, e.g.:
    ```
    SQLALCHEMY_DATABASE_URI=sqlite:///C:/Users/youruser/Projects/converterapp/instance/app.db
    ```
  - Make sure the `instance` directory exists in your project root and is writable.

### 5. Initialize the Database
```sh
flask db upgrade
```

### 6. Run the Application
**On Windows:**
```sh
set FLASK_APP=run.py
flask run
```
**On Linux/Mac:**
```sh
export FLASK_APP=run.py
flask run
```
Or, to run with the provided script (all OS):
```sh
python run.py
```

The app will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000) or the port specified in `run.py`.

---

## Data Storage Verification

### Overview
This application includes comprehensive data storage verification to ensure all pages and features properly store data in the database. The verification covers both original features and new Git integration features.

### Database Tables Verified

| **Table** | **Purpose** | **Status** |
|-----------|-------------|------------|
| `file_type` | File type definitions | ✅ Verified |
| `configuration` | Conversion configurations | ✅ Verified |
| `converter_config` | Source→target mappings | ✅ Verified |
| `workflow` | Workflow definitions with stages | ✅ Verified |
| `test_case` | Test case definitions | ✅ Verified |
| `test_run` | Test execution results | ✅ Verified |
| `git_repository` | Git repository configurations | ✅ Verified |
| `test_framework` | Framework patterns and settings | ✅ Verified |
| `label` | Test case labels | ✅ Verified |
| `testcase_label` | Label associations | ✅ Verified |
| `test_execution_queue` | Queued executions | ✅ Verified |
| `audit_log` | User action logs | ✅ Verified |
| `user` | User accounts | ✅ Verified |
| `role` | User roles | ✅ Verified |
| `permission` | System permissions | ✅ Verified |

### Features Verified

#### Original Features
- ✅ **File Types Management** - Create, store, and retrieve file types
- ✅ **Configuration Management** - Store conversion rules and schemas
- ✅ **Converter Configs** - Store source→target mappings with rules
- ✅ **Workflows** - Store workflow stages and converter associations
- ✅ **Test Cases** - Store test cases with workflow associations
- ✅ **Test Runs** - Store execution results, logs, and environments
- ✅ **Audit Logs** - Store user actions and changes

#### New Features
- ✅ **Git Repositories** - Store repo configs with framework associations
- ✅ **Test Frameworks** - Store framework patterns and settings
- ✅ **Labels** - Store labels and test case associations
- ✅ **Test Execution Queue** - Store queued test executions

### Verification Commands

#### 1. Check Current Database Data
```bash
# Check all data in the database
PYTHONPATH=/path/to/converterapp python scripts/check_data.py
```

#### 2. Run Comprehensive Data Storage Tests
```bash
# Run all data storage tests (creates test data)
python test_all_pages_data.py
```

#### 3. Verify Data Persistence After Migration
```bash
# Run migration (simulates server restart)
PYTHONPATH=/path/to/converterapp python scripts/startup_migrate.py

# Check data again to verify persistence
PYTHONPATH=/path/to/converterapp python scripts/check_data.py
```

### Expected Test Results

When running the comprehensive tests, you should see:

```
🧪 Running Comprehensive Data Storage Tests...
============================================================

🔍 Testing File Types...
📁 Testing File Types Data Storage...
  ✅ Created 3 file types
    - MT103: SWIFT MT103 message format
    - pacs008: ISO 20022 pacs008 format
    - pain001: ISO 20022 pain001 format
  ✅ PASSED

🔍 Testing Configurations...
⚙️ Testing Configuration Data Storage...
  ✅ Created 2 configurations
    - MT103 to XML: MT103
    - pacs008 to JSON: pacs008
  ✅ PASSED

[... additional tests ...]

============================================================
📊 TEST RESULTS SUMMARY
============================================================
File Types           ✅ PASSED
Configurations       ✅ PASSED
Converter Configs    ✅ PASSED
Workflows            ✅ PASSED
Test Cases           ✅ PASSED
Test Runs            ✅ PASSED
Git Repositories     ✅ PASSED
Labels               ✅ PASSED
Frameworks           ✅ PASSED
Audit Logs           ✅ PASSED

Overall: 10/10 tests passed
🎉 ALL TESTS PASSED! All page data is being stored correctly.
```

### Data Persistence Verification

After running migrations, verify that all data persists:

```bash
# Before migration
FileTypes: 3 records
Configurations: 2 records
ConverterConfigs: 2 records
Workflows: 2 records
TestCases: 2 records
TestFrameworks: 8 records
Labels: 8 records
Users: 1 records

# After migration (should be identical)
FileTypes: 3 records ✅
Configurations: 2 records ✅
ConverterConfigs: 2 records ✅
Workflows: 2 records ✅
TestCases: 2 records ✅
TestFrameworks: 8 records ✅
Labels: 8 records ✅
Users: 1 records ✅
```

### Troubleshooting Data Storage Issues

#### If Tests Fail
1. **Check Database Connection**: Ensure the database file exists and is writable
2. **Verify Models**: Check that all models are properly imported and defined
3. **Check Migrations**: Run `python scripts/startup_migrate.py` to ensure schema is up to date
4. **Review Error Messages**: Look for specific error details in test output

#### If Data is Lost After Restart
1. **Use Safe Migration**: Always use `scripts/startup_migrate.py` instead of `scripts/fix_database_schema.py`
2. **Check Migration Script**: Ensure the migration script preserves existing data
3. **Verify Database File**: Check that the database file path is correct and accessible

#### Common Issues
- **Port Already in Use**: Use `flask run --port=5001` or kill existing processes
- **Permission Errors**: Ensure database file and directories are writable
- **Import Errors**: Verify `PYTHONPATH` is set correctly

### Migration Best Practices

#### Safe Migration (Recommended)
```bash
# Always use this for safe migrations that preserve data
PYTHONPATH=/path/to/converterapp python scripts/startup_migrate.py
```

#### Database Recreation (Use with Caution)
```bash
# Only use this if you want to start fresh (WILL DELETE ALL DATA)
PYTHONPATH=/path/to/converterapp python scripts/fix_database_schema.py
```

#### Startup Script (Recommended for Production)
```bash
# Use the startup script which handles migrations automatically
python start_app.py
```

### Continuous Integration

For CI/CD pipelines, include these verification steps:

```yaml
# Example CI step
- name: Verify Data Storage
  run: |
    python test_all_pages_data.py
    PYTHONPATH=${{ github.workspace }} python scripts/startup_migrate.py
    PYTHONPATH=${{ github.workspace }} python scripts/check_data.py
```

---

## Configurable Test Execution Commands

The platform supports **fully configurable test execution commands** for all test frameworks. Instead of hardcoded CLI commands, you can now customize how tests are executed through the Test Framework configuration screen.

### How It Works

1. **Framework Configuration**: Each test framework has configurable execution commands stored as JSON
2. **Template Variables**: Commands use template variables that are substituted at runtime
3. **Flexible Parameters**: Timeout, success codes, and working directory are all configurable
4. **Real-time Execution**: Tests are executed using the configured commands with full logging

### Configuration Format

Execution commands are configured as JSON with the following structure:

```json
{
  "command_template": "command {file_path} --name \"{test_name}\"",
  "working_dir": "{repo_path}",
  "timeout": 300,
  "success_codes": [0]
}
```

### Template Variables

The following variables are available for command templates:

- `{file_path}` - Path to the test file relative to repository root
- `{test_name}` - Name of the test case
- `{repo_path}` - Local path of the Git repository
- `{test_function}` - Test function name (for pytest-style frameworks)
- `{class_name}` - Test class name (for Java/TestNG frameworks)
- `{method_name}` - Test method name (for Java/TestNG frameworks)

### Framework Examples

#### Cucumber (Java)
```json
{
  "command_template": "cucumber {file_path} --name \"{test_name}\" --format json --out -",
  "working_dir": "{repo_path}",
  "timeout": 300,
  "success_codes": [0]
}
```

#### Pytest (Python)
```json
{
  "command_template": "pytest {file_path}::{test_function} -v --json-report --json-report-file=-",
  "working_dir": "{repo_path}",
  "timeout": 300,
  "success_codes": [0]
}
```

#### Playwright (JavaScript)
```json
{
  "command_template": "npx playwright test {file_path} --grep \"{test_name}\" --reporter=json",
  "working_dir": "{repo_path}",
  "timeout": 300,
  "success_codes": [0]
}
```

#### Selenium/TestNG (Java)
```json
{
  "command_template": "mvn test -Dtest={class_name}#{method_name} -Dtestng.output.format=json",
  "working_dir": "{repo_path}",
  "timeout": 300,
  "success_codes": [0]
}
```

#### Jest (JavaScript)
```json
{
  "command_template": "npx jest {file_path} --testNamePattern \"{test_name}\" --json --outputFile=-",
  "working_dir": "{repo_path}",
  "timeout": 300,
  "success_codes": [0]
}
```

#### Cypress (JavaScript)
```json
{
  "command_template": "npx cypress run --spec {file_path} --reporter json --reporter-options output=-",
  "working_dir": "{repo_path}",
  "timeout": 300,
  "success_codes": [0]
}
```

#### NUnit (.NET)
```json
{
  "command_template": "dotnet test {file_path} --filter TestName=\"{test_name}\" --logger json",
  "working_dir": "{repo_path}",
  "timeout": 300,
  "success_codes": [0]
}
```

#### Robot Framework (Python)
```json
{
  "command_template": "robot --test \"{test_name}\" --output - --report - --log - {file_path}",
  "working_dir": "{repo_path}",
  "timeout": 300,
  "success_codes": [0]
}
```

### Customization Benefits

#### ✅ **Framework Flexibility**
- Support any test framework with custom commands
- Add new frameworks without code changes
- Modify existing framework commands through UI

#### ✅ **Environment Adaptation**
- Different commands for different environments
- Custom timeout values per framework
- Configurable success/failure codes

#### ✅ **Tool Integration**
- Integrate with custom test runners
- Support for different output formats
- Custom working directory configurations

#### ✅ **Maintenance**
- Update commands without redeployment
- Version control for command configurations
- Easy troubleshooting and debugging

### Configuration Steps

1. **Access Framework Configuration**: Go to Test Management → Test Frameworks
2. **Edit Framework**: Click "Edit" on any framework
3. **Configure Execution Commands**: Update the "Execution Commands (JSON)" field
4. **Save Changes**: Click "Save" to update the framework
5. **Test Execution**: Execute tests to verify the new commands work

### Advanced Configuration

#### Custom Success Codes
Some tools may return different exit codes for success:
```json
{
  "success_codes": [0, 1, 2]  // Accept multiple exit codes as success
}
```

#### Environment-Specific Commands
Use different commands for different environments:
```json
{
  "command_template": "npm run test:{environment} {file_path}",
  "working_dir": "{repo_path}",
  "timeout": 600,  // Longer timeout for integration tests
  "success_codes": [0]
}
```

#### Custom Output Formats
Configure different output formats for better integration:
```json
{
  "command_template": "pytest {file_path} --junitxml=test-results.xml --json-report",
  "working_dir": "{repo_path}",
  "timeout": 300,
  "success_codes": [0]
}
```

---

## Notes
- The SQLite database file is created in the `instance/` directory by default.
- To create an admin user, register via the UI and manually update the user role in the database if needed.
- For production, set `FLASK_ENV=production` and use a production-ready WSGI server (e.g., Gunicorn or uWSGI).
- All configuration and extension initialization is handled in `app/__init__.py`.
- **Workflow Audit Log:** All workflow changes are tracked in the database and viewable from the UI.
- **Template Viewing:** TXT and XML templates are viewable as plain text from the File Types page.
- Uploaded files are saved in the `uploads/` directory (auto-created if missing)
- **Data Persistence:** All data is preserved between server restarts using safe migration scripts.

---

## Troubleshooting
- If you get migration errors, try deleting the `instance/app.db` file and re-running `flask db upgrade` (this will delete all data).
- Ensure you have Python 3.8+ installed.
- If you see issues with dropdowns or UI, ensure you have an internet connection for Bootstrap CDN.
- If you get `ModuleNotFoundError` for any dependency, ensure you are in the virtual environment and have run `pip install -r requirements.txt`.
- If you change requirements, re-run `pip install -r requirements.txt`.
- **For data storage issues**, run the verification tests using the commands above.
- **For port conflicts**, use `flask run --port=5001` or check for existing processes.

---

## License
MIT License 