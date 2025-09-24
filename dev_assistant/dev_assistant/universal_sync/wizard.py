# Copyright (c) 2025, Swapnil and contributors
# Wizard helper functions for creating sync chains

import frappe
from frappe import _
import json


@frappe.whitelist()
def create_sync_chain_from_wizard(process_data, activate_immediately=True):
	"""Create sync chain from wizard data"""
	try:
		# Parse process data if it's a string
		if isinstance(process_data, str):
			process_data = json.loads(process_data)

		# Create new sync chain document
		chain_doc = frappe.new_doc("Sync Chain")
		chain_doc.chain_name = process_data.get("process_name", "New Sync Process")
		chain_doc.description = process_data.get("description", "")
		chain_doc.is_active = 1 if activate_immediately else 0

		# Set template reference
		template_key = process_data.get("template_key")
		if template_key and template_key != "custom":
			chain_doc.template_used = template_key

		# Apply settings
		settings = process_data.get("settings", {})
		chain_doc.sync_frequency = settings.get("sync_frequency", "Immediately")
		chain_doc.conflict_resolution = settings.get("conflict_resolution", "Use Latest Data")

		# Add steps
		steps = process_data.get("steps", [])
		field_mappings = process_data.get("field_mappings", {})

		for step_data in steps:
			step_row = chain_doc.append("chain_steps")
			step_row.step_number = step_data.get("step_number")
			step_row.doctype_name = step_data.get("doctype_name")
			step_row.doctype_label = step_data.get("doctype_label") or step_data.get("doctype_name")
			step_row.sync_condition = step_data.get("sync_condition", "Always")

			# Add field mappings for this step
			step_index = step_data.get("step_number", 1) - 1
			if str(step_index) in field_mappings:
				step_row.field_mappings = json.dumps(field_mappings[str(step_index)], indent=2)

		# Validate and save
		chain_doc.insert()

		return {
			"success": True,
			"chain_name": chain_doc.name,
			"chain_title": chain_doc.chain_name,
			"message": _("Sync process '{}' created successfully{}").format(
				chain_doc.chain_name,
				" and activated" if activate_immediately else ""
			)
		}

	except Exception as e:
		frappe.log_error(f"Wizard sync chain creation failed: {str(e)}", "Sync Chain Wizard")
		return {
			"success": False,
			"message": _("Failed to create sync process: {}").format(str(e))
		}


@frappe.whitelist()
def validate_wizard_configuration(process_data):
	"""Validate wizard configuration before creation"""
	try:
		if isinstance(process_data, str):
			process_data = json.loads(process_data)

		errors = []
		warnings = []

		# Validate basic info
		if not process_data.get("process_name"):
			errors.append(_("Process name is required"))

		# Validate steps
		steps = process_data.get("steps", [])
		if not steps:
			errors.append(_("At least one process step is required"))

		# Validate DocTypes exist
		for step in steps:
			doctype_name = step.get("doctype_name")
			if doctype_name:
				if not frappe.db.exists("DocType", doctype_name):
					errors.append(_("DocType '{}' does not exist").format(doctype_name))
				else:
					# Check permissions
					try:
						frappe.get_meta(doctype_name)
					except frappe.PermissionError:
						warnings.append(_("Limited access to DocType '{}'").format(doctype_name))

		# Validate field mappings
		field_mappings = process_data.get("field_mappings", {})
		for step_index, mappings in field_mappings.items():
			if isinstance(mappings, dict) and mappings:
				# Basic validation - could be enhanced
				if len(mappings) == 0:
					warnings.append(_("No field mappings configured for step {}").format(int(step_index) + 1))

		return {
			"valid": len(errors) == 0,
			"errors": errors,
			"warnings": warnings
		}

	except Exception as e:
		return {
			"valid": False,
			"errors": [_("Configuration validation failed: {}").format(str(e))],
			"warnings": []
		}


@frappe.whitelist()
def get_wizard_doctype_suggestions(search_term=""):
	"""Get DocType suggestions for wizard"""
	filters = {
		'issingle': 0,
		'istable': 0,
		'module': ['not in', ['Core', 'Desk', 'Custom', 'Website']]
	}

	if search_term:
		# Add search filter
		doctypes = frappe.db.sql("""
			SELECT name, description, module
			FROM `tabDocType`
			WHERE issingle = 0 AND istable = 0
			AND module NOT IN ('Core', 'Desk', 'Custom', 'Website')
			AND (name LIKE %(search)s OR description LIKE %(search)s)
			ORDER BY
				CASE WHEN name LIKE %(exact)s THEN 1 ELSE 2 END,
				name
			LIMIT 20
		""", {
			'search': f"%{search_term}%",
			'exact': f"{search_term}%"
		}, as_dict=True)
	else:
		doctypes = frappe.get_all("DocType",
			filters=filters,
			fields=["name", "description", "module"],
			order_by="name",
			limit=50
		)

	# Add usage hints for common DocTypes
	usage_hints = {
		'Lead': 'Sales leads and prospects',
		'Customer': 'Customer master data',
		'Opportunity': 'Sales opportunities',
		'Quotation': 'Price quotations to customers',
		'Sales Order': 'Confirmed sales orders',
		'Job Applicant': 'Job applications and candidates',
		'Employee': 'Employee master records',
		'Project': 'Project management',
		'Task': 'Project tasks and activities',
		'Purchase Order': 'Purchase orders to suppliers',
		'Sales Invoice': 'Sales invoices to customers',
		'Item': 'Product and service items'
	}

	for doctype in doctypes:
		doctype['usage_hint'] = usage_hints.get(doctype['name'], doctype.get('description', ''))

	return doctypes


@frappe.whitelist()
def get_doctype_fields_for_wizard(doctype):
	"""Get DocType fields formatted for wizard use"""
	try:
		meta = frappe.get_meta(doctype)
		fields = []

		for field in meta.fields:
			if field.fieldtype not in ['Section Break', 'Column Break', 'HTML', 'Heading']:
				if not field.fieldname.startswith('__'):
					fields.append({
						'fieldname': field.fieldname,
						'label': field.label or field.fieldname,
						'fieldtype': field.fieldtype,
						'reqd': field.reqd,
						'description': field.description,
						'options': field.options,
						'is_system_field': field.fieldname in ['name', 'owner', 'creation', 'modified']
					})

		# Sort fields: required first, then alphabetically
		fields.sort(key=lambda x: (not x['reqd'], x['label'].lower()))

		return fields

	except Exception as e:
		frappe.throw(_("Failed to get fields for DocType '{}': {}").format(doctype, str(e)))


@frappe.whitelist()
def preview_wizard_sync_flow(process_data):
	"""Preview the sync flow before creation"""
	try:
		if isinstance(process_data, str):
			process_data = json.loads(process_data)

		steps = process_data.get("steps", [])
		field_mappings = process_data.get("field_mappings", {})

		flow_preview = {
			"steps": [],
			"connections": [],
			"summary": {
				"total_steps": len(steps),
				"total_mappings": sum(len(mappings) for mappings in field_mappings.values() if isinstance(mappings, dict)),
				"estimated_records_per_hour": estimate_sync_volume(steps)
			}
		}

		# Build step details
		for step in steps:
			step_detail = {
				"step_number": step.get("step_number"),
				"doctype_name": step.get("doctype_name"),
				"doctype_label": step.get("doctype_label"),
				"sync_condition": step.get("sync_condition"),
				"field_count": len(field_mappings.get(str(step.get("step_number", 1) - 1), {}))
			}

			# Add record count estimate if possible
			try:
				record_count = frappe.db.count(step.get("doctype_name"))
				step_detail["existing_records"] = record_count
			except:
				step_detail["existing_records"] = "Unknown"

			flow_preview["steps"].append(step_detail)

		# Build connections between steps
		for i in range(len(steps) - 1):
			connection = {
				"from_step": i + 1,
				"to_step": i + 2,
				"field_mappings": field_mappings.get(str(i), {}),
				"mapping_count": len(field_mappings.get(str(i), {}))
			}
			flow_preview["connections"].append(connection)

		return flow_preview

	except Exception as e:
		frappe.log_error(f"Preview generation failed: {str(e)}", "Sync Wizard Preview")
		return {"error": str(e)}


def estimate_sync_volume(steps):
	"""Estimate sync volume per hour based on DocTypes"""
	# Simple heuristic based on DocType complexity
	base_rate = 1000  # records per hour base rate

	complexity_factors = {
		'Lead': 1.0,
		'Customer': 0.8,
		'Opportunity': 0.9,
		'Quotation': 0.7,
		'Sales Order': 0.6,
		'Employee': 0.8,
		'Project': 0.5,
		'Task': 1.2
	}

	if not steps:
		return base_rate

	# Use the most complex step as the bottleneck
	min_factor = min(complexity_factors.get(step.get("doctype_name", ""), 0.7) for step in steps)
	return int(base_rate * min_factor)


@frappe.whitelist()
def save_wizard_draft(process_data):
	"""Save wizard progress as draft"""
	try:
		# Store in user's preferences or a temporary DocType
		user = frappe.session.user
		draft_key = f"sync_wizard_draft_{user}"

		frappe.cache().set_value(draft_key, process_data, expires_in_sec=3600)  # 1 hour

		return {
			"success": True,
			"message": _("Wizard progress saved")
		}

	except Exception as e:
		return {
			"success": False,
			"message": _("Failed to save progress: {}").format(str(e))
		}


@frappe.whitelist()
def load_wizard_draft():
	"""Load saved wizard draft"""
	try:
		user = frappe.session.user
		draft_key = f"sync_wizard_draft_{user}"

		draft_data = frappe.cache().get_value(draft_key)

		if draft_data:
			return {
				"success": True,
				"data": draft_data
			}
		else:
			return {
				"success": False,
				"message": _("No saved draft found")
			}

	except Exception as e:
		return {
			"success": False,
			"message": _("Failed to load draft: {}").format(str(e))
		}


@frappe.whitelist()
def clear_wizard_draft():
	"""Clear saved wizard draft"""
	try:
		user = frappe.session.user
		draft_key = f"sync_wizard_draft_{user}"

		frappe.cache().delete_value(draft_key)

		return {
			"success": True,
			"message": _("Draft cleared")
		}

	except Exception as e:
		return {
			"success": False,
			"message": _("Failed to clear draft: {}").format(str(e))
		}