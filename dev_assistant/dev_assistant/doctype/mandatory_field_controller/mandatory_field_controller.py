import frappe
from frappe.model.document import Document

class MandatoryFieldController(Document):
	def before_save(self):
		if self.mandatory_fields:
			for field in self.mandatory_fields:
				if field.field_label and not field.field_name:
					if self.document_type:
						meta = frappe.get_meta(self.document_type)
						found = False
						for meta_field in meta.fields:
							if meta_field.label == field.field_label:
								field.field_name = meta_field.fieldname
								found = True
								break
						if not found:
							frappe.throw(f"Field with label '{field.field_label}' not found in {self.document_type}")

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