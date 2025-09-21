# Copyright (c) 2025, Swapnil and contributors
# For license information, please see license.txt

"""
Event Engine for Enhanced Mandatory Field Controller
Handles document event interception and rule execution
"""

import frappe
from frappe import _
from frappe.utils import cint, get_datetime
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from functools import lru_cache


class MandatoryFieldEventEngine:
	"""
	Main event engine that processes mandatory field validations
	based on document events and field changes.
	"""

	def __init__(self):
		"""Initialize the event engine with caching."""
		self._cache = {}
		self._field_change_cache = {}
		self._execution_stack = []

	@staticmethod
	@lru_cache(maxsize=128)
	def get_active_controllers(doctype: str, event_type: str = None) -> List[Dict]:
		"""
		Get active mandatory field controllers for a doctype.

		Args:
			doctype: Document type to get controllers for
			event_type: Optional specific event to filter by

		Returns:
			List of controller configurations
		"""
		filters = {
			"document_type": doctype,
			"disabled": 0
		}

		controllers = frappe.get_all(
			"Mandatory Field Controller",
			filters=filters,
			fields=["name", "priority", "execution_mode", "condition_logic",
					"custom_condition_script", "error_handling_mode",
					"apply_to_child_tables"],
			order_by="priority desc, creation desc"
		)

		# Load child tables for each controller
		for controller in controllers:
			controller_doc = frappe.get_doc("Mandatory Field Controller", controller["name"])

			# Filter by event type if specified
			if event_type and controller["execution_mode"] in ["Event Based", "Combined"]:
				event_triggers = [
					trigger for trigger in controller_doc.event_triggers
					if trigger.enabled and trigger.event_type == event_type
				]
				if not event_triggers:
					continue

			controller["event_triggers"] = controller_doc.event_triggers
			controller["monitored_fields"] = controller_doc.monitored_fields
			controller["conditions"] = controller_doc.conditions
			controller["mandatory_fields"] = controller_doc.mandatory_fields
			controller["bypass_roles"] = controller_doc.bypass_roles

		return controllers

	def execute_for_event(self, doc: frappe.model.document.Document, event_type: str) -> None:
		"""
		Execute mandatory field validation for a specific event.

		Args:
			doc: Document being processed
			event_type: Event that triggered the execution
		"""
		# Skip if document is being deleted
		if doc.flags.ignore_mandatory or doc.flags.ignore_validate:
			return

		# Prevent recursive execution
		execution_key = f"{doc.doctype}:{doc.name}:{event_type}"
		if execution_key in self._execution_stack:
			return

		self._execution_stack.append(execution_key)

		try:
			controllers = self.get_active_controllers(doc.doctype, event_type)

			all_errors = []
			has_warnings = False

			for controller in controllers:
				# Check bypass roles
				if self._user_has_bypass_role(controller.get("bypass_roles", [])):
					continue

				# Check execution mode
				if not self._should_execute_for_event(controller, event_type):
					continue

				# Evaluate conditions
				if not self._evaluate_conditions(doc, controller):
					continue

				# Validate mandatory fields
				errors, is_warning = self._validate_fields(doc, controller)

				if errors:
					if controller.get("error_handling_mode") == "Warning Only":
						has_warnings = True
						self._show_warnings(errors)
					else:
						all_errors.extend(errors)

						if controller.get("error_handling_mode") == "Stop on First Error":
							break

			# Raise consolidated errors if any
			if all_errors:
				self._raise_validation_error(all_errors)

		finally:
			# Clean up execution stack
			if execution_key in self._execution_stack:
				self._execution_stack.remove(execution_key)

	def execute_for_field_change(
		self,
		doc: frappe.model.document.Document,
		field_name: str,
		old_value: Any,
		new_value: Any
	) -> None:
		"""
		Execute mandatory field validation triggered by field change.

		Args:
			doc: Document being processed
			field_name: Field that changed
			old_value: Previous value
			new_value: New value
		"""
		controllers = self.get_active_controllers(doc.doctype)

		for controller in controllers:
			# Check if controller monitors this field
			if controller.get("execution_mode") not in ["Field Change Based", "Combined"]:
				continue

			monitored_fields = controller.get("monitored_fields", [])
			for monitor in monitored_fields:
				if monitor.field_name != field_name:
					continue

				# Check trigger condition
				if self._check_field_trigger(monitor, old_value, new_value, doc):
					# Apply debounce if configured
					if monitor.debounce_time:
						time.sleep(monitor.debounce_time / 1000.0)

					# Validate mandatory fields
					errors, _ = self._validate_fields(doc, controller)
					if errors:
						self._raise_validation_error(errors)

	def _should_execute_for_event(self, controller: Dict, event_type: str) -> bool:
		"""Check if controller should execute for the given event."""
		execution_mode = controller.get("execution_mode")

		if execution_mode == "Field Change Based":
			return False

		event_triggers = controller.get("event_triggers", [])
		for trigger in event_triggers:
			if trigger.enabled and trigger.event_type == event_type:
				return True

		return False

	def _user_has_bypass_role(self, bypass_roles: List) -> bool:
		"""Check if current user has any bypass role."""
		if frappe.session.user == "Administrator":
			return True

		user_roles = frappe.get_roles()
		for bypass_role in bypass_roles:
			if bypass_role.role in user_roles:
				return True

		return False

	def _evaluate_conditions(self, doc: frappe.model.document.Document, controller: Dict) -> bool:
		"""
		Evaluate controller conditions.

		Args:
			doc: Document to evaluate
			controller: Controller configuration

		Returns:
			True if conditions are met
		"""
		conditions = controller.get("conditions", [])
		if not conditions:
			return True

		condition_logic = controller.get("condition_logic", "AND")

		# Custom script logic
		if condition_logic == "Custom" and controller.get("custom_condition_script"):
			try:
				# Create safe execution context
				context = {
					"doc": doc,
					"user": frappe.session.user,
					"frappe": frappe,
					"_": _
				}

				# Execute custom script
				result = frappe.safe_eval(
					controller["custom_condition_script"],
					eval_globals=context,
					eval_locals=context
				)
				return bool(result)
			except Exception as e:
				frappe.log_error(f"Custom condition script error: {str(e)}",
								"Mandatory Field Controller")
				return False

		# Standard AND/OR logic
		results = []
		for condition in conditions:
			result = self._evaluate_single_condition(doc, condition)
			results.append(result)

		if condition_logic == "AND":
			return all(results)
		elif condition_logic == "OR":
			return any(results)

		return True

	def _evaluate_single_condition(
		self,
		doc: frappe.model.document.Document,
		condition: Any
	) -> bool:
		"""Evaluate a single condition."""
		from .condition_evaluator import ConditionEvaluator

		evaluator = ConditionEvaluator()
		result = evaluator.evaluate(doc, condition)

		# Handle negation
		if hasattr(condition, 'negate_condition') and condition.negate_condition:
			result = not result

		return result

	def _check_field_trigger(
		self,
		monitor: Any,
		old_value: Any,
		new_value: Any,
		doc: frappe.model.document.Document
	) -> bool:
		"""Check if field change triggers validation."""
		if hasattr(monitor, 'check_trigger_condition'):
			return monitor.check_trigger_condition(old_value, new_value, doc)

		# Fallback to simple change detection
		return old_value != new_value

	def _validate_fields(
		self,
		doc: frappe.model.document.Document,
		controller: Dict
	) -> Tuple[List[str], bool]:
		"""
		Validate mandatory fields according to controller configuration.

		Args:
			doc: Document to validate
			controller: Controller configuration

		Returns:
			Tuple of (errors list, is_warning flag)
		"""
		from .field_validator import FieldValidator

		validator = FieldValidator()
		errors = []
		is_warning = controller.get("error_handling_mode") == "Warning Only"

		mandatory_fields = controller.get("mandatory_fields", [])

		for field_config in mandatory_fields:
			error = validator.validate_field(doc, field_config)
			if error:
				errors.append(error)

				# Stop on first error if configured
				if controller.get("error_handling_mode") == "Stop on First Error":
					break

		# Handle child tables if configured
		if controller.get("apply_to_child_tables"):
			child_errors = self._validate_child_tables(doc, mandatory_fields, validator)
			errors.extend(child_errors)

		return errors, is_warning

	def _validate_child_tables(
		self,
		doc: frappe.model.document.Document,
		mandatory_fields: List,
		validator: Any
	) -> List[str]:
		"""Validate mandatory fields in child tables."""
		errors = []

		meta = frappe.get_meta(doc.doctype)
		for field in meta.fields:
			if field.fieldtype == "Table":
				child_docs = doc.get(field.fieldname, [])
				for idx, child_doc in enumerate(child_docs, 1):
					for field_config in mandatory_fields:
						# Check if field exists in child table
						child_meta = frappe.get_meta(field.options)
						if child_meta.has_field(field_config.field_name):
							error = validator.validate_field(child_doc, field_config)
							if error:
								errors.append(
									f"Row #{idx} in {field.label}: {error}"
								)

		return errors

	def _show_warnings(self, warnings: List[str]) -> None:
		"""Show warnings to user without blocking."""
		if warnings:
			warning_html = self._format_error_html(warnings, title="Warning")
			frappe.msgprint(warning_html, indicator="orange", alert=True)

	def _raise_validation_error(self, errors: List[str]) -> None:
		"""Raise validation error with formatted message."""
		if errors:
			error_html = self._format_error_html(errors)
			frappe.throw(
				error_html,
				title="Required Fields Missing",
				exc=frappe.ValidationError
			)

	def _format_error_html(self, errors: List[str], title: str = None) -> str:
		"""Format errors as HTML for display."""
		if not errors:
			return ""

		error_html = "<div style='text-align: left;'>"
		error_html += "<ul style='margin: 10px 0; padding-left: 20px;'>"

		for error in errors:
			error_html += f"<li style='margin: 5px 0;'>{error}</li>"

		error_html += "</ul></div>"

		return error_html

	def clear_cache(self, doctype: str = None) -> None:
		"""Clear cached data for a doctype or all doctypes."""
		if doctype:
			# Clear specific doctype cache
			cache_keys = [k for k in self._cache.keys() if k.startswith(doctype)]
			for key in cache_keys:
				del self._cache[key]
		else:
			# Clear all cache
			self._cache.clear()
			self._field_change_cache.clear()

		# Clear LRU cache
		self.get_active_controllers.cache_clear()


# Global instance
_event_engine = None


def get_event_engine() -> MandatoryFieldEventEngine:
	"""Get singleton instance of event engine."""
	global _event_engine
	if _event_engine is None:
		_event_engine = MandatoryFieldEventEngine()
	return _event_engine


def execute_mandatory_validation(doc: frappe.model.document.Document, event_type: str) -> None:
	"""
	Main entry point for mandatory field validation.

	Args:
		doc: Document being processed
		event_type: Event that triggered validation
	"""
	engine = get_event_engine()
	engine.execute_for_event(doc, event_type)


def execute_field_change_validation(
	doc: frappe.model.document.Document,
	field_name: str,
	old_value: Any,
	new_value: Any
) -> None:
	"""
	Execute validation triggered by field change.

	Args:
		doc: Document being processed
		field_name: Field that changed
		old_value: Previous value
		new_value: New value
	"""
	engine = get_event_engine()
	engine.execute_for_field_change(doc, field_name, old_value, new_value)