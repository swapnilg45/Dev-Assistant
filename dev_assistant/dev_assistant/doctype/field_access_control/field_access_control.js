// Copyright (c) 2025, Hybrowlabs and contributors
// For license information, please see license.txt

frappe.ui.form.on("Field Access Control", {
	refresh(frm) {
		// Add Select Fields button
		frm.add_custom_button(__('Select Fields'), function() {
			loadDoctypeFields(frm);
		});
		
		// Add Select Child Tables button if child table control is enabled
		if (frm.doc.enable_child_table_control && frm.doc.doctype_name) {
			frm.add_custom_button(__('Select Child Tables'), function() {
				loadChildTables(frm);
			});
		}
	},
	
	doctype_name: function(frm) {
		// Clear existing field configurations when doctype changes
		if (frm.doc.doctype_name) {
			frm.set_value('field_configurations', []);
			frm.refresh_field('field_configurations');
		}
	},
	
	enable_child_table_control: function(frm) {
		// Refresh buttons when child table control is toggled
		frm.trigger('refresh');
	}
});

function loadDoctypeFields(frm) {
	if (!frm.doc.doctype_name) {
		frappe.msgprint({
			title: __('No Doctype Selected'),
			message: __('Please select a Document Type first.'),
			indicator: 'orange'
		});
		return;
	}
	
	frappe.call({
		method: 'dev_assistant.dev_assistant.doctype.field_access_control.field_access_control.get_doctype_fields',
		args: {
			doctype_name: frm.doc.doctype_name
		},
		callback: function(r) {
			if (!r.exc && r.message) {
				showFieldSelectionModal(frm, r.message);
			} else {
				frappe.msgprint({
					title: __('Error'),
					message: __('Failed to load fields.'),
					indicator: 'red'
				});
			}
		}
	});
}

function showFieldSelectionModal(frm, fields) {
	let d = new frappe.ui.Dialog({
		title: __('Select Fields to Control'),
		width: 700,
		fields: [
			{
				fieldtype: 'Data',
				label: __('Search Fields'),
				fieldname: 'search_field',
				placeholder: __('Type to search fields...')
			},
			{
				fieldtype: 'HTML',
				fieldname: 'fields_list',
				options: createFieldsListHTML(fields)
			}
		],
		primary_action_label: __('Add Selected Fields'),
		primary_action: function() {
			addSelectedFields(frm, d);
		}
	});
	
	d.show();
	
	// Add search functionality
	d.fields_dict.search_field.$input.on('input', function() {
		const searchTerm = $(this).val().toLowerCase();
		filterFields(d, fields, searchTerm);
	});
}

function filterFields(dialog, allFields, searchTerm) {
	const tbody = dialog.fields_dict.fields_list.$wrapper.find('tbody');
	
	if (!searchTerm) {
		// Show all fields if search is empty
		tbody.find('tr').show();
		return;
	}
	
	// Filter fields based on search term
	tbody.find('tr').each(function() {
		const row = $(this);
		const fieldLabel = row.find('td:nth-child(2)').text().toLowerCase();
		const fieldName = row.find('td:nth-child(3)').text().toLowerCase();
		
		if (fieldLabel.includes(searchTerm) || fieldName.includes(searchTerm)) {
			row.show();
		} else {
			row.hide();
		}
	});
}

function createFieldsListHTML(fields) {
	let html = '<div style="max-height: 400px; overflow-y: auto;">';
	html += '<table class="table table-bordered">';
	html += '<thead><tr><th><input type="checkbox" id="select-all"></th><th>Field Label</th><th>Field Name</th><th>Type</th></tr></thead>';
	html += '<tbody>';
	
	fields.forEach(function(field, index) {
		html += `<tr>`;
		html += `<td><input type="checkbox" class="field-checkbox" value="${index}" data-fieldname="${field.fieldname}" data-label="${field.label}"></td>`;
		html += `<td><strong>${field.label}</strong></td>`;
		html += `<td><code>${field.fieldname}</code></td>`;
		html += `<td>${field.fieldtype || 'Data'}</td>`;
		html += '</tr>';
	});
	
	html += '</tbody></table></div>';
	
	// Add select all functionality
	html += '<script>';
	html += '$("#select-all").on("change", function() {';
	html += '  $(".field-checkbox:visible").prop("checked", $(this).prop("checked"));';
	html += '});';
	html += '</script>';
	
	return html;
}

function addSelectedFields(frm, dialog) {
	const selectedCheckboxes = $('.field-checkbox:checked');
	const selectedFields = [];
	
	selectedCheckboxes.each(function() {
		const checkbox = $(this);
		selectedFields.push({
			fieldname: checkbox.data('fieldname'),
			label: checkbox.data('label')
		});
	});
	
	if (selectedFields.length === 0) {
		frappe.msgprint({
			title: __('No Fields Selected'),
			message: __('Please select at least one field to control.'),
			indicator: 'orange'
		});
		return;
	}
	
	// Get existing fieldnames to avoid duplicates
	const existingFieldnames = [];
	if (frm.doc.field_configurations) {
		frm.doc.field_configurations.forEach(function(row) {
			if (row.fieldname) {
				existingFieldnames.push(row.fieldname);
			}
		});
	}
	
	// Use Python API to add fields
	frappe.call({
		method: 'dev_assistant.dev_assistant.doctype.field_access_control.field_access_control.add_field_configurations',
		args: {
			docname: frm.doc.name,
			fieldnames: JSON.stringify(selectedFields)
		},
		callback: function(r) {
			dialog.hide();
			
			if (r.message && r.message.status === 'success') {
				frappe.msgprint({
					title: __('Fields Added'),
					message: __(r.message.message),
					indicator: 'green'
				});
				
				// Refresh the form to show new fields
				frm.reload_doc();
			} else {
				frappe.msgprint({
					title: __('Error'),
					message: __(r.message.message || 'Failed to add fields'),
					indicator: 'red'
				});
			}
		}
	});
}

function applyConfigurations(frm) {
	if (!frm.doc.doctype_name) {
		frappe.msgprint({
			title: __('No Doctype Selected'),
			message: __('Please select a Document Type first.'),
			indicator: 'orange'
		});
		return;
	}
	
	if (!frm.doc.role) {
		frappe.msgprint({
			title: __('No Role Selected'),
			message: __('Please select a Role to apply field controls.'),
			indicator: 'orange'
		});
		return;
	}
	
	frappe.msgprint({
		title: __('Configuration Saved'),
		message: __('Field access control configuration has been saved. The settings will be automatically applied when users with the selected role access forms.'),
		indicator: 'green'
	});
}

function loadChildTables(frm) {
	if (!frm.doc.doctype_name) {
		frappe.msgprint({
			title: __('No Doctype Selected'),
			message: __('Please select a Document Type first.'),
			indicator: 'orange'
		});
		return;
	}
	
	frappe.call({
		method: 'dev_assistant.dev_assistant.doctype.field_access_control.field_access_control.get_child_table_fields',
		args: {
			doctype_name: frm.doc.doctype_name
		},
		callback: function(r) {
			if (!r.exc && r.message && r.message.length > 0) {
				showChildTableSelectionModal(frm, r.message);
			} else {
				frappe.msgprint({
					title: __('No Child Tables'),
					message: __('No child tables found for this Document Type.'),
					indicator: 'orange'
				});
			}
		}
	});
}

function showChildTableSelectionModal(frm, tables) {
	let d = new frappe.ui.Dialog({
		title: __('Select Child Tables to Control'),
		width: 600,
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'tables_list',
				options: createChildTablesListHTML(tables)
			}
		],
		primary_action_label: __('Add Selected Tables'),
		primary_action: function() {
			addSelectedChildTables(frm, d, tables);
		}
	});
	
	d.show();
}

function createChildTablesListHTML(tables) {
	let html = '<div style="max-height: 400px; overflow-y: auto;">';
	html += '<table class="table table-bordered">';
	html += '<thead><tr><th><input type="checkbox" id="select-all-tables"></th><th>Table Label</th><th>Table Fieldname</th></tr></thead>';
	html += '<tbody>';
	
	tables.forEach(function(table, index) {
		html += `<tr>`;
		html += `<td><input type="checkbox" class="table-checkbox" value="${index}" data-fieldname="${table.fieldname}" data-label="${table.label}"></td>`;
		html += `<td><strong>${table.label}</strong></td>`;
		html += `<td><code>${table.fieldname}</code></td>`;
		html += '</tr>';
	});
	
	html += '</tbody></table></div>';
	
	// Add select all functionality
	html += '<script>';
	html += '$("#select-all-tables").on("change", function() {';
	html += '  $(".table-checkbox").prop("checked", $(this).prop("checked"));';
	html += '});';
	html += '</script>';
	
	return html;
}

function addSelectedChildTables(frm, dialog, tables) {
	const selectedCheckboxes = $('.table-checkbox:checked');
	const selectedTables = [];
	
	selectedCheckboxes.each(function() {
		const checkbox = $(this);
		const tableIndex = parseInt(checkbox.val());
		const table = tables[tableIndex];
		selectedTables.push({
			table_fieldname: table.fieldname,
			table_label: table.label
		});
	});
	
	if (selectedTables.length === 0) {
		frappe.msgprint({
			title: __('No Tables Selected'),
			message: __('Please select at least one child table to control.'),
			indicator: 'orange'
		});
		return;
	}
	
	// Add tables to the child table configurations
	selectedTables.forEach(function(table) {
		const row = frm.add_child('child_table_configurations');
		row.table_fieldname = table.table_fieldname;
		row.table_label = table.table_label;
		row.hide_add_button = 0;
		row.hide_delete_button = 0;
		row.is_active = 1;
	});
	
	frm.refresh_field('child_table_configurations');
	dialog.hide();
	
	frappe.msgprint({
		title: __('Tables Added'),
		message: __(`Added ${selectedTables.length} child table(s) to configuration.`),
		indicator: 'green'
	});
}
