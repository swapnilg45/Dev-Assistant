import frappe
from frappe import _
import json


def get_permission_query_conditions(user=None):
	"""
	Global permission query conditions hook
	This function is called by Frappe for every DocType to get permission conditions
	"""
	if not user:
		user = frappe.session.user

	# Skip for system users and during installation/migration
	if (
		user in ["Administrator", "Guest"]
		or frappe.flags.in_install
		or frappe.flags.in_migrate
		or frappe.flags.in_patch
	):
		return ""

	# Get the current doctype from the request context
	doctype = frappe.local.form_dict.get("doctype") or getattr(frappe.local, "doctype", None)

	if not doctype:
		return ""

	try:
		# Get permission query configurations for this doctype
		from dev_assistant.dev_assistant.doctype.permission_query_configuration.permission_query_configuration import apply_permission_query

		conditions = apply_permission_query(doctype, "Read", user)

		if not conditions:
			return ""

		# Convert conditions to SQL WHERE clause
		sql_conditions = build_sql_conditions(conditions, doctype)

		return sql_conditions

	except Exception as e:
		frappe.log_error(f"Error in permission query conditions for {doctype}: {str(e)}")
		# Return empty string to avoid blocking access
		return ""


def has_permission(doc, user=None, permission_type="read"):
	"""
	Global has_permission hook
	This function is called by Frappe to check if user has permission on a specific document
	"""
	if not user:
		user = frappe.session.user

	# Skip for system users and during installation/migration
	if (
		user in ["Administrator", "Guest"]
		or frappe.flags.in_install
		or frappe.flags.in_migrate
		or frappe.flags.in_patch
	):
		return True

	# If no doc provided, allow (will be handled by permission_query_conditions)
	if not doc:
		return True

	try:
		doctype = doc.doctype if hasattr(doc, 'doctype') else type(doc).__name__

		# Get permission query configurations for this doctype
		from dev_assistant.dev_assistant.doctype.permission_query_configuration.permission_query_configuration import get_active_configurations

		permission_type_map = {
			"read": "Read",
			"write": "Write",
			"create": "Create",
			"delete": "Delete",
			"print": "Print",
			"email": "Email",
			"report": "Report",
			"export": "Export",
			"import": "Import"
		}

		mapped_permission = permission_type_map.get(permission_type.lower(), "Read")
		configurations = get_active_configurations(doctype, mapped_permission, user)

		if not configurations:
			# No specific permission query configs found, use default Frappe permission
			return True

		# Check each configuration
		for config in configurations:
			conditions = config.get("conditions", {})

			if not conditions:
				continue

			# Check if document matches the conditions
			if check_document_conditions(doc, conditions):
				# Document matches conditions, permission granted
				return True

		# If we reach here, document doesn't match any permission conditions
		return False

	except Exception as e:
		frappe.log_error(f"Error in has_permission for {doc}: {str(e)}")
		# Return True to avoid blocking access on errors
		return True


def build_sql_conditions(conditions, doctype):
	"""Convert permission conditions to SQL WHERE clause"""
	if not conditions:
		return ""

	sql_parts = []

	# Handle raw SQL conditions
	if "__sql" in conditions:
		return conditions["__sql"]

	# Handle regular field conditions
	for field, value in conditions.items():
		if field.startswith("__"):
			continue

		if isinstance(value, str):
			sql_parts.append(f"`tab{doctype}`.`{field}` = {frappe.db.escape(value)}")
		elif isinstance(value, list):
			escaped_values = [frappe.db.escape(str(v)) for v in value]
			sql_parts.append(f"`tab{doctype}`.`{field}` IN ({','.join(escaped_values)})")
		elif value is None:
			sql_parts.append(f"`tab{doctype}`.`{field}` IS NULL")
		else:
			sql_parts.append(f"`tab{doctype}`.`{field}` = frappe.db.escape(str(value))")

	return " AND ".join(sql_parts) if sql_parts else ""


def check_document_conditions(doc, conditions):
	"""Check if document matches the given conditions"""
	if not conditions:
		return True

	# Handle raw SQL conditions (cannot check on document level)
	if "__sql" in conditions:
		return True

	# Check each condition
	for field, expected_value in conditions.items():
		if field.startswith("__"):
			continue

		doc_value = getattr(doc, field, None)

		# Handle different comparison types
		if isinstance(expected_value, list):
			if doc_value not in expected_value:
				return False
		elif expected_value != doc_value:
			return False

	return True


@frappe.whitelist()
def test_permission_query(doctype, user=None):
	"""Test function to see what permission queries would be applied"""
	if not user:
		user = frappe.session.user

	try:
		from dev_assistant.dev_assistant.doctype.permission_query_configuration.permission_query_configuration import get_active_configurations

		result = {
			"doctype": doctype,
			"user": user,
			"configurations": []
		}

		for permission_type in ["Read", "Write", "Create", "Delete"]:
			configs = get_active_configurations(doctype, permission_type, user)

			if configs:
				for config in configs:
					conditions = config.get("conditions", {})
					sql_conditions = build_sql_conditions(conditions, doctype)

					result["configurations"].append({
						"permission_type": permission_type,
						"config_name": config.get("name"),
						"role": config.get("role"),
						"priority": config.get("priority"),
						"conditions": conditions,
						"sql_conditions": sql_conditions
					})

		return result

	except Exception as e:
		frappe.throw(f"Error testing permission query: {str(e)}")