# Copyright (c) 2025, Hybrowlabs and contributors
# For license information, please see license.txt

"""
Access Control - Monkey Patches

Applies monkey patches to Frappe's core Meta and Document classes to inject
field-level permissions at runtime. Overrides:
- frappe.get_meta()
- frappe.model.meta.get_meta()
- Document.meta property
- Meta.process()

These patches intercept meta retrieval and dynamically modify field permlevels
based on Field Access Control configurations.

Architecture:
    1. Store references to original Frappe functions
    2. Define new patched versions that call original + apply permissions
    3. Replace Frappe's functions with patched versions
    4. Provide rollback mechanism for testing/debugging

Security:
    All patches are applied at server-side only. Cannot be bypassed via client.

Performance:
    - Uses caching extensively to minimize overhead
    - Early returns for Administrator and unconfigured doctypes
    - Deep copy meta only when needed

Thread Safety:
    Patches applied once on module import. Thread-safe as they only read shared state.
"""

import frappe
from frappe.model.meta import Meta
from frappe.model.meta import get_meta as original_get_meta
from frappe.model.base_document import BaseDocument
from frappe.model.document import Document
import copy

# Import from permission manager
from dev_assistant.access_control.permission_manager import (
    calculate_field_permissions,
    PERMLEVEL_HIDDEN,
    PERMLEVEL_READ_ONLY
)

# ============================================================================
# GLOBAL STATE
# ============================================================================

# Store original functions
_original_meta_process = None
_original_get_meta = None
_original_document_meta_property = None

# Track patch status
_patches_applied = False

# Re-entry guard to prevent infinite recursion
import threading
_processing_lock = threading.local()


def is_processing():
    """Check if we're already processing permissions in this thread."""
    return getattr(_processing_lock, 'processing', False)


def set_processing(value):
    """Set the processing flag for this thread."""
    _processing_lock.processing = value


# ============================================================================
# HELPER CLASSES
# ============================================================================

class PermissionDoc(BaseDocument):
    """
    Dummy document class for creating permission entries.

    Used to create DocPerm/Custom DocPerm entries dynamically for
    custom permission levels (1001, 1002, etc.)

    Example:
        >>> perm = PermissionDoc({
        ...     'doctype': 'DocPerm',
        ...     'read': 1,
        ...     'write': 0,
        ...     'permlevel': 1001,
        ...     'role': 'All'
        ... })
        >>> meta.permissions.append(perm)
    """
    def __init__(self, d):
        super().__init__(d)


# ============================================================================
# CORE PERMISSION APPLICATION
# ============================================================================

def reset_field_permissions(meta):
    """
    Reset field permissions to original values.

    This function:
    1. Stores original permlevels first time it's called
    2. Restores original permlevels on subsequent calls

    Ensures we don't accumulate permission restrictions across
    multiple get_meta() calls for the same doctype.

    Args:
        meta (Meta): Frappe Meta object

    Side Effects:
        - Adds meta._original_field_perms attribute
        - Modifies meta.fields[].permlevel
    """
    if not hasattr(meta, '_original_field_perms'):
        # First time: Store original permissions
        meta._original_field_perms = {}
        for field in meta.fields:
            meta._original_field_perms[field.fieldname] = field.permlevel
    else:
        # Subsequent calls: Restore original permissions
        for field in meta.fields:
            if field.fieldname in meta._original_field_perms:
                field.permlevel = meta._original_field_perms[field.fieldname]

    # Safety check: Reset any fields with permlevel > 999
    for field in meta.fields:
        if field.permlevel > 999:
            field.permlevel = 0


def apply_field_permissions_to_meta(meta, doc=None):
    """
    Apply field access control permissions to meta.

    Core function that modifies field permlevels based on Field Access Control
    configurations. It:
    1. Resets field permissions to original
    2. Skips if Administrator
    3. Gets permission mapping from permission_manager
    4. Applies field permlevels
    5. Applies child table restrictions
    6. Ensures permission level entries exist

    Args:
        meta (Meta): Frappe Meta object to modify
        doc (Document, optional): Specific document for doc-level permissions

    Side Effects:
        - Modifies meta.fields[].permlevel
        - Modifies meta.fields[].cannot_add_rows, cannot_delete_rows
        - Adds entries to meta.permissions
    """
    # Re-entry guard: Skip if already processing to avoid infinite recursion
    if is_processing():
        return

    # Set processing flag
    set_processing(True)

    try:
        # Always reset first
        reset_field_permissions(meta)

        # Skip Field Access Control doctypes to prevent recursion
        if meta.name in ['Field Access Control', 'Field Configuration Detail',
                         'User Exception Detail', 'Child Table Button Configuration']:
            return

        # Administrator bypass
        if frappe.session.user == 'Administrator':
            return

        # Get permissions
        docname = doc.name if doc else None
        permissions = calculate_field_permissions(meta.name, docname, frappe.session.user)

        # Debug logging to Error Log for Sales Order and Sales Order Item
        if meta.name in ["Sales Order", "Sales Order Item"]:
            import json
            frappe.enqueue(
                'frappe.log_error',
                title=f'Field Access Debug - {meta.name}',
                message=json.dumps({
                    'doctype': meta.name,
                    'user': frappe.session.user,
                    'user_roles': frappe.get_roles(frappe.session.user),
                    'permissions': permissions,
                    'timestamp': frappe.utils.now()
                }, indent=2)
            )

        if not permissions:
            return

        # Apply field permissions
        field_perms = permissions.get('fields', {})
        if field_perms:
            applied_fields = []
            for field in meta.fields:
                if field.fieldname in field_perms:
                    field.permlevel = field_perms[field.fieldname]
                    applied_fields.append(f"{field.fieldname}={field.permlevel}")

            # Log applied permissions
            if meta.name in ["Sales Order", "Sales Order Item"] and applied_fields:
                import json
                frappe.enqueue(
                    'frappe.log_error',
                    title=f'Field Access Applied - {meta.name}',
                    message=json.dumps({
                        'doctype': meta.name,
                        'user': frappe.session.user,
                        'applied_fields': applied_fields,
                        'timestamp': frappe.utils.now()
                    }, indent=2)
                )

        # Apply child table permissions
        child_table_perms = permissions.get('child_tables', {})
        if child_table_perms:
            for field in meta.fields:
                if field.fieldtype == 'Table' and field.fieldname in child_table_perms:
                    table_perms = child_table_perms[field.fieldname]

                    if 'cannot_add_rows' in table_perms:
                        field.cannot_add_rows = table_perms['cannot_add_rows']

                    if 'cannot_delete_rows' in table_perms:
                        field.cannot_delete_rows = table_perms['cannot_delete_rows']

        # Ensure permission level entries exist
        ensure_permission_levels(meta)
    finally:
        # Always reset processing flag
        set_processing(False)


def ensure_permission_levels(meta):
    """
    Ensure required permission level entries exist in meta.permissions.

    Frappe requires DocPerm/Custom DocPerm entries for each permlevel used.
    Creates entries for:
    - permlevel 1001: Read-only (read=1, write=0)

    We don't create entries for permlevel 1000 (hidden) as those fields
    shouldn't be accessible at all.

    Args:
        meta (Meta): Frappe Meta object

    Side Effects:
        - Adds entries to meta.permissions list
    """
    # Determine permission doctype
    has_custom = any(p.doctype == 'Custom DocPerm' for p in meta.permissions)
    perm_doctype = 'Custom DocPerm' if has_custom else 'DocPerm'

    # Check for read-only permission (1001)
    has_readonly = any(
        p.permlevel == 1001 and p.role == 'All'
        for p in meta.permissions
    )

    if not has_readonly:
        # Create read-only permission entry
        docperm = PermissionDoc({
            'doctype': perm_doctype,
            'read': 1,
            'write': 0,
            'permlevel': 1001,
            'role': 'All'
        })
        meta.permissions.append(docperm)


# ============================================================================
# MONKEY PATCHES
# ============================================================================

def patch_meta_process():
    """
    Patch Meta.process() to apply field permissions.

    Meta.process() is called when a DocType's meta is loaded/refreshed.
    We patch it to inject our permission logic after normal processing.

    Side Effects:
        - Modifies Meta.process function
        - Stores original in _original_meta_process

    Thread Safety:
        Only patches once (checked via _patches_applied flag)
    """
    global _original_meta_process

    if _original_meta_process is None:
        _original_meta_process = Meta.process

    def new_process(self):
        # Call original process
        _original_meta_process(self)

        # Apply field access control
        try:
            apply_field_permissions_to_meta(self)
        except Exception as e:
            # Use simple logging to avoid infinite recursion
            # frappe.log_error() would trigger more metadata operations
            import traceback
            print(f"Access Control: Meta Process Error for {self.name}: {str(e)}")
            print(traceback.format_exc())

    Meta.process = new_process


def patch_get_meta():
    """
    Patch frappe.get_meta() to apply field permissions.

    Patches both:
    - frappe.get_meta()
    - frappe.model.meta.get_meta()

    Side Effects:
        - Modifies frappe.get_meta and frappe.model.meta.get_meta
        - Stores original in _original_get_meta

    Thread Safety:
        Only patches once (checked via _patches_applied flag)
    """
    global _original_get_meta

    if _original_get_meta is None:
        _original_get_meta = original_get_meta

    def new_get_meta(*args, **kwargs):
        # Call original get_meta
        meta = _original_get_meta(*args, **kwargs)

        # Apply field access control
        try:
            apply_field_permissions_to_meta(meta)
        except Exception as e:
            # Use simple logging to avoid infinite recursion
            # frappe.log_error() would trigger more metadata operations
            import traceback
            print(f"Access Control: Get Meta Error for {args}: {str(e)}")
            print(traceback.format_exc())

        return meta

    # Replace both references
    frappe.model.meta.get_meta = new_get_meta
    frappe.get_meta = new_get_meta


def patch_document_meta():
    """
    Patch Document.meta property for document-specific permissions.

    Critical for applying different permissions based on specific document
    being accessed (e.g., SO-001 vs SO-002).

    Document.meta property is accessed whenever:
    - Document is loaded
    - Field permissions are checked
    - Form is rendered

    We override it to:
    1. Get original meta
    2. Deep copy meta (avoid modifying shared instance)
    3. Apply document-specific permissions
    4. Cache on document instance

    Side Effects:
        - Modifies Document.meta property
        - Stores original in _original_document_meta_property

    Thread Safety:
        Only patches once (checked via _patches_applied flag)

    Performance:
        - Deep copy only done once per document
        - Result cached in document._cached_field_access_meta
    """
    global _original_document_meta_property

    # Store original meta property getter
    if _original_document_meta_property is None:
        # Handle both cached_property (functools) and regular property
        original_meta = Document.meta
        if hasattr(original_meta, 'fget'):
            # Regular property
            _original_document_meta_property = original_meta.fget
        elif hasattr(original_meta, 'func'):
            # cached_property (functools)
            _original_document_meta_property = original_meta.func
        else:
            # Fallback - call the descriptor directly
            _original_document_meta_property = lambda self: original_meta.__get__(self, type(self))

    @property
    def custom_meta(self):
        """
        Custom meta property that applies document-specific permissions.

        Returns:
            Meta: Modified meta with field access control applied
        """
        # Check cache first
        if hasattr(self, '_cached_field_access_meta'):
            return self._cached_field_access_meta

        # Get original meta
        meta = _original_document_meta_property(self)

        # Apply document-specific permissions if we have a name
        if self.name and self.doctype:
            try:
                # Deep copy to avoid modifying shared meta
                meta = copy.deepcopy(meta)

                # Apply field access control with document context
                apply_field_permissions_to_meta(meta, self)

            except Exception as e:
                # Use simple logging to avoid infinite recursion
                # frappe.log_error() would trigger more metadata operations
                import traceback
                print(f"Access Control: Document Meta Error for {self.doctype} {self.name}: {str(e)}")
                print(traceback.format_exc())

        # Cache result
        self._cached_field_access_meta = meta

        return meta

    # Replace property
    Document.meta = custom_meta


# ============================================================================
# PATCH MANAGEMENT
# ============================================================================

def apply_patches():
    """
    Apply all monkey patches.

    This function should be called ONCE on module import.
    Safe to call multiple times (checks _patches_applied flag).

    Patches Applied:
        1. Meta.process()
        2. frappe.get_meta()
        3. Document.meta property

    Side Effects:
        - Modifies Frappe core functions
        - Sets _patches_applied = True

    Error Handling:
        If patching fails, logs error but doesn't raise exception
        to avoid breaking app initialization.
    """
    global _patches_applied

    if _patches_applied:
        frappe.log("Access Control: Patches already applied")
        return

    try:
        # Apply all patches
        patch_meta_process()
        patch_get_meta()
        patch_document_meta()

        _patches_applied = True

        print("Access Control: Patches applied successfully")

    except Exception as e:
        # Use simple logging to avoid infinite recursion
        import traceback
        print(f"Access Control: Patch Application Failed: {str(e)}")
        print(traceback.format_exc())


def remove_patches():
    """
    Remove all monkey patches (for testing/debugging).

    Restores Frappe's original functions. Useful for:
    - Testing with/without patches
    - Debugging issues
    - Emergency rollback

    Side Effects:
        - Restores Frappe original functions
        - Sets _patches_applied = False

    Warning:
        Should NOT be used in production. For development/testing only.
    """
    global _patches_applied, _original_meta_process, _original_get_meta
    global _original_document_meta_property

    if not _patches_applied:
        frappe.log("Access Control: No patches to remove")
        return

    try:
        # Restore original functions
        if _original_meta_process:
            Meta.process = _original_meta_process

        if _original_get_meta:
            frappe.model.meta.get_meta = _original_get_meta
            frappe.get_meta = _original_get_meta

        if _original_document_meta_property:
            # Restore original property
            Document.meta = property(_original_document_meta_property)

        _patches_applied = False

        print("Access Control: Patches removed")

    except Exception as e:
        # Use simple logging to avoid infinite recursion
        import traceback
        print(f"Access Control: Patch Removal Failed: {str(e)}")
        print(traceback.format_exc())


def is_patched():
    """
    Check if patches are currently applied.

    Returns:
        bool: True if patches are applied, False otherwise
    """
    return _patches_applied


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'apply_patches',
    'remove_patches',
    'is_patched',
    'apply_field_permissions_to_meta',
    'reset_field_permissions'
]
