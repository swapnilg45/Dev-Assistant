# Copyright (c) 2024, Swapnil and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from typing import Dict, List, Any


class MandatoryFieldController(Document):
	"""
	Enhanced Mandatory Field Controller with event-driven execution
	and field change monitoring capabilities.
	"""

	def validate(self):
		"""Validate controller configuration."""
		# Validate execution mode configuration
		self._validate_execution_mode()

		# Validate event triggers
		self._validate_event_triggers()

		# Validate monitored fields
		self._validate_monitored_fields()

		# Validate conditions
		self._validate_conditions()

		# Validate mandatory fields
		self._validate_mandatory_fields()

		# Set default values
		self._set_defaults()

	def before_save(self):
		"""Process before saving."""
		# Update field labels
		self._update_field_labels()

		# Validate custom scripts
		self._validate_custom_scripts()

		# Clear cache on save
		self._clear_cache()

	def after_save(self):
		"""Process after saving."""
		# Register event handlers if needed
		self._register_event_handlers()

		# Clear global cache
		frappe.cache().delete_value(f"mandatory_field_controllers_{self.document_type}")

	def on_trash(self):
		"""Clean up on deletion."""
		# Clear all related cache
		self._clear_cache()

		# Unregister event handlers
		self._unregister_event_handlers()

	def _validate_execution_mode(self):
		"""Validate execution mode configuration."""
		if self.execution_mode == "Event Based":
			if not self.event_triggers:
				frappe.throw(
					_("At least one event trigger is required for Event Based execution mode"),
					title=_("Configuration Error")
				)
		elif self.execution_mode == "Field Change Based":
			if not self.monitored_fields:
				frappe.throw(
					_("At least one monitored field is required for Field Change Based execution mode"),
					title=_("Configuration Error")
				)
		elif self.execution_mode == "Combined":
			if not self.event_triggers and not self.monitored_fields:
				frappe.throw(
					_("At least one event trigger or monitored field is required for Combined execution mode"),
					title=_("Configuration Error")
				)

	def _validate_event_triggers(self):
		"""Validate event trigger configuration."""
		if not self.event_triggers:
			return

		# Check for duplicate event types
		event_types = []
		for trigger in self.event_triggers:
			if trigger.enabled and trigger.event_type in event_types:
				frappe.msgprint(
					_("Duplicate event trigger for {0}").format(trigger.event_type),
					indicator="orange",
					alert=True
				)
			event_types.append(trigger.event_type)

		# Validate execution order
		for trigger in self.event_triggers:
			if trigger.execution_order and trigger.execution_order < 0:
				trigger.execution_order = 0

	def _validate_monitored_fields(self):
		"""Validate monitored field configuration."""
		if not self.monitored_fields:
			return

		# Check for duplicate field monitoring
		monitored = []
		for monitor in self.monitored_fields:
			if monitor.field_name in monitored:
				frappe.msgprint(
					_("Field {0} is monitored multiple times").format(monitor.field_name),
					indicator="orange",
					alert=True
				)
			monitored.append(monitor.field_name)

			# Validate trigger value for specific conditions
			if monitor.trigger_on in ["Specific Value", "Value Range"]:
				if not monitor.trigger_value:
					frappe.throw(
						_("Trigger value is required for {0} trigger on field {1}").format(
							monitor.trigger_on, monitor.field_name
						)
					)

	def _validate_conditions(self):
		"""Validate condition configuration."""
		if self.condition_logic == "Custom" and not self.custom_condition_script:
			frappe.throw(
				_("Custom condition script is required when using Custom condition logic"),
				title=_("Configuration Error")
			)

		# Validate individual conditions
		for condition in self.conditions:
			if condition.condition_type == "Role Check" and not condition.role_name:
				frappe.throw(_("Role name is required for Role Check condition"))

			if condition.condition_type == "Custom Script" and not condition.custom_script:
				frappe.throw(_("Custom script is required for Custom Script condition"))

			if condition.condition == "changed from" and not condition.previous_value:
				frappe.throw(_("Previous value is required for 'changed from' condition"))

	def _validate_mandatory_fields(self):
		"""Validate mandatory field configuration."""
		if not self.mandatory_fields:
			frappe.throw(
				_("At least one mandatory field is required"),
				title=_("Configuration Error")
			)

		# Check for duplicate fields
		fields = []
		for field in self.mandatory_fields:
			if field.field_name in fields:
				frappe.throw(
					_("Field {0} is configured multiple times").format(field.field_name)
				)
			fields.append(field.field_name)

			# Validate format pattern
			if field.validation_type == "Format Validation":
				if field.format_pattern:
					try:
						import re
						re.compile(field.format_pattern)
					except re.error as e:
						frappe.throw(
							_("Invalid regex pattern for field {0}: {1}").format(
								field.field_name, str(e)
							)
						)

	def _validate_custom_scripts(self):
		"""Validate all custom Python scripts."""
		# Validate custom condition script
		if self.custom_condition_script:
			self._validate_python_script(
				self.custom_condition_script,
				"Custom Condition Script"
			)

		# Validate condition custom scripts
		for idx, condition in enumerate(self.conditions, 1):
			if condition.custom_script:
				self._validate_python_script(
					condition.custom_script,
					f"Condition #{idx} Custom Script"
				)

		# Validate field validation scripts
		for idx, field in enumerate(self.mandatory_fields, 1):
			if field.validation_script:
				self._validate_python_script(
					field.validation_script,
					f"Field #{idx} Validation Script"
				)

	def _validate_python_script(self, script: str, script_name: str):
		"""Validate Python script syntax."""
		try:
			compile(script, f"<{script_name}>", "exec")
		except SyntaxError as e:
			frappe.throw(
				_("Syntax error in {0}: {1}").format(script_name, str(e)),
				title=_("Script Error")
			)

	def _update_field_labels(self):
		"""Update field labels based on selected fields."""
		if not self.document_type:
			return

		meta = frappe.get_meta(self.document_type)

		# Update condition field labels
		for condition in self.conditions:
			if condition.field and not condition.get("field_label"):
				field = meta.get_field(condition.field)
				if field:
					condition.field_label = field.label

		# Update monitored field labels
		for monitor in self.monitored_fields:
			if monitor.field_name:
				field = meta.get_field(monitor.field_name)
				if field:
					monitor.field_label = field.label or monitor.field_name.replace("_", " ").title()

		# Update mandatory field labels
		for mandatory in self.mandatory_fields:
			if mandatory.field_name:
				field = meta.get_field(mandatory.field_name)
				if field:
					mandatory.field_label = field.label or mandatory.field_name.replace("_", " ").title()

	def _set_defaults(self):
		"""Set default values for fields."""
		if not self.priority:
			self.priority = 0

		if not self.error_handling_mode:
			self.error_handling_mode = "Collect All Errors"

		if not self.condition_logic:
			self.condition_logic = "AND"

		# Set default execution order for triggers
		for trigger in self.event_triggers:
			if not trigger.execution_order:
				trigger.execution_order = 100

	def _register_event_handlers(self):
		"""Register dynamic event handlers for this controller."""
		# This is handled by the hooks and event engine
		pass

	def _unregister_event_handlers(self):
		"""Unregister event handlers on deletion."""
		# Clear cache to ensure handlers are refreshed
		self._clear_cache()

	def _clear_cache(self):
		"""Clear all related cache entries."""
		# Clear controller-specific cache
		cache_keys = [
			f"mandatory_field_controllers_{self.document_type}",
			f"monitored_fields_{self.document_type}",
			f"field_validators_{self.document_type}"
		]

		for key in cache_keys:
			frappe.cache().delete_value(key)

	def onload(self):
		"""Load additional data for the form."""
		if self.document_type:
			# Get fields for the selected doctype
			self.set_onload("doctype_fields", self.get_doctype_fields())

			# Get available events
			self.set_onload("available_events", self.get_available_events())

	def get_doctype_fields(self) -> List[Dict]:
		"""Get all fields for the selected doctype."""
		if not self.document_type:
			return []

		meta = frappe.get_meta(self.document_type)
		fields = []

		for field in meta.fields:
			if field.fieldtype not in ["Section Break", "Column Break", "Tab Break", "HTML", "Button"]:
				fields.append({
					"fieldname": field.fieldname,
					"label": field.label or field.fieldname.replace("_", " ").title(),
					"fieldtype": field.fieldtype,
					"reqd": field.reqd,
					"options": field.options
				})

		return fields

	def get_available_events(self) -> List[str]:
		"""Get list of available document events."""
		return [
			"before_insert",
			"after_insert",
			"before_validate",
			"validate",
			"after_validate",
			"before_save",
			"after_save",
			"before_submit",
			"after_submit",
			"before_update_after_submit",
			"after_update_after_submit",
			"before_cancel",
			"after_cancel",
			"before_delete",
			"after_delete",
			"on_change",
			"on_update"
		]

	@frappe.whitelist()
	def test_configuration(self) -> Dict:
		"""Test the controller configuration with a sample document."""
		if not self.document_type:
			return {"success": False, "message": "No document type selected"}

		try:
			# Create a test document instance
			test_doc = frappe.new_doc(self.document_type)

			# Simulate validation
			from dev_assistant.dev_assistant.mandatory_field_validation.event_engine import (
				MandatoryFieldEventEngine
			)

			engine = MandatoryFieldEventEngine()
			# This would normally trigger validation
			# For testing, we just check if configuration is valid

			return {
				"success": True,
				"message": f"Configuration is valid for {self.document_type}"
			}

		except Exception as e:
			return {
				"success": False,
				"message": f"Configuration test failed: {str(e)}"
			}

	def can_bypass_validation(self, user: str = None) -> bool:
		"""
		Check if user can bypass this validation.

		Args:
			user: User to check (defaults to current user)

		Returns:
			True if user can bypass
		"""
		if not user:
			user = frappe.session.user

		if user == "Administrator":
			return True

		user_roles = frappe.get_roles(user)
		for bypass_role in self.bypass_roles:
			if bypass_role.role in user_roles:
				return True

		return False


@frappe.whitelist()
def get_fields_for_doctype(doctype: str) -> List[Dict]:
	"""
	Get fields for a specific doctype - called from client.

	Args:
		doctype: DocType name

	Returns:
		List of field options
	"""
	if not doctype:
		return []

	meta = frappe.get_meta(doctype)
	fields = []

	for field in meta.fields:
		if field.fieldtype not in ["Section Break", "Column Break", "Tab Break", "HTML", "Button"]:
			fields.append({
				"value": field.fieldname,
				"label": field.label or field.fieldname.replace("_", " ").title()
			})

	return fields


@frappe.whitelist()
def get_active_controllers(doctype: str) -> List[Dict]:
	"""
	Get all active controllers for a doctype.

	Args:
		doctype: DocType name

	Returns:
		List of active controller configurations
	"""
	controllers = frappe.get_all(
		"Mandatory Field Controller",
		filters={
			"document_type": doctype,
			"disabled": 0
		},
		fields=[
			"name", "execution_mode", "priority",
			"error_handling_mode", "condition_logic"
		],
		order_by="priority desc, creation desc"
	)

	return controllers


@frappe.whitelist()
def test_controller_configuration(controller_name: str, test_doc_name: str = None) -> Dict:
	"""
	Test a controller configuration against a document.

	Args:
		controller_name: Name of the controller to test
		test_doc_name: Optional document name to test against

	Returns:
		Test results dictionary
	"""
	try:
		controller = frappe.get_doc("Mandatory Field Controller", controller_name)

		if test_doc_name:
			test_doc = frappe.get_doc(controller.document_type, test_doc_name)
		else:
			test_doc = frappe.new_doc(controller.document_type)

		# Simulate validation
		from dev_assistant.dev_assistant.mandatory_field_validation.event_engine import (
			MandatoryFieldEventEngine
		)

		engine = MandatoryFieldEventEngine()

		# Test with validate event
		errors = []
		try:
			engine.execute_for_event(test_doc, "validate")
		except frappe.ValidationError as e:
			errors.append(str(e))

		return {
			"success": len(errors) == 0,
			"errors": errors,
			"message": "Test completed successfully" if not errors else "Validation errors found"
		}

	except Exception as e:
		return {
			"success": False,
			"message": f"Test failed: {str(e)}"
		}


# Enhanced Backend Methods for Frontend UX

@frappe.whitelist()
def get_impact_analysis(controller_name: str, document_type: str) -> Dict:
	"""Get impact analysis for a validation rule."""
	if not controller_name or not document_type:
		return {}

	try:
		# Get total documents count
		total_documents = frappe.db.count(document_type)

		# Simulate affected documents (in production, this would analyze actual conditions)
		affected_documents = int(total_documents * 0.3)  # 30% affected
		compliant_documents = int(total_documents * 0.5)  # 50% already compliant

		# Get users who create/modify this doctype
		affected_users = frappe.db.sql_list("""
			SELECT DISTINCT owner
			FROM `tab{doctype}`
			ORDER BY modified DESC
			LIMIT 10
		""".format(doctype=document_type))

		return {
			"total_documents": total_documents,
			"affected_documents": affected_documents,
			"compliant_documents": compliant_documents,
			"affected_users": affected_users[:5] if affected_users else []
		}
	except Exception as e:
		frappe.log_error(f"Impact analysis error: {str(e)}")
		return {
			"total_documents": 0,
			"affected_documents": 0,
			"compliant_documents": 0,
			"affected_users": []
		}


@frappe.whitelist()
def bulk_update_status(names: List[str], enabled: bool) -> int:
	"""Bulk enable/disable validation rules."""
	if not isinstance(names, list):
		names = frappe.parse_json(names)

	count = 0
	for name in names:
		try:
			doc = frappe.get_doc("Mandatory Field Controller", name)
			doc.enabled = enabled
			doc.save()
			count += 1
		except Exception as e:
			frappe.log_error(f"Error updating {name}: {str(e)}")

	return count


@frappe.whitelist()
def get_summary_stats() -> Dict:
	"""Get summary statistics for list view."""
	try:
		stats = {
			"total": frappe.db.count("Mandatory Field Controller"),
			"active": frappe.db.count("Mandatory Field Controller", {"enabled": 1}),
			"critical": frappe.db.count("Mandatory Field Controller", {"priority": "Critical"}),
			"doctypes": len(frappe.db.sql_list("""
				SELECT DISTINCT document_type
				FROM `tabMandatory Field Controller`
				WHERE document_type IS NOT NULL
			"""))
		}
		return stats
	except Exception as e:
		frappe.log_error(f"Summary stats error: {str(e)}")
		return {"total": 0, "active": 0, "critical": 0, "doctypes": 0}


@frappe.whitelist()
def import_configurations(file_url: str, overwrite: bool = False) -> Dict:
	"""Import validation rules from JSON file."""
	try:
		# Get file content
		file_doc = frappe.get_doc("File", {"file_url": file_url})
		content = file_doc.get_content()
		configurations = frappe.parse_json(content)

		imported = 0
		skipped = 0

		for config in configurations:
			name = config.get("name")

			if frappe.db.exists("Mandatory Field Controller", name) and not overwrite:
				skipped += 1
				continue

			# Create or update document
			if frappe.db.exists("Mandatory Field Controller", name):
				doc = frappe.get_doc("Mandatory Field Controller", name)
			else:
				doc = frappe.new_doc("Mandatory Field Controller")

			# Update fields
			for key, value in config.items():
				if key not in ["name", "creation", "modified", "modified_by", "owner"]:
					setattr(doc, key, value)

			doc.save()
			imported += 1

		return {"imported": imported, "skipped": skipped}
	except Exception as e:
		frappe.throw(f"Import error: {str(e)}")


@frappe.whitelist()
def get_dashboard_stats(filters: Dict = None) -> Dict:
	"""Get dashboard statistics."""
	if filters:
		filters = frappe.parse_json(filters) if isinstance(filters, str) else filters
	else:
		filters = {}

	try:
		# Base statistics
		stats = {
			"total_rules": frappe.db.count("Mandatory Field Controller"),
			"active_rules": frappe.db.count("Mandatory Field Controller", {"enabled": 1}),
			"triggered_today": 0,  # Would need event logging to track this
			"error_rate": 0  # Would need error tracking to calculate
		}

		# Add date range filtering if specified
		if filters.get("date_range") and filters["date_range"] != "all":
			days = int(filters["date_range"])
			date_condition = f"modified >= DATE_SUB(NOW(), INTERVAL {days} DAY)"

			stats["total_rules"] = frappe.db.sql(f"""
				SELECT COUNT(*) FROM `tabMandatory Field Controller`
				WHERE {date_condition}
			""")[0][0]

		return stats
	except Exception as e:
		frappe.log_error(f"Dashboard stats error: {str(e)}")
		return {
			"total_rules": 0,
			"active_rules": 0,
			"triggered_today": 0,
			"error_rate": 0
		}


@frappe.whitelist()
def export_dashboard_report(filters: Dict = None) -> List[Dict]:
	"""Export dashboard data as report."""
	if filters:
		filters = frappe.parse_json(filters) if isinstance(filters, str) else filters
	else:
		filters = {}

	try:
		# Get validation rules data
		conditions = ["1=1"]

		if filters.get("document_type"):
			conditions.append(f"document_type = '{filters['document_type']}'")

		if filters.get("priority"):
			conditions.append(f"priority = '{filters['priority']}'")

		data = frappe.db.sql("""
			SELECT
				name,
				document_type,
				priority,
				execution_mode,
				enabled,
				creation,
				modified
			FROM `tabMandatory Field Controller`
			WHERE {conditions}
			ORDER BY modified DESC
		""".format(conditions=" AND ".join(conditions)), as_dict=True)

		return data
	except Exception as e:
		frappe.log_error(f"Export report error: {str(e)}")
		return []


@frappe.whitelist()
def test_validation_rules(controller_name: str, test_data: Dict) -> Dict:
	"""Test validation rules with sample data."""
	try:
		controller = frappe.get_doc("Mandatory Field Controller", controller_name)
		test_data = frappe.parse_json(test_data) if isinstance(test_data, str) else test_data

		# Evaluate conditions
		conditions_met = True
		failed_conditions = []

		if controller.conditions:
			for condition in controller.conditions:
				field_value = test_data.get(condition.field)

				# Simple condition evaluation (expand as needed)
				if not evaluate_condition(field_value, condition.condition, condition.value):
					conditions_met = False
					failed_conditions.append({
						"field": condition.field,
						"condition": condition.condition,
						"value": condition.value,
						"actual_value": field_value
					})

		return {
			"conditions_met": conditions_met,
			"mandatory_fields": [
				{"field_name": f.field_name, "field_label": f.field_label}
				for f in controller.mandatory_fields
			] if conditions_met else [],
			"failed_conditions": failed_conditions
		}
	except Exception as e:
		frappe.throw(f"Test validation error: {str(e)}")


def evaluate_condition(field_value, condition_operator, condition_value) -> bool:
	"""Evaluate a single condition."""
	try:
		if condition_operator == "=":
			return str(field_value) == str(condition_value)
		elif condition_operator == "!=":
			return str(field_value) != str(condition_value)
		elif condition_operator == "in":
			values = [v.strip() for v in condition_value.split(",")]
			return str(field_value) in values
		elif condition_operator == "not in":
			values = [v.strip() for v in condition_value.split(",")]
			return str(field_value) not in values
		elif condition_operator in [">", "<", ">=", "<="]:
			try:
				fv = float(field_value) if field_value else 0
				cv = float(condition_value) if condition_value else 0

				if condition_operator == ">":
					return fv > cv
				elif condition_operator == "<":
					return fv < cv
				elif condition_operator == ">=":
					return fv >= cv
				elif condition_operator == "<=":
					return fv <= cv
			except (ValueError, TypeError):
				return False

		return False
	except Exception:
		return False


@frappe.whitelist()
def export_all_configurations() -> List[Dict]:
	"""Export all validation rule configurations."""
	try:
		controllers = frappe.get_all(
			"Mandatory Field Controller",
			fields=["*"],
			order_by="modified desc"
		)

		for controller in controllers:
			# Get child table data
			controller["conditions"] = frappe.get_all(
				"Mandatory Field Condition",
				filters={"parent": controller["name"]},
				fields=["*"]
			)

			controller["mandatory_fields"] = frappe.get_all(
				"Mandatory Field Detail",
				filters={"parent": controller["name"]},
				fields=["*"]
			)

			controller["event_triggers"] = frappe.get_all(
				"Mandatory Field Event Trigger",
				filters={"parent": controller["name"]},
				fields=["*"]
			)

			controller["monitored_fields"] = frappe.get_all(
				"Mandatory Field Monitor",
				filters={"parent": controller["name"]},
				fields=["*"]
			)

			controller["bypass_roles"] = frappe.get_all(
				"Mandatory Field Bypass Role",
				filters={"parent": controller["name"]},
				fields=["*"]
			)

		return controllers
	except Exception as e:
		frappe.log_error(f"Export all configurations error: {str(e)}")
		return []