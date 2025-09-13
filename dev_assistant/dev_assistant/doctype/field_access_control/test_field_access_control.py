# Copyright (c) 2025, Swapnil and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestFieldAccessControl(FrappeTestCase):
	def test_get_doctype_fields_with_child_tables(self):
		"""Test that get_doctype_fields returns both main and child table fields"""
		# Test with a doctype that has child tables (like Sales Invoice)
		fields = frappe.call('dev_assistant.dev_assistant.doctype.field_access_control.field_access_control.get_doctype_fields', 
							doctype_name='Sales Invoice')
		
		# Should return a dictionary with main_fields and child_table_fields
		self.assertIsInstance(fields, dict)
		self.assertIn('main_fields', fields)
		self.assertIn('child_table_fields', fields)
		self.assertIsInstance(fields['main_fields'], list)
		self.assertIsInstance(fields['child_table_fields'], list)
		
		# Should have some main fields
		self.assertGreater(len(fields['main_fields']), 0)
		
		# Should have some child table fields (Sales Invoice has items table)
		self.assertGreater(len(fields['child_table_fields']), 0)
		
		# Check structure of child table fields
		if fields['child_table_fields']:
			child_field = fields['child_table_fields'][0]
			self.assertIn('parent_field', child_field)
			self.assertIn('child_doctype', child_field)
			self.assertIn('child_fieldname', child_field)
			self.assertIn('is_child_table', child_field)
			self.assertTrue(child_field['is_child_table'])
	
	def test_field_configuration_validation(self):
		"""Test that field configuration validation works with child table fields"""
		# Create a test Field Access Control document
		doc = frappe.get_doc({
			'doctype': 'Field Access Control',
			'doctype_name': 'Sales Invoice',
			'role': 'System Manager',
			'is_active': 1,
			'field_configurations': [
				{
					'fieldname': 'customer',
					'field_label': 'Customer',
					'action_type': 'Read Only',
					'is_active': 1
				},
				{
					'fieldname': 'item_code',
					'field_label': 'Item Code',
					'action_type': 'Hide',
					'is_active': 1,
					'is_child_table_field': 1,
					'parent_field': 'items',
					'child_doctype': 'Sales Invoice Item',
					'child_fieldname': 'item_code'
				}
			]
		})
		
		# Should not throw validation error
		doc.validate()
		self.assertTrue(True)  # If we reach here, validation passed
