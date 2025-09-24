# Copyright (c) 2025, Swapnil and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import difflib
import json


class SmartFieldMapper:
	"""Intelligent field mapping with auto-suggestions"""

	def __init__(self):
		self.common_field_patterns = {
			'customer': ['customer', 'customer_name', 'party_name', 'client', 'customer_group'],
			'email': ['email', 'email_id', 'email_address', 'contact_email', 'personal_email'],
			'phone': ['phone', 'phone_no', 'mobile', 'contact_phone', 'cell_number', 'mobile_no'],
			'amount': ['amount', 'total', 'grand_total', 'net_total', 'base_total', 'total_amount'],
			'date': ['date', 'creation_date', 'posting_date', 'transaction_date', 'date_of_joining'],
			'name': ['name', 'title', 'subject', 'description', 'item_name', 'full_name'],
			'status': ['status', 'workflow_state', 'docstatus', 'approval_status'],
			'company': ['company', 'organization', 'firm'],
			'address': ['address', 'address_line_1', 'address_line_2', 'street'],
			'city': ['city', 'town', 'location'],
			'state': ['state', 'province', 'region'],
			'country': ['country', 'nation'],
			'currency': ['currency', 'base_currency'],
			'department': ['department', 'dept', 'division'],
			'designation': ['designation', 'position', 'job_title'],
			'employee': ['employee', 'employee_name', 'staff', 'worker'],
			'project': ['project', 'project_name', 'project_code'],
			'item': ['item', 'item_code', 'item_name', 'product', 'product_name'],
			'quantity': ['qty', 'quantity', 'amount', 'count'],
			'rate': ['rate', 'price', 'unit_price', 'cost'],
			'reference': ['reference', 'ref_no', 'reference_no', 'voucher_no']
		}

		self.fieldtype_compatibility = {
			'Data': ['Data', 'Link', 'Small Text', 'Text Editor'],
			'Link': ['Data', 'Link'],
			'Select': ['Select', 'Data'],
			'Check': ['Check', 'Int'],
			'Int': ['Int', 'Float', 'Currency', 'Percent'],
			'Float': ['Float', 'Currency', 'Percent', 'Int'],
			'Currency': ['Currency', 'Float', 'Int'],
			'Date': ['Date', 'Datetime'],
			'Datetime': ['Datetime', 'Date'],
			'Small Text': ['Small Text', 'Text', 'Text Editor', 'Data'],
			'Text': ['Text', 'Text Editor', 'Small Text'],
			'Text Editor': ['Text Editor', 'Text', 'Small Text']
		}

	def get_field_suggestions(self, source_doctype, target_doctype):
		"""Get intelligent field mapping suggestions"""
		source_fields = self.get_mappable_fields(source_doctype)
		target_fields = self.get_mappable_fields(target_doctype)

		suggestions = []

		for source_field in source_fields:
			best_matches = self.find_best_matches(source_field, target_fields)
			if best_matches:
				suggestions.append({
					'source_field': source_field,
					'target_suggestions': best_matches,
					'confidence': self.calculate_confidence(source_field, best_matches[0])
				})

		# Sort by confidence
		suggestions.sort(key=lambda x: x['confidence'], reverse=True)
		return suggestions

	def get_mappable_fields(self, doctype):
		"""Get fields that can be mapped (excluding system fields)"""
		try:
			meta = frappe.get_meta(doctype)
			mappable_fields = []

			for field in meta.fields:
				if self.is_mappable_field(field):
					mappable_fields.append({
						'fieldname': field.fieldname,
						'label': field.label or field.fieldname,
						'fieldtype': field.fieldtype,
						'options': field.options,
						'reqd': field.reqd,
						'description': field.description or ''
					})

			return mappable_fields
		except frappe.DoesNotExistError:
			frappe.throw(_(f"DocType '{doctype}' does not exist"))

	def is_mappable_field(self, field):
		"""Check if field can be mapped"""
		# Exclude layout and system fields
		if field.fieldtype in ['Section Break', 'Column Break', 'HTML', 'Heading', 'Tab Break']:
			return False

		# Exclude system fields
		if field.fieldname.startswith('__'):
			return False

		# Exclude certain system fields
		system_fields = ['name', 'owner', 'creation', 'modified', 'modified_by', 'docstatus', 'idx']
		if field.fieldname in system_fields:
			return False

		return True

	def find_best_matches(self, source_field, target_fields):
		"""Find best matching target fields"""
		source_name = source_field['fieldname'].lower()
		source_label = source_field['label'].lower()
		source_type = source_field['fieldtype']

		matches = []

		# Exact name match (highest priority)
		for target_field in target_fields:
			if target_field['fieldname'].lower() == source_name:
				if self.is_type_compatible(source_type, target_field['fieldtype']):
					matches.append((target_field, 1.0, 'exact_name'))

		# Pattern-based matching
		for pattern_type, patterns in self.common_field_patterns.items():
			if source_name in patterns:
				for target_field in target_fields:
					if target_field['fieldname'].lower() in patterns:
						if self.is_type_compatible(source_type, target_field['fieldtype']):
							# Avoid duplicates
							if not any(m[0]['fieldname'] == target_field['fieldname'] for m in matches):
								matches.append((target_field, 0.95, 'pattern'))

		# Label similarity matching
		for target_field in target_fields:
			target_name = target_field['fieldname'].lower()
			target_label = target_field['label'].lower()

			# Skip if already matched
			if any(m[0]['fieldname'] == target_field['fieldname'] for m in matches):
				continue

			name_similarity = difflib.SequenceMatcher(None, source_name, target_name).ratio()
			label_similarity = difflib.SequenceMatcher(None, source_label, target_label).ratio()

			max_similarity = max(name_similarity, label_similarity)
			if max_similarity > 0.7:  # 70% similarity threshold
				if self.is_type_compatible(source_type, target_field['fieldtype']):
					matches.append((target_field, max_similarity * 0.8, 'similarity'))

		# Type-based matching for similar field types
		for target_field in target_fields:
			# Skip if already matched
			if any(m[0]['fieldname'] == target_field['fieldname'] for m in matches):
				continue

			if self.is_type_compatible(source_type, target_field['fieldtype']):
				# Lower priority type matching
				type_score = 0.3 if source_type == target_field['fieldtype'] else 0.2
				matches.append((target_field, type_score, 'type'))

		# Sort by confidence and return top matches
		matches.sort(key=lambda x: x[1], reverse=True)
		return [{'field': match[0], 'confidence': match[1], 'reason': match[2]} for match in matches[:3]]

	def is_type_compatible(self, source_type, target_type):
		"""Check if field types are compatible for mapping"""
		if source_type == target_type:
			return True

		compatible_types = self.fieldtype_compatibility.get(source_type, [])
		return target_type in compatible_types

	def calculate_confidence(self, source_field, target_match):
		"""Calculate mapping confidence score"""
		return target_match.get('confidence', 0)

	def auto_map_fields(self, source_doctype, target_doctype, confidence_threshold=0.8):
		"""Automatically map fields with high confidence"""
		suggestions = self.get_field_suggestions(source_doctype, target_doctype)
		auto_mappings = {}

		for suggestion in suggestions:
			if suggestion['confidence'] >= confidence_threshold:
				best_match = suggestion['target_suggestions'][0]
				auto_mappings[suggestion['source_field']['fieldname']] = best_match['field']['fieldname']

		return auto_mappings

	def validate_field_mapping(self, source_doctype, target_doctype, field_mappings):
		"""Validate field mappings between DocTypes"""
		try:
			source_fields = {f['fieldname']: f for f in self.get_mappable_fields(source_doctype)}
			target_fields = {f['fieldname']: f for f in self.get_mappable_fields(target_doctype)}

			validation_results = []

			for source_field, target_field in field_mappings.items():
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
					source_fieldtype = source_fields[source_field]['fieldtype']
					target_fieldtype = target_fields[target_field]['fieldtype']

					if not self.is_type_compatible(source_fieldtype, target_fieldtype):
						result['warnings'].append(
							f"Field type incompatibility: {source_fieldtype} -> {target_fieldtype}"
						)

					# Required field mapping check
					if target_fields[target_field]['reqd'] and not source_fields[source_field]['reqd']:
						result['warnings'].append(
							f"Mapping optional field to required field: {target_field}"
						)

				validation_results.append(result)

			return validation_results

		except Exception as e:
			frappe.throw(f"Validation failed: {str(e)}")

	def get_mapping_preview(self, source_doctype, target_doctype, field_mappings, sample_docname=None):
		"""Get preview of field mapping with sample data"""
		try:
			if sample_docname:
				sample_doc = frappe.get_doc(source_doctype, sample_docname)
			else:
				# Get a random sample document
				sample_docs = frappe.get_all(source_doctype, limit=1)
				if sample_docs:
					sample_doc = frappe.get_doc(source_doctype, sample_docs[0].name)
				else:
					return {"error": f"No sample documents found for {source_doctype}"}

			preview_data = []
			for source_field, target_field in field_mappings.items():
				source_value = getattr(sample_doc, source_field, None)
				preview_data.append({
					'source_field': source_field,
					'target_field': target_field,
					'sample_value': source_value,
					'formatted_value': frappe.format(source_value, {"fieldtype": "Data"})
				})

			return {
				'sample_doc': sample_doc.name,
				'preview_data': preview_data
			}

		except Exception as e:
			return {"error": str(e)}


@frappe.whitelist()
def get_field_mapping_suggestions(source_doctype, target_doctype):
	"""API endpoint for field mapping suggestions"""
	mapper = SmartFieldMapper()
	return mapper.get_field_suggestions(source_doctype, target_doctype)


@frappe.whitelist()
def auto_map_fields(source_doctype, target_doctype, confidence_threshold=0.8):
	"""API endpoint for automatic field mapping"""
	mapper = SmartFieldMapper()
	return mapper.auto_map_fields(source_doctype, target_doctype, float(confidence_threshold))


@frappe.whitelist()
def validate_field_mapping(source_doctype, target_doctype, field_mappings):
	"""API endpoint for field mapping validation"""
	mapper = SmartFieldMapper()
	if isinstance(field_mappings, str):
		field_mappings = json.loads(field_mappings)
	return mapper.validate_field_mapping(source_doctype, target_doctype, field_mappings)


@frappe.whitelist()
def get_mappable_fields(doctype):
	"""API endpoint to get mappable fields for a DocType"""
	mapper = SmartFieldMapper()
	return mapper.get_mappable_fields(doctype)


@frappe.whitelist()
def get_mapping_preview(source_doctype, target_doctype, field_mappings, sample_docname=None):
	"""API endpoint for mapping preview"""
	mapper = SmartFieldMapper()
	if isinstance(field_mappings, str):
		field_mappings = json.loads(field_mappings)
	return mapper.get_mapping_preview(source_doctype, target_doctype, field_mappings, sample_docname)


@frappe.whitelist()
def save_field_mapping(sync_chain, step_number, field_mappings):
	"""Save field mappings to sync chain step"""
	try:
		chain_doc = frappe.get_doc("Sync Chain", sync_chain)
		for step in chain_doc.chain_steps:
			if step.step_number == int(step_number):
				if isinstance(field_mappings, str):
					field_mappings = json.loads(field_mappings)
				step.field_mappings = json.dumps(field_mappings, indent=2)
				break

		chain_doc.save()
		return {"success": True, "message": "Field mappings saved successfully"}

	except Exception as e:
		frappe.log_error(f"Failed to save field mappings: {str(e)}", "Field Mapper")
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_common_mapping_patterns():
	"""Get common field mapping patterns for UI hints"""
	mapper = SmartFieldMapper()
	return {
		"patterns": mapper.common_field_patterns,
		"compatibility": mapper.fieldtype_compatibility
	}