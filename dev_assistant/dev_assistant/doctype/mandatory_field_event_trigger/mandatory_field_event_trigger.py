# Copyright (c) 2025, Swapnil and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MandatoryFieldEventTrigger(Document):
	"""
	Child table for configuring event triggers for mandatory field validation.
	Allows specifying which document events should trigger validation.
	"""

	def validate(self):
		"""Validate event trigger configuration."""
		# Validate execution order
		if self.execution_order and self.execution_order < 0:
			frappe.throw("Execution order must be a positive number")

		# Validate event type
		valid_events = [
			"before_insert", "after_insert", "before_validate", "validate",
			"after_validate", "before_save", "after_save", "before_submit",
			"after_submit", "before_update_after_submit", "after_update_after_submit",
			"before_cancel", "after_cancel", "before_delete", "after_delete",
			"on_change", "on_update"
		]

		if self.event_type and self.event_type not in valid_events:
			frappe.throw(f"Invalid event type: {self.event_type}")

	def get_event_method_name(self):
		"""Get the actual method name for the event."""
		# Map event types to actual Frappe method names
		event_map = {
			"before_validate": "before_validate",
			"validate": "validate",
			"after_validate": "after_validate",
			"before_insert": "before_insert",
			"after_insert": "after_insert",
			"before_save": "before_save",
			"after_save": "after_save",
			"before_submit": "before_submit",
			"after_submit": "on_submit",
			"before_update_after_submit": "before_update_after_submit",
			"after_update_after_submit": "on_update_after_submit",
			"before_cancel": "before_cancel",
			"after_cancel": "on_cancel",
			"before_delete": "before_trash",
			"after_delete": "after_delete",
			"on_change": "on_change",
			"on_update": "on_update"
		}

		return event_map.get(self.event_type, self.event_type)