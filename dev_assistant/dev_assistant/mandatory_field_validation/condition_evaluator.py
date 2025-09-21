# Copyright (c) 2025, Swapnil and contributors
# For license information, please see license.txt

"""
Condition Evaluator for Enhanced Mandatory Field Controller
Evaluates complex conditions including field changes, role checks, and custom scripts
"""

import frappe
from frappe import _
from frappe.utils import cint, cstr, flt, get_datetime
import operator
import re
from typing import Any, List, Dict
from datetime import datetime, date


class ConditionEvaluator:
	"""
	Evaluates conditions for mandatory field validation with support for
	field values, field changes, role checks, and custom scripts.
	"""

	def __init__(self):
		"""Initialize condition evaluator with operator mappings."""
		self.operators = {
			"=": operator.eq,
			"!=": operator.ne,
			">": operator.gt,
			"<": operator.lt,
			">=": operator.ge,
			"<=": operator.le,
			"in": self._in_operator,
			"not in": self._not_in_operator,
			"like": self._like_operator,
			"not like": self._not_like_operator,
			"is set": self._is_set,
			"is not set": self._is_not_set,
			"changed": self._has_changed,
			"changed from": self._changed_from,
			"changed to": self._changed_to
		}

	def evaluate(
		self,
		doc: frappe.model.document.Document,
		condition: Any,
		field_history: Dict = None
	) -> bool:
		"""
		Evaluate a single condition.

		Args:
			doc: Document to evaluate
			condition: Condition object with type and parameters
			field_history: Optional field value history

		Returns:
			True if condition is met
		"""
		try:
			condition_type = getattr(condition, 'condition_type', 'Field Value')

			if condition_type == "Field Value":
				return self._evaluate_field_value(doc, condition)
			elif condition_type == "Field Changed":
				return self._evaluate_field_change(doc, condition)
			elif condition_type == "Role Check":
				return self._evaluate_role_check(condition)
			elif condition_type == "Custom Script":
				return self._evaluate_custom_script(doc, condition)
			else:
				# Default to field value evaluation for backward compatibility
				return self._evaluate_field_value(doc, condition)

		except Exception as e:
			frappe.log_error(
				f"Condition evaluation error: {str(e)}",
				"Mandatory Field Controller"
			)
			return False

	def _evaluate_field_value(
		self,
		doc: frappe.model.document.Document,
		condition: Any
	) -> bool:
		"""Evaluate field value condition."""
		field_name = condition.field
		if not field_name:
			return True

		# Use Frappe's safe_getattr for field access
		field_value = frappe.utils.safe_getattr(doc, field_name, None)
		condition_op = condition.condition
		compare_value = condition.value

		# Get operator function
		op_func = self.operators.get(condition_op)
		if not op_func:
			return False

		# Special handling for operators that don't need a comparison value
		if condition_op in ["is set", "is not set", "changed"]:
			return op_func(field_value)

		# Evaluate condition
		return op_func(field_value, compare_value)

	def _evaluate_field_change(
		self,
		doc: frappe.model.document.Document,
		condition: Any
	) -> bool:
		"""Evaluate field change condition using Frappe's built-in methods."""
		field_name = condition.field
		if not field_name:
			return False

		# Use Frappe's built-in change detection
		if doc.is_new():
			return False

		condition_op = condition.condition

		if condition_op == "changed":
			# Use Frappe's has_value_changed
			return doc.has_value_changed(field_name)
		elif condition_op == "changed from":
			if doc.has_value_changed(field_name):
				old_value = doc.get_db_value(field_name)
				return old_value == condition.previous_value
		elif condition_op == "changed to":
			if doc.has_value_changed(field_name):
				current_value = frappe.utils.safe_getattr(doc, field_name, None)
				return current_value == condition.value
		else:
			# Use standard operators on current value
			current_value = frappe.utils.safe_getattr(doc, field_name, None)
			op_func = self.operators.get(condition_op)
			if op_func:
				return op_func(current_value, condition.value)

		return False

	def _evaluate_role_check(self, condition: Any) -> bool:
		"""Evaluate role-based condition."""
		if not condition.role_name:
			return False

		# Use Frappe's built-in role checking
		return condition.role_name in frappe.get_roles()

	def _evaluate_custom_script(
		self,
		doc: frappe.model.document.Document,
		condition: Any
	) -> bool:
		"""Evaluate custom Python script condition."""
		if not condition.custom_script:
			return True

		try:
			# Create safe execution context with Frappe utilities
			context = {
				"doc": doc,
				"user": frappe.session.user,
				"frappe": frappe,
				"_": _,
				"datetime": datetime,
				"date": date,
				"cint": cint,
				"cstr": cstr,
				"flt": flt
			}

			# Execute custom script using Frappe's safe_eval
			result = frappe.safe_eval(
				condition.custom_script,
				eval_globals=context,
				eval_locals=context
			)

			return bool(result)

		except Exception as e:
			frappe.log_error(
				f"Custom script evaluation error: {str(e)}",
				"Mandatory Field Controller"
			)
			return False

	# Operator functions
	def _in_operator(self, field_value: Any, compare_value: str) -> bool:
		"""Check if field value is in comma-separated list."""
		if compare_value is None:
			return False

		value_list = [v.strip() for v in cstr(compare_value).split(",")]
		return cstr(field_value) in value_list

	def _not_in_operator(self, field_value: Any, compare_value: str) -> bool:
		"""Check if field value is not in comma-separated list."""
		if compare_value is None:
			return True

		value_list = [v.strip() for v in cstr(compare_value).split(",")]
		return cstr(field_value) not in value_list

	def _like_operator(self, field_value: Any, pattern: str) -> bool:
		"""Check if field value matches pattern (SQL LIKE syntax)."""
		if not pattern:
			return False

		# Convert SQL LIKE pattern to regex
		regex_pattern = pattern.replace("%", ".*").replace("_", ".")
		regex_pattern = f"^{regex_pattern}$"

		try:
			return bool(re.match(regex_pattern, cstr(field_value), re.IGNORECASE))
		except re.error:
			return False

	def _not_like_operator(self, field_value: Any, pattern: str) -> bool:
		"""Check if field value doesn't match pattern."""
		return not self._like_operator(field_value, pattern)

	def _is_set(self, field_value: Any) -> bool:
		"""Check if field has a value using Frappe's utility."""
		# Use Frappe's built-in has_value utility
		return frappe.utils.has_value(field_value)

	def _is_not_set(self, field_value: Any) -> bool:
		"""Check if field doesn't have a value using Frappe's utility."""
		return not frappe.utils.has_value(field_value)

	def _has_changed(self, field_value: Any) -> bool:
		"""Check if field value has changed - placeholder method."""
		# This method is context-dependent and handled in _evaluate_field_change
		return True

	def _changed_from(self, field_value: Any, previous_value: Any) -> bool:
		"""Check if field changed from a specific value - placeholder method."""
		# This method is context-dependent and handled in _evaluate_field_change
		return False

	def _changed_to(self, field_value: Any, new_value: Any) -> bool:
		"""Check if field changed to a specific value."""
		return field_value == new_value


class ConditionGroup:
	"""
	Handles evaluation of multiple conditions with AND/OR/Custom logic.
	"""

	def __init__(self, conditions: List, logic: str = "AND", custom_script: str = None):
		"""
		Initialize condition group.

		Args:
			conditions: List of conditions
			logic: Logic type (AND, OR, Custom)
			custom_script: Custom Python script for complex logic
		"""
		self.conditions = conditions
		self.logic = logic
		self.custom_script = custom_script
		self.evaluator = ConditionEvaluator()

	def evaluate(
		self,
		doc: frappe.model.document.Document,
		field_history: Dict = None
	) -> bool:
		"""
		Evaluate all conditions based on logic type.

		Args:
			doc: Document to evaluate
			field_history: Optional field value history

		Returns:
			True if condition group is satisfied
		"""
		if not self.conditions:
			return True

		if self.logic == "Custom" and self.custom_script:
			return self._evaluate_custom_logic(doc, field_history)

		# Evaluate individual conditions
		results = []
		for condition in self.conditions:
			result = self.evaluator.evaluate(doc, condition, field_history)

			# Handle negation
			if hasattr(condition, 'negate_condition') and condition.negate_condition:
				result = not result

			results.append(result)

		# Apply logic
		if self.logic == "AND":
			return all(results)
		elif self.logic == "OR":
			return any(results)
		else:
			# Default to AND
			return all(results)

	def _evaluate_custom_logic(
		self,
		doc: frappe.model.document.Document,
		field_history: Dict
	) -> bool:
		"""Evaluate custom logic script."""
		try:
			# Evaluate individual conditions first
			condition_results = {}
			for idx, condition in enumerate(self.conditions):
				result = self.evaluator.evaluate(doc, condition, field_history)
				condition_results[f"c{idx}"] = result

			# Create execution context
			context = {
				"doc": doc,
				"conditions": condition_results,
				"all": all,
				"any": any,
				"frappe": frappe,
				"_": _
			}

			# Execute custom script using Frappe's safe_eval
			result = frappe.safe_eval(
				self.custom_script,
				eval_globals=context,
				eval_locals=context
			)

			return bool(result)

		except Exception as e:
			frappe.log_error(
				f"Custom condition logic error: {str(e)}",
				"Mandatory Field Controller"
			)
			# Default to AND logic on error
			return all([
				self.evaluator.evaluate(doc, c, field_history)
				for c in self.conditions
			])