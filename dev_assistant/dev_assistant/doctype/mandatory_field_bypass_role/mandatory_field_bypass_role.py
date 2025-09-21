# Copyright (c) 2025, Swapnil and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MandatoryFieldBypassRole(Document):
	"""
	Child table for defining roles that can bypass mandatory field validation.
	"""

	def validate(self):
		"""Validate bypass role configuration."""
		if self.role:
			# Check if role exists
			if not frappe.db.exists("Role", self.role):
				frappe.throw(f"Role {self.role} does not exist")

	def user_has_role(self, user=None):
		"""
		Check if the specified user has this bypass role.

		Args:
			user: User to check (defaults to current user)

		Returns:
			bool: True if user has the role
		"""
		if not user:
			user = frappe.session.user

		if user == "Administrator":
			return True

		return self.role in frappe.get_roles(user)