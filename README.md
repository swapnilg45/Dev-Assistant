# Dev Assistant

A Frappe app for developer productivity tools and utilities.

## Features

### Field Access Control
- Role-based field visibility and read-only controls
- User exception management
- Document-specific filtering
- Easy field selection interface

### Field Options Manager
- Dynamic field options based on conditions
- Automatic options population without client scripts
- Conditional logic for field options
- Support for Select, Link, and MultiSelect fields
- Easy options management interface

## Installation

```bash
bench get-app dev_assistant
bench --site [site-name] install-app dev_assistant
```

## Usage

### Field Access Control
1. Create a new "Field Access Control" record
2. Select doctype and role
3. Use "Select Fields" button to choose fields
4. Configure hide/read-only actions
5. Save and the rules will be automatically applied

### Field Options Manager
1. Create a new "Field Options Manager" record
2. Select doctype and field
3. Use "Select Fields" button to choose the target field
4. Use "Add Options" button to configure dynamic options
5. Set conditions if needed
6. Save and options will be automatically applied to forms

## Requirements

- Frappe Framework
- ERPNext (optional)

## License

MIT
