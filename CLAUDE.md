# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a Frappe custom app called "Dev Assistant" that provides developer productivity tools and utilities for Frappe/ERPNext systems. The app focuses on field-level access control and role permission management.

### Core Components

**Field Access Control System:**
- **DocType**: `Field Access Control` - Main configuration doctype for field visibility rules
- **Child Tables**: 
  - `Field Configuration Detail` - Individual field hide/read-only configurations
  - `User Exception Detail` - Users exempt from field access rules
- **Controller**: `dev_assistant/doctype/field_access_control/field_access_control.py`
- **Client Scripts**: `field_access_control.js` for UI interactions

**Role Permission Utilities:**
- **API**: `dev_assistant/utils.py` contains `copy_role_permissions()` function
- **Client Integration**: `role_copy_permissions.js` adds "Copy Permissions" button to Role doctype

### Key Features

1. **Role-based Field Control**: Hide or make fields read-only based on user roles
2. **Document Filtering**: Apply rules to specific documents via patterns or custom conditions  
3. **User Exceptions**: Exclude specific users from field access rules
4. **Bulk Permission Copy**: Copy all permissions from one role to another
5. **Dynamic Field Selection**: UI for selecting fields from any doctype

### Configuration Structure

Field Access Control supports multiple filtering modes:
- **Role-based**: Apply to specific role or all roles
- **Document filtering**: All documents, specific document, name patterns, or custom Python conditions
- **User exceptions**: Exclude specific users when enabled

## Development Commands

### Testing
```bash
# Run tests for the app
bench --site [site-name] run-tests --app dev_assistant

# Run specific test
bench --site [site-name] run-tests dev_assistant.dev_assistant.doctype.field_access_control.test_field_access_control
```

### Installation
```bash
# Install app to site
bench --site [site-name] install-app dev_assistant

# Migrate after changes
bench --site [site-name] migrate
```

### Code Quality
```bash
# Run ruff linter
ruff check dev_assistant/

# Run ruff formatter  
ruff format dev_assistant/

# Pre-commit hooks (configured in .pre-commit-config.yaml)
pre-commit run --all-files
```

### Development Setup
```bash
# Clear cache after changes
bench --site [site-name] clear-cache

# Build assets
bench build --app dev_assistant

# Watch for changes during development
bench watch
```

## File Structure

```
dev_assistant/
├── dev_assistant/
│   ├── doctype/
│   │   ├── field_access_control/           # Main configuration doctype
│   │   ├── field_configuration_detail/     # Child table for field configs
│   │   └── user_exception_detail/          # Child table for user exceptions
│   ├── hooks.py                            # App configuration and hooks
│   └── utils.py                            # Role permission copy utilities
├── public/js/
│   ├── field_access_control.js             # Global field access client scripts
│   └── role_copy_permissions.js            # Role doctype customization
└── templates/                              # Jinja templates (if any)
```

## Key APIs

### Whitelisted Methods

- `get_doctype_fields(doctype_name)` - Get all fields for a doctype
- `add_field_configurations(docname, fieldnames)` - Bulk add field configurations  
- `get_active_configurations(doctype_name, role, docname)` - Get applicable field rules
- `copy_role_permissions(source_role, target_role, overwrite_existing)` - Copy role permissions

### Client Script Integration

The app includes global JavaScript that automatically applies field access rules based on:
- Current user's roles
- Document type being viewed
- Document name (if applicable)
- Active field access configurations

## Configuration Notes

- **Ruff Configuration**: Uses 110 character line length, Python 3.10+ target
- **Pre-commit Hooks**: Configured for ruff, prettier, eslint, and standard checks
- **Frappe Integration**: Follows standard Frappe app structure and conventions
- **Permissions**: System Manager and Administrator have full access to configurations

## Development Patterns

When extending the app:
1. Use standard Frappe DocType patterns for new configurations
2. Follow existing naming conventions (snake_case for files, PascalCase for doctypes)
3. Add client scripts to `public/js/` for global functionality
4. Use whitelisted methods for API endpoints
5. Include proper error handling and logging in Python methods
6. Test configurations thoroughly as they affect UI behavior globally

## User Environment Notes

- **Screenshots Directory**: `/home/swapnilg45/Pictures/Screenshots/`
  - Use this path when user provides screenshot filenames for analysis
  - Read screenshots using the Read tool with full path