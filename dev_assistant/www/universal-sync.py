import frappe

def get_context(context):
	"""Context for Universal Data Sync application"""

	# Check if user is logged in
	if frappe.session.user == 'Guest':
		frappe.throw("Please login to access Universal Data Sync", frappe.AuthenticationError)

	# Get current user info
	user = frappe.get_doc("User", frappe.session.user)

	context.update({
		"title": "Universal Data Sync",
		"user": {
			"name": user.name,
			"full_name": user.full_name,
			"email": user.email,
			"user_image": user.user_image
		},
		"boot": {
			"user": frappe.session.user,
			"user_info": {
				"name": user.name,
				"full_name": user.full_name,
				"email": user.email,
				"user_image": user.user_image
			},
			"csrf_token": frappe.sessions.get_csrf_token()
		}
	})

	return context