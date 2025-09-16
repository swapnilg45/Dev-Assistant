frappe.ui.form.on('Mandatory Field Controller', {
	refresh: function(frm) {
		// Update field options on form load
		if (frm.doc.document_type) {
			update_field_options(frm);
		}
	},

	document_type: function(frm) {
		if (frm.doc.document_type) {
			// Only clear child tables if this is a new form or user changed document type
			if (frm.is_new() || (frm.doc.__islocal === 0 && frm._last_doctype !== frm.doc.document_type)) {
				frm.clear_table('conditions');
				frm.clear_table('mandatory_fields');
				frm.refresh_fields(['conditions', 'mandatory_fields']);
			}

			// Remember the current doctype
			frm._last_doctype = frm.doc.document_type;

			// Update field options
			update_field_options(frm);
		}
	}
});

frappe.ui.form.on('Mandatory Field Detail', {
	field_name: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.field_name && frm.doc.document_type) {
			// Get the field meta and populate field_label
			frappe.model.with_doctype(frm.doc.document_type, () => {
				let meta = frappe.get_meta(frm.doc.document_type);
				let field_meta = meta.fields.find(f => f.fieldname === row.field_name);

				if (field_meta && field_meta.label) {
					frappe.model.set_value(cdt, cdn, 'field_label', field_meta.label);
				} else {
					// Fallback: convert fieldname to readable label
					let label = row.field_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
					frappe.model.set_value(cdt, cdn, 'field_label', label);
				}
			});
		}
	}
});

function update_field_options(frm) {
	if (!frm.doc.document_type) return;

	// Load doctype meta and update field options
	frappe.model.with_doctype(frm.doc.document_type, () => {
		let fieldnames = frappe
			.get_meta(frm.doc.document_type)
			.fields.filter((d) => {
				return frappe.model.no_value_type.indexOf(d.fieldtype) === -1;
			})
			.map((d) => {
				return { label: `${d.label} (${d.fieldname})`, value: d.fieldname };
			});

		// Update field options in conditions table
		frm.fields_dict.conditions.grid.update_docfield_property(
			"field",
			"options",
			fieldnames
		);

		// Update field options in mandatory fields table
		frm.fields_dict.mandatory_fields.grid.update_docfield_property(
			"field_name",
			"options",
			fieldnames
		);

		console.log('Field options updated for:', frm.doc.document_type);
		console.log('Available fields:', fieldnames);
	});
}