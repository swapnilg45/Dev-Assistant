# Copyright (c) 2024, Swapnil and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MandatoryFieldCondition(Document):
	"""
	Enhanced child table for defining conditions when mandatory fields are required.
	Supports field values, field changes, role checks, and custom scripts.
	"""

	def validate(self):
		"""Validate condition configuration."""
		# Validate condition type requirements
		if self.condition_type == "Field Value" or self.condition_type == "Field Changed":
			if not self.field:
				frappe.throw("Field is required for Field Value or Field Changed condition type")

		elif self.condition_type == "Role Check":
			if not self.role_name:
				frappe.throw("Role name is required for Role Check condition type")

		elif self.condition_type == "Custom Script":
			if not self.custom_script:
				frappe.throw("Custom script is required for Custom Script condition type")

		# Validate condition operators
		if self.condition_type != "Custom Script":
			if self.condition == "changed from" and not self.previous_value:
				frappe.throw("Previous value is required for 'changed from' condition")

			if self.condition in ["changed to", "=", "!=", ">", "<", ">=", "<=", "in", "not in", "like", "not like"]:
				if not self.value and self.condition not in ["is set", "is not set", "changed"]:
					frappe.msgprint(f"Value recommended for condition '{self.condition}'", indicator="orange")

	def evaluate(self, doc, field_history=None):
		"""
		Evaluate this condition against a document.

		Args:
			doc: Document to evaluate
			field_history: Optional field value history

		Returns:
			bool: True if condition is met
		"""
		from dev_assistant.dev_assistant.mandatory_field_validation.condition_evaluator import ConditionEvaluator

		evaluator = ConditionEvaluator()
		result = evaluator.evaluate(doc, self, field_history)

		# Apply negation if configured
		if self.negate_condition:
			result = not result

		return result

	def get_description(self):
		"""
		Get human-readable description of this condition.

		Returns:
			str: Description of the condition
		"""
		if self.condition_type == "Field Value":
			desc = f"Field '{self.field}' {self.condition}"
			if self.value:
				desc += f" '{self.value}'"

		elif self.condition_type == "Field Changed":
			desc = f"Field '{self.field}' has changed"
			if self.condition == "changed from":
				desc += f" from '{self.previous_value}'"
			elif self.condition == "changed to":
				desc += f" to '{self.value}'"

		elif self.condition_type == "Role Check":
			desc = f"User has role '{self.role_name}'"

		elif self.condition_type == "Custom Script":
			desc = "Custom script evaluation"

		else:
			desc = "Unknown condition"

		if self.negate_condition:
			desc = f"NOT ({desc})"

		return desc