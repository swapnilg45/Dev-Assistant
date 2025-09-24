# Copyright (c) 2025, Swapnil and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json


class SyncChain(Document):
	def validate(self):
		"""Validate sync chain configuration"""
		self.validate_chain_steps()
		self.validate_field_mappings()
		self.update_step_labels()

	def validate_chain_steps(self):
		"""Ensure chain steps are properly ordered and valid"""
		if not self.chain_steps:
			frappe.throw("At least one process step is required")

		step_numbers = [step.step_number for step in self.chain_steps]

		# Check for duplicate step numbers
		if len(step_numbers) != len(set(step_numbers)):
			frappe.throw("Step numbers must be unique")

		# Validate step order starts from 1
		if min(step_numbers) != 1:
			frappe.throw("First step should be numbered as 1")

		# Check for sequential numbering
		expected_steps = list(range(1, len(step_numbers) + 1))
		if sorted(step_numbers) != expected_steps:
			frappe.throw("Steps must be numbered sequentially starting from 1")

	def validate_field_mappings(self):
		"""Validate field mappings for each step"""
		for step in self.chain_steps:
			if step.field_mappings:
				try:
					json.loads(step.field_mappings)
				except json.JSONDecodeError:
					frappe.throw(f"Invalid field mappings JSON format for step {step.step_number}")

	def update_step_labels(self):
		"""Update DocType labels for display purposes"""
		for step in self.chain_steps:
			if step.doctype_name and not step.doctype_label:
				try:
					meta = frappe.get_meta(step.doctype_name)
					step.doctype_label = meta.get_label() or step.doctype_name
				except frappe.DoesNotExistError:
					step.doctype_label = step.doctype_name

	def on_update(self):
		"""Actions after saving sync chain"""
		self.clear_sync_cache()

	def clear_sync_cache(self):
		"""Clear sync-related caches"""
		frappe.cache().delete_key("sync_chain_active_configs")

	@frappe.whitelist()
	def get_sync_statistics(self):
		"""Get sync statistics for this chain"""
		stats = frappe.db.sql("""
			SELECT
				COUNT(*) as total_syncs,
				SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) as successful_syncs,
				SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed_syncs,
				MAX(sync_timestamp) as last_sync
			FROM `tabSync Activity Log`
			WHERE sync_chain = %s
		""", self.name, as_dict=True)

		return stats[0] if stats else {
			"total_syncs": 0,
			"successful_syncs": 0,
			"failed_syncs": 0,
			"last_sync": None
		}

	@frappe.whitelist()
	def test_sync_chain(self, test_doctype=None, test_docname=None):
		"""Test sync chain with sample data"""
		from dev_assistant.dev_assistant.universal_sync.sync_engine import SimpleSyncEngine

		if not test_doctype or not test_docname:
			# Find first step DocType if not specified
			if self.chain_steps:
				test_doctype = self.chain_steps[0].doctype_name
				# Get a sample document of this DocType
				sample_doc = frappe.get_all(test_doctype, limit=1)
				if sample_doc:
					test_docname = sample_doc[0].name
				else:
					frappe.throw(f"No sample documents found for {test_doctype}")

		try:
			sync_engine = SimpleSyncEngine(self.name)
			test_doc = frappe.get_doc(test_doctype, test_docname)
			result = sync_engine.execute_sync(test_doc, test_doctype, "manual")

			return {
				"success": True,
				"message": "Test sync completed successfully",
				"result": result
			}
		except Exception as e:
			return {
				"success": False,
				"message": f"Test sync failed: {str(e)}"
			}

	@frappe.whitelist()
	def clone_chain(self, new_name):
		"""Create a copy of this sync chain"""
		new_chain = frappe.copy_doc(self)
		new_chain.chain_name = new_name
		new_chain.is_active = 0  # Start inactive
		new_chain.template_used = ""  # Clear template reference
		new_chain.insert()

		return {
			"success": True,
			"new_chain": new_chain.name,
			"message": f"Chain cloned successfully as {new_name}"
		}

	def get_next_step(self, current_step_number):
		"""Get the next step in the chain"""
		for step in self.chain_steps:
			if step.step_number == current_step_number + 1:
				return step
		return None

	def get_step_by_doctype(self, doctype):
		"""Get step configuration for a specific DocType"""
		for step in self.chain_steps:
			if step.doctype_name == doctype:
				return step
		return None


@frappe.whitelist()
def get_active_chains_for_doctype(doctype):
	"""Get all active sync chains that include the specified DocType"""
	chains = frappe.db.sql("""
		SELECT DISTINCT scs.parent as chain_name, sc.chain_name as display_name
		FROM `tabSync Chain Step` scs
		JOIN `tabSync Chain` sc ON scs.parent = sc.name
		WHERE scs.doctype_name = %s AND sc.is_active = 1
	""", doctype, as_dict=True)

	return chains


@frappe.whitelist()
def get_doctype_suggestions():
	"""Get DocType suggestions for chain configuration"""
	# Get all submittable and standard DocTypes
	doctypes = frappe.get_all("DocType",
		filters={
			"issingle": 0,
			"istable": 0,
			"module": ["not in", ["Core", "Desk", "Custom", "Website", "Portal"]]
		},
		fields=["name", "module", "description"],
		order_by="name"
	)

	return doctypes


@frappe.whitelist()
def create_chain_from_template(template_name, chain_name=None):
	"""Create a new sync chain from a pre-built template"""
	from dev_assistant.dev_assistant.universal_sync.sync_templates import create_chain_from_template as create_template_chain

	try:
		chain_doc = create_template_chain(template_name, chain_name)
		return {
			"success": True,
			"chain_name": chain_doc.name,
			"message": f"Sync chain created successfully from {template_name} template"
		}
	except Exception as e:
		frappe.log_error(f"Template creation failed: {str(e)}", "Sync Chain Template")
		return {
			"success": False,
			"message": f"Failed to create chain from template: {str(e)}"
		}