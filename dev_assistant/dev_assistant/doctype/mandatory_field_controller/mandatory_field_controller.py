import frappe
from frappe.model.document import Document

class MandatoryFieldController(Document):
	def onload(self):
		if self.document_type:
			# Get fields for the selected doctype
			self.set_onload("doctype_fields", self.get_doctype_fields())

	def get_doctype_fields(self):
		"""Get all fields for the selected doctype"""
		if not self.document_type:
			return []

		meta = frappe.get_meta(self.document_type)
		fields = []

		for field in meta.fields:
			if field.fieldtype not in ["Section Break", "Column Break", "Tab Break", "HTML"]:
				fields.append({
					"fieldname": field.fieldname,
					"label": field.label or field.fieldname.replace("_", " ").title(),
					"fieldtype": field.fieldtype
				})

		return fields

@frappe.whitelist()
def get_fields_for_doctype(doctype):
	"""Get fields for a specific doctype - called from client"""
	meta = frappe.get_meta(doctype)
	fields = []

	for field in meta.fields:
		if field.fieldtype not in ["Section Break", "Column Break", "Tab Break", "HTML"]:
			fields.append({
				"value": field.fieldname,
				"label": field.label or field.fieldname.replace("_", " ").title()
			})

	return fields