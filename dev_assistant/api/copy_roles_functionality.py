import frappe
import requests
import json
from frappe import _
from frappe.permissions import get_all_perms
from urllib.parse import urljoin, urlparse

@frappe.whitelist()
def copy_role_permissions(source_role, target_role, overwrite_existing=False, skip_source_validation=False):
    """
    Copy all permissions from source_role to target_role
    
    Args:
        source_role (str): Source role name to copy from
        target_role (str): Target role name to copy to
        overwrite_existing (bool): Whether to overwrite existing permissions in target role
    """
    
    try:
        # Validate that both roles exist
        if not skip_source_validation and not frappe.db.exists("Role", source_role):
            frappe.throw(_("Source role '{0}' does not exist").format(source_role))

        if not frappe.db.exists("Role", target_role):
            frappe.throw(_("Target role '{0}' does not exist").format(target_role))
        
        # Get all permissions from source role
        if skip_source_validation:
            # For cross-site operations, this function should not be used
            # Use copy_selective_permissions instead which handles remote permissions
            frappe.throw(_("For cross-site operations, please use the selective copy method"))

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
                    "read": perm.read or 0,
                    "write": perm.write or 0,
                    "create": perm.create or 0,
                    "delete": perm.delete or 0,
                    "submit": perm.submit or 0,
                    "cancel": perm.cancel or 0,
                    "amend": perm.amend or 0,
                    "print": perm.print or 0,
                    "email": perm.email or 0,
                    "report": perm.report or 0,
                    "import": perm.import_doc or 0,
                    "export": perm.export or 0,
                    "share": perm.share or 0
                })
            else:
                # Create new permission
                new_permission = frappe.get_doc({
                    "doctype": "Custom DocPerm",
                    "role": target_role,
                    "parent": parent,
                    "permlevel": permlevel,
                    "if_owner": if_owner,
                    "read": perm.read or 0,
                    "write": perm.write or 0,
                    "create": perm.create or 0,
                    "delete": perm.delete or 0,
                    "submit": perm.submit or 0,
                    "cancel": perm.cancel or 0,
                    "amend": perm.amend or 0,
                    "print": perm.print or 0,
                    "email": perm.email or 0,
                    "report": perm.report or 0,
                    "import": perm.import_doc or 0,
                    "export": perm.export or 0,
                    "share": perm.share or 0
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


# NEW: Cross-Site Role Permission Copy Methods

@frappe.whitelist()
def authenticate_remote_site(site_url, username, password):
    """
    Authenticate with remote site and return session token
    """
    try:
        # Normalize URL
        if not site_url.startswith(('http://', 'https://')):
            site_url = f'https://{site_url}'

        parsed = urlparse(site_url)
        if not parsed.netloc:
            return {"success": False, "error": _("Invalid site URL format")}

        site_url = f"{parsed.scheme}://{parsed.netloc}"

        # Authenticate - try both possible endpoints
        session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'DevAssistant-CrossSite/1.0'
        })

        # First try the standard login endpoint
        auth_url = urljoin(site_url, '/api/method/login')
        frappe.logger().info(f"Attempting authentication to: {auth_url}")

        response = session.post(
            auth_url,
            json={'usr': username, 'pwd': password},
            timeout=30,
            verify=False
        )

        # If that fails, try alternative endpoint
        if response.status_code != 200:
            auth_url = urljoin(site_url, '/api/method/frappe.auth.login')
            frappe.logger().info(f"Trying alternative endpoint: {auth_url}")

            response = session.post(
                auth_url,
                json={'usr': username, 'pwd': password},
                timeout=30,
                verify=False
            )

        frappe.logger().info(f"Response status: {response.status_code}")
        frappe.logger().info(f"Response text: {response.text[:500]}")

        if response.status_code == 200:
            try:
                result = response.json()
                frappe.logger().info(f"Login response: {result}")

                # Check different possible success indicators
                if (result.get('message') == 'Logged In' or
                    'sid' in session.cookies or
                    'user_id' in session.cookies or
                    result.get('full_name')):

                    # Convert cookies properly
                    cookies_dict = {}
                    for cookie in session.cookies:
                        cookies_dict[cookie.name] = cookie.value

                    return {
                        "success": True,
                        "session_cookies": cookies_dict,
                        "site_url": site_url,
                        "user": result.get('full_name', result.get('user', username))
                    }
                else:
                    frappe.logger().info(f"Login failed - no success indicators found")
                    return {
                        "success": False,
                        "error": _("Authentication failed. Please check credentials.")
                    }
            except Exception as json_error:
                frappe.logger().error(f"JSON parsing error: {str(json_error)}")
                # If JSON parsing fails but status is 200, try with cookies
                if 'sid' in session.cookies:
                    cookies_dict = {}
                    for cookie in session.cookies:
                        cookies_dict[cookie.name] = cookie.value

                    return {
                        "success": True,
                        "session_cookies": cookies_dict,
                        "site_url": site_url,
                        "user": username
                    }
                return {
                    "success": False,
                    "error": f"Response parsing error: {str(json_error)}"
                }

        frappe.logger().info(f"Authentication failed with status: {response.status_code}")
        return {
            "success": False,
            "error": f"Authentication failed (Status: {response.status_code}). Please check credentials."
        }

    except requests.exceptions.Timeout:
        return {"success": False, "error": _("Connection timeout. Please check site URL.")}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": _("Cannot connect to remote site.")}
    except Exception as e:
        frappe.log_error(f"Remote authentication error: {str(e)}")
        return {"success": False, "error": f"Authentication error: {str(e)}"}


@frappe.whitelist()
def get_remote_roles(site_url, session_cookies):
    """
    Get available roles from remote site
    """
    try:
        # Handle string/dict conversion for session_cookies
        if isinstance(session_cookies, str) and session_cookies:
            session_cookies = json.loads(session_cookies)
        elif not session_cookies:
            session_cookies = None

        session = requests.Session()

        # Set cookies properly
        for name, value in session_cookies.items():
            session.cookies.set(name, value)

        roles_url = urljoin(site_url, '/api/resource/Role')
        response = session.get(
            roles_url,
            params={
                'fields': '["name", "disabled"]',
                'filters': '[["disabled", "=", 0]]',
                'limit_page_length': 1000  # Get all roles, not just 20
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "roles": [role['name'] for role in result.get('data', [])]
            }

        return {"success": False, "error": _("Failed to fetch roles from remote site")}

    except Exception as e:
        frappe.log_error(f"Error fetching remote roles: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_doctype_list():
    """
    Get categorized list of DocTypes for selection
    """
    try:
        # Get all DocTypes with module information
        doctypes = frappe.get_all(
            'DocType',
            fields=['name', 'module', 'custom', 'istable'],
            filters={'istable': 0, 'issingle': 0},
            order_by='name'
        )

        result = {
            'core': [],
            'custom': [],
            'by_module': {}
        }

        for dt in doctypes:
            doctype_info = {
                'name': dt.name,
                'module': dt.module,
                'is_custom': dt.custom
            }

            if dt.custom:
                result['custom'].append(doctype_info)
            else:
                result['core'].append(doctype_info)

            # Group by module
            if dt.module not in result['by_module']:
                result['by_module'][dt.module] = []
            result['by_module'][dt.module].append(dt.name)

        return {
            "success": True,
            "doctypes": result,
            "total_count": len(doctypes)
        }

    except Exception as e:
        frappe.log_error(f"Error getting DocType list: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_remote_role_permissions(site_url, session_cookies, role_name, selected_doctypes=None):
    """
    Get permissions for a specific role from remote site
    """
    try:
        # Handle string/dict conversion for session_cookies
        if isinstance(session_cookies, str) and session_cookies:
            session_cookies = json.loads(session_cookies)
        elif not session_cookies:
            session_cookies = None

        session = requests.Session()

        # Set cookies properly
        for name, value in session_cookies.items():
            session.cookies.set(name, value)

        # Get Custom DocPerm records for the role
        perms_url = urljoin(site_url, '/api/resource/Custom DocPerm')
        filters = json.dumps([['role', '=', role_name]])

        if selected_doctypes:
            selected_doctypes = json.loads(selected_doctypes) if isinstance(selected_doctypes, str) else selected_doctypes
            # Only add doctype filter if selected_doctypes is not empty
            if selected_doctypes:  # Check if list is not empty
                filters = json.dumps([
                    ['role', '=', role_name],
                    ['parent', 'in', selected_doctypes]
                ])

        response = session.get(
            perms_url,
            params={
                'fields': '["*"]',
                'filters': filters,
                'limit_page_length': 1000  # Get all permissions
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "permissions": result.get('data', [])
            }

        return {"success": False, "error": _("Failed to fetch permissions from remote site")}

    except Exception as e:
        frappe.log_error(f"Error fetching remote permissions: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def copy_selective_permissions(source_role, target_role, selected_doctypes, overwrite_existing=False,
                             source_site_url=None, session_cookies=None):
    """
    Copy permissions for selected DocTypes only (local or cross-site)
    """
    try:
        # Convert selected_doctypes from string if needed
        if isinstance(selected_doctypes, str):
            selected_doctypes = json.loads(selected_doctypes)

        if isinstance(session_cookies, str) and session_cookies:
            session_cookies = json.loads(session_cookies)
        elif not session_cookies:
            session_cookies = None

        # Validate target role exists
        if not frappe.db.exists("Role", target_role):
            frappe.throw(_("Target role '{0}' does not exist").format(target_role))

        # For cross-site operations, skip source role validation
        if not (source_site_url and session_cookies):
            # Local operation - validate source role exists
            if not frappe.db.exists("Role", source_role):
                frappe.throw(_("Source role '{0}' does not exist").format(source_role))

        # Get source permissions
        if source_site_url and session_cookies:
            # Cross-site copy
            # If selected_doctypes is empty, get all permissions for the role
            doctypes_to_fetch = selected_doctypes if selected_doctypes else None

            perm_response = get_remote_role_permissions(
                source_site_url, session_cookies, source_role, doctypes_to_fetch
            )
            if not perm_response.get("success"):
                frappe.throw(_("Failed to get remote permissions: {0}").format(perm_response.get("error")))

            source_permissions = perm_response["permissions"]
        else:
            # Local copy
            source_permissions = frappe.get_all(
                "Custom DocPerm",
                filters={
                    "role": source_role,
                    "parent": ["in", selected_doctypes]
                },
                fields=["*"]
            )

        if not source_permissions:
            frappe.msgprint(_("No permissions found for selected DocTypes in source role"))
            return {"success": True, "copied_count": 0, "skipped_count": 0}

        # Copy permissions
        copied_count = 0
        skipped_count = 0

        for perm in source_permissions:
            # Check if permission already exists
            existing = frappe.db.exists("Custom DocPerm", {
                "role": target_role,
                "parent": perm.get("parent"),
                "permlevel": perm.get("permlevel", 0),
                "if_owner": perm.get("if_owner", 0)
            })

            if existing and not overwrite_existing:
                skipped_count += 1
                continue

            if existing:
                # Update existing
                frappe.db.set_value("Custom DocPerm", existing, {
                    "read": perm.get("read", 0),
                    "write": perm.get("write", 0),
                    "create": perm.get("create", 0),
                    "delete": perm.get("delete", 0),
                    "submit": perm.get("submit", 0),
                    "cancel": perm.get("cancel", 0),
                    "amend": perm.get("amend", 0),
                    "print": perm.get("print", 0),
                    "email": perm.get("email", 0),
                    "report": perm.get("report", 0),
                    "import": perm.get("import", 0),
                    "export": perm.get("export", 0),
                    "share": perm.get("share", 0)
                })
            else:
                # Create new
                new_perm = frappe.get_doc({
                    "doctype": "Custom DocPerm",
                    "role": target_role,
                    "parent": perm.get("parent"),
                    "permlevel": perm.get("permlevel", 0),
                    "if_owner": perm.get("if_owner", 0),
                    "read": perm.get("read", 0),
                    "write": perm.get("write", 0),
                    "create": perm.get("create", 0),
                    "delete": perm.get("delete", 0),
                    "submit": perm.get("submit", 0),
                    "cancel": perm.get("cancel", 0),
                    "amend": perm.get("amend", 0),
                    "print": perm.get("print", 0),
                    "email": perm.get("email", 0),
                    "report": perm.get("report", 0),
                    "import": perm.get("import", 0),
                    "export": perm.get("export", 0),
                    "share": perm.get("share", 0)
                })
                new_perm.insert(ignore_permissions=True)

            copied_count += 1

        frappe.db.commit()
        frappe.clear_cache()

        return {
            "success": True,
            "copied_count": copied_count,
            "skipped_count": skipped_count,
            "message": _("Successfully copied {0} permissions for {1} DocTypes").format(
                copied_count, len(selected_doctypes)
            )
        }

    except Exception as e:
        frappe.log_error(f"Error in selective permission copy: {str(e)}")
        frappe.throw(_("Error copying selective permissions: {0}").format(str(e)))
