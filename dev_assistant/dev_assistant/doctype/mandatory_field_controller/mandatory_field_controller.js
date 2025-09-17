frappe.ui.form.on('Mandatory Field Controller', {
	refresh: function(frm) {
		// Update field options on form load
		if (frm.doc.document_type) {
			update_field_options(frm);
		}

		// Add bulk selection button for mandatory fields
		if (frm.doc.document_type && !frm.is_new()) {
			frm.add_custom_button(__('Bulk Add Fields'), function() {
				show_bulk_field_selector(frm);
			}, __('Actions'));

			frm.add_custom_button(__('Smart Add Conditions'), function() {
				show_smart_condition_builder(frm);
			}, __('Actions'));
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

frappe.ui.form.on('Mandatory Field Condition', {
	field: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		console.log('Field selected:', row.field, 'for row:', cdn);
		if (row.field && frm.doc.document_type) {
			// Show smart value suggestions for the selected field
			setTimeout(() => {
				show_smart_value_suggestions(frm, row.field, cdn);
			}, 500);
		}
	}
});

// Add event listener for value field clicks using event delegation - works for both inline and dialog editing
$(document).on('focus', '[data-fieldname="value"] input', function() {
	console.log('Value field focused');

	let cdn, row;

	// Check if we're in a dialog (row editing) or inline grid
	let dialog = $(this).closest('.modal-dialog');
	if (dialog.length > 0) {
		// We're in row edit dialog
		console.log('In row edit dialog');

		// Try to get the dialog form instance
		let dialog_wrapper = $(this).closest('.frappe-dialog');
		if (dialog_wrapper.length > 0) {
			let dialog_obj = dialog_wrapper.data('dialog');
			if (dialog_obj && dialog_obj.doc) {
				row = dialog_obj.doc;
				cdn = row.name;
				console.log('Dialog row found:', row.field, cdn);
			}
		}
	} else {
		// We're in inline grid editing
		let grid_row = $(this).closest('.grid-row');
		cdn = grid_row.data('name');

		if (cdn) {
			row = locals['Mandatory Field Condition'][cdn];
		}
	}

	if (row && row.field) {
		console.log('Showing suggestions for field:', row.field);

		// Get the form reference
		let frm = cur_frm;
		if (frm && frm.doc.document_type) {
			show_smart_value_suggestions_for_dialog(frm, row.field, $(this));
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

function show_bulk_field_selector(frm) {
	if (!frm.doc.document_type) {
		frappe.msgprint(__('Please select Document Type first'));
		return;
	}

	// Get fields for the selected doctype
	frappe.model.with_doctype(frm.doc.document_type, () => {
		let fieldnames = frappe
			.get_meta(frm.doc.document_type)
			.fields.filter((d) => {
				return frappe.model.no_value_type.indexOf(d.fieldtype) === -1;
			})
			.map((d) => {
				return {
					value: d.fieldname,
					label: d.label || d.fieldname.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
				};
			});

		// Create dialog for bulk selection
		let d = new frappe.ui.Dialog({
			title: __('Select Fields to Make Mandatory'),
			size: 'large',
			fields: [
				{
					fieldtype: 'HTML',
					fieldname: 'help_text',
					options: '<div class="alert alert-info"><strong>Tip:</strong> Select multiple fields to add them as mandatory fields at once. You can search using the box below.</div>'
				},
				{
					fieldtype: 'Data',
					fieldname: 'search_field',
					label: __('Search Fields'),
					placeholder: __('Type to search fields...'),
					onchange: function() {
						filter_field_checkboxes(this.value);
					}
				},
				{
					fieldtype: 'HTML',
					fieldname: 'field_list',
					options: get_field_checkboxes_html(fieldnames)
				}
			],
			primary_action: function() {
				let selected_fields = [];

				// Get all checked fields
				$('.field-checkbox:checked').each(function() {
					selected_fields.push({
						field_name: $(this).val(),
						field_label: $(this).data('label')
					});
				});

				if (selected_fields.length === 0) {
					frappe.msgprint(__('Please select at least one field'));
					return;
				}

				// Add selected fields to the child table
				selected_fields.forEach(function(field) {
					let existing = frm.doc.mandatory_fields.find(f => f.field_name === field.field_name);
					if (!existing) {
						let row = frm.add_child('mandatory_fields');
						row.field_name = field.field_name;
						row.field_label = field.field_label;
					}
				});

				frm.refresh_field('mandatory_fields');
				frappe.show_alert({
					message: __('Added {0} fields successfully', [selected_fields.length]),
					indicator: 'green'
				});

				d.hide();
			},
			primary_action_label: __('Add Selected Fields')
		});

		d.show();
	});
}

function get_field_checkboxes_html(fields) {
	let html = `
		<style>
			.field-selector {
				max-height: 400px;
				overflow-y: auto;
				border: 1px solid #d1d8dd;
				border-radius: 4px;
				padding: 10px;
				background: #fafbfc;
			}
			.field-checkbox-item {
				display: flex;
				align-items: center;
				padding: 6px 8px;
				margin: 2px 0;
				border-radius: 3px;
				transition: background-color 0.2s;
			}
			.field-checkbox-item:hover {
				background-color: #e9ecef;
			}
			.field-checkbox-item input[type="checkbox"] {
				margin-right: 8px;
				transform: scale(1.2);
			}
			.field-checkbox-item label {
				margin: 0;
				cursor: pointer;
				flex: 1;
				font-size: 13px;
			}
			.field-name {
				color: #6c757d;
				font-size: 11px;
				margin-left: 4px;
			}
			.select-all-section {
				background: #e3f2fd;
				padding: 8px 12px;
				border-radius: 4px;
				margin-bottom: 10px;
				border: 1px solid #bbdefb;
			}
		</style>
	`;

	html += `
		<div class="select-all-section">
			<label style="margin: 0; font-weight: 500;">
				<input type="checkbox" id="select-all-fields" style="margin-right: 8px; transform: scale(1.2);">
				Select All Fields (${fields.length} total)
			</label>
		</div>
	`;

	html += '<div class="field-selector">';

	fields.forEach(function(field) {
		html += `
			<div class="field-checkbox-item">
				<input type="checkbox" class="field-checkbox" value="${field.value}" data-label="${field.label}">
				<label>
					<strong>${field.label}</strong>
					<span class="field-name">(${field.value})</span>
				</label>
			</div>
		`;
	});

	html += '</div>';

	// Add JavaScript for select all functionality
	setTimeout(function() {
		// Select all functionality with event delegation
		$(document).off('change', '#select-all-fields').on('change', '#select-all-fields', function() {
			let isChecked = $(this).is(':checked');
			$('.field-checkbox:visible').prop('checked', isChecked);
			console.log('Select all clicked:', isChecked);
		});

		// Individual checkbox change
		$(document).off('change', '.field-checkbox').on('change', '.field-checkbox', function() {
			let total = $('.field-checkbox:visible').length;
			let checked = $('.field-checkbox:visible:checked').length;

			if (checked === 0) {
				$('#select-all-fields').prop('indeterminate', false).prop('checked', false);
			} else if (checked === total) {
				$('#select-all-fields').prop('indeterminate', false).prop('checked', true);
			} else {
				$('#select-all-fields').prop('indeterminate', true).prop('checked', false);
			}
		});
	}, 500);

	return html;
}

function filter_field_checkboxes(search_term) {
	$('.field-checkbox-item').each(function() {
		let text = $(this).text().toLowerCase();
		if (text.includes(search_term.toLowerCase()) || search_term === '') {
			$(this).show();
		} else {
			$(this).hide();
		}
	});

	// Update select all checkbox state after filtering
	let total = $('.field-checkbox:visible').length;
	let checked = $('.field-checkbox:visible:checked').length;
	$('#select-all-fields').prop('indeterminate', checked > 0 && checked < total);
	$('#select-all-fields').prop('checked', checked === total && total > 0);
}

function show_smart_condition_builder(frm) {
	if (!frm.doc.document_type) {
		frappe.msgprint(__('Please select Document Type first'));
		return;
	}

	// Get fields for the selected doctype with their types
	frappe.model.with_doctype(frm.doc.document_type, () => {
		let meta = frappe.get_meta(frm.doc.document_type);
		let fields = meta.fields.filter((d) => {
			return frappe.model.no_value_type.indexOf(d.fieldtype) === -1;
		}).map((d) => {
			return {
				value: d.fieldname,
				label: d.label || d.fieldname.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
				fieldtype: d.fieldtype,
				options: d.options
			};
		});

		// Create dynamic condition builder dialog
		let d = new frappe.ui.Dialog({
			title: __('🎯 Smart Condition Builder'),
			size: 'large',
			fields: [
				{
					fieldtype: 'HTML',
					fieldname: 'help_text',
					options: `<div class="alert alert-primary">
						<strong>💡 Smart Tips:</strong>
						<ul style="margin: 8px 0; padding-left: 20px;">
							<li>Select a field and we'll show relevant values automatically</li>
							<li>Link fields will show actual records from the linked DocType</li>
							<li>Select fields will show available options</li>
							<li>Use "in" operator for multiple values (comma separated)</li>
						</ul>
					</div>`
				},
				{
					fieldtype: 'Select',
					fieldname: 'field_name',
					label: __('Field'),
					options: fields.map(f => ({ label: f.label, value: f.value })),
					reqd: 1,
					change: function() {
						handle_field_selection(this, fields, d);
					}
				},
				{
					fieldtype: 'Select',
					fieldname: 'condition',
					label: __('Condition'),
					options: [
						{ label: 'Equals (=)', value: '=' },
						{ label: 'Not Equals (≠)', value: '!=' },
						{ label: 'In (any of)', value: 'in' },
						{ label: 'Not In (none of)', value: 'not in' },
						{ label: 'Greater Than (>)', value: '>' },
						{ label: 'Less Than (<)', value: '<' },
						{ label: 'Greater or Equal (≥)', value: '>=' },
						{ label: 'Less or Equal (≤)', value: '<=' }
					],
					reqd: 1,
					change: function() {
						handle_condition_change(this, d);
					}
				},
				{
					fieldtype: 'HTML',
					fieldname: 'value_section',
					options: '<div id="value-input-section">Please select a field first</div>'
				}
			],
			primary_action: function() {
				let values = d.get_values();

				if (!values.field_name || !values.condition) {
					frappe.msgprint(__('Please fill all required fields'));
					return;
				}

				let condition_value = get_condition_value_from_dialog();
				if (!condition_value) {
					frappe.msgprint(__('Please enter a value for the condition'));
					return;
				}

				// Add condition to the child table
				let row = frm.add_child('conditions');
				row.field = values.field_name;
				row.condition = values.condition;
				row.value = condition_value;

				frm.refresh_field('conditions');

				frappe.show_alert({
					message: __('Condition added successfully!'),
					indicator: 'green'
				});

				d.hide();
			},
			primary_action_label: __('Add Condition')
		});

		d.show();
	});
}

function handle_field_selection(field_obj, fields, dialog) {
	let selected_field = fields.find(f => f.value === field_obj.value);

	if (!selected_field) {
		$('#value-input-section').html('Please select a field first');
		return;
	}

	let html = '<div style="margin-top: 10px;">';
	html += `<label class="control-label" style="margin-bottom: 6px; display: block;">Value</label>`;

	// Handle different field types
	if (selected_field.fieldtype === 'Link') {
		html += create_link_field_input(selected_field);
	} else if (selected_field.fieldtype === 'Select') {
		html += create_select_field_input(selected_field);
	} else if (['Data', 'Small Text', 'Text', 'Text Editor'].includes(selected_field.fieldtype)) {
		html += create_text_field_input(selected_field);
	} else if (['Int', 'Float', 'Currency'].includes(selected_field.fieldtype)) {
		html += create_number_field_input(selected_field);
	} else if (selected_field.fieldtype === 'Check') {
		html += create_checkbox_field_input(selected_field);
	} else if (['Date', 'Datetime'].includes(selected_field.fieldtype)) {
		html += create_date_field_input(selected_field);
	} else {
		html += create_text_field_input(selected_field);
	}

	html += '</div>';
	$('#value-input-section').html(html);

	// Load actual values for Link and Select fields
	if (selected_field.fieldtype === 'Link') {
		load_link_field_values(selected_field);
	}
}

function create_link_field_input(field) {
	return `
		<div class="link-field-container">
			<select class="form-control condition-value-input" id="link-value-select" style="margin-bottom: 8px;">
				<option value="">Loading ${field.options} records...</option>
			</select>
			<div class="help-text">
				<small class="text-muted">💡 Select from actual ${field.options} records or type custom value below</small>
			</div>
			<input type="text" class="form-control condition-value-input" id="custom-value-input"
				   placeholder="Or enter custom value..." style="margin-top: 8px;">
		</div>
	`;
}

function create_select_field_input(field) {
	let options = field.options ? field.options.split('\n') : [];
	let optionsHtml = '<option value="">Select an option...</option>';

	options.forEach(option => {
		if (option.trim()) {
			optionsHtml += `<option value="${option.trim()}">${option.trim()}</option>`;
		}
	});

	return `
		<div class="select-field-container">
			<select class="form-control condition-value-input" id="select-value-input">
				${optionsHtml}
			</select>
			<div class="help-text">
				<small class="text-muted">💡 Available options for this field</small>
			</div>
		</div>
	`;
}

function create_text_field_input(field) {
	return `
		<div class="text-field-container">
			<input type="text" class="form-control condition-value-input" id="text-value-input"
				   placeholder="Enter value for ${field.label}...">
			<div class="help-text">
				<small class="text-muted">💡 For "in" operator, separate multiple values with commas</small>
			</div>
		</div>
	`;
}

function create_number_field_input(field) {
	return `
		<div class="number-field-container">
			<input type="number" class="form-control condition-value-input" id="number-value-input"
				   placeholder="Enter numeric value..." step="any">
			<div class="help-text">
				<small class="text-muted">💡 Use numeric values for comparison</small>
			</div>
		</div>
	`;
}

function create_checkbox_field_input(field) {
	return `
		<div class="checkbox-field-container">
			<select class="form-control condition-value-input" id="checkbox-value-input">
				<option value="">Select...</option>
				<option value="1">Checked (Yes)</option>
				<option value="0">Unchecked (No)</option>
			</select>
			<div class="help-text">
				<small class="text-muted">💡 Choose whether checkbox should be checked or unchecked</small>
			</div>
		</div>
	`;
}

function create_date_field_input(field) {
	return `
		<div class="date-field-container">
			<input type="date" class="form-control condition-value-input" id="date-value-input">
			<div class="help-text">
				<small class="text-muted">💡 Select date for comparison</small>
			</div>
		</div>
	`;
}

function load_link_field_values(field) {
	if (!field.options) return;

	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: field.options,
			fields: ['name'],
			limit_page_length: 50,
			order_by: 'modified desc'
		},
		callback: function(r) {
			if (r.message && r.message.length > 0) {
				let optionsHtml = '<option value="">Select a record...</option>';

				r.message.forEach(record => {
					optionsHtml += `<option value="${record.name}">${record.name}</option>`;
				});

				$('#link-value-select').html(optionsHtml);
			} else {
				$('#link-value-select').html('<option value="">No records found</option>');
			}
		}
	});
}

function handle_condition_change(condition_obj, dialog) {
	let condition = condition_obj.value;
	let helpTexts = {
		'in': '💡 Enter multiple values separated by commas (e.g., "A,B,C")',
		'not in': '💡 Enter values to exclude, separated by commas (e.g., "X,Y,Z")',
		'=': '💡 Enter exact value to match',
		'!=': '💡 Enter value that should NOT match',
		'>': '💡 Enter minimum value (for numbers/dates)',
		'<': '💡 Enter maximum value (for numbers/dates)',
		'>=': '💡 Enter minimum value (inclusive)',
		'<=': '💡 Enter maximum value (inclusive)'
	};

	if (helpTexts[condition]) {
		$('.help-text small').text(helpTexts[condition]);
	}
}

function get_condition_value_from_dialog() {
	// Try different input types
	let value = $('#link-value-select').val() ||
				$('#custom-value-input').val() ||
				$('#select-value-input').val() ||
				$('#text-value-input').val() ||
				$('#number-value-input').val() ||
				$('#checkbox-value-input').val() ||
				$('#date-value-input').val();

	return value ? value.toString().trim() : '';
}

function show_smart_value_suggestions(frm, fieldname, cdn) {
	if (!frm.doc.document_type || !fieldname) return;

	// Get field metadata
	frappe.model.with_doctype(frm.doc.document_type, () => {
		let meta = frappe.get_meta(frm.doc.document_type);
		let field_meta = meta.fields.find(f => f.fieldname === fieldname);

		if (!field_meta) return;

		let suggestions = [];
		let field_label = field_meta.label || fieldname.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

		// Handle different field types
		if (field_meta.fieldtype === 'Link') {
			// Load actual records from linked doctype
			load_link_suggestions(field_meta, fieldname, cdn, field_label);
		} else if (field_meta.fieldtype === 'Select') {
			// Show select options
			load_select_suggestions(field_meta, fieldname, cdn, field_label);
		} else if (field_meta.fieldtype === 'Check') {
			// Show checkbox options
			suggestions = [
				{ label: '✅ Checked (Yes)', value: '1' },
				{ label: '❌ Unchecked (No)', value: '0' }
			];
			show_value_suggestions_popup(suggestions, fieldname, cdn, field_label);
		} else {
			// For other field types, show common value examples
			load_common_values_suggestions(frm.doc.document_type, fieldname, cdn, field_label);
		}
	});
}

function load_link_suggestions(field_meta, fieldname, cdn, field_label) {
	if (!field_meta.options) return;

	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: field_meta.options,
			fields: ['name'],
			limit_page_length: 20,
			order_by: 'modified desc'
		},
		callback: function(r) {
			if (r.message && r.message.length > 0) {
				let suggestions = r.message.map(record => ({
					label: `🔗 ${record.name}`,
					value: record.name
				}));

				show_value_suggestions_popup(suggestions, fieldname, cdn, `${field_label} (${field_meta.options})`);
			}
		}
	});
}

function load_select_suggestions(field_meta, fieldname, cdn, field_label) {
	if (!field_meta.options) return;

	let options = field_meta.options.split('\n').filter(opt => opt.trim());
	let suggestions = options.map(option => ({
		label: `📋 ${option.trim()}`,
		value: option.trim()
	}));

	show_value_suggestions_popup(suggestions, fieldname, cdn, field_label);
}

function load_common_values_suggestions(doctype, fieldname, cdn, field_label) {
	// Load actual values from existing records
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: doctype,
			fields: [fieldname],
			limit_page_length: 20,
			order_by: 'modified desc',
			filters: [[fieldname, '!=', '']]
		},
		callback: function(r) {
			if (r.message && r.message.length > 0) {
				// Get unique values
				let unique_values = [...new Set(r.message.map(record => record[fieldname]).filter(val => val))];

				let suggestions = unique_values.slice(0, 10).map(value => ({
					label: `💡 ${value}`,
					value: value
				}));

				if (suggestions.length > 0) {
					show_value_suggestions_popup(suggestions, fieldname, cdn, `${field_label} (Recent Values)`);
				}
			}
		}
	});
}

function show_value_suggestions_popup(suggestions, fieldname, cdn, title) {
	if (!suggestions || suggestions.length === 0) return;

	console.log('Creating popup for:', title, 'with', suggestions.length, 'suggestions');

	// Create popup near the value field - try multiple selectors
	let field_element = $(`.grid-row[data-name="${cdn}"] [data-fieldname="value"] input`);

	if (!field_element.length) {
		field_element = $(`.grid-row[data-name="${cdn}"] input[data-fieldname="value"]`);
	}

	if (!field_element.length) {
		console.log('Field element not found for CDN:', cdn);
		return;
	}

	console.log('Field element found:', field_element.length);

	// Remove existing popup
	$('.value-suggestions-popup').remove();

	let popup_html = `
		<div class="value-suggestions-popup" style="
			position: absolute;
			z-index: 9999;
			background: white;
			border: 1px solid #d1d8dd;
			border-radius: 6px;
			box-shadow: 0 4px 12px rgba(0,0,0,0.15);
			max-width: 300px;
			max-height: 250px;
			overflow-y: auto;
		">
			<div style="padding: 8px 12px; background: #f8f9fa; border-bottom: 1px solid #dee2e6; font-weight: 500; font-size: 12px;">
				${title}
			</div>
			<div class="suggestions-list">
				${suggestions.map(suggestion => `
					<div class="suggestion-item" data-value="${suggestion.value}" style="
						padding: 6px 12px;
						cursor: pointer;
						font-size: 13px;
						border-bottom: 1px solid #f1f3f4;
						transition: background-color 0.2s;
					">
						${suggestion.label}
					</div>
				`).join('')}
			</div>
		</div>
	`;

	let popup = $(popup_html);

	// Position popup below the input field
	let offset = field_element.offset();
	popup.css({
		top: offset.top + field_element.outerHeight() + 2,
		left: offset.left
	});

	// Add popup to body
	$('body').append(popup);

	// Handle suggestion clicks
	popup.find('.suggestion-item').on('click', function() {
		let value = $(this).data('value');
		field_element.val(value).trigger('change');
		popup.remove();
	});

	// Handle hover effects
	popup.find('.suggestion-item').on('mouseenter', function() {
		$(this).css('background-color', '#e9ecef');
	}).on('mouseleave', function() {
		$(this).css('background-color', 'transparent');
	});

	// Close popup when clicking outside
	$(document).one('click', function(e) {
		if (!popup.is(e.target) && popup.has(e.target).length === 0) {
			popup.remove();
		}
	});

	// Close popup when pressing escape
	$(document).one('keydown', function(e) {
		if (e.key === 'Escape') {
			popup.remove();
		}
	});
}

function show_smart_value_suggestions_for_dialog(frm, fieldname, input_element) {
	if (!frm.doc.document_type || !fieldname) return;

	console.log('Loading suggestions for dialog field:', fieldname);

	// Get field metadata
	frappe.model.with_doctype(frm.doc.document_type, () => {
		let meta = frappe.get_meta(frm.doc.document_type);
		let field_meta = meta.fields.find(f => f.fieldname === fieldname);

		if (!field_meta) return;

		let field_label = field_meta.label || fieldname.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

		// Handle different field types
		if (field_meta.fieldtype === 'Link') {
			// Load actual records from linked doctype
			load_link_suggestions_for_dialog(field_meta, input_element, field_label);
		} else if (field_meta.fieldtype === 'Select') {
			// Show select options
			load_select_suggestions_for_dialog(field_meta, input_element, field_label);
		} else if (field_meta.fieldtype === 'Check') {
			// Show checkbox options
			let suggestions = [
				{ label: '✅ Checked (Yes)', value: '1' },
				{ label: '❌ Unchecked (No)', value: '0' }
			];
			show_dialog_suggestions_popup(suggestions, input_element, field_label);
		} else {
			// For other field types, show common value examples
			load_common_values_suggestions_for_dialog(frm.doc.document_type, fieldname, input_element, field_label);
		}
	});
}

function load_link_suggestions_for_dialog(field_meta, input_element, field_label) {
	if (!field_meta.options) return;

	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: field_meta.options,
			fields: ['name'],
			limit_page_length: 20,
			order_by: 'modified desc'
		},
		callback: function(r) {
			if (r.message && r.message.length > 0) {
				let suggestions = r.message.map(record => ({
					label: `🔗 ${record.name}`,
					value: record.name
				}));

				show_dialog_suggestions_popup(suggestions, input_element, `${field_label} (${field_meta.options})`);
			}
		}
	});
}

function load_select_suggestions_for_dialog(field_meta, input_element, field_label) {
	if (!field_meta.options) return;

	let options = field_meta.options.split('\n').filter(opt => opt.trim());
	let suggestions = options.map(option => ({
		label: `📋 ${option.trim()}`,
		value: option.trim()
	}));

	show_dialog_suggestions_popup(suggestions, input_element, field_label);
}

function load_common_values_suggestions_for_dialog(doctype, fieldname, input_element, field_label) {
	// Load actual values from existing records
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: doctype,
			fields: [fieldname],
			limit_page_length: 20,
			order_by: 'modified desc',
			filters: [[fieldname, '!=', '']]
		},
		callback: function(r) {
			if (r.message && r.message.length > 0) {
				// Get unique values
				let unique_values = [...new Set(r.message.map(record => record[fieldname]).filter(val => val))];

				let suggestions = unique_values.slice(0, 10).map(value => ({
					label: `💡 ${value}`,
					value: value
				}));

				if (suggestions.length > 0) {
					show_dialog_suggestions_popup(suggestions, input_element, `${field_label} (Recent Values)`);
				}
			}
		}
	});
}

function show_dialog_suggestions_popup(suggestions, input_element, title) {
	if (!suggestions || suggestions.length === 0) return;

	console.log('Creating dialog popup for:', title, 'with', suggestions.length, 'suggestions');

	// Remove existing popup
	$('.value-suggestions-popup').remove();

	let popup_html = `
		<div class="value-suggestions-popup" style="
			position: absolute;
			z-index: 99999;
			background: white;
			border: 1px solid #d1d8dd;
			border-radius: 6px;
			box-shadow: 0 4px 12px rgba(0,0,0,0.15);
			max-width: 300px;
			max-height: 250px;
			overflow-y: auto;
		">
			<div style="padding: 8px 12px; background: #f8f9fa; border-bottom: 1px solid #dee2e6; font-weight: 500; font-size: 12px;">
				${title}
			</div>
			<div class="suggestions-list">
				${suggestions.map(suggestion => `
					<div class="suggestion-item" data-value="${suggestion.value}" style="
						padding: 6px 12px;
						cursor: pointer;
						font-size: 13px;
						border-bottom: 1px solid #f1f3f4;
						transition: background-color 0.2s;
					">
						${suggestion.label}
					</div>
				`).join('')}
			</div>
		</div>
	`;

	let popup = $(popup_html);

	// Position popup below the input field
	let offset = input_element.offset();
	popup.css({
		top: offset.top + input_element.outerHeight() + 2,
		left: offset.left
	});

	// Add popup to body
	$('body').append(popup);

	// Handle suggestion clicks
	popup.find('.suggestion-item').on('click', function() {
		let value = $(this).data('value');
		input_element.val(value).trigger('change');
		popup.remove();
	});

	// Handle hover effects
	popup.find('.suggestion-item').on('mouseenter', function() {
		$(this).css('background-color', '#e9ecef');
	}).on('mouseleave', function() {
		$(this).css('background-color', 'transparent');
	});

	// Close popup when clicking outside
	$(document).one('click', function(e) {
		if (!popup.is(e.target) && popup.has(e.target).length === 0) {
			popup.remove();
		}
	});

	// Close popup when pressing escape
	$(document).one('keydown', function(e) {
		if (e.key === 'Escape') {
			popup.remove();
		}
	});
}