# Copyright (c) 2025, Swapnil and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import re


class MandatoryFieldMonitor(Document):
	"""
	Child table for configuring field change monitoring.
	Monitors specific fields for changes and triggers validation accordingly.
	"""

	def validate(self):
		"""Validate field monitor configuration."""
		# Validate debounce time
		if self.debounce_time and self.debounce_time < 0:
			frappe.throw("Debounce time must be a positive number")

		# Validate trigger value for specific conditions
		if self.trigger_on == "Value Range" and self.trigger_value:
			if not self._is_valid_range(self.trigger_value):
				frappe.throw(f"Invalid range format: {self.trigger_value}. Use format like '1-100' or '0.5-10.5'")

	def _is_valid_range(self, value_range):
		"""Check if the value range is in valid format."""
		if not value_range:
			return False

		# Check for valid range format (e.g., "1-100", "0.5-10.5")
		pattern = r'^-?\d+(\.\d+)?--?\d+(\.\d+)?$'
		return bool(re.match(pattern, value_range))

	def check_trigger_condition(self, old_value, new_value, doc=None):
		"""
		Check if the trigger condition is met based on field values.

		Args:
			old_value: Previous value of the field
			new_value: Current value of the field
			doc: Document object for context

		Returns:
			bool: True if trigger condition is met
		"""
		if not self.enabled:
			return False

		# Handle different trigger conditions
		if self.trigger_on == "Value Changed":
			if self.compare_with_previous:
				return old_value != new_value
			else:
				return True  # Always trigger if not comparing

		elif self.trigger_on == "Value Set":
			# Trigger when value goes from empty to set
			is_old_empty = not old_value or (isinstance(old_value, str) and not old_value.strip())
			is_new_set = new_value and (not isinstance(new_value, str) or new_value.strip())
			return is_old_empty and is_new_set

		elif self.trigger_on == "Value Cleared":
			# Trigger when value goes from set to empty
			is_old_set = old_value and (not isinstance(old_value, str) or old_value.strip())
			is_new_empty = not new_value or (isinstance(new_value, str) and not new_value.strip())
			return is_old_set and is_new_empty

		elif self.trigger_on == "Specific Value":
			if not self.trigger_value:
				return False

			# Convert to string for comparison if needed
			if isinstance(new_value, (int, float)):
				return str(new_value) == self.trigger_value
			else:
				return new_value == self.trigger_value

		elif self.trigger_on == "Value Range":
			if not self.trigger_value or not self._is_valid_range(self.trigger_value):
				return False

			try:
				# Parse range
				range_parts = self.trigger_value.split("-")
				if len(range_parts) != 2:
					return False

				min_val = float(range_parts[0])
				max_val = float(range_parts[1])

				# Convert new_value to float for comparison
				if isinstance(new_value, (int, float, str)):
					num_value = float(new_value) if new_value else 0
					return min_val <= num_value <= max_val
			except (ValueError, TypeError):
				return False

		return False

	def get_field_metadata(self, doctype):
		"""Get metadata for the monitored field."""
		if not self.field_name or not doctype:
			return None

		try:
			meta = frappe.get_meta(doctype)
			field = meta.get_field(self.field_name)
			return field
		except Exception:
			return None