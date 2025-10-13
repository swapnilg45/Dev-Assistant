# Copyright (c) 2025, Hybrowlabs and contributors
# For license information, please see license.txt

"""
Access Control - Utilities

Helper functions for cache management, logging, and misc utilities.
Used by hooks for cache invalidation and testing/debugging.
"""

import frappe
from frappe import _


# ============================================================================
# CACHE MANAGEMENT - Called by hooks.py
# ============================================================================

def clear_configuration_cache(doc, method=None):
    """
    Clear cache when Field Access Control configuration changes.

    Called via doc_events hook when:
    - Field Access Control is created/updated/deleted

    Args:
        doc: Field Access Control document
        method: Event method name (on_update, on_trash, etc.)
    """
    try:
        doctype = doc.doctype_name

        # 1. Clear field access control caches
        cache_key = f"field_access:configs:{doctype}"
        frappe.cache().delete_value(cache_key)

        # 2. Clear ALL permission caches for this doctype (for all users)
        try:
            # Get all field_access cache keys
            all_keys = frappe.cache().get_keys("field_access:*")
            for key in all_keys:
                key_str = key.decode() if isinstance(key, bytes) else str(key)
                # Clear if it contains this doctype
                if doctype in key_str:
                    frappe.cache().delete_value(key)
        except Exception:
            # Fallback: Clear known patterns
            try:
                frappe.cache().delete_value(f"field_access:permissions:{doctype}:*")
            except:
                pass

        # 3. Clear meta caches - ALL variations
        frappe.cache().delete_value(f"form_meta:{doctype}")
        frappe.cache().delete_value(f"meta:{doctype}")
        frappe.cache().hdel("doctype_meta", doctype)
        frappe.cache().hdel("doctype_form_meta", doctype)
        frappe.cache().hdel("doctype_modified", doctype)

        # 4. Update modified timestamp to force browser cache invalidation
        # This is the key to forcing browser to fetch fresh meta
        frappe.db.set_value("DocType", doctype, "modified", frappe.utils.now(), update_modified=False)
        frappe.db.commit()

        # 5. Clear for parent if child table
        try:
            parent_dt = frappe.model.meta.get_parent_dt(doctype)
            if parent_dt:
                frappe.cache().delete_value(f"form_meta:{parent_dt}")
                frappe.cache().delete_value(f"meta:{parent_dt}")
                frappe.cache().hdel("doctype_meta", parent_dt)
                frappe.cache().hdel("doctype_form_meta", parent_dt)
                frappe.cache().hdel("doctype_modified", parent_dt)

                # Update parent timestamp too
                frappe.db.set_value("DocType", parent_dt, "modified", frappe.utils.now(), update_modified=False)
                frappe.db.commit()
        except:
            pass

        # 6. Send realtime event to force reload
        frappe.publish_realtime(
            event='field_access_config_changed',
            message={
                'doctype': doctype,
                'timestamp': frappe.utils.now()
            },
            after_commit=True
        )

        # 7. Show message to user who made the change
        frappe.msgprint(
            msg=f"Field Access Control updated for {doctype}. All users will see changes immediately.",
            title="Configuration Saved",
            indicator="green"
        )

        print(f"✅ Access Control: Cleared ALL caches for {doctype}")

    except Exception as e:
        import traceback
        print(f"❌ Access Control: Cache Clear Failed for {doc.doctype_name}")
        print(traceback.format_exc())


def clear_parent_cache(doc, method=None):
    """
    Clear cache when child table is updated.

    Called via doc_events hook when child tables are modified.
    Clears cache for the parent Field Access Control configuration.

    Args:
        doc: Child table document (Field Configuration Detail, etc.)
        method: Event method name
    """
    try:
        # Get parent Field Access Control
        parent = frappe.get_doc("Field Access Control", doc.parent)

        # Clear cache for this configuration
        clear_configuration_cache(parent, method)

    except Exception as e:
        frappe.log_error(
            title="Access Control: Parent Cache Clear Failed",
            message=f"Error clearing parent cache: {str(e)}"
        )


def clear_user_cache(user=None):
    """
    Clear cache for specific user or all users.

    Called when:
    - User logs out
    - User roles change
    - Need to force permission recalculation

    Args:
        user (str, optional): User email. If None, clears all users.
    """
    try:
        if user:
            # Clear specific user's caches
            try:
                # Pattern: field_access:*:*:*:{user}
                keys = frappe.cache().get_keys(f"*:{user}")
                for key in keys:
                    if key.startswith('field_access:'):
                        frappe.cache().delete_value(key)
            except Exception:
                pass

            # Clear user roles cache
            frappe.cache().delete_value(f"field_access:user_roles:{user}")

            frappe.log(f"Access Control: Cleared cache for user {user}")
        else:
            # Clear all field access caches
            clear_all_cache()

    except Exception as e:
        frappe.log_error(
            title="Access Control: User Cache Clear Failed",
            message=f"Error clearing user cache: {str(e)}"
        )


def clear_all_cache():
    """
    Clear all Field Access Control caches.

    Use with caution - clears ALL caches and may impact performance
    temporarily as caches are rebuilt.
    """
    try:
        # Try to get all field access cache keys
        try:
            keys = frappe.cache().get_keys("field_access:*")
            for key in keys:
                frappe.cache().delete_value(key)
        except Exception:
            # If get_keys fails, clear known cache patterns
            # This is a fallback for Redis versions without SCAN support
            pass

        frappe.log("Access Control: Cleared all caches")

    except Exception as e:
        frappe.log_error(
            title="Access Control: All Cache Clear Failed",
            message=f"Error clearing all caches: {str(e)}"
        )


# ============================================================================
# DOCTYPE HELPERS - For Field Selection UI
# ============================================================================

@frappe.whitelist()
def get_doctype_fields_for_select(doctype):
    """
    Get doctype fields for selection in Field Configuration Detail.

    Used by field selection UI to populate field options.

    Args:
        doctype (str): DocType name

    Returns:
        list: List of field dicts with fieldname and label
    """
    try:
        meta = frappe.get_meta(doctype)
        fields = []

        for field in meta.fields:
            # Skip system fields
            if field.fieldname in ['name', 'owner', 'creation', 'modified', 'modified_by', 'docstatus']:
                continue

            # Skip child tables (handled separately)
            if field.fieldtype == 'Table':
                continue

            fields.append({
                'fieldname': field.fieldname,
                'label': field.label or field.fieldname,
                'fieldtype': field.fieldtype
            })

        return fields

    except Exception as e:
        frappe.log_error(
            title="Access Control: Get Fields Failed",
            message=f"Error getting fields for {doctype}: {str(e)}"
        )
        return []


@frappe.whitelist()
def get_child_tables_for_select(doctype):
    """
    Get child table fields for selection in Child Table Button Configuration.

    Args:
        doctype (str): DocType name

    Returns:
        list: List of child table field dicts
    """
    try:
        meta = frappe.get_meta(doctype)
        tables = []

        for field in meta.fields:
            if field.fieldtype == 'Table':
                tables.append({
                    'fieldname': field.fieldname,
                    'label': field.label or field.fieldname,
                    'options': field.options  # Child DocType name
                })

        return tables

    except Exception as e:
        frappe.log_error(
            title="Access Control: Get Child Tables Failed",
            message=f"Error getting child tables for {doctype}: {str(e)}"
        )
        return []


# ============================================================================
# TESTING / DEBUGGING
# ============================================================================

@frappe.whitelist()
def test_configuration(config_name, docname=None, user=None):
    """
    Test a Field Access Control configuration.

    Useful for debugging and verifying configurations work as expected.

    Args:
        config_name (str): Field Access Control name
        docname (str, optional): Document name to test
        user (str, optional): User email to test (defaults to session user)

    Returns:
        dict: Test results including applied permissions
    """
    try:
        if not user:
            user = frappe.session.user

        # Get configuration
        config = frappe.get_doc("Field Access Control", config_name)

        # Import permission manager functions
        from dev_assistant.access_control.permission_manager import (
            should_apply_to_user,
            should_apply_to_docname,
            calculate_field_permissions,
            get_user_roles
        )

        # Get user roles
        user_roles = get_user_roles(user)

        # Check if applies to user
        applies_to_user = should_apply_to_user(config.as_dict(), user, user_roles)

        # Check if applies to docname
        applies_to_docname = should_apply_to_docname(config.as_dict(), docname)

        # Calculate permissions
        permissions = calculate_field_permissions(
            config.doctype_name,
            docname,
            user
        )

        return {
            'config_name': config_name,
            'doctype': config.doctype_name,
            'user': user,
            'user_roles': user_roles,
            'docname': docname,
            'applies_to_user': applies_to_user,
            'applies_to_docname': applies_to_docname,
            'field_permissions': permissions.get('fields', {}),
            'child_table_permissions': permissions.get('child_tables', {})
        }

    except Exception as e:
        frappe.log_error(
            title="Access Control: Test Configuration Failed",
            message=f"Error testing configuration {config_name}: {str(e)}"
        )
        return {
            'error': str(e)
        }


@frappe.whitelist()
def get_cache_stats():
    """
    Get cache statistics for monitoring.

    Returns:
        dict: Cache statistics including key counts by type
    """
    try:
        stats = {
            'total_keys': 0,
            'keys_by_type': {}
        }

        try:
            keys = frappe.cache().get_keys("field_access:*")
            stats['total_keys'] = len(keys)

            # Categorize keys by type
            for key in keys:
                parts = key.split(':')
                if len(parts) >= 2:
                    key_type = parts[1]
                    if key_type not in stats['keys_by_type']:
                        stats['keys_by_type'][key_type] = 0
                    stats['keys_by_type'][key_type] += 1
        except Exception:
            # get_keys not supported
            stats['note'] = 'Cache key scanning not supported in this Redis version'

        return stats

    except Exception as e:
        frappe.log_error(
            title="Access Control: Get Cache Stats Failed",
            message=f"Error getting cache stats: {str(e)}"
        )
        return {
            'error': str(e)
        }


@frappe.whitelist()
def debug_field_permissions(doctype, docname=None, user=None):
    """
    Debug helper to see calculated field permissions.

    Args:
        doctype (str): DocType name
        docname (str, optional): Document name
        user (str, optional): User email

    Returns:
        dict: Debug information
    """
    try:
        if not user:
            user = frappe.session.user

        from dev_assistant.access_control.permission_manager import (
            calculate_field_permissions,
            get_field_access_configurations,
            get_user_roles
        )

        # Get user roles
        user_roles = get_user_roles(user)

        # Get configurations
        configs = get_field_access_configurations(doctype, use_cache=False)

        # Calculate permissions
        permissions = calculate_field_permissions(doctype, docname, user)

        return {
            'doctype': doctype,
            'docname': docname,
            'user': user,
            'user_roles': user_roles,
            'configurations_count': len(configs),
            'configurations': [c.get('name') for c in configs],
            'field_permissions': permissions.get('fields', {}),
            'child_table_permissions': permissions.get('child_tables', {})
        }

    except Exception as e:
        frappe.log_error(
            title="Access Control: Debug Failed",
            message=f"Error debugging permissions: {str(e)}"
        )
        return {
            'error': str(e)
        }


# ============================================================================
# PATCH STATUS CHECK
# ============================================================================

@frappe.whitelist()
def check_patch_status():
    """
    Check if access control patches are applied.

    Returns:
        dict: Patch status information
    """
    try:
        from dev_assistant.access_control.monkey_patches import is_patched

        return {
            'patches_applied': is_patched(),
            'status': 'Active' if is_patched() else 'Inactive'
        }

    except Exception as e:
        return {
            'error': str(e),
            'status': 'Error'
        }


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    # Cache management
    'clear_configuration_cache',
    'clear_parent_cache',
    'clear_user_cache',
    'clear_all_cache',
    # Field helpers
    'get_doctype_fields_for_select',
    'get_child_tables_for_select',
    # Testing/debugging
    'test_configuration',
    'get_cache_stats',
    'debug_field_permissions',
    'check_patch_status'
]
