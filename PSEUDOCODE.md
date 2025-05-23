# ConverterApp Pseudocode Reference

This file provides high-level pseudocode for each major screen and route in the app, to help developers quickly understand the flow and logic.

---

## Test Case List Screen

- **Route:** `/testcases` [GET]
- **Permission:** `testcase_view`
- **Logic:**
    - Query all test cases, join workflows and test runs
    - Render table:
        - Name (link to detail)
        - Workflows (list, with sample file icon if present)
        - Last Run, Last Status
        - Actions: Edit, Delete, Run, Clone
    - Bulk actions: Execute selected

---

## Test Case Form Screen (Create/Edit)

- **Route:** `/testcases/new` [GET, POST], `/testcases/<id>/edit` [GET, POST]
- **Permission:** `testcase_create` / `testcase_edit`
- **UI:**
    - Name (text)
    - [Dynamic Workflow+File rows]:
        - Add Workflow button
        - For each row: Workflow dropdown (exclude already selected), File input, Remove button
    - Description (text)
    - Schedule (dropdown)
    - Submit, Cancel
- **Logic:**
    - On Add Workflow: Add new row (dropdown + file input)
    - On Remove: Remove row
    - On Submit:
        - Validate: at least one workflow, no duplicates
        - Save TestCase
        - For each workflow row: save association, save file to uploads/
        - Redirect to list

---

## Test Case Detail Screen

- **Route:** `/testcases/<id>` [GET]
- **Permission:** `testcase_view`
- **Logic:**
    - Query test case, workflows, test runs
    - Render:
        - Name, Description
        - Workflows (list, with download link for sample file if present)
        - Actions: Edit, Clone, Back
        - Test Run History (table)

---

## Workflow List Screen

- **Route:** `/workflows` [GET]
- **Permission:** `workflow_view`
- **Logic:**
    - Query all workflows
    - Render table: Name, Stages, Actions (Edit, Delete, Clone)

---

## Workflow Form Screen (Create/Edit)

- **Route:** `/workflows/new` [GET, POST], `/workflows/<id>/edit` [GET, POST]
- **Permission:** `workflow_create` / `workflow_edit`
- **UI:**
    - Name (text)
    - Stages (ordered list of converter configs)
    - Submit, Cancel
- **Logic:**
    - On Submit: Validate, save workflow, redirect

---

## User List Screen

- **Route:** `/auth/users` [GET]
- **Permission:** `user_manage`
- **Logic:**
    - Query all users
    - Render table: Username, Email, Role, Actions (Edit, Deactivate)

---

## User Form Screen (Create/Edit)

- **Route:** `/auth/user/new` [GET, POST], `/auth/user/<id>/edit` [GET, POST]
- **Permission:** `user_manage`
- **UI:**
    - Username, Email, Password, Role (dropdown)
    - Submit, Cancel
- **Logic:**
    - On Submit: Validate, save user, redirect

---

## Role/Permission Management

- **Route:** `/roles`, `/roles/<id>/permissions` [GET, POST]
- **Permission:** `role_manage`
- **Logic:**
    - List roles, assign permissions to roles
    - UI: Role list, permission checkboxes, save

---

## Audit Log Screen

- **Route:** `/testcases/auditlog`, `/auditlog` [GET]
- **Permission:** `auditlog_view`
- **Logic:**
    - Query audit logs (filterable)
    - Render table: User, Action, Timestamp, Details

---

## Dashboard Screen

- **Route:** `/dashboard` [GET]
- **Permission:** `dashboard_view`
- **Logic:**
    - Show KPIs, charts, recent activity
    - Links to major sections

---

## Test Execution Report Screen

- **Route:** `/testruns` [GET], `/testruns/<id>` [GET]
- **Permission:** `testrun_view`
- **Logic:**
    - Query test runs (optionally filter by status, date, test case)
    - Render table: Status, Executed At, Duration, Output, Details (link)
    - On Details: Show run output, status, timestamps, link to test case and workflow
    - Export: Option to export filtered runs as CSV

---

## Execution Configurator Screen

- **Route:** `/configurations` [GET], `/configuration/new` [GET, POST], `/configuration/<id>/edit` [GET, POST]
- **Permission:** `config_manage`
- **UI:**
    - Name, Description
    - File Type (dropdown)
    - Rules (JSON/text)
    - Schema (JSON/text)
    - Submit, Cancel
- **Logic:**
    - On Submit: Validate, save configuration, redirect
    - List: Show all configurations, filter/search, actions (Edit, Delete, Clone)

---

## Workflow Page (Detail)

- **Route:** `/workflow/<id>` [GET]
- **Permission:** `workflow_view`
- **Logic:**
    - Query workflow, stages (converter configs), associated test cases
    - Render:
        - Name, Description
        - Stages (list of converter configs)
        - Associated Test Cases (list, link to each)
        - Actions: Edit, Clone, Delete, Back

---

## Notes
- All screens enforce permissions via decorators.
- All create/edit forms use Flask-WTF for CSRF and validation.
- File uploads are saved in `uploads/` (auto-created if missing).
- All actions are logged in the audit log. 