// Copyright (c) 2025, Hybrowlabs and contributors
// For license information, please see license.txt

// Define global functions for field selection modal
window.toggleFieldCheckbox = function(element) {
	const checkbox = element.querySelector(".field-checkbox");
	if (checkbox) {
		checkbox.checked = !checkbox.checked;
		window.updateFieldSelection();
	}
};

window.updateFieldSelection = function() {
	const selected = document.querySelectorAll(".field-checkbox:checked").length;
	console.log("Selected fields:", selected);
};

frappe.ui.form.on("Field Access Control", {
	refresh(frm) {
		// Only show Select Fields button and field_configurations after form is saved
		if (!frm.is_new()) {
			// Add Select Fields button
			frm.add_custom_button(__('Select Fields'), function() {
				loadDoctypeFields(frm);
			});
			
			// Show field_configurations section
			frm.set_df_property('field_configurations', 'hidden', 0);
		} else {
			// Hide field_configurations section for new records
			frm.set_df_property('field_configurations', 'hidden', 1);
		}
	},
	
	doctype_name: function(frm) {
		// Clear existing field configurations when doctype changes
		if (frm.doc.doctype_name) {
			frm.set_value('field_configurations', []);
			frm.refresh_field('field_configurations');
		}
	},
	
	make_all_readonly: function(frm) {
		// Handle mode change - show/hide appropriate tables
		if (frm.doc.make_all_readonly) {
			// Read-only mode: show editable exceptions, hide field configurations
			frm.set_df_property('editable_field_exceptions', 'hidden', 0);
			frm.set_df_property('field_configurations', 'hidden', 1);
			
			// Auto-populate editable field exceptions if table is empty
			if (!frm.doc.editable_field_exceptions || frm.doc.editable_field_exceptions.length === 0) {
				autoPopulateEditableFields(frm);
			}
		} else {
			// Normal mode: show field configurations, hide editable exceptions
			frm.set_df_property('field_configurations', 'hidden', 0);
			frm.set_df_property('editable_field_exceptions', 'hidden', 1);
			
			// Clear editable exceptions when switching to normal mode
			if (frm.doc.editable_field_exceptions && frm.doc.editable_field_exceptions.length > 0) {
				frm.set_value('editable_field_exceptions', []);
				frm.refresh_field('editable_field_exceptions');
			}
		}
	}
});

function autoPopulateEditableFields(frm) {
	if (!frm.doc.doctype_name) {
		return;
	}
	
	frappe.call({
		method: 'dev_assistant.dev_assistant.doctype.field_access_control.field_access_control.get_doctype_fields',
		args: {
			doctype_name: frm.doc.doctype_name
		},
		callback: function(r) {
			if (!r.exc && r.message) {
				const response = r.message;
				const mainFields = response.main_fields || [];
				const childTableFields = response.child_table_fields || [];
				
				// Auto-add first few important fields as editable exceptions
				const importantFields = mainFields.slice(0, 3); // First 3 main fields
				
				// Use Python API to add editable field exceptions
				frappe.call({
					method: 'dev_assistant.dev_assistant.doctype.field_access_control.field_access_control.add_editable_field_exceptions',
					args: {
						docname: frm.doc.name,
						fieldnames: JSON.stringify(importantFields)
					},
					callback: function(response) {
						if (response.message && response.message.status === 'success') {
							frappe.msgprint({
								title: __('Auto-Populated Fields'),
								message: __(response.message.message),
								indicator: 'green'
							});
							
							// Refresh the form to show new fields
							frm.reload_doc();
						} else {
							frappe.msgprint({
								title: __('Error'),
								message: __(response.message.message || 'Failed to auto-populate fields'),
								indicator: 'red'
							});
						}
					}
				});
			}
		}
	});
}

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

function showFieldSelectionModal(frm, response) {
	const mainFields = response.main_fields || [];
	const childTableFields = response.child_table_fields || [];
	
	// Debug: Log the response data
	console.log('Modal response:', response);
	console.log('Main fields:', mainFields);
	console.log('Child table fields:', childTableFields);
	
	let d = new frappe.ui.Dialog({
		title: __('Choose Fields to Control'),
		width: 800,
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'help_text',
				options: '<div class="alert alert-info"><i class="fa fa-info-circle"></i> Select which fields you want to hide or make read-only for users with this role.</div>'
			},
			{
				fieldtype: 'Data',
				label: __('Search Fields'),
				fieldname: 'search_field',
				placeholder: __('Type field name to search...')
			},
			{
				fieldtype: 'Select',
				label: __('Show'),
				fieldname: 'filter_type',
				options: 'All Fields\nMain Document Fields\nChild Table Fields',
				default: 'All Fields'
			},
			{
				fieldtype: 'Select',
				label: __('Field Type'),
				fieldname: 'filter_fieldtype',
				options: 'All Types\nData\nLink\nSelect\nDate\nDatetime\nTime\nInt\nFloat\nCurrency\nPercent\nText\nSmall Text\nLong Text\nCode\nTable\nCheck\nAttach\nAttach Image\nHTML\nButton',
				default: 'All Types'
			},
		{
			fieldtype: 'HTML',
			fieldname: 'fields_list',
			options: (function() {
				const html = createUserFriendlyFieldsListHTML(mainFields, childTableFields);
				console.log('Generated HTML:', html);
				return html;
			})()
		}
		],
		primary_action_label: __('Add Selected Fields'),
		primary_action: function() {
			addSelectedFields(frm, d, mainFields, childTableFields);
		}
	});
	
	d.show();
	
	// Search functionality
	d.fields_dict.search_field.$input.on('input', function() {
		const searchTerm = $(this).val().toLowerCase();
		const filterType = d.get_value('filter_type');
		const filterFieldtype = d.get_value('filter_fieldtype');
		filterFieldsUserFriendly(d, searchTerm, filterType, filterFieldtype);
	});
	
	// Filter functionality
	d.fields_dict.filter_type.$input.on('change', function() {
		const searchTerm = d.get_value('search_field').toLowerCase();
		const filterType = $(this).val();
		const filterFieldtype = d.get_value('filter_fieldtype');
		filterFieldsUserFriendly(d, searchTerm, filterType, filterFieldtype);
	});
	
	// Field type filter functionality
	d.fields_dict.filter_fieldtype.$input.on('change', function() {
		const searchTerm = d.get_value('search_field').toLowerCase();
		const filterType = d.get_value('filter_type');
		const filterFieldtype = $(this).val();
		filterFieldsUserFriendly(d, searchTerm, filterType, filterFieldtype);
	});
}

function filterFieldsUserFriendly(dialog, searchTerm, filterType, filterFieldtype) {
	const container = dialog.fields_dict.fields_list.$wrapper;
	
	// Hide all sections first
	container.find('.field-section').hide();
	
	// Show sections based on filter
	if (filterType === 'All Fields') {
		container.find('.field-section').show();
	} else if (filterType === 'Main Document Fields') {
		container.find('.field-section').each(function() {
			const section = $(this);
			if (section.find('.main-field-row').length > 0) {
				section.show();
			}
		});
	} else if (filterType === 'Child Table Fields') {
		container.find('.field-section').each(function() {
			const section = $(this);
			if (section.find('.child-field-row').length > 0) {
				section.show();
			}
		});
	}
	
	// Apply field type and search filters within visible sections
	container.find('.field-item').each(function() {
		const item = $(this);
		const fieldText = item.text().toLowerCase();
		const fieldType = item.find('.field-type-badge').text().toLowerCase();
		
		let showItem = true;
		
		// Apply field type filter
		if (filterFieldtype !== 'All Types') {
			if (!fieldType.includes(filterFieldtype.toLowerCase())) {
				showItem = false;
			}
		}
		
		// Apply search filter
		if (showItem && searchTerm) {
			if (!fieldText.includes(searchTerm)) {
				showItem = false;
			}
		}
		
		if (showItem) {
			item.show();
		} else {
			item.hide();
		}
	});
}

function createUserFriendlyFieldsListHTML(mainFields, childTableFields) {
	let html = '<div style="max-height: 450px; overflow-y: auto; border: 1px solid #e0e0e0; border-radius: 6px;">';
	
	// Main Document Fields Section
	if (mainFields.length > 0) {
		html += '<div class="field-section" style="margin-bottom: 20px;">';
		html += '<div class="section-header" style="background: #f8f9fa; padding: 10px; border-bottom: 1px solid #e0e0e0; font-weight: bold; color: #495057;">';
		html += '<i class="fa fa-file-text-o" style="margin-right: 8px; color: #007bff;"></i>';
		html += `Main Document Fields (${mainFields.length})`;
		html += '</div>';
		html += '<div class="section-content" style="padding: 10px;">';
		
		mainFields.forEach(function(field, index) {
			const fieldType = field.fieldtype || 'Data';
			const fieldTypeIcon = getFieldTypeIcon(fieldType);
			html += '<div class="field-item" style="display: flex; align-items: center; padding: 8px; border-bottom: 1px solid #f0f0f0; cursor: pointer;" onclick="window.toggleFieldCheckbox(this)">';
			html += `<input type="checkbox" class="field-checkbox main-field-row" value="${index}" data-fieldname="${field.fieldname}" data-label="${field.label}" data-is-child-table="false" style="margin-right: 10px;" onchange="window.updateFieldSelection()">`;
			html += '<div style="flex: 1;">';
			html += `<div style="font-weight: 500; color: #333;">${field.label || field.fieldname}</div>`;
			html += `<div style="font-size: 12px; color: #666; font-family: monospace;">${field.fieldname}</div>`;
			html += '</div>';
			html += `<span class="field-type-badge badge badge-secondary" style="font-size: 10px; margin-right: 5px;"><i class="fa ${fieldTypeIcon}"></i> ${fieldType}</span>`;
			html += '<span class="badge badge-primary" style="font-size: 11px;">Main</span>';
			html += '</div>';
		});
		
		html += '</div></div>';
	}
	
	// Child Table Fields Section - Multiple Tables Support
	if (childTableFields.length > 0) {
		const groupedChildFields = {};
		childTableFields.forEach(function(field) {
			const parentField = field.parent_field;
			if (!groupedChildFields[parentField]) {
				groupedChildFields[parentField] = [];
			}
			groupedChildFields[parentField].push(field);
		});
		
		// Sort child tables by name for better organization
		const sortedChildTables = Object.keys(groupedChildFields).sort();
		
		sortedChildTables.forEach(function(parentField, tableIndex) {
			const fields = groupedChildFields[parentField];
			const tableColor = getTableColor(tableIndex);
			
			html += '<div class="field-section child-table-section" style="margin-bottom: 20px;">';
			html += '<div class="section-header" style="background: ' + tableColor.background + '; padding: 10px; border-bottom: 1px solid ' + tableColor.border + '; font-weight: bold; color: ' + tableColor.text + ';">';
			html += '<i class="fa fa-table" style="margin-right: 8px; color: ' + tableColor.icon + ';"></i>';
			html += `${parentField} Table (${fields.length} fields)`;
			html += '</div>';
			html += '<div class="section-content" style="padding: 10px;">';
			
			fields.forEach(function(field, index) {
				const fieldType = field.fieldtype || 'Data';
				const fieldTypeIcon = getFieldTypeIcon(fieldType);
				html += '<div class="field-item" style="display: flex; align-items: center; padding: 8px; border-bottom: 1px solid #f0f0f0; cursor: pointer; background-color: #fefefe;" onclick="window.toggleFieldCheckbox(this)">';
				html += `<input type="checkbox" class="field-checkbox child-field-row" value="child_${tableIndex}_${index}" data-fieldname="${field.fieldname}" data-label="${field.label}" data-is-child-table="true" data-parent-field="${field.parent_field}" data-child-doctype="${field.child_doctype}" data-child-fieldname="${field.child_fieldname}" style="margin-right: 10px;" onchange="window.updateFieldSelection()">`;
				html += '<div style="flex: 1;">';
				html += `<div style="font-weight: 500; color: #333;">${field.label || field.fieldname}</div>`;
				html += `<div style="font-size: 12px; color: #666; font-family: monospace;">${field.fieldname}</div>`;
				html += '</div>';
				html += `<span class="field-type-badge badge badge-secondary" style="font-size: 10px; margin-right: 5px;"><i class="fa ${fieldTypeIcon}"></i> ${fieldType}</span>`;
				html += '<span class="badge badge-warning" style="font-size: 11px;">Child</span>';
				html += '</div>';
			});
			
			html += '</div></div>';
		});
	}
	
	html += '</div>';
	
	// Functions are now defined globally at the top of the file
	
	return html;
}

function getTableColor(tableIndex) {
	const colors = [
		{ background: '#fff3cd', border: '#ffeaa7', text: '#856404', icon: '#ffc107' }, // Yellow
		{ background: '#d1ecf1', border: '#bee5eb', text: '#0c5460', icon: '#17a2b8' }, // Blue
		{ background: '#d4edda', border: '#c3e6cb', text: '#155724', icon: '#28a745' }, // Green
		{ background: '#f8d7da', border: '#f5c6cb', text: '#721c24', icon: '#dc3545' }, // Red
		{ background: '#e2e3e5', border: '#d6d8db', text: '#383d41', icon: '#6c757d' }, // Gray
		{ background: '#fce4ec', border: '#f8bbd9', text: '#880e4f', icon: '#e91e63' }  // Pink
	];
	return colors[tableIndex % colors.length];
}

function getFieldTypeIcon(fieldtype) {
	const iconMap = {
		'Data': 'fa-font',
		'Link': 'fa-link',
		'Select': 'fa-list',
		'Date': 'fa-calendar',
		'Datetime': 'fa-clock-o',
		'Time': 'fa-clock-o',
		'Int': 'fa-hashtag',
		'Float': 'fa-calculator',
		'Currency': 'fa-money',
		'Percent': 'fa-percent',
		'Text': 'fa-align-left',
		'Small Text': 'fa-align-left',
		'Long Text': 'fa-align-left',
		'Code': 'fa-code',
		'Table': 'fa-table',
		'Check': 'fa-check-square-o',
		'Attach': 'fa-paperclip',
		'Attach Image': 'fa-image',
		'HTML': 'fa-code',
		'Button': 'fa-hand-pointer-o',
		'Section Break': 'fa-minus',
		'Column Break': 'fa-columns',
		'Tab Break': 'fa-folder-o'
	};
	return iconMap[fieldtype] || 'fa-cog';
}


function addSelectedFields(frm, dialog, mainFields, childTableFields) {
	const selectedCheckboxes = $('.field-checkbox:checked');
	const selectedFields = [];
	
	// Debug: Log all checkboxes and selected ones
	console.log('All checkboxes:', $('.field-checkbox').length);
	console.log('Selected checkboxes:', selectedCheckboxes.length);
	console.log('Selected checkboxes data:', selectedCheckboxes);
	
	selectedCheckboxes.each(function() {
		const checkbox = $(this);
		const isChildTable = checkbox.data('is-child-table') === 'true' || checkbox.hasClass('child-field-row');
		
		// Debug: Log checkbox data
		console.log('Checkbox data:', {
			fieldname: checkbox.data('fieldname'),
			label: checkbox.data('label'),
			isChildTable: isChildTable,
			parentField: checkbox.data('parent-field'),
			childDoctype: checkbox.data('child-doctype'),
			childFieldname: checkbox.data('child-fieldname'),
			classes: checkbox.attr('class')
		});
		
		const fieldData = {
			fieldname: checkbox.data('fieldname'),
			label: checkbox.data('label'),
			is_child_table: isChildTable
		};
		
		// Add child table specific data
		if (isChildTable) {
			fieldData.parent_field = checkbox.data('parent-field');
			fieldData.child_doctype = checkbox.data('child-doctype');
			fieldData.child_fieldname = checkbox.data('child-fieldname');
		}
		
		selectedFields.push(fieldData);
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
	
	// Debug: Log the selected fields data
	console.log('Selected fields data:', selectedFields);
	
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
