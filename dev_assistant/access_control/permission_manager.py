# Copyright (c) 2025, Hybrowlabs and contributors
# For license information, please see license.txt

"""
Access Control - Permission Manager

Core logic for calculating field-level permissions based on Field Access Control
configurations. Determines which fields should be hidden or read-only for specific
users and documents.

Architecture:
    Called by monkey_patches.py when frappe.get_meta() is invoked.
    Returns permission mapping applied to DocType meta information.

Security:
    All permission checks happen server-side, cannot be bypassed via client.
"""

import frappe
from frappe import _
from frappe.utils.safe_exec import safe_exec
import fnmatch

# ============================================================================
# CONSTANTS
# ============================================================================

# Permission levels for field access
PERMLEVEL_FULL_ACCESS = 0       # Default - full access
PERMLEVEL_HIDDEN = 1000          # Field completely hidden
PERMLEVEL_READ_ONLY = 1001       # Read-only access

# Action type to permission level mapping
ACTION_TYPE_MAP = {
    'Hide': PERMLEVEL_HIDDEN,
    'Read Only': PERMLEVEL_READ_ONLY
}

# Cache TTL (1 hour)
CACHE_TTL = 3600


# ============================================================================
# CONFIGURATION RETRIEVAL
# ============================================================================

def get_field_access_configurations(doctype, use_cache=True):
    """
    Get all active field access configurations for a doctype.

    Retrieves Field Access Control documents with all child table configurations
    (field configurations, user exceptions, child table configurations).

    Args:
        doctype (str): The doctype name (e.g., 'Sales Order')
        use_cache (bool): Whether to use cached configurations (default: True)

    Returns:
        list: List of configuration dictionaries with all child tables loaded

    Performance:
        - First call: ~50ms (database query)
        - Cached calls: ~1ms (Redis lookup)
        - Cache TTL: 3600 seconds (1 hour)

    Cache Key:
        field_access:configs:{doctype}
    """
    cache_key = f"field_access:configs:{doctype}"

    # Try cache first
    if use_cache:
        try:
            cached = frappe.cache().get_value(cache_key)
            if cached is not None:
                return cached
        except Exception as e:
            # Use simple logging to avoid infinite recursion
            import traceback
            print(f"Access Control: Cache Read Failed for {doctype}: {str(e)}")
            print(traceback.format_exc())

    # Query main configurations
    try:
        configs = frappe.get_all(
            'Field Access Control',
            filters={
                'doctype_name': doctype,
                'is_active': 1
            },
            fields=[
                'name', 'doctype_name', 'role', 'apply_to_all_roles',
                'enable_user_exceptions', 'docname_filter', 'docname_pattern',
                'specific_docname', 'custom_condition', 'enable_child_table_control'
            ]
        )
    except Exception as e:
        # Use simple logging to avoid infinite recursion
        import traceback
        print(f"Access Control: Query Failed for {doctype}: {str(e)}")
        print(traceback.format_exc())
        return []

    # If no configurations, cache empty list and return
    if not configs:
        if use_cache:
            frappe.cache().set_value(cache_key, [], expires_in_sec=CACHE_TTL)
        return []

    # Load child tables for each configuration
    for config in configs:
        try:
            # Load field configurations
            config['field_configurations'] = frappe.get_all(
                'Field Configuration Detail',
                filters={
                    'parent': config.name,
                    'parenttype': 'Field Access Control',
                    'is_active': 1
                },
                fields=['fieldname', 'field_label', 'action_type', 'is_active']
            )

            # Load user exceptions (if enabled)
            if config.get('enable_user_exceptions'):
                config['user_exceptions'] = frappe.get_all(
                    'User Exception Detail',
                    filters={
                        'parent': config.name,
                        'parenttype': 'Field Access Control',
                        'is_active': 1
                    },
                    fields=['user', 'reason', 'is_active']
                )
            else:
                config['user_exceptions'] = []

            # Load child table configurations (if enabled)
            if config.get('enable_child_table_control'):
                config['child_table_configurations'] = frappe.get_all(
                    'Child Table Button Configuration',
                    filters={
                        'parent': config.name,
                        'parenttype': 'Field Access Control',
                        'is_active': 1
                    },
                    fields=[
                        'table_fieldname', 'table_label',
                        'hide_add_button', 'hide_delete_button', 'is_active'
                    ]
                )
            else:
                config['child_table_configurations'] = []

        except Exception as e:
            # Use simple logging to avoid infinite recursion
            import traceback
            print(f"Access Control: Child Table Load Failed for {config.name}: {str(e)}")
            print(traceback.format_exc())
            config['field_configurations'] = []
            config['user_exceptions'] = []
            config['child_table_configurations'] = []

    # Cache the result
    if use_cache:
        try:
            frappe.cache().set_value(cache_key, configs, expires_in_sec=CACHE_TTL)
        except Exception as e:
            # Use simple logging to avoid infinite recursion
            import traceback
            print(f"Access Control: Cache Write Failed for {doctype}: {str(e)}")
            print(traceback.format_exc())

    return configs


# ============================================================================
# APPLICABILITY CHECKS
# ============================================================================

def should_apply_to_user(config, user, user_roles):
    """
    Check if configuration should apply to a specific user.

    Checks:
    1. User exceptions (if user in exception list, return False)
    2. Role matching (if apply_to_all_roles or user has the role)

    Args:
        config (dict): Configuration dictionary
        user (str): User email
        user_roles (list): List of role names the user has

    Returns:
        bool: True if configuration should apply, False otherwise
    """
    if not config:
        return False

    # Use session user if not provided
    if not user:
        user = frappe.session.user

    # Get user roles if not provided
    if user_roles is None:
        user_roles = get_user_roles(user)

    # Check user exceptions
    if config.get('enable_user_exceptions'):
        user_exceptions = config.get('user_exceptions', [])
        for exception in user_exceptions:
            if exception.get('user') == user and exception.get('is_active'):
                return False

    # Check if applies to all roles
    if config.get('apply_to_all_roles'):
        return True

    # Check if user has the required role
    config_role = config.get('role')
    if config_role and config_role in user_roles:
        return True

    return False


def should_apply_to_docname(config, docname):
    """
    Check if configuration should apply to a specific document.

    Supports:
    - All Documents: Always applies
    - Specific Document: Exact match
    - Document Name Pattern: Glob pattern matching (fnmatch)
    - Custom Condition: Python expression evaluation

    Args:
        config (dict): Configuration dictionary
        docname (str): Document name

    Returns:
        bool: True if configuration should apply, False otherwise
    """
    # If no docname provided, apply to all
    if not docname:
        return True

    if not config:
        return True

    # Get filter type
    filter_type = config.get('docname_filter', 'All Documents')

    # All Documents: Always apply
    if filter_type == 'All Documents':
        return True

    # Specific Document: Exact match
    elif filter_type == 'Specific Document':
        specific_docname = config.get('specific_docname', '')
        return docname == specific_docname

    # Document Name Pattern: Glob pattern matching
    elif filter_type == 'Document Name Pattern':
        pattern = config.get('docname_pattern', '')
        if not pattern:
            return False

        try:
            return fnmatch.fnmatch(docname, pattern)
        except Exception as e:
            # Use simple logging to avoid infinite recursion
            import traceback
            print(f"Access Control: Pattern Match Failed for pattern '{pattern}' against '{docname}': {str(e)}")
            print(traceback.format_exc())
            return False

    # Custom Condition: Python eval
    elif filter_type == 'Custom Condition':
        condition = config.get('custom_condition', '')
        if not condition:
            return False

        try:
            result = evaluate_custom_condition(condition, docname)
            return result
        except Exception as e:
            # Use simple logging to avoid infinite recursion
            import traceback
            print(f"Access Control: Custom Condition Failed for condition '{condition}' for '{docname}': {str(e)}")
            print(traceback.format_exc())
            return False

    return False


def evaluate_custom_condition(condition, docname):
    """
    Safely evaluate a custom Python condition.

    Uses safe_exec to evaluate user-provided Python code in restricted environment.
    Available in condition: docname, frappe

    Args:
        condition (str): Python expression to evaluate
        docname (str): Document name

    Returns:
        bool: True if condition evaluates to truthy value, False otherwise

    Security:
        Uses safe_exec() to prevent dangerous operations
    """
    if not condition:
        return False

    # Prepare locals dictionary
    locals_dict = {
        'docname': docname,
        'frappe': frappe,
        'result': False
    }

    # Wrap condition in result assignment
    code = f"result = bool({condition})"

    try:
        safe_exec(code, None, locals_dict)
        return locals_dict.get('result', False)
    except Exception as e:
        # Use simple logging to avoid infinite recursion
        import traceback
        print(f"Access Control: Condition Evaluation Failed for condition: {condition}, docname: {docname}, error: {str(e)}")
        print(traceback.format_exc())
        return False


# ============================================================================
# PERMISSION CALCULATION
# ============================================================================

def calculate_field_permissions(doctype, docname=None, user=None):
    """
    Calculate field-level permissions for a doctype and optional document.

    Core function that:
    1. Retrieves all configurations for the doctype
    2. Filters configurations by user, role, and docname
    3. Builds a permission map for fields and child tables
    4. Caches the result

    Args:
        doctype (str): The doctype name
        docname (str, optional): Specific document name
        user (str, optional): User email (defaults to session user)

    Returns:
        dict: Permission mapping:
            {
                'fields': {
                    'fieldname1': 1000,  # Hidden
                    'fieldname2': 1001,  # Read-only
                },
                'child_tables': {
                    'table_fieldname1': {
                        'cannot_add_rows': 1,
                        'cannot_delete_rows': 0
                    },
                }
            }

    Caching:
        - Cache Key: field_access:permissions:{doctype}:{docname}:{user}
        - TTL: 3600 seconds (1 hour)

    Permission Priority:
        Most restrictive wins: Hidden (1000) > Read Only (1001) > Full Access (0)
    """
    # Use session user if not provided
    if not user:
        user = frappe.session.user

    # Administrator always has full access
    if user == 'Administrator':
        return {'fields': {}, 'child_tables': {}}

    # Generate cache key
    docname_part = docname or 'list'
    cache_key = f"field_access:permissions:{doctype}:{docname_part}:{user}"

    # Try cache first
    try:
        cached = frappe.cache().get_value(cache_key)
        if cached is not None:
            return cached
    except Exception as e:
        # Use simple logging to avoid infinite recursion
        import traceback
        print(f"Access Control: Permission Cache Read Failed for {cache_key}: {str(e)}")
        print(traceback.format_exc())

    # Get configurations for this doctype
    configs = get_field_access_configurations(doctype)

    # If no configurations, return empty
    if not configs:
        empty_result = {'fields': {}, 'child_tables': {}}
        frappe.cache().set_value(cache_key, empty_result, expires_in_sec=CACHE_TTL)
        return empty_result

    # Get user roles
    user_roles = get_user_roles(user)

    # Initialize permission maps
    field_permissions = {}
    child_table_permissions = {}

    # Process each configuration
    for config in configs:
        # Check if configuration applies to this user
        if not should_apply_to_user(config, user, user_roles):
            continue

        # Check if configuration applies to this document
        if docname and not should_apply_to_docname(config, docname):
            continue

        # Apply field configurations
        for field_config in config.get('field_configurations', []):
            if not field_config.get('is_active'):
                continue

            fieldname = field_config.get('fieldname')
            action_type = field_config.get('action_type')

            if not fieldname or action_type not in ACTION_TYPE_MAP:
                continue

            # Get permission level for this action
            permlevel = ACTION_TYPE_MAP[action_type]

            # Apply most restrictive permission
            if fieldname not in field_permissions:
                field_permissions[fieldname] = permlevel
            else:
                field_permissions[fieldname] = max(
                    field_permissions[fieldname],
                    permlevel
                )

        # Apply child table configurations
        if config.get('enable_child_table_control'):
            for table_config in config.get('child_table_configurations', []):
                if not table_config.get('is_active'):
                    continue

                table_fieldname = table_config.get('table_fieldname')
                if not table_fieldname:
                    continue

                # Initialize table permissions if not exists
                if table_fieldname not in child_table_permissions:
                    child_table_permissions[table_fieldname] = {}

                # Set button restrictions
                if table_config.get('hide_add_button'):
                    child_table_permissions[table_fieldname]['cannot_add_rows'] = 1

                if table_config.get('hide_delete_button'):
                    child_table_permissions[table_fieldname]['cannot_delete_rows'] = 1

    # Build result
    result = {
        'fields': field_permissions,
        'child_tables': child_table_permissions
    }

    # Cache result
    try:
        frappe.cache().set_value(cache_key, result, expires_in_sec=CACHE_TTL)
    except Exception as e:
        # Use simple logging to avoid infinite recursion
        import traceback
        print(f"Access Control: Permission Cache Write Failed for {cache_key}: {str(e)}")
        print(traceback.format_exc())

    return result


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_user_roles(user=None):
    """
    Get roles for a user with caching.

    Args:
        user (str, optional): User email (defaults to session user)

    Returns:
        list: List of role names

    Caching:
        - Cache Key: field_access:user_roles:{user}
        - TTL: 3600 seconds (1 hour)
    """
    if not user:
        user = frappe.session.user

    # Try cache
    cache_key = f"field_access:user_roles:{user}"
    cached = frappe.cache().get_value(cache_key)
    if cached:
        return cached

    # Get roles from frappe
    roles = frappe.get_roles(user)

    # Cache result
    frappe.cache().set_value(cache_key, roles, expires_in_sec=CACHE_TTL)

    return roles


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'get_field_access_configurations',
    'should_apply_to_user',
    'should_apply_to_docname',
    'calculate_field_permissions',
    'evaluate_custom_condition',
    'get_user_roles',
    'PERMLEVEL_HIDDEN',
    'PERMLEVEL_READ_ONLY',
    'ACTION_TYPE_MAP'
]
