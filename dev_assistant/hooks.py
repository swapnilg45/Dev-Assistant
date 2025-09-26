app_name = "dev_assistant"
app_title = "Dev Assistant"
app_publisher = "Swapnil"
app_description = "This is a custom app."
app_email = "swapnil.ghadi066@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "dev_assistant",
		"logo": "/assets/dev_assistant/images/logo.png",
		"title": "Universal Data Sync",
		"route": "/universal-sync",
		"has_permission": "dev_assistant.api.permission.has_app_permission"
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/dev_assistant/css/dev_assistant.css"
app_include_js = "/assets/dev_assistant/js/field_access_control.js"

# Vue.js Frontend Assets - Only loaded on specific pages, not globally

# include js, css files in header of web template
# web_include_css = "/assets/dev_assistant/css/dev_assistant.css"
# web_include_js = "/assets/dev_assistant/js/dev_assistant.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "dev_assistant/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Role": "public/js/role_copy_permissions.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "dev_assistant/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Website
# --------

website_route_rules = [
	{"from_route": "/universal-sync", "to_route": "universal-sync"},
	{"from_route": "/universal-sync/<path:path>", "to_route": "universal-sync"},
	{"from_route": "/sync", "to_route": "universal-sync"},
	{"from_route": "/dev-assistant", "to_route": "universal-sync"},
]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "dev_assistant.utils.jinja_methods",
# 	"filters": "dev_assistant.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "dev_assistant.install.before_install"
after_install = "dev_assistant.dev_assistant.universal_sync.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "dev_assistant.uninstall.before_uninstall"
# after_uninstall = "dev_assistant.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "dev_assistant.utils.before_app_install"
# after_app_install = "dev_assistant.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "dev_assistant.utils.before_app_uninstall"
# after_app_uninstall = "dev_assistant.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "dev_assistant.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"*": {
		"validate": "dev_assistant.dev_assistant.mandatory_field_validation.validator.validate_mandatory_fields",
		"on_update": "dev_assistant.dev_assistant.universal_sync.sync_engine.sync_on_document_event",
		"on_submit": "dev_assistant.dev_assistant.universal_sync.sync_engine.sync_on_document_event",
		"on_update_after_submit": "dev_assistant.dev_assistant.universal_sync.sync_engine.sync_on_document_event"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": [
		"dev_assistant.dev_assistant.universal_sync.sync_engine.scheduled_sync"
	],
	"daily": [
		"dev_assistant.dev_assistant.universal_sync.sync_engine.daily_sync_cleanup"
	]
}

# Testing
# -------

# before_tests = "dev_assistant.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "dev_assistant.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "dev_assistant.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["dev_assistant.utils.before_request"]
# after_request = ["dev_assistant.utils.after_request"]

# Job Events
# ----------
# before_job = ["dev_assistant.utils.before_job"]
# after_job = ["dev_assistant.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"dev_assistant.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

