import frappe
from frappe.model.document import Document


class PermissionQueryFieldFilter(Document):
	def validate(self):
		if self.operator in ["is set", "is not set"]:
			self.value = None
			self.value_type = None

		if self.value_type in ["Today", "Now"]:
			self.value = None

	def get_filter_condition(self):
		"""Convert this field filter to a query condition"""
		field = self.field_name
		operator = self.operator

		# Handle special operators
		if operator in ["is set", "is not set"]:
			if operator == "is set":
				return [field, "!=", ""]
			else:
				return [field, "in", ["", None]]

		# Get the comparison value based on value_type
		value = self.get_comparison_value()

		# Handle special operators that need transformation
		if operator == "like":
			value = f"%{value}%"
		elif operator == "not like":
			value = f"%{value}%"
			operator = "not like"

		return [field, operator, value]

	def get_comparison_value(self):
		"""Get the actual value to compare based on value_type"""
		if self.value_type == "Static Value":
			return self.value
		elif self.value_type == "Current User":
			return frappe.session.user
		elif self.value_type == "User Property":
			return frappe.db.get_value("User", frappe.session.user, self.value)
		elif self.value_type == "Session Value":
			return frappe.session.get(self.value)
		elif self.value_type == "Default Value":
			return frappe.defaults.get_user_default(self.value)
		elif self.value_type == "Today":
			return frappe.utils.today()
		elif self.value_type == "Now":
			return frappe.utils.now()
		else:
			return self.value