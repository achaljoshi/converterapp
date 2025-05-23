# Contributing to ConverterApp

Thank you for your interest in contributing! Please follow these guidelines to help us maintain a high-quality project.

## How to Contribute
- Fork the repository and create your branch from `main`.
- Open a pull request (PR) with a clear description of your changes.
- Reference any related issues in your PR.
- For bug reports or feature requests, open an issue first.

## Code Style
- Follow PEP8 for Python code.
- Use descriptive commit messages.
- Keep functions and classes small and focused.

## Running Tests
- Activate your virtual environment:
  ```sh
  source venv/bin/activate
  ```
- Run tests (if available):
  ```sh
  pytest
  ```
- For manual testing, see WORKFLOW.md for checklists.

## Adding a New Entity or Feature
- Add a new model or field as needed.
- Update backend validation and dynamic form logic if adding fields to TestCase or workflows.
- For file fields, ensure uploads directory is handled.
- Create a migration:
  ```sh
  flask db migrate -m "Add <entity>"
  flask db upgrade
  ```
- Add forms, views, and templates as needed.
- Add permissions and update the role management UI.
- Update documentation (DESIGN.md, WORKFLOW.md, API_REFERENCE.md).

## Questions?
Open an issue or contact a maintainer. 