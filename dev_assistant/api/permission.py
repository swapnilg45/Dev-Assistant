import frappe

@frappe.whitelist()
def has_app_permission():
	"""Check if user has permission to access Universal Data Sync"""

	# Allow System Manager always
	if "System Manager" in frappe.get_roles():
		return True

	# Check if user has permission for Sync Chain DocType
	if frappe.has_permission("Sync Chain", "read"):
		return True

	# Check if user has specific roles
	allowed_roles = ["Sync Manager", "Data Manager", "Administrator"]
	user_roles = frappe.get_roles()

	if any(role in user_roles for role in allowed_roles):
		return True

	return False