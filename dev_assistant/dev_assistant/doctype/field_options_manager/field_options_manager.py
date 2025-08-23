# Copyright (c) 2025, Dev Assistant and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _
from frappe.model.document import Document
from datetime import datetime

class FieldOptionsManager(Document):
	def autoname(self):
		"""Generate simple name for Field Options Manager documents"""
		try:
			# Get doctype name
			doctype_name = self.doctype_name or 'Unknown'
			
			# Get field name
			field_name = self.field_name or 'All'
			if self.apply_to_all_fields:
				field_name = 'All'
			
			# Create simple name: {Doctype}-{Field}
			generated_name = f"{doctype_name}-{field_name}"
			
			# Ensure name is unique
			counter = 1
			original_name = generated_name
			while frappe.db.exists('Field Options Manager', generated_name):
				generated_name = f"{original_name}-{counter}"
				counter += 1
			
			self.name = generated_name
			
		except Exception as e:
			frappe.log_error(f"Error generating Field Options Manager name: {str(e)}")
	
	def validate(self):
		self.validate_configurations()
		self.validate_conditions()
	
	def validate_configurations(self):
		"""Validate options configurations"""
		if not self.options_configuration:
			return
		
		# Check for duplicate configurations
		configs = []
		for config in self.options_configuration:
			config_key = (config.condition_value, config.option_value)
			if config_key in configs:
				frappe.throw(_("Duplicate configuration found for condition: {0}, option: {1}").format(
					config.condition_value, config.option_value))
			configs.append(config_key)
	
	def validate_conditions(self):
		"""Validate conditions - no duplicate conditions"""
		if not self.conditions:
			return
		
		# Check for duplicate conditions
		condition_fields = []
		for condition in self.conditions:
			if condition.condition_field in condition_fields:
				frappe.throw(_("Duplicate condition field found: {0}").format(condition.condition_field))
			condition_fields.append(condition.condition_field)

@frappe.whitelist()
def get_doctype_fields(doctype_name):
	"""Get all fields for a given doctype"""
	try:
		meta = frappe.get_meta(doctype_name)
		fields = []
		
		for field in meta.fields:
			# Skip system fields and child tables
			if field.fieldname in ['name', 'owner', 'creation', 'modified', 'modified_by', 'docstatus']:
				continue
			
			# Only include fields that can have options
			if field.fieldtype in ['Link', 'Select', 'MultiSelect', 'Dynamic Link']:
				fields.append({
					'fieldname': field.fieldname,
					'label': field.label,
					'fieldtype': field.fieldtype,
					'options': field.options if hasattr(field, 'options') else None
				})
		
		return fields
	except Exception as e:
		frappe.log_error(f"Error getting fields for doctype {doctype_name}: {str(e)}")
		return []

@frappe.whitelist()
def get_field_options(doctype_name, field_name, docname=None):
	"""Get dynamic options for a field based on configurations"""
	try:
		# Get active configurations for this doctype and field
		configurations = get_active_configurations(doctype_name, field_name, docname)
		
		if not configurations:
			return []
		
		# Get current document values for condition evaluation
		doc_values = {}
		if docname:
			doc = frappe.get_doc(doctype_name, docname)
			doc_values = doc.as_dict()
		
		# Evaluate conditions and get options
		options = []
		for config in configurations:
			if should_apply_configuration(config, doc_values):
				options.extend(get_configuration_options(config))
		
		return list(set(options))  # Remove duplicates
	except Exception as e:
		frappe.log_error(f"Error getting field options: {str(e)}")
		return []

def should_apply_configuration(config, doc_values):
	"""Check if configuration should apply based on conditions"""
	try:
		if not config.get('enable_conditions'):
			return True
		
		conditions = frappe.get_all(
			'Field Options Condition',
			filters={'parent': config.name, 'is_active': 1},
			fields=['condition_field', 'condition_operator', 'condition_value']
		)
		
		for condition in conditions:
			field_value = doc_values.get(condition.condition_field)
			if not evaluate_condition(field_value, condition.condition_operator, condition.condition_value):
				return False
		
		return True
	except Exception as e:
		frappe.log_error(f"Error evaluating configuration conditions: {str(e)}")
		return True

def evaluate_condition(field_value, operator, expected_value):
	"""Evaluate a single condition"""
	try:
		if operator == 'equals':
			return field_value == expected_value
		elif operator == 'not equals':
			return field_value != expected_value
		elif operator == 'contains':
			return expected_value in str(field_value) if field_value else False
		elif operator == 'not contains':
			return expected_value not in str(field_value) if field_value else True
		elif operator == 'is empty':
			return not field_value
		elif operator == 'is not empty':
			return bool(field_value)
		elif operator == 'greater than':
			return float(field_value or 0) > float(expected_value)
		elif operator == 'less than':
			return float(field_value or 0) < float(expected_value)
		else:
			return True
	except Exception as e:
		frappe.log_error(f"Error evaluating condition: {str(e)}")
		return True

def get_configuration_options(config):
	"""Get options from a configuration"""
	try:
		options = []
		config_details = frappe.get_all(
			'Field Options Configuration',
			filters={'parent': config.name, 'is_active': 1},
			fields=['option_value', 'option_label']
		)
		
		for detail in config_details:
			if detail.option_label:
				options.append(detail.option_label)
			else:
				options.append(detail.option_value)
		
		return options
	except Exception as e:
		frappe.log_error(f"Error getting configuration options: {str(e)}")
		return []

@frappe.whitelist()
def get_active_configurations(doctype_name=None, field_name=None, docname=None):
	"""Get active field options configurations"""
	try:
		filters = {'is_active': 1}
		
		if doctype_name and not frappe.db.get_value('Field Options Manager', filters, 'apply_to_all_doctypes'):
			filters['doctype_name'] = doctype_name
		
		if field_name and not frappe.db.get_value('Field Options Manager', filters, 'apply_to_all_fields'):
			filters['field_name'] = field_name
		
		configurations = frappe.get_all(
			'Field Options Manager',
			filters=filters,
			fields=['name', 'doctype_name', 'field_name', 'apply_to_all_doctypes', 'apply_to_all_fields', 'enable_conditions']
		)
		
		return configurations
	except Exception as e:
		frappe.log_error(f"Error getting active configurations: {str(e)}")
		return []

@frappe.whitelist()
def add_options_configuration(docname, options_data):
	"""Add options configuration to a Field Options Manager document"""
	try:
		doc = frappe.get_doc("Field Options Manager", docname)
		
		# Parse options data (expecting JSON string)
		if isinstance(options_data, str):
			options_data = json.loads(options_data)
		
		added_count = 0
		for option in options_data:
			option_value = option.get('option_value')
			option_label = option.get('option_label', option_value)
			
			if option_value:
				doc.append('options_configuration', {
					'option_value': option_value,
					'option_label': option_label,
					'is_active': 1
				})
				added_count += 1
		
		doc.save()
		
		return {
			'status': 'success',
			'message': f'Successfully added {added_count} option(s)',
			'added_count': added_count
		}
		
	except Exception as e:
		frappe.log_error(f"Error adding options configuration: {str(e)}")
		return {
			'status': 'error',
			'message': str(e)
		}

