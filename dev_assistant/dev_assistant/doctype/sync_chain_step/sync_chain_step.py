# Copyright (c) 2025, Swapnil and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json


class SyncChainStep(Document):
	def validate(self):
		"""Validate sync chain step configuration"""
		self.validate_doctype()
		self.validate_field_mappings()
		self.update_doctype_label()

	def validate_doctype(self):
		"""Validate selected DocType exists and is valid for sync"""
		if self.doctype_name:
			try:
				meta = frappe.get_meta(self.doctype_name)

				# Check if it's a valid DocType for sync (not single, not table)
				if meta.issingle:
					frappe.throw(f"Single DocTypes cannot be used in sync chains: {self.doctype_name}")

				if meta.istable:
					frappe.throw(f"Child Table DocTypes cannot be used in sync chains: {self.doctype_name}")

			except frappe.DoesNotExistError:
				frappe.throw(f"DocType does not exist: {self.doctype_name}")

	def validate_field_mappings(self):
		"""Validate field mappings JSON structure"""
		if self.field_mappings:
			try:
				mappings = json.loads(self.field_mappings)
				if not isinstance(mappings, dict):
					frappe.throw("Field mappings must be a JSON object")

				# Validate field names exist in DocType
				if self.doctype_name:
					meta = frappe.get_meta(self.doctype_name)
					valid_fields = {field.fieldname for field in meta.fields}

					for source_field in mappings.keys():
						if source_field not in valid_fields:
							frappe.msgprint(f"Warning: Field '{source_field}' not found in {self.doctype_name}")

			except json.JSONDecodeError:
				frappe.throw("Invalid JSON format in field mappings")

	def update_doctype_label(self):
		"""Update DocType label for display"""
		if self.doctype_name and not self.doctype_label:
			try:
				meta = frappe.get_meta(self.doctype_name)
				self.doctype_label = meta.get_label() or self.doctype_name
			except frappe.DoesNotExistError:
				self.doctype_label = self.doctype_name

	def get_field_mappings_dict(self):
		"""Get field mappings as dictionary"""
		if self.field_mappings:
			try:
				return json.loads(self.field_mappings)
			except json.JSONDecodeError:
				return {}
		return {}

	def set_field_mappings_dict(self, mappings_dict):
		"""Set field mappings from dictionary"""
		self.field_mappings = json.dumps(mappings_dict, indent=2)

	def get_mappable_fields(self):
		"""Get list of fields that can be mapped for this DocType"""
		if not self.doctype_name:
			return []

		meta = frappe.get_meta(self.doctype_name)
		mappable_fields = []

		for field in meta.fields:
			# Exclude layout fields and system fields
			if field.fieldtype not in ['Section Break', 'Column Break', 'HTML', 'Heading']:
				if not field.fieldname.startswith('__'):
					mappable_fields.append({
						'fieldname': field.fieldname,
						'label': field.label or field.fieldname,
						'fieldtype': field.fieldtype,
						'options': field.options,
						'reqd': field.reqd
					})

		return mappable_fields

	@frappe.whitelist()
	def get_field_suggestions(self, target_doctype):
		"""Get field mapping suggestions for target DocType"""
		from dev_assistant.dev_assistant.universal_sync.field_mapper import SmartFieldMapper

		if not self.doctype_name or not target_doctype:
			return []

		mapper = SmartFieldMapper()
		return mapper.get_field_suggestions(self.doctype_name, target_doctype)

	def should_sync_on_event(self, event_type):
		"""Check if sync should happen based on condition and event"""
		if self.sync_condition == "Always":
			return event_type in ["on_update", "on_submit", "on_update_after_submit"]
		elif self.sync_condition == "Status Changes":
			return event_type in ["on_update", "on_update_after_submit", "on_submit"]
		elif self.sync_condition == "Specific Field Changes":
			return event_type in ["on_update", "on_update_after_submit"]
		elif self.sync_condition == "Manual Trigger":
			return event_type == "manual"

		return False


@frappe.whitelist()
def get_doctype_fields(doctype):
	"""Get mappable fields for a DocType"""
	if not doctype:
		return []

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
						'options': field.options,
						'reqd': field.reqd,
						'description': field.description
					})

		return fields

	except frappe.DoesNotExistError:
		frappe.throw(f"DocType '{doctype}' does not exist")


@frappe.whitelist()
def validate_field_mapping(source_doctype, target_doctype, field_mappings):
	"""Validate field mappings between two DocTypes"""
	try:
		mappings = json.loads(field_mappings) if isinstance(field_mappings, str) else field_mappings

		source_meta = frappe.get_meta(source_doctype)
		target_meta = frappe.get_meta(target_doctype)

		source_fields = {field.fieldname: field for field in source_meta.fields}
		target_fields = {field.fieldname: field for field in target_meta.fields}

		validation_results = []

		for source_field, target_field in mappings.items():
			result = {
				'source_field': source_field,
				'target_field': target_field,
				'valid': True,
				'warnings': [],
				'errors': []
			}

			# Check source field exists
			if source_field not in source_fields:
				result['valid'] = False
				result['errors'].append(f"Source field '{source_field}' not found in {source_doctype}")

			# Check target field exists
			if target_field not in target_fields:
				result['valid'] = False
				result['errors'].append(f"Target field '{target_field}' not found in {target_doctype}")

			# Type compatibility check
			if result['valid']:
				source_fieldtype = source_fields[source_field].fieldtype
				target_fieldtype = target_fields[target_field].fieldtype

				if source_fieldtype != target_fieldtype:
					result['warnings'].append(
						f"Field type mismatch: {source_fieldtype} -> {target_fieldtype}"
					)

			validation_results.append(result)

		return validation_results

	except Exception as e:
		frappe.throw(f"Validation failed: {str(e)}")