import frappe
from frappe import _
from frappe.permissions import get_all_perms

@frappe.whitelist()
def copy_role_permissions(source_role, target_role, overwrite_existing=False):
    """
    Copy all permissions from source_role to target_role
    
    Args:
        source_role (str): Source role name to copy from
        target_role (str): Target role name to copy to
        overwrite_existing (bool): Whether to overwrite existing permissions in target role
    """
    
    try:
        # Validate that both roles exist
        if not frappe.db.exists("Role", source_role):
            frappe.throw(_("Source role '{0}' does not exist").format(source_role))
            
        if not frappe.db.exists("Role", target_role):
            frappe.throw(_("Target role '{0}' does not exist").format(target_role))
        
        # Get all permissions from source role
        source_permissions = get_all_perms(source_role)
        
        if not source_permissions:
            frappe.msgprint(_("No permissions found in source role '{0}'").format(source_role))
            return
        
        # Get existing permissions in target role (if not overwriting)
        existing_permissions = set()
        if not overwrite_existing:
            existing_permissions = frappe.get_all(
                "Custom DocPerm",
                filters={"role": target_role},
                fields=["parent", "permlevel", "if_owner"],
                as_list=True
            )
            existing_permissions = set([(p[0], p[1], p[2]) for p in existing_permissions])
        
        # Copy permissions
        copied_count = 0
        skipped_count = 0
        
        for perm in source_permissions:
            parent = perm.parent
            permlevel = perm.permlevel
            if_owner = perm.if_owner
            
            # Skip if permission already exists and not overwriting
            if not overwrite_existing and (parent, permlevel, if_owner) in existing_permissions:
                skipped_count += 1
                continue
            
            # Check if permission already exists in target role
            existing = frappe.db.exists("Custom DocPerm", {
                "role": target_role,
                "parent": parent,
                "permlevel": permlevel,
                "if_owner": if_owner
            })
            
            if existing and not overwrite_existing:
                skipped_count += 1
                continue
            
            # Create new permission
            if existing:
                # Update existing permission
                frappe.db.set_value("Custom DocPerm", existing, {
                    "role": target_role,
                    "parent": parent,
                    "permlevel": permlevel,
                    "if_owner": if_owner,
                    "read": perm.read,
                    "write": perm.write,
                    "create": perm.create,
                    "delete": perm.delete,
                    "submit": perm.submit,
                    "cancel": perm.cancel,
                    "amend": perm.amend,
                    "print": perm.print,
                    "email": perm.email,
                    "report": perm.report,
                    "import": perm.import_doc,
                    "export": perm.export,
                    "share": perm.share
                })
            else:
                # Create new permission
                new_permission = frappe.get_doc({
                    "doctype": "Custom DocPerm",
                    "role": target_role,
                    "parent": parent,
                    "permlevel": permlevel,
                    "if_owner": if_owner,
                    "read": perm.read,
                    "write": perm.write,
                    "create": perm.create,
                    "delete": perm.delete,
                    "submit": perm.submit,
                    "cancel": perm.cancel,
                    "amend": perm.amend,
                    "print": perm.print,
                    "email": perm.email,
                    "report": perm.report,
                    "import": perm.import_doc,
                    "export": perm.export,
                    "share": perm.share
                })
                new_permission.insert(ignore_permissions=True)
            
            copied_count += 1
        
        # Commit changes
        frappe.db.commit()
        
        # Clear cache
        frappe.clear_cache()
        
        # Show results
        frappe.msgprint(
            _("Successfully copied {0} permissions from '{1}' to '{2}'").format(
                copied_count, source_role, target_role
            )
        )
        
        if skipped_count > 0:
            frappe.msgprint(_("Skipped {0} existing permissions").format(skipped_count))
            
        return {
            "copied_count": copied_count,
            "skipped_count": skipped_count,
            "success": True
        }
            
    except Exception as e:
        frappe.log_error(f"Error copying role permissions: {str(e)}")
        frappe.throw(_("Error copying role permissions: {0}").format(str(e)))
