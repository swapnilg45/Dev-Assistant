# Dev Assistant

A Frappe app for developer productivity tools and utilities.

## Features

### Field Access Control
- Role-based field visibility and read-only controls
- User exception management
- Document-specific filtering
- Easy field selection interface

## Installation

```bash
bench get-app dev_assistant
bench --site [site-name] install-app dev_assistant
```

## Usage

1. Create a new "Field Access Control" record
2. Select doctype and role
3. Use "Select Fields" button to choose fields
4. Configure hide/read-only actions
5. Save and the rules will be automatically applied

## Requirements

- Frappe Framework
- ERPNext (optional)

## License

MIT
