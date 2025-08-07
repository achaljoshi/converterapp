# Navigation Structure

## Overview
The application navigation is organized into logical sections for better user experience and feature grouping.

## Navigation Menu Structure

```
Test Accelerator
├── Dashboard
├── Payments
│   ├── File Types
│   ├── Mapping Rules
│   ├── Test Workflow
│   ├── ──────────────────
│   ├── Converter
│   └── Data Generator
├── Test Management
│   ├── Test Cases
│   ├── Git Repositories
│   ├── Test Frameworks
│   └── Labels
└── Admin
    ├── Users
    ├── Permissions
    └── Roles
```

## Section Details

### 🏠 Dashboard
- **Purpose**: Main overview and analytics
- **Features**: KPI metrics, recent test runs, charts
- **Access**: All authenticated users

### 💳 Payments
- **Purpose**: Payment message processing and conversion
- **Features**:
  - **File Types**: Define SWIFT MT and ISO 20022 message formats
  - **Mapping Rules**: Configure conversion rules between formats
  - **Test Workflow**: Create and manage conversion workflows
  - **Converter**: Test individual conversions with sample data
  - **Data Generator**: Generate sample payment messages

### 🧪 Test Management
- **Purpose**: Automated testing and test case management
- **Features**:
  - **Test Cases**: Manage test scenarios and metadata
  - **Git Repositories**: Configure source code repositories
  - **Test Frameworks**: Define testing frameworks and patterns
  - **Labels**: Categorize and organize test cases

### ⚙️ Admin
- **Purpose**: System administration and user management
- **Features**:
  - **Users**: Manage user accounts and permissions
  - **Permissions**: Define system permissions
  - **Roles**: Create and assign user roles

## User Experience Benefits

### ✅ Improved Organization
- **Logical Grouping**: Related features are grouped together
- **Clear Separation**: Payment processing vs. test management
- **Reduced Clutter**: Fewer top-level menu items

### ✅ Better Workflow
- **Payment Processing**: Complete workflow from file types to conversion
- **Test Management**: End-to-end test case lifecycle
- **Administration**: Centralized system management

### ✅ Enhanced Usability
- **Intuitive Navigation**: Features are where users expect them
- **Reduced Cognitive Load**: Clearer mental model of the application
- **Faster Access**: Related features are grouped for quick access

## Technical Implementation

### Navigation Structure
```html
<!-- Payments Dropdown -->
<li class="nav-item dropdown">
    <a class="nav-link dropdown-toggle" href="#" id="paymentsDropdown">
        Payments
    </a>
    <ul class="dropdown-menu">
        <li><a href="/filetypes">File Types</a></li>
        <li><a href="/config/converters">Mapping Rules</a></li>
        <li><a href="/test-workflow">Test Workflow</a></li>
        <li><hr class="dropdown-divider"></li>
        <li><a href="/converters/test">Converter</a></li>
        <li><a href="/data-generator">Data Generator</a></li>
    </ul>
</li>
```

### Bootstrap Integration
- Uses Bootstrap 5 dropdown components
- Responsive design for mobile devices
- Consistent styling across all sections

## Future Enhancements

### Potential Additions
- **Reports Section**: Analytics and reporting features
- **Settings Section**: User preferences and system configuration
- **Help Section**: Documentation and support resources

### Navigation Improvements
- **Breadcrumbs**: Show current location in the application
- **Quick Actions**: Frequently used features as buttons
- **Search**: Global search across all features
- **Favorites**: User-customizable quick access menu

---

**Last Updated**: August 6, 2025
**Version**: 2.0 