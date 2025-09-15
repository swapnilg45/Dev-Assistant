import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, flt
import json


class PermissionQueryConfiguration(Document):
	def validate(self):
		"""Validate the permission query configuration"""
		self.validate_filter_method()
		self.validate_priority()

	def validate_filter_method(self):
		"""Validate based on selected filter method"""
		if self.filter_method == "Simple Field Match":
			if not self.field_filters:
				frappe.throw(_("Field Filter Conditions are required for Simple Field Match method"))

		elif self.filter_method == "Custom Python Query":
			if not self.custom_query:
				frappe.throw(_("Custom Query Code is required for Custom Python Query method"))

		elif self.filter_method == "SQL Query":
			if not self.sql_query:
				frappe.throw(_("SQL WHERE Clause is required for SQL Query method"))

	def validate_priority(self):
		"""Ensure priority is set"""
		if not self.priority:
			self.priority = 1

	@frappe.whitelist()
	def get_permission_query_conditions(self, user=None):
		"""Generate query conditions based on configuration"""
		if not user:
			user = frappe.session.user

		# Check if user is in exceptions
		if self.is_user_exception(user):
			return {}

		try:
			if self.filter_method == "Simple Field Match":
				return self.get_simple_field_conditions()
			elif self.filter_method == "Custom Python Query":
				return self.get_custom_query_conditions(user)
			elif self.filter_method == "SQL Query":
				return self.get_sql_query_conditions(user)
		except Exception as e:
			frappe.log_error(f"Error in permission query for {self.name}: {str(e)}")
			# Return empty conditions on error to avoid blocking access
			return {}

		return {}

	def get_simple_field_conditions(self):
		"""Generate conditions from field filters"""
		conditions = {}

		for field_filter in self.field_filters:
			filter_doc = frappe.get_doc("Permission Query Field Filter", field_filter.name)
			field_name = filter_doc.field_name

			try:
				condition = filter_doc.get_filter_condition()
				# Convert list format [field, operator, value] to dict format
				if isinstance(condition, list) and len(condition) == 3:
					field, operator, value = condition
					if operator == "=":
						conditions[field] = value
					else:
						# For complex operators, we'll handle them in get_permission_query_conditions_list
						pass
			except Exception as e:
				frappe.log_error(f"Error processing field filter {field_filter.name}: {str(e)}")
				continue

		return conditions

	def get_simple_field_conditions_list(self):
		"""Generate conditions as list for complex operators"""
		conditions = []

		for field_filter in self.field_filters:
			filter_doc = frappe.get_doc("Permission Query Field Filter", field_filter.name)

			try:
				condition = filter_doc.get_filter_condition()
				if isinstance(condition, list) and len(condition) == 3:
					conditions.append(condition)
			except Exception as e:
				frappe.log_error(f"Error processing field filter {field_filter.name}: {str(e)}")
				continue

		return conditions

	def get_custom_query_conditions(self, user):
		"""Execute custom Python code to get conditions"""
		if not self.custom_query:
			return {}

		# Prepare safe execution context
		context = {
			'frappe': frappe,
			'user': user,
			'doc': self,
			'_': _,
		}

		try:
			# Execute the custom query code
			exec(self.custom_query, context)

			# The custom code should define a 'result' variable or return statement
			if 'result' in context:
				result = context['result']
			else:
				# Try to evaluate the code as an expression
				result = eval(self.custom_query, context)

			# Update last applied timestamp
			self.db_set('last_applied', frappe.utils.now(), update_modified=False)

			return result if result else {}

		except Exception as e:
			frappe.log_error(f"Error executing custom query in {self.name}: {str(e)}")
			return {}

	def get_sql_query_conditions(self, user):
		"""Generate SQL WHERE clause conditions"""
		if not self.sql_query:
			return {}

		try:
			# Replace placeholders in SQL query
			sql_query = self.sql_query.format(
				user=user,
				company=frappe.defaults.get_user_default("Company") or "",
				today=frappe.utils.today(),
				now=frappe.utils.now()
			)

			# Update last applied timestamp
			self.db_set('last_applied', frappe.utils.now(), update_modified=False)

			# Return as raw SQL condition
			return {"__sql": sql_query}

		except Exception as e:
			frappe.log_error(f"Error processing SQL query in {self.name}: {str(e)}")
			return {}

	def is_user_exception(self, user):
		"""Check if user is in exceptions list"""
		if not self.enable_user_exceptions or not self.user_exceptions:
			return False

		exception_users = [row.user for row in self.user_exceptions]
		return user in exception_users

	@frappe.whitelist()
	def test_query(self):
		"""Test the permission query configuration"""
		try:
			conditions = self.get_permission_query_conditions()

			# Try to run a sample query
			doctype = self.doctype_name
			sample_query = frappe.get_list(
				doctype,
				filters=conditions,
				limit=1,
				as_list=True
			)

			return {
				"success": True,
				"conditions": conditions,
				"message": f"Query test successful. Conditions: {conditions}"
			}

		except Exception as e:
			return {
				"success": False,
				"error": str(e),
				"message": f"Query test failed: {str(e)}"
			}


@frappe.whitelist()
def get_active_configurations(doctype, permission_type="Read", user=None):
	"""Get all active permission query configurations for a doctype and user"""
	if not user:
		user = frappe.session.user

	# Get user roles
	user_roles = frappe.get_roles(user)

	# Get active configurations for this doctype and user's roles
	configurations = frappe.get_all(
		"Permission Query Configuration",
		filters={
			"doctype_name": doctype,
			"permission_type": permission_type,
			"is_active": 1,
			"role": ["in", user_roles]
		},
		fields=["name", "role", "priority", "filter_method"],
		order_by="priority DESC, creation DESC"
	)

	results = []
	for config_data in configurations:
		try:
			config_doc = frappe.get_doc("Permission Query Configuration", config_data.name)

			# Check if user is exception
			if config_doc.is_user_exception(user):
				continue

			conditions = config_doc.get_permission_query_conditions(user)
			if conditions:
				results.append({
					"name": config_data.name,
					"role": config_data.role,
					"priority": config_data.priority,
					"conditions": conditions,
					"filter_method": config_data.filter_method
				})
		except Exception as e:
			frappe.log_error(f"Error processing config {config_data.name}: {str(e)}")
			continue

	return results


@frappe.whitelist()
def apply_permission_query(doctype, permission_type="Read", user=None):
	"""Apply permission query configurations to get final conditions"""
	configurations = get_active_configurations(doctype, permission_type, user)

	if not configurations:
		return {}

	# Take the highest priority configuration
	# In the future, we could merge multiple configurations
	highest_priority_config = configurations[0]

	return highest_priority_config["conditions"]