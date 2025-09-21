# Copyright (c) 2025, Swapnil and contributors
# For license information, please see license.txt

"""
Field Monitor for Enhanced Mandatory Field Controller
Monitors field changes and triggers validation accordingly
"""

import frappe
from frappe import _
from frappe.utils import cstr, flt
from typing import Dict, List, Any, Tuple
from collections import defaultdict


class FieldMonitor:
	"""
	Monitors document field changes and triggers mandatory field validation
	when configured conditions are met.
	"""

	def __init__(self):
		"""Initialize field monitor with cache."""
		self._monitored_fields_cache = {}

	def track_document_changes(
		self,
		doc: frappe.model.document.Document
	) -> Dict[str, Tuple[Any, Any]]:
		"""
		Track field changes in a document using Frappe's built-in has_value_changed.

		Args:
			doc: Document to track

		Returns:
			Dictionary of field changes {field_name: (old_value, new_value)}
		"""
		changes = {}

		# Use Frappe's built-in change detection for existing documents
		if not doc.is_new():
			for field in doc.meta.fields:
				fieldname = field.fieldname
				if field.fieldtype in ["Section Break", "Column Break", "Tab Break", "HTML"]:
					continue

				# Use Frappe's built-in has_value_changed method
				if doc.has_value_changed(fieldname):
					old_value = doc.get_db_value(fieldname)
					new_value = frappe.utils.safe_getattr(doc, fieldname, None)
					changes[fieldname] = (old_value, new_value)

		# For new documents, all non-empty fields are considered changes
		else:
			for field in doc.meta.fields:
				fieldname = field.fieldname
				if field.fieldtype in ["Section Break", "Column Break", "Tab Break", "HTML"]:
					continue

				new_value = frappe.utils.safe_getattr(doc, fieldname, None)
				if new_value:
					changes[fieldname] = (None, new_value)

		return changes

	def get_monitored_fields(self, doctype: str) -> Dict[str, List]:
		"""
		Get all monitored fields for a doctype from active controllers.

		Args:
			doctype: Document type

		Returns:
			Dictionary mapping field names to list of monitor configurations
		"""
		cache_key = doctype
		if cache_key in self._monitored_fields_cache:
			return self._monitored_fields_cache[cache_key]

		monitored = defaultdict(list)

		# Get all active controllers for this doctype
		controllers = frappe.get_all(
			"Mandatory Field Controller",
			filters={
				"document_type": doctype,
				"disabled": 0,
				"execution_mode": ["in", ["Field Change Based", "Combined"]]
			},
			fields=["name"]
		)

		for controller in controllers:
			controller_doc = frappe.get_doc("Mandatory Field Controller", controller["name"])

			for monitor_config in controller_doc.monitored_fields:
				if monitor_config.field_name:
					monitored[monitor_config.field_name].append({
						"controller": controller_doc.name,
						"config": monitor_config,
						"controller_doc": controller_doc
					})

		self._monitored_fields_cache[cache_key] = dict(monitored)
		return dict(monitored)

	def check_field_triggers(
		self,
		doc: frappe.model.document.Document,
		changes: Dict[str, Tuple[Any, Any]]
	) -> List[Dict]:
		"""
		Check if any field changes trigger mandatory field validation.

		Args:
			doc: Document being processed
			changes: Dictionary of field changes

		Returns:
			List of triggered controller configurations
		"""
		triggered_controllers = []
		monitored_fields = self.get_monitored_fields(doc.doctype)

		for field_name, (old_value, new_value) in changes.items():
			if field_name not in monitored_fields:
				continue

			for monitor_info in monitored_fields[field_name]:
				monitor_config = monitor_info["config"]

				# Check if trigger condition is met
				if self._evaluate_trigger_condition(
					monitor_config,
					old_value,
					new_value
				):
					if monitor_info["controller_doc"] not in triggered_controllers:
						triggered_controllers.append(monitor_info["controller_doc"])

		return triggered_controllers

	def _evaluate_trigger_condition(
		self,
		monitor_config: Any,
		old_value: Any,
		new_value: Any
	) -> bool:
		"""
		Evaluate if a field change meets the trigger condition.

		Args:
			monitor_config: Monitor configuration
			old_value: Previous field value
			new_value: New field value

		Returns:
			True if trigger condition is met
		"""
		trigger_on = monitor_config.trigger_on

		if trigger_on == "Value Changed":
			if monitor_config.compare_with_previous:
				# Use Frappe's built-in comparison
				return old_value != new_value
			else:
				return True

		elif trigger_on == "Value Set":
			# Trigger when value goes from empty to set
			# Use Frappe's has_value utility
			is_old_empty = not frappe.utils.has_value(old_value)
			is_new_set = frappe.utils.has_value(new_value)
			return is_old_empty and is_new_set

		elif trigger_on == "Value Cleared":
			# Trigger when value goes from set to empty
			is_old_set = frappe.utils.has_value(old_value)
			is_new_empty = not frappe.utils.has_value(new_value)
			return is_old_set and is_new_empty

		elif trigger_on == "Specific Value":
			if not monitor_config.trigger_value:
				return False

			# Use Frappe's string comparison
			return cstr(new_value) == cstr(monitor_config.trigger_value)

		elif trigger_on == "Value Range":
			if not monitor_config.trigger_value:
				return False

			return self._check_value_in_range(new_value, monitor_config.trigger_value)

		return False

	def _check_value_in_range(self, value: Any, range_str: str) -> bool:
		"""
		Check if value falls within a specified range using Frappe utils.

		Args:
			value: Value to check
			range_str: Range string (e.g., "1-100", "0.5-10.5")

		Returns:
			True if value is in range
		"""
		try:
			# Parse range string
			if "-" not in range_str:
				return False

			parts = range_str.split("-", 1)
			if len(parts) != 2:
				return False

			# Use Frappe's flt for conversion
			min_val = flt(parts[0])
			max_val = flt(parts[1])
			num_value = flt(value)

			return min_val <= num_value <= max_val

		except (ValueError, TypeError):
			return False

	def clear_cache(self, doctype: str = None) -> None:
		"""Clear cached monitored fields configuration."""
		if doctype:
			if doctype in self._monitored_fields_cache:
				del self._monitored_fields_cache[doctype]
		else:
			self._monitored_fields_cache.clear()


# Global monitor instance
_field_monitor = None


def get_field_monitor() -> FieldMonitor:
	"""Get singleton instance of field monitor."""
	global _field_monitor
	if _field_monitor is None:
		_field_monitor = FieldMonitor()
	return _field_monitor