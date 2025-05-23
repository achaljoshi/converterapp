# Testing Guide

This document explains how to run and add tests for ConverterApp.

## Running Tests

1. **Activate your virtual environment:**
   ```sh
   source venv/bin/activate
   ```
2. **Run all tests:**
   ```sh
   pytest
   ```

## Adding New Tests
- Place unit and integration tests in the appropriate `tests/` directory or next to the code being tested.
- Use `pytest` for writing tests.
- Name test files as `test_*.py`.
- Write clear, focused test functions.

## Manual Testing
- Create/edit test cases with multiple workflows and sample files.
- Add/remove workflow rows dynamically.
- Upload files for each workflow.
- Ensure validation: at least one workflow, no duplicates.
- Check that files are saved in uploads/.

## Coverage
- Aim for high coverage on core logic, models, and views.
- Use `pytest --cov` to check coverage (if configured). 