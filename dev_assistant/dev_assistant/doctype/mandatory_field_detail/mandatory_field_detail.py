# Copyright (c) 2024, Swapnil and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import re


class MandatoryFieldDetail(Document):
	"""
	Enhanced child table for defining mandatory field details and validation rules.
	Supports different validation types including required, conditional, format, and custom.
	"""

	def validate(self):
		"""Validate field detail configuration."""
		# Validate field name is provided
		if not self.field_name:
			frappe.throw("Field name is required")

		# Validate format pattern if provided
		if self.validation_type == "Format Validation":
			if self.format_pattern:
				try:
					re.compile(self.format_pattern)
				except re.error as e:
					frappe.throw(f"Invalid format pattern: {str(e)}")

			# Validate min/max length
			if self.min_length and self.max_length:
				if self.min_length > self.max_length:
					frappe.throw("Minimum length cannot be greater than maximum length")

		# Validate custom validation script
		if self.validation_type == "Custom Validation":
			if self.validation_script:
				try:
					compile(self.validation_script, "<validation_script>", "exec")
				except SyntaxError as e:
					frappe.throw(f"Syntax error in validation script: {str(e)}")

	def validate_field(self, doc):
		"""
		Validate field value in the document.

		Args:
			doc: Document containing the field

		Returns:
			str or None: Error message if validation fails, None if valid
		"""
		from dev_assistant.dev_assistant.mandatory_field_validation.field_validator import FieldValidator

		validator = FieldValidator()
		return validator.validate_field(doc, self)

	def get_field_metadata(self, doctype):
		"""
		Get metadata for this field from the doctype.

		Args:
			doctype: DocType name

		Returns:
			dict: Field metadata or None
		"""
		if not self.field_name or not doctype:
			return None

		try:
			meta = frappe.get_meta(doctype)
			field = meta.get_field(self.field_name)
			if field:
				return {
					"fieldname": field.fieldname,
					"label": field.label,
					"fieldtype": field.fieldtype,
					"reqd": field.reqd,
					"options": field.options
				}
		except Exception:
			pass

		return None

	def get_validation_description(self):
		"""
		Get human-readable description of the validation.

		Returns:
			str: Description of the validation type
		"""
		if self.validation_type == "Required":
			return "Field is always required"

		elif self.validation_type == "Conditionally Required":
			return "Field is required based on conditions"

		elif self.validation_type == "Format Validation":
			desc = "Field must match format"
			if self.format_pattern:
				desc += f": {self.format_pattern}"
			if self.min_length:
				desc += f", min length: {self.min_length}"
			if self.max_length:
				desc += f", max length: {self.max_length}"
			return desc

		elif self.validation_type == "Custom Validation":
			return "Field validated by custom script"

		return "Unknown validation type"

	def get_error_message(self, default_message=None):
		"""
		Get the error message for this field.

		Args:
			default_message: Default message to use if no custom message

		Returns:
			str: Error message
		"""
		if self.custom_error_message:
			return self.custom_error_message

		if default_message:
			field_label = self.field_label or self.field_name.replace("_", " ").title()
			return f"<strong>{field_label}</strong> {default_message}"

		# Generate default message based on validation type
		field_label = self.field_label or self.field_name.replace("_", " ").title()

		if self.validation_type == "Required":
			return f"<strong>{field_label}</strong> is required"

		elif self.validation_type == "Format Validation":
			return f"<strong>{field_label}</strong> does not match the required format"

		elif self.validation_type == "Custom Validation":
			return f"<strong>{field_label}</strong> validation failed"

		return f"<strong>{field_label}</strong> is invalid"