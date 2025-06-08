# Test Accelerator Workflow Reference

This document describes the main business and technical workflows in the Test Accelerator system. Use this as a reference for onboarding, development, and process understanding.

---

## 1. Test Case Management Workflow

**Actors:** Admin, Tester, Analyst

1. **Create Test Case**
    - Fill in name, workflow, config, description, schedule.
    - Save to database; audit log entry created.
2. **Edit Test Case**
    - Update fields as needed; audit log entry created.
3. **Clone Test Case**
    - Duplicate all fields except ID and timestamps; name is suffixed with "(Clone)".
    - Redirect to edit page for the new test case.
4. **Delete Test Case**
    - Removes test case and all associated test runs; audit log entry created.
5. **Bulk Execute**
    - Select multiple test cases and execute them in batch; results and audit log entries created.
6. **View Test Run History**
    - See all runs for a test case, with status, output, and details.

---

## 2. Workflow Management

**Actors:** Admin, Developer

1. **Create Workflow**
    - Define workflow name and stages (ordered list of converter configs).
    - Save to database; audit log entry created.
2. **Edit Workflow**
    - Update name or stages; audit log entry created.
3. **Clone Workflow**
    - Duplicate all fields except ID and timestamps; name is suffixed with "(Clone)".
    - Redirect to edit page for the new workflow.
4. **Delete Workflow**
    - Removes workflow; audit log entry created.

---

## 3. Converter Config, File Type, and Configuration Management

**Actors:** Admin, Developer

- **Create/Edit/Clone/Delete** for each entity (Converter Config, File Type, Configuration) follows the same pattern as above.
- Cloning creates a new entity with the same fields, except for ID and name (name is suffixed with "(Clone)").
- All actions are logged in the audit log.

---

## 4. Execution & Scheduling

**Actors:** Tester, Scheduler

- **Manual Execution:**
    - Test cases can be executed individually or in bulk.
    - Workflows can be executed step-by-step with file uploads and diffs.
- **Scheduled Execution:**
    - Test cases with a schedule (daily/weekly) are picked up by the background scheduler and executed automatically.
    - Results and audit log entries are created.

---

## 5. Permissions & Roles

**Actors:** Admin

- **Roles** are collections of permissions.
- **Permissions** control access to all major actions (view, create, edit, delete, execute, manage, audit log, etc.).
- **Users** are assigned a single role.
- **Role/Permission Management UI** allows for fine-grained access control.

---

## 6. Cloning Pattern

- All major entities (test case, workflow, converter config, file type, configuration) support cloning.
- Cloning is always a POST action, permission-protected, and redirects to the edit page for the new entity.
- Cloned entities have "(Clone)" appended to their name.

---

## 7. Audit Logging

- All create, edit, delete, execute, and clone actions are logged with user, timestamp, action, and details.
- Audit logs are viewable and filterable in the UI.

---

## 8. User Management

- Admins can create, edit, assign roles, and (optionally) deactivate users.
- Users can update their own profile (if enabled).

---

## 9. Data Flow Diagram (Simplified)

```
User → [UI] → [Flask App] → [Database]
                        ↓
                [Scheduler]
```

- All actions go through the Flask app, which enforces permissions and logs actions.
- The scheduler runs in the background for scheduled test case execution.

---

## 10. References
- See `README.md` for setup and deployment.
- See `DESIGN.md` for technical design and architecture.

---

## 11. Example User Stories

- As an **admin**, I can create a test case with multiple workflows, each with a sample file.
- As a **tester**, I can add/remove workflows dynamically and upload files per workflow.
- As an **admin**, I can create, edit, and assign roles to users.
- As a **tester**, I can execute test cases and view results.
- As a **developer**, I can define new workflows and converter configs.
- As an **analyst**, I can view dashboards and export test run data.

---

## 12. Example Flows for Common Tasks

### How to Schedule a Test Case
1. Go to the Test Cases list.
2. Click "Edit" on the desired test case.
3. Set the schedule (e.g., daily, weekly) and save.
4. The scheduler will pick up and execute the test case automatically.

### How to Clone a Workflow
1. Go to the Workflows list.
2. Click the "Clone" button next to the workflow.
3. You will be redirected to the edit page for the new workflow (with "(Clone)" in the name).
4. Make any changes and save.

### How to Assign a Role to a User
1. Go to the Users list (Admin menu).
2. Click "Edit" on the user.
3. Select the desired role and save.

### How to Add a Test Case with Multiple Workflows
1. Go to the Test Cases list.
2. Click "+ New Test Case".
3. Click "Add Workflow" for each workflow you want to add.
4. For each row, select a workflow and upload a sample file.
5. Remove a workflow row if needed.
6. Save the test case.

### Validation
- At least one workflow is required.
- No duplicate workflows allowed.
- Files are saved in uploads/.

---

## 13. Troubleshooting / FAQ

**Q: Why can't I see certain menu items?**
A: You may not have the required permissions. Contact an admin to review your role.

**Q: Why isn't my scheduled test case running?**
A: Ensure the schedule is set and the scheduler is running. Check the audit log for errors.

**Q: How do I reset a user's password?**
A: Admins can edit a user and set a new password.

**Q: How do I add a new entity type?**
A: Follow the blueprint/model/template pattern described in DESIGN.md. 