# API Reference

This document lists the main API endpoints for ConverterApp. All endpoints are permission-protected as described.

| Endpoint                        | Method | Description                | Permissions Required      | Params/Body                | Response         |
|----------------------------------|--------|----------------------------|--------------------------|----------------------------|------------------|
| `/auth/login`                    | POST   | User login                 | -                        | username, password         | JWT/session      |

**Example:**
```sh
curl -X POST http://localhost:5000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username": "admin", "password": "yourpassword"}'
```
**Response:**
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "Admin"
  }
}
```

| `/auth/logout`                   | GET    | User logout                | Authenticated            | -                          | Redirect         |

**Example:**
```sh
curl -X GET http://localhost:5000/auth/logout \
  -H 'Authorization: Bearer <token>'
```
**Response:**
Redirects to login page or returns:
```json
{
  "message": "Logged out successfully"
}
```

| `/auth/register`                 | POST   | Register new user          | Admin                    | username, email, password, role | Success/Error   |

**Example:**
```sh
curl -X POST http://localhost:5000/auth/register \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{"username": "newuser", "email": "new@user.com", "password": "pass123", "role": "Tester"}'
```
**Response:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 2,
    "username": "newuser"
  }
}
```

| `/auth/users`                    | GET    | List users                 | user_manage              | page, search               | User list        |

**Example:**
```sh
curl -X GET http://localhost:5000/auth/users \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
[
  {"id": 1, "username": "admin", "email": "admin@site.com", "role": "Admin"},
  {"id": 2, "username": "newuser", "email": "new@user.com", "role": "Tester"}
]
```

| `/auth/user/<id>`                | GET    | Get user details           | user_manage/self         | -                          | User object      |

**Example:**
```sh
curl -X GET http://localhost:5000/auth/user/2 \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "id": 2,
  "username": "newuser",
  "email": "new@user.com",
  "role": "Tester",
  "date_joined": "2024-06-01T12:00:00",
  "last_login": "2024-06-02T09:00:00"
}
```

| `/auth/user/<id>/edit`           | POST   | Edit user                  | user_manage/self         | fields to update           | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/auth/user/2/edit \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{"email": "updated@user.com", "role": "Analyst"}'
```
**Response:**
```json
{
  "message": "User updated successfully"
}
```

| `/auth/user/<id>/deactivate`     | POST   | Deactivate user            | user_manage              | -                          | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/auth/user/2/deactivate \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "message": "User deactivated successfully"
}
```

| `/auth/roles`                    | GET    | List roles                 | role_manage              | -                          | Role list        |

**Example:**
```sh
curl -X GET http://localhost:5000/auth/roles \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
[
  {"id": 1, "name": "Admin"},
  {"id": 2, "name": "Tester"},
  {"id": 3, "name": "Analyst"}
]
```

| `/auth/role/<id>`                | GET    | Get role details           | role_manage              | -                          | Role object      |

**Example:**
```sh
curl -X GET http://localhost:5000/auth/role/2 \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "id": 2,
  "name": "Tester",
  "description": "Can execute and view test cases",
  "permissions": ["testcase_view", "testcase_execute"]
}
```

| `/auth/role/create`              | POST   | Create role                | role_manage              | name, description          | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/auth/role/create \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{"name": "Scheduler", "description": "Can manage schedules"}'
```
**Response:**
```json
{
  "message": "Role created successfully",
  "role": {"id": 4, "name": "Scheduler"}
}
```

| `/auth/role/<id>/edit`           | POST   | Edit role                  | role_manage              | fields to update           | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/auth/role/2/edit \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{"description": "Can view and execute test cases"}'
```
**Response:**
```json
{
  "message": "Role updated successfully"
}
```

| `/auth/role/<id>/permissions`    | POST   | Assign permissions         | role_manage              | permission_ids             | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/auth/role/2/permissions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{"permission_ids": [1, 2, 3]}'
```
**Response:**
```json
{
  "message": "Permissions updated successfully"
}
```

| `/auth/permissions`              | GET    | List permissions           | role_manage              | -                          | Permission list  |

**Example:**
```sh
curl -X GET http://localhost:5000/auth/permissions \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
[
  {"id": 1, "name": "testcase_view"},
  {"id": 2, "name": "testcase_create"},
  {"id": 3, "name": "testcase_edit"}
]
```

| `/testcases`                     | GET    | List test cases            | testcase_view            | filters, search            | Test case list   |

**Example:**
```sh
curl -X GET http://localhost:5000/testcases \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
[
  {
    "id": 1,
    "name": "Test Case 1",
    "workflow": "Workflow A"
  },
  {
    "id": 2,
    "name": "Test Case 2",
    "workflow": "Workflow B"
  }
]
```

| `/testcase/<id>`                 | GET    | Get test case details      | testcase_view            | -                          | Test case object |

**Example:**
```sh
curl -X GET http://localhost:5000/testcase/1 \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "id": 1,
  "name": "Test Case 1",
  "workflow": "Workflow A",
  "config": "Config A",
  "description": "Test case for workflow 1",
  "schedule": "daily"
}
```

| `/testcase/create`               | POST   | Create test case           | testcase_create          | multipart/form-data: name, description, schedule, workflow_0, sample_file_0, workflow_1, sample_file_1, ... | TestCase object |

**Example:**
```sh
curl -X POST http://localhost:5000/testcase/create \
  -H 'Authorization: Bearer <token>' \
  -F 'name=My Test Case' \
  -F 'description=Example' \
  -F 'schedule=none' \
  -F 'workflow_0=1' -F 'sample_file_0=@/path/to/file1.txt' \
  -F 'workflow_1=2' -F 'sample_file_1=@/path/to/file2.txt'
```
**Response:**
```json
{
  "message": "Test case created successfully",
  "test_case": {
    "id": 5,
    "name": "My Test Case"
  }
}
```

| `/testcase/<id>/edit`            | POST   | Edit test case             | testcase_edit            | fields                     | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/testcase/1/edit \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{"name": "Updated Test Case", "description": "Updated description"}'
```
**Response:**
```json
{
  "message": "Test case updated successfully"
}
```

| `/testcase/<id>/delete`          | POST   | Delete test case           | testcase_delete          | -                          | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/testcase/1/delete \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "message": "Test case deleted successfully"
}
```

| `/testcase/<id>/clone`           | POST   | Clone test case            | testcase_clone           | -                          | Redirect         |

**Example:**
```sh
curl -X POST http://localhost:5000/testcase/1/clone \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "message": "Test case cloned successfully",
  "test_case": {
    "id": 6,
    "name": "Sample Test Case (Clone)"
  }
}
```

| `/testcase/bulk_execute`         | POST   | Bulk execute test cases    | testcase_execute         | test_case_ids              | Results          |

**Example:**
```sh
curl -X POST http://localhost:5000/testcase/bulk_execute \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{"test_case_ids": [1, 2, 3]}'
```
**Response:**
```json
{
  "message": "Test cases executed successfully",
  "results": [
    {"id": 1, "status": "Passed"},
    {"id": 2, "status": "Failed"},
    {"id": 3, "status": "Passed"}
  ]
}
```

| `/testcase/<id>/runs`            | GET    | List test runs for case    | testcase_view            | -                          | Test run list    |

**Example:**
```sh
curl -X GET http://localhost:5000/testcase/1/runs \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
[
  {
    "id": 1,
    "status": "Passed",
    "start_time": "2024-06-01T12:34:56",
    "end_time": "2024-06-01T13:00:00"
  },
  {
    "id": 2,
    "status": "Failed",
    "start_time": "2024-06-02T12:34:56",
    "end_time": "2024-06-02T13:00:00"
  }
]
```

| `/workflows`                     | GET    | List workflows             | workflow_view            | filters, search            | Workflow list    |

**Example:**
```sh
curl -X GET http://localhost:5000/workflows \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
[
  {"id": 1, "name": "Workflow A"},
  {"id": 2, "name": "Workflow B"}
]
```

| `/workflow/<id>`                 | GET    | Get workflow details       | workflow_view            | -                          | Workflow object  |

**Example:**
```sh
curl -X GET http://localhost:5000/workflow/1 \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "id": 1,
  "name": "Workflow A",
  "description": "Workflow for test cases",
  "test_cases": [1, 2]
}
```

| `/workflow/create`               | POST   | Create workflow            | workflow_create          | fields                     | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/workflow/create \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{"name": "New Workflow", "description": "New workflow description"}'
```
**Response:**
```json
{
  "message": "Workflow created successfully",
  "workflow": {"id": 3, "name": "New Workflow"}
}
```

| `/workflow/<id>/edit`            | POST   | Edit workflow              | workflow_edit            | fields                     | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/workflow/1/edit \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{"name": "Updated Workflow", "description": "Updated workflow description"}'
```
**Response:**
```json
{
  "message": "Workflow updated successfully"
}
```

| `/workflow/<id>/delete`          | POST   | Delete workflow            | workflow_delete          | -                          | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/workflow/1/delete \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "message": "Workflow deleted successfully"
}
```

| `/workflow/<id>/clone`           | POST   | Clone workflow             | workflow_clone           | -                          | Redirect         |

**Example:**
```sh
curl -X POST http://localhost:5000/workflow/1/clone \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "message": "Workflow cloned successfully",
  "workflow": {
    "id": 4,
    "name": "Original Workflow (Clone)"
  }
}
```

| `/configs`                       | GET    | List converter configs     | config_view              | filters, search            | Config list      |

**Example:**
```sh
curl -X GET http://localhost:5000/configs \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
[
  {"id": 1, "name": "Config A"},
  {"id": 2, "name": "Config B"}
]
```

| `/config/<id>`                   | GET    | Get config details         | config_view              | -                          | Config object    |

**Example:**
```sh
curl -X GET http://localhost:5000/config/1 \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "id": 1,
  "name": "Config A",
  "description": "Configuration for workflow A"
}
```

| `/config/create`                 | POST   | Create config              | config_create            | fields                     | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/config/create \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{"name": "New Config", "description": "New configuration description"}'
```
**Response:**
```json
{
  "message": "Configuration created successfully",
  "config": {"id": 3, "name": "New Config"}
}
```

| `/config/<id>/edit`              | POST   | Edit config                | config_edit              | fields                     | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/config/1/edit \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{"name": "Updated Config", "description": "Updated configuration description"}'
```
**Response:**
```json
{
  "message": "Configuration updated successfully"
}
```

| `/config/<id>/delete`            | POST   | Delete config              | config_delete            | -                          | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/config/1/delete \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "message": "Configuration deleted successfully"
}
```

| `/config/<id>/clone`             | POST   | Clone config               | config_clone             | -                          | Redirect         |

**Example:**
```sh
curl -X POST http://localhost:5000/config/1/clone \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "message": "Configuration cloned successfully",
  "config": {
    "id": 4,
    "name": "Original Config (Clone)"
  }
}
```

| `/filetypes`                     | GET    | List file types            | filetype_view            | filters, search            | File type list   |

**Example:**
```sh
curl -X GET http://localhost:5000/filetypes \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
[
  {"id": 1, "name": "File Type A"},
  {"id": 2, "name": "File Type B"}
]
```

| `/filetype/<id>`                 | GET    | Get file type details      | filetype_view            | -                          | File type object |

**Example:**
```sh
curl -X GET http://localhost:5000/filetype/1 \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "id": 1,
  "name": "File Type A",
  "description": "Description of File Type A"
}
```

| `/filetype/create`               | POST   | Create file type           | filetype_create          | fields                     | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/filetype/create \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{"name": "New File Type", "description": "New file type description"}'
```
**Response:**
```json
{
  "message": "File type created successfully",
  "file_type": {"id": 5, "name": "New File Type"}
}
```

| `/filetype/<id>/edit`            | POST   | Edit file type             | filetype_edit            | fields                     | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/filetype/1/edit \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{"name": "Updated File Type", "description": "Updated file type description"}'
```
**Response:**
```json
{
  "message": "File type updated successfully"
}
```

| `/filetype/<id>/delete`          | POST   | Delete file type           | filetype_delete          | -                          | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/filetype/1/delete \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "message": "File type deleted successfully"
}
```

| `/filetype/<id>/clone`           | POST   | Clone file type            | filetype_clone           | -                          | Redirect         |

**Example:**
```sh
curl -X POST http://localhost:5000/filetype/1/clone \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "message": "File type cloned successfully",
  "file_type": {
    "id": 6,
    "name": "Original File Type (Clone)"
  }
}
```

| `/configurations`                | GET    | List configurations        | configuration_view       | filters, search            | Config list      |

**Example:**
```sh
curl -X GET http://localhost:5000/configurations \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
[
  {"id": 1, "name": "Config A"},
  {"id": 2, "name": "Config B"}
]
```

| `/configuration/<id>`            | GET    | Get configuration details  | configuration_view       | -                          | Config object    |

**Example:**
```sh
curl -X GET http://localhost:5000/configuration/1 \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "id": 1,
  "name": "Config A",
  "description": "Configuration for workflow A"
}
```

| `/configuration/create`          | POST   | Create configuration       | configuration_create     | fields                     | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/configuration/create \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{"name": "New Config", "description": "New configuration description"}'
```
**Response:**
```json
{
  "message": "Configuration created successfully",
  "config": {"id": 3, "name": "New Config"}
}
```

| `/configuration/<id>/edit`       | POST   | Edit configuration         | configuration_edit       | fields                     | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/configuration/1/edit \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{"name": "Updated Config", "description": "Updated configuration description"}'
```
**Response:**
```json
{
  "message": "Configuration updated successfully"
}
```

| `/configuration/<id>/delete`     | POST   | Delete configuration       | configuration_delete     | -                          | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/configuration/1/delete \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "message": "Configuration deleted successfully"
}
```

| `/configuration/<id>/clone`      | POST   | Clone configuration        | configuration_clone      | -                          | Redirect         |

**Example:**
```sh
curl -X POST http://localhost:5000/configuration/1/clone \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "message": "Configuration cloned successfully",
  "config": {
    "id": 4,
    "name": "Original Config (Clone)"
  }
}
```

| `/auditlog`                      | GET    | List/filter audit logs     | auditlog_view            | filters, search            | Log list         |

**Example:**
```sh
curl -X GET http://localhost:5000/auditlog \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
[
  {"id": 1, "user": "admin", "action": "create_testcase", "timestamp": "2024-06-01T12:34:56"},
  ...
]
```

| `/auditlog/<id>`                 | GET    | View audit log entry       | auditlog_view            | -                          | Log entry        |

**Example:**
```sh
curl -X GET http://localhost:5000/auditlog/1 \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "id": 1,
  "user": "admin",
  "action": "create_testcase",
  "timestamp": "2024-06-01T12:34:56"
}
```

| `/scheduler/status`              | GET    | Scheduler status           | scheduler_view           | -                          | Status           |

**Example:**
```sh
curl -X GET http://localhost:5000/scheduler/status \
  -H 'Authorization: Bearer <token>'
```
**Response:**
```json
{
  "status": "Running"
}
```

| `/scheduler/trigger`             | POST   | Trigger scheduled run      | scheduler_manage         | test_case_id               | Success/Error    |

**Example:**
```sh
curl -X POST http://localhost:5000/scheduler/trigger \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{"test_case_id": 1}'
```
**Response:**
```json
{
  "message": "Scheduled run triggered successfully"
}
``` 