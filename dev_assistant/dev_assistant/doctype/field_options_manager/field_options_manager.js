// Copyright (c) 2025, Dev Assistant and contributors
// For license information, please see license.txt

frappe.ui.form.on("Field Options Manager", {
	refresh(frm) {
		// Add Select Fields button
		frm.add_custom_button(__('Select Fields'), function() {
			loadDoctypeFields(frm);
		});
		
		// Add Add Options button
		frm.add_custom_button(__('Add Options'), function() {
			showAddOptionsModal(frm);
		});
	},
	
	doctype_name: function(frm) {
		// Clear existing field configurations when doctype changes
		if (frm.doc.doctype_name) {
			frm.set_value('field_name', '');
			frm.set_value('options_configuration', []);
			frm.refresh_field('options_configuration');
		}
	},
	
	field_name: function(frm) {
		// Clear existing options when field changes
		if (frm.doc.field_name) {
			frm.set_value('options_configuration', []);
			frm.refresh_field('options_configuration');
		}
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
		method: 'dev_assistant.dev_assistant.doctype.field_options_manager.field_options_manager.get_doctype_fields',
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
		title: __('Select Field for Options Management'),
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
		primary_action_label: __('Select Field'),
		primary_action: function() {
			selectField(frm, d);
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
	html += '<thead><tr><th><input type="radio" name="field_radio" value=""></th><th>Field Label</th><th>Field Name</th><th>Type</th></tr></thead>';
	html += '<tbody>';
	
	fields.forEach(function(field, index) {
		html += `<tr>`;
		html += `<td><input type="radio" name="field_radio" value="${index}" data-fieldname="${field.fieldname}" data-label="${field.label}"></td>`;
		html += `<td><strong>${field.label}</strong></td>`;
		html += `<td><code>${field.fieldname}</code></td>`;
		html += `<td>${field.fieldtype || 'Data'}</td>`;
		html += '</tr>';
	});
	
	html += '</tbody></table></div>';
	
	return html;
}

function selectField(frm, dialog) {
	const selectedRadio = $('input[name="field_radio"]:checked');
	
	if (selectedRadio.length === 0) {
		frappe.msgprint({
			title: __('No Field Selected'),
			message: __('Please select a field to manage options.'),
			indicator: 'orange'
		});
		return;
	}
	
	const fieldData = selectedRadio.data();
	frm.set_value('field_name', fieldData.fieldname);
	dialog.hide();
	
	frappe.msgprint({
		title: __('Field Selected'),
		message: __('Field "{0}" has been selected for options management.').format(fieldData.label),
		indicator: 'green'
	});
}

function showAddOptionsModal(frm) {
	if (!frm.doc.doctype_name || !frm.doc.field_name) {
		frappe.msgprint({
			title: __('Configuration Required'),
			message: __('Please select a Document Type and Field first.'),
			indicator: 'orange'
		});
		return;
	}
	
	let d = new frappe.ui.Dialog({
		title: __('Add Options'),
		width: 600,
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'options_help',
				options: '<div class="alert alert-info">Add options for the field. You can add multiple options separated by commas or add them one by one.</div>'
			},
			{
				fieldtype: 'Text',
				label: __('Options (comma separated)'),
				fieldname: 'bulk_options',
				placeholder: __('Option 1, Option 2, Option 3')
			},
			{
				fieldtype: 'Section Break',
				label: __('Or Add Individual Options')
			},
			{
				fieldtype: 'Data',
				label: __('Option Value'),
				fieldname: 'option_value',
				placeholder: __('Enter option value')
			},
			{
				fieldtype: 'Data',
				label: __('Option Label (optional)'),
				fieldname: 'option_label',
				placeholder: __('Enter display label (optional)')
			},
			{
				fieldtype: 'Button',
				label: __('Add Option'),
				fieldname: 'add_option_btn'
			},
			{
				fieldtype: 'HTML',
				fieldname: 'added_options',
				options: '<div id="added-options-list"></div>'
			}
		],
		primary_action_label: __('Save Options'),
		primary_action: function() {
			saveOptions(frm, d);
		}
	});
	
	d.show();
	
	// Handle bulk options input
	d.fields_dict.bulk_options.$input.on('input', function() {
		const bulkOptions = $(this).val();
		if (bulkOptions) {
			const options = bulkOptions.split(',').map(opt => opt.trim()).filter(opt => opt);
			updateAddedOptionsList(options);
		}
	});
	
	// Handle individual option addition
	d.fields_dict.add_option_btn.$wrapper.on('click', function() {
		const optionValue = d.fields_dict.option_value.value;
		const optionLabel = d.fields_dict.option_label.value;
		
		if (optionValue) {
			const option = {
				option_value: optionValue,
				option_label: optionLabel || optionValue
			};
			addOptionToList(option);
			
			// Clear input fields
			d.fields_dict.option_value.value = '';
			d.fields_dict.option_label.value = '';
		}
	});
	
	// Initialize added options list
	window.addedOptionsList = [];
}

function addOptionToList(option) {
	if (!window.addedOptionsList) {
		window.addedOptionsList = [];
	}
	
	window.addedOptionsList.push(option);
	updateAddedOptionsList();
}

function updateAddedOptionsList(options = null) {
	if (options) {
		window.addedOptionsList = options.map(opt => ({
			option_value: opt,
			option_label: opt
		}));
	}
	
	const container = $('#added-options-list');
	container.empty();
	
	if (window.addedOptionsList && window.addedOptionsList.length > 0) {
		let html = '<table class="table table-bordered">';
		html += '<thead><tr><th>Option Value</th><th>Option Label</th><th>Action</th></tr></thead><tbody>';
		
		window.addedOptionsList.forEach(function(option, index) {
			html += `<tr>`;
			html += `<td>${option.option_value}</td>`;
			html += `<td>${option.option_label}</td>`;
			html += `<td><button class="btn btn-xs btn-danger" onclick="removeOption(${index})">Remove</button></td>`;
			html += '</tr>';
		});
		
		html += '</tbody></table>';
		container.html(html);
	} else {
		container.html('<div class="text-muted">No options added yet.</div>');
	}
}

function removeOption(index) {
	window.addedOptionsList.splice(index, 1);
	updateAddedOptionsList();
}

function saveOptions(frm, dialog) {
	if (!window.addedOptionsList || window.addedOptionsList.length === 0) {
		frappe.msgprint({
			title: __('No Options'),
			message: __('Please add at least one option.'),
			indicator: 'orange'
		});
		return;
	}
	
	frappe.call({
		method: 'dev_assistant.dev_assistant.doctype.field_options_manager.field_options_manager.add_options_configuration',
		args: {
			docname: frm.doc.name,
			options_data: JSON.stringify(window.addedOptionsList)
		},
		callback: function(r) {
			dialog.hide();
			
			if (r.message && r.message.status === 'success') {
				frappe.msgprint({
					title: __('Options Added'),
					message: __(r.message.message),
					indicator: 'green'
				});
				
				// Refresh the form to show new options
				frm.reload_doc();
			} else {
				frappe.msgprint({
					title: __('Error'),
					message: __(r.message.message || 'Failed to add options'),
					indicator: 'red'
				});
			}
		}
	});
}

