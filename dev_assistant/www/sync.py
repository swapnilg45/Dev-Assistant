import frappe

def get_context(context):
	"""Context for the Universal Data Sync page"""

	context.update({
		"title": "Universal Data Sync",
		"description": "Data synchronization system for Frappe/ERPNext"
	})

	return context