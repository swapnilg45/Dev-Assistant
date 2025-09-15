# Copyright (c) 2025, Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _
from frappe.model.document import Document
import json
from datetime import datetime

class FieldAccessControl(Document):
	def autoname(self):
		"""Generate simple name for Field Access Control documents"""
		try:
			# Get doctype name
			doctype_name = self.doctype_name or 'Unknown'
			
			# Get role name
			role = self.role or 'All'
			if self.apply_to_all_roles:
				role = 'All'
			
			# Create simple name: {Doctype}-{Role}
			generated_name = f"{doctype_name}-{role}"
			
			# Ensure name is unique
			counter = 1
			original_name = generated_name
			while frappe.db.exists('Field Access Control', generated_name):
				generated_name = f"{original_name}-{counter}"
				counter += 1
			
			self.name = generated_name
			
		except Exception as e:
			frappe.log_error(f"Error generating Field Access Control name: {str(e)}")
	
	def validate(self):
		self.validate_configurations()
		self.validate_user_exceptions()
		self.validate_child_table_configurations()
	
	def validate_configurations(self):
		"""Validate field configurations"""
		if not self.field_configurations:
			return
		
		# Check for duplicate field configurations
		fieldnames = []
		for config in self.field_configurations:
			if config.fieldname in fieldnames:
				frappe.throw(_("Duplicate field configuration found for field: {0}").format(config.fieldname))
			fieldnames.append(config.fieldname)
	
	def validate_user_exceptions(self):
		"""Validate user exceptions - no duplicate users"""
		if not self.user_exceptions:
			return
		
		# Check for duplicate users in exceptions
		users = []
		for exception in self.user_exceptions:
			if exception.user in users:
				frappe.throw(_("Duplicate user found in exceptions: {0}").format(exception.user))
			users.append(exception.user)
	
	def validate_child_table_configurations(self):
		"""Validate child table configurations - no duplicate table fieldnames"""
		if not self.child_table_configurations:
			return
		
		# Check for duplicate table fieldnames
		table_fieldnames = []
		for config in self.child_table_configurations:
			if config.table_fieldname in table_fieldnames:
				frappe.throw(_("Duplicate child table configuration found for table: {0}").format(config.table_fieldname))
			table_fieldnames.append(config.table_fieldname)




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
def get_child_table_fields(doctype_name):
	"""Get child table fields for a given doctype"""
	try:
		meta = frappe.get_meta(doctype_name)
		child_tables = []
		
		for field in meta.fields:
			if field.fieldtype == 'Table':
				child_tables.append({
					'fieldname': field.fieldname,
					'label': field.label,
					'fieldtype': field.fieldtype,
					'options': field.options
				})
		
		return child_tables
	except Exception as e:
		frappe.log_error(f"Error getting child table fields for doctype {doctype_name}: {str(e)}")
		return []

def is_user_excepted(config_name, user):
	"""Check if user is in exception list for a configuration"""
	try:
		# First check if user exceptions are enabled for this config
		enable_user_exceptions = frappe.db.get_value("Field Access Control", config_name, "enable_user_exceptions")
		frappe.log_error(f"DEBUG: config_name={config_name}, user={user}, enable_user_exceptions={enable_user_exceptions}")
		
		if not enable_user_exceptions:
			frappe.log_error(f"DEBUG: User exceptions disabled for {config_name}")
			return False
		
		# Then check if user is in exception list
		exceptions = frappe.get_all(
			'User Exception Detail',
			filters={
				'parent': config_name,
				'user': user,
				'is_active': 1
			},
			fields=['name']
		)
		frappe.log_error(f"DEBUG: Found {len(exceptions)} exceptions for user {user}")
		return len(exceptions) > 0
	except Exception as e:
		frappe.log_error(f"Error checking user exceptions: {str(e)}")
		return False

def should_apply_to_docname(config, docname):
	"""Check if configuration should apply to specific document"""
	try:
		if not docname:
			return True
			
		# Check document name filter
		if config.docname_filter == 'All Documents':
			return True
		elif config.docname_filter == 'Specific Document':
			return docname == config.specific_docname
		elif config.docname_filter == 'Document Name Pattern':
			import fnmatch
			return fnmatch.fnmatch(docname, config.docname_pattern)
		elif config.docname_filter == 'Custom Condition':
			# Execute custom Python code
			if config.custom_condition:
				locals_dict = {'docname': docname, 'config': config}
				return eval(config.custom_condition, {}, locals_dict)
		
		return True
	except Exception as e:
		frappe.log_error(f"Error checking docname filter: {str(e)}")
		return True

@frappe.whitelist()
def add_field_configurations(docname, fieldnames):
	"""Add field configurations to a Field Access Control document"""
	try:
		doc = frappe.get_doc("Field Access Control", docname)
		
		# Get existing fieldnames to avoid duplicates
		existing_fieldnames = [config.fieldname for config in doc.field_configurations]
		
		# Parse fieldnames (expecting JSON string)
		if isinstance(fieldnames, str):
			fieldnames = json.loads(fieldnames)
		
		added_count = 0
		for field_data in fieldnames:
			fieldname = field_data.get('fieldname')
			field_label = field_data.get('label')
			
			if fieldname and fieldname not in existing_fieldnames:
				doc.append('field_configurations', {
					'fieldname': fieldname,
					'field_label': field_label,
					'action_type': 'Hide',
					'is_active': 1
				})
				added_count += 1
		
		doc.save()
		
		return {
			'status': 'success',
			'message': f'Successfully added {added_count} field(s)',
			'added_count': added_count
		}
		
	except Exception as e:
		frappe.log_error(f"Error adding field configurations: {str(e)}")
		return {
			'status': 'error',
			'message': str(e)
		}

@frappe.whitelist()
def get_active_configurations(doctype_name=None, role=None, docname=None):
	"""Get active field access configurations"""
	try:
		filters = {'is_active': 1}
		
		if doctype_name:
			filters['doctype_name'] = doctype_name
		
		if role:
			filters['role'] = role
		
		configurations = frappe.get_all(
			'Field Access Control',
			filters=filters,
			fields=['name', 'doctype_name', 'role', 'apply_to_all_roles', 'docname_filter', 'docname_pattern', 'specific_docname', 'custom_condition', 'enable_child_table_control']
		)
		
		# Filter configurations based on docname and user exceptions
		filtered_configurations = []
		current_user = frappe.session.user
		
		for config in configurations:
			# Check if user is in exception list (only if user exceptions are enabled)
			if is_user_excepted(config.name, current_user):
				continue
				
			if should_apply_to_docname(config, docname):
				# Get detailed field configurations for this config
				field_configs = frappe.get_all(
					'Field Configuration Detail',
					filters={
						'parent': config.name,
						'is_active': 1
					},
					fields=['fieldname', 'field_label', 'action_type', 'is_active']
				)
				config.field_configurations = field_configs
				
				# Get child table configurations if enabled
				if config.enable_child_table_control:
					child_table_configs = frappe.get_all(
						'Child Table Button Configuration',
						filters={
							'parent': config.name,
							'is_active': 1
						},
						fields=['table_fieldname', 'table_label', 'hide_add_button', 'hide_delete_button', 'is_active']
					)
					config.child_table_configurations = child_table_configs
				else:
					config.child_table_configurations = []
				
				filtered_configurations.append(config)
		
		return filtered_configurations
	except Exception as e:
		frappe.log_error(f"Error getting active configurations: {str(e)}")
		return []

def should_apply_to_docname(config, docname):
	"""Check if configuration should apply to the given document name"""
	if not docname:
		return True
	
	docname_filter = config.get('docname_filter', 'All Documents')
	
	if docname_filter == 'All Documents':
		return True
	elif docname_filter == 'Specific Document':
		specific_docname = config.get('specific_docname', '')
		return docname == specific_docname
	elif docname_filter == 'Document Name Pattern':
		pattern = config.get('docname_pattern', '')
		if pattern:
			import fnmatch
			return fnmatch.fnmatch(docname, pattern)
		return False
	elif docname_filter == 'Custom Condition':
		custom_condition = config.get('custom_condition', '')
		if custom_condition:
			try:
				# Create a safe environment for evaluation
				locals_dict = {
					'docname': docname,
					'frappe': frappe,
					'get_doc': frappe.get_doc,
					'get_value': frappe.get_value,
					'get_list': frappe.get_list
				}
				return eval(custom_condition, {"__builtins__": {}}, locals_dict)
			except Exception as e:
				frappe.log_error(f"Error evaluating custom condition: {str(e)}")
				return False
		return False
	
	return True


