import frappe

def get_context(context):
	"""Context for the Dev Assistant main application page"""

	# Basic permission check - allow access to System Manager role
	if not frappe.has_permission("User", "read"):
		frappe.throw("You don't have permission to access Dev Assistant", frappe.PermissionError)

	# Get user info
	user = frappe.get_doc("User", frappe.session.user)

	# Get app features status
	features_status = {
		"field_access_control": True,  # Always available
		"role_management": True,       # Always available
		"universal_sync": True,        # Universal sync feature
		"dashboard": True              # Dashboard feature
	}

	context.update({
		"title": "Dev Assistant - Developer Productivity Platform",
		"app_name": "Dev Assistant",
		"app_description": "Enterprise-grade developer productivity tools for Frappe/ERPNext systems",
		"user": {
			"name": user.name,
			"full_name": user.full_name,
			"email": user.email,
			"user_image": user.user_image,
			"roles": [role.role for role in frappe.get_all("Has Role", filters={"parent": user.name}, fields=["role"])]
		},
		"features": features_status,
		"csrf_token": frappe.sessions.get_csrf_token(),
		"base_url": frappe.utils.get_url(),
		"app_version": frappe.get_attr("dev_assistant.__version__") or "0.0.1",
		"frontend_url": "/dev-assistant"
	})

	return context