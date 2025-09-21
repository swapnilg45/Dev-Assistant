# Copyright (c) 2024, Swapnil and contributors
# For license information, please see license.txt

"""
Enhanced Mandatory Field Validator - Backward Compatible
Integrates with the new event engine while maintaining existing functionality
"""

import frappe
from frappe import _
import operator
from typing import Any, Dict, List, Optional


def validate_mandatory_fields(doc, method=None):
	"""
	Main entry point for mandatory field validation.
	Maintains backward compatibility while using the enhanced event engine.

	Args:
		doc: Document being validated
		method: Event method that triggered validation
	"""
	# Skip validation for system operations
	if (frappe.flags.in_migrate or
		frappe.flags.in_install or
		frappe.flags.in_import or
		frappe.flags.in_setup_wizard or
		getattr(frappe.local, 'in_migrate', False)):
		return

	# Skip validation for the controller doctypes themselves
	if doc.doctype in [
		"Mandatory Field Controller",
		"Mandatory Field Condition",
		"Mandatory Field Detail",
		"Mandatory Field Event Trigger",
		"Mandatory Field Monitor",
		"Mandatory Field Bypass Role"
	]:
		return

	# Skip during DocType sync operations
	if doc.doctype in ['DocType', 'DocField', 'Custom Field'] and method in ['after_delete', 'on_trash']:
		return

	# Skip if ignore flags are set
	if doc.flags.ignore_mandatory or doc.flags.ignore_validate:
		return

	# Determine event type from method
	event_type = _get_event_type(method)

	try:
		# Try to use the enhanced event engine
		from .event_engine import execute_mandatory_validation

		# Execute enhanced validation
		execute_mandatory_validation(doc, event_type)

	except ImportError:
		# Fallback to legacy validation if event engine not available
		_legacy_validate_mandatory_fields(doc, event_type)
	except Exception as e:
		# Log error but don't break the document operation
		frappe.log_error(f"Error in mandatory field validation: {str(e)}")
		return


def _get_event_type(method: Optional[str]) -> str:
	"""
	Determine event type from method name.

	Args:
		method: Method name

	Returns:
		Event type string
	"""
	if not method:
		return "validate"

	# Map method names to event types
	event_map = {
		"validate": "validate",
		"before_save": "before_save",
		"after_save": "after_save",
		"before_insert": "before_insert",
		"after_insert": "after_insert",
		"before_submit": "before_submit",
		"on_submit": "after_submit",
		"on_update": "on_update",
		"on_cancel": "after_cancel",
		"on_trash": "before_delete",
		"after_delete": "after_delete",
		"before_update_after_submit": "before_update_after_submit",
		"on_update_after_submit": "after_update_after_submit"
	}

	return event_map.get(method, "validate")


def _legacy_validate_mandatory_fields(doc, event_type: str = "validate"):
	"""
	Legacy validation function for backward compatibility.
	Used when enhanced features are not available or for simple validate-only rules.

	Args:
		doc: Document to validate
		event_type: Event that triggered validation
	"""
	# Get active rules for this doctype
	rules = frappe.get_all(
		"Mandatory Field Controller",
		filters={
			"document_type": doc.doctype,
			"disabled": 0
		},
		fields=["name", "priority", "execution_mode"],
		order_by="priority desc, creation desc"
	)

	if not rules:
		return

	# Process rules in order of priority
	for rule in rules:
		rule_doc = frappe.get_doc("Mandatory Field Controller", rule.name)

		# Check execution mode compatibility
		if not _should_execute_legacy(rule_doc, event_type):
			continue

		# Check if user can bypass
		if _can_bypass_validation(rule_doc):
			continue

		# Check if conditions are met
		if _check_conditions(doc, rule_doc):
			# Validate mandatory fields
			_validate_mandatory_fields_legacy(doc, rule_doc)


def _should_execute_legacy(rule_doc, event_type: str) -> bool:
	"""
	Check if rule should execute in legacy mode.

	Args:
		rule_doc: Rule document
		event_type: Current event type

	Returns:
		True if should execute
	"""
	# For backward compatibility, execute on validate if no specific triggers defined
	if not hasattr(rule_doc, 'execution_mode') or not rule_doc.execution_mode:
		return event_type == "validate"

	if rule_doc.execution_mode == "Event Based":
		# Check if this event is configured
		if hasattr(rule_doc, 'event_triggers') and rule_doc.event_triggers:
			for trigger in rule_doc.event_triggers:
				if trigger.enabled and trigger.event_type == event_type:
					return True
			return False
		else:
			# No triggers defined, use validate only for backward compatibility
			return event_type == "validate"

	elif rule_doc.execution_mode == "Field Change Based":
		# Field change based rules need the enhanced engine
		return False

	elif rule_doc.execution_mode == "Combined":
		# Check event triggers
		if hasattr(rule_doc, 'event_triggers') and rule_doc.event_triggers:
			for trigger in rule_doc.event_triggers:
				if trigger.enabled and trigger.event_type == event_type:
					return True

	# Default to validate event for backward compatibility
	return event_type == "validate"


def _can_bypass_validation(rule_doc) -> bool:
	"""
	Check if current user can bypass validation.

	Args:
		rule_doc: Rule document

	Returns:
		True if user can bypass
	"""
	if frappe.session.user == "Administrator":
		return True

	if hasattr(rule_doc, 'bypass_roles') and rule_doc.bypass_roles:
		user_roles = frappe.get_roles()
		for bypass_role in rule_doc.bypass_roles:
			if bypass_role.role in user_roles:
				return True

	return False


def _check_conditions(doc, rule_doc) -> bool:
	"""
	Check if all conditions in the rule are met.
	Enhanced version with support for new condition types.

	Args:
		doc: Document to check
		rule_doc: Rule document

	Returns:
		True if conditions are met
	"""
	if not rule_doc.conditions:
		return True

	# Check for enhanced condition logic
	condition_logic = getattr(rule_doc, 'condition_logic', 'AND')

	if condition_logic == "Custom" and hasattr(rule_doc, 'custom_condition_script'):
		# Evaluate custom condition script
		try:
			context = {
				"doc": doc,
				"user": frappe.session.user,
				"frappe": frappe
			}
			result = frappe.safe_eval(
				rule_doc.custom_condition_script,
				eval_globals=context,
				eval_locals=context
			)
			return bool(result)
		except Exception as e:
			frappe.log_error(f"Custom condition script error: {str(e)}", "Mandatory Field Controller")
			return False

	# Evaluate individual conditions
	results = []
	for condition in rule_doc.conditions:
		result = _evaluate_condition(doc, condition)
		results.append(result)

	# Apply logic
	if condition_logic == "OR":
		return any(results)
	else:  # Default to AND
		return all(results)


def _evaluate_condition(doc, condition) -> bool:
	"""
	Evaluate a single condition with support for enhanced condition types.

	Args:
		doc: Document to evaluate
		condition: Condition object

	Returns:
		True if condition is met
	"""
	# Check condition type (enhanced feature)
	condition_type = getattr(condition, 'condition_type', 'Field Value')

	if condition_type == "Role Check":
		# Check if user has the specified role
		if hasattr(condition, 'role_name') and condition.role_name:
			return condition.role_name in frappe.get_roles()
		return False

	elif condition_type == "Custom Script":
		# Evaluate custom script
		if hasattr(condition, 'custom_script') and condition.custom_script:
			try:
				context = {
					"doc": doc,
					"user": frappe.session.user,
					"frappe": frappe
				}
				result = frappe.safe_eval(
					condition.custom_script,
					eval_globals=context,
					eval_locals=context
				)
				return bool(result)
			except Exception:
				return False
		return True

	# Default to field value evaluation (backward compatible)
	field_value = frappe.utils.safe_getattr(doc, condition.field, None)
	condition_op = condition.condition

	# Enhanced operators
	operators_map = {
		"=": operator.eq,
		"!=": operator.ne,
		">": operator.gt,
		"<": operator.lt,
		">=": operator.ge,
		"<=": operator.le,
		"in": lambda x, y: cstr(x) in cstr(y).split(","),
		"not in": lambda x, y: cstr(x) not in cstr(y).split(","),
		"like": lambda x, y: cstr(y).lower() in cstr(x).lower() if x and y else False,
		"not like": lambda x, y: cstr(y).lower() not in cstr(x).lower() if x and y else True,
		"is set": lambda x, y=None: frappe.utils.has_value(x),
		"is not set": lambda x, y=None: not frappe.utils.has_value(x)
	}

	op_func = operators_map.get(condition_op)
	if not op_func:
		return False

	try:
		# Special handling for operators that don't need a value
		if condition_op in ["is set", "is not set"]:
			result = op_func(field_value)
		else:
			# Get comparison value
			compare_value = getattr(condition, 'value', None)

			# Convert values for comparison
			if condition_op in ["in", "not in", "like", "not like"]:
				result = op_func(str(field_value) if field_value else "", compare_value)
			else:
				# Try to convert to appropriate types for comparison
				if field_value is None:
					field_value = ""
				if isinstance(field_value, (int, float)) and compare_value and compare_value.replace(".", "").replace("-", "").isdigit():
					result = op_func(field_value, float(compare_value))
				else:
					result = op_func(str(field_value), str(compare_value) if compare_value else "")

		# Handle negation if configured
		if hasattr(condition, 'negate_condition') and condition.negate_condition:
			result = not result

		return result

	except (ValueError, TypeError, AttributeError):
		return False


def _validate_mandatory_fields_legacy(doc, rule_doc):
	"""
	Validate that mandatory fields have values (legacy version).

	Args:
		doc: Document to validate
		rule_doc: Rule document
	"""
	errors = []
	error_handling = getattr(rule_doc, 'error_handling_mode', 'Collect All Errors')

	for field in rule_doc.mandatory_fields:
		error = _validate_single_field(doc, field)
		if error:
			if error_handling == "Warning Only":
				# Show as warning instead of error
				frappe.msgprint(error, indicator="orange", alert=True)
			else:
				errors.append(error)
				if error_handling == "Stop on First Error":
					break

	# Handle child tables if configured
	if getattr(rule_doc, 'apply_to_child_tables', False):
		child_errors = _validate_child_tables(doc, rule_doc.mandatory_fields)
		errors.extend(child_errors)

	if errors and error_handling != "Warning Only":
		error_html = _format_error_html(errors)
		frappe.throw(
			error_html,
			title="Required Fields Missing",
			exc=frappe.ValidationError
		)


def _validate_single_field(doc, field_config) -> Optional[str]:
	"""
	Validate a single field based on configuration.

	Args:
		doc: Document containing the field
		field_config: Field configuration

	Returns:
		Error message if validation fails
	"""
	field_value = frappe.utils.safe_getattr(doc, field_config.field_name, None)

	# Get validation type (enhanced feature)
	validation_type = getattr(field_config, 'validation_type', 'Required')

	# Check if field is empty based on validation type
	is_empty = False

	if validation_type == "Required" or validation_type == "Conditionally Required":
		is_empty = not frappe.utils.has_value(field_value)

	elif validation_type == "Format Validation":
		# Format validation
		if hasattr(field_config, 'format_pattern') and field_config.format_pattern:
			import re
			if field_value and not re.match(field_config.format_pattern, str(field_value)):
				return _get_field_error_message(field_config, "does not match required format")

		# Length validation
		if field_value:
			value_str = str(field_value)
			if hasattr(field_config, 'min_length') and field_config.min_length:
				if len(value_str) < field_config.min_length:
					return _get_field_error_message(
						field_config,
						f"must be at least {field_config.min_length} characters"
					)
			if hasattr(field_config, 'max_length') and field_config.max_length:
				if len(value_str) > field_config.max_length:
					return _get_field_error_message(
						field_config,
						f"must not exceed {field_config.max_length} characters"
					)

	elif validation_type == "Custom Validation":
		# Custom validation script
		if hasattr(field_config, 'validation_script') and field_config.validation_script:
			try:
				context = {
					"value": field_value,
					"doc": doc,
					"user": frappe.session.user,
					"frappe": frappe
				}
				result = frappe.safe_eval(
					field_config.validation_script,
					eval_globals=context,
					eval_locals=context
				)
				if not result:
					return _get_field_error_message(field_config, "validation failed")
			except Exception:
				pass

	# Check if field is empty for required validation
	if validation_type in ["Required", "Conditionally Required"] and is_empty:
		return _get_field_error_message(field_config, "is required")

	return None




def _get_field_error_message(field_config, default_suffix: str) -> str:
	"""
	Get error message for a field.

	Args:
		field_config: Field configuration
		default_suffix: Default message suffix

	Returns:
		Formatted error message
	"""
	if field_config.custom_error_message:
		return field_config.custom_error_message

	field_label = field_config.field_label or field_config.field_name.replace('_', ' ').title()
	return f"<strong>{field_label}</strong> {default_suffix}"


def _validate_child_tables(doc, mandatory_fields) -> List[str]:
	"""
	Validate mandatory fields in child tables.

	Args:
		doc: Parent document
		mandatory_fields: List of mandatory field configurations

	Returns:
		List of error messages
	"""
	errors = []
	meta = frappe.get_meta(doc.doctype)

	for field in meta.fields:
		if field.fieldtype == "Table":
			child_docs = doc.get(field.fieldname, [])
			for idx, child_doc in enumerate(child_docs, 1):
				for field_config in mandatory_fields:
					# Check if field exists in child table
					try:
						child_meta = frappe.get_meta(field.options)
						if child_meta.has_field(field_config.field_name):
							error = _validate_single_field(child_doc, field_config)
							if error:
								errors.append(f"Row #{idx} in {field.label}: {error}")
					except Exception:
						continue

	return errors


def _format_error_html(errors: List[str]) -> str:
	"""
	Format error messages as HTML.

	Args:
		errors: List of error messages

	Returns:
		Formatted HTML string
	"""
	if not errors:
		return ""

	error_html = "<div style='text-align: left;'>"
	error_html += "<ul style='margin: 10px 0; padding-left: 20px;'>"

	for error in errors:
		error_html += f"<li style='margin: 5px 0;'>{error}</li>"

	error_html += "</ul></div>"

	return error_html


# Additional utility functions for enhanced features

def monitor_field_change(doc, field_name: str, old_value: Any, new_value: Any):
	"""
	Monitor field changes and trigger validation if needed.

	Args:
		doc: Document with field change
		field_name: Field that changed
		old_value: Previous value
		new_value: New value
	"""
	try:
		from .field_monitor import get_field_monitor
		from .event_engine import get_event_engine

		monitor = get_field_monitor()
		triggered_controllers = monitor.check_field_triggers(
			doc,
			{field_name: (old_value, new_value)}
		)

		if triggered_controllers:
			engine = get_event_engine()
			for controller in triggered_controllers:
				engine.execute_for_field_change(doc, field_name, old_value, new_value)

	except ImportError:
		# Enhanced features not available
		pass


def clear_validation_cache(doctype: str = None):
	"""
	Clear validation cache for a doctype or all doctypes.

	Args:
		doctype: Optional doctype to clear cache for
	"""
	try:
		from .event_engine import get_event_engine
		from .field_monitor import get_field_monitor

		engine = get_event_engine()
		monitor = get_field_monitor()

		engine.clear_cache(doctype)
		monitor.clear_cache(doctype)

	except ImportError:
		# Enhanced features not available
		pass

	# Clear legacy cache keys
	if doctype:
		frappe.cache().delete_value(f"mandatory_field_controllers_{doctype}")
	else:
		# Clear all related cache
		for key in frappe.cache().get_keys("mandatory_field_controllers_*"):
			frappe.cache().delete_value(key)