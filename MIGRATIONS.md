# Database Migrations Guide

This guide explains how to manage database migrations using Flask-Migrate (Alembic).

## Running Migrations

1. **Upgrade the database to the latest migration:**
   ```sh
   flask db upgrade
   ```

2. **Downgrade the database (if needed):**
   ```sh
   flask db downgrade
   ```

## Creating a New Migration

1. **Make your model changes in the codebase.**
2. **Generate a migration script:**
   ```sh
   flask db migrate -m "Describe your change"
   ```
3. **Apply the migration:**
   ```sh
   flask db upgrade
   ```

## Troubleshooting
- If you get errors, check for missing or duplicate migration files in `migrations/versions/`.
- For more info, see the Flask-Migrate and Alembic documentation.

## Notes
- The migration for TestCase <-> Workflow many-to-many adds the testcase_workflow table.
- Uploaded files are saved in uploads/, which is auto-created if missing. 