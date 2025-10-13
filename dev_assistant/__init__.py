__version__ = "0.0.1"


# ============================================================================
# ACCESS CONTROL INITIALIZATION
# ============================================================================

def initialize_access_control():
    """
    Initialize Access Control system by applying monkey patches.

    This function is called automatically when the module is imported.
    It applies patches to Frappe's core functions to enable field-level
    access control.

    Safe to call multiple times - patches check if already applied.
    """
    try:
        from dev_assistant.access_control.monkey_patches import apply_patches
        apply_patches()
    except Exception as e:
        import frappe
        frappe.log_error(
            title="Access Control: Initialization Failed",
            message=f"Failed to initialize Access Control: {str(e)}"
        )


# ============================================================================
# FIXED - Added re-entry guard to prevent infinite recursion
# ============================================================================
# Auto-initialize on module import
initialize_access_control()
