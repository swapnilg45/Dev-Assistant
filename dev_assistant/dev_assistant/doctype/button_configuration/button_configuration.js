// Copyright (c) 2025, Dev Assistant Team and contributors
// For license information, please see license.txt

frappe.ui.form.on('Button Configuration', {
    refresh: function(frm) {
        // Add custom buttons for testing
        if (!frm.is_new()) {
            frm.add_custom_button(__('Test Configuration'), function() {
                test_button_configuration(frm);
            });

            frm.add_custom_button(__('Get DocType Fields'), function() {
                get_doctype_fields(frm);
            });
        }
    },

    button_location: function(frm) {
        // Clear target fields when location changes
        if (frm.doc.button_location === 'DocType Form') {
            frm.set_value('target_report', '');
        } else if (frm.doc.button_location === 'Report') {
            frm.set_value('target_doctype', '');
        }
    },

    button_type: function(frm) {
        // Clear button group if changing to Normal
        if (frm.doc.button_type === 'Normal') {
            frm.set_value('button_group', '');
        }
    },

    target_doctype: function(frm) {
        // Provide option to get fields for conditions
        if (frm.doc.target_doctype) {
            frm.set_df_property('conditions', 'description',
                `Define when the button should be visible. Use "Get DocType Fields" button to see available fields for ${frm.doc.target_doctype}`);
        }
    }
});

frappe.ui.form.on('Button Condition', {
    operator: function(frm, cdt, cdn) {
        const row = frappe.get_doc(cdt, cdn);
        // Clear value for operators that don't need it
        if (row.operator === 'is set' || row.operator === 'is not set') {
            frappe.model.set_value(cdt, cdn, 'condition_value', '');
        }
    }
});

// Helper functions
function test_button_configuration(frm) {
    // Dialog to test the button configuration
    const dialog = new frappe.ui.Dialog({
        title: __('Test Button Configuration'),
        fields: [
            {
                fieldname: 'test_doctype',
                fieldtype: 'Link',
                label: 'Test DocType',
                options: 'DocType',
                reqd: 1,
                default: frm.doc.target_doctype,
                read_only: frm.doc.button_location === 'DocType Form'
            },
            {
                fieldname: 'test_document',
                fieldtype: 'Dynamic Link',
                label: 'Test Document',
                options: 'test_doctype',
                reqd: 1,
                depends_on: "eval:doc.test_doctype"
            }
        ],
        primary_action_label: __('Test'),
        primary_action: function(values) {
            frappe.call({
                method: 'dev_assistant.dev_assistant.doctype.button_configuration.button_configuration.evaluate_button_visibility',
                args: {
                    button_name: frm.doc.name,
                    doc_data: {
                        doctype: values.test_doctype,
                        name: values.test_document
                    }
                },
                callback: function(r) {
                    if (r.message) {
                        const result = r.message;
                        const message = `
                            <h5>Test Results</h5>
                            <p><strong>Visible:</strong> ${result.visible ? 'Yes' : 'No'}</p>
                            <p><strong>Reason:</strong> ${result.reason}</p>
                            ${result.details ? '<hr><pre>' + JSON.stringify(result.details, null, 2) + '</pre>' : ''}
                        `;
                        frappe.msgprint({
                            title: __('Button Visibility Test'),
                            message: message,
                            indicator: result.visible ? 'green' : 'red'
                        });
                    }
                }
            });
            dialog.hide();
        }
    });
    dialog.show();
}

function get_doctype_fields(frm) {
    if (!frm.doc.target_doctype) {
        frappe.msgprint(__('Please select a Target DocType first'));
        return;
    }

    frappe.call({
        method: 'dev_assistant.dev_assistant.doctype.button_configuration.button_configuration.get_doctype_fields',
        args: {
            doctype: frm.doc.target_doctype
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                // Create a proper dialog instead of msgprint
                const dialog = new frappe.ui.Dialog({
                    title: __('Available Fields for {0}', [frm.doc.target_doctype]),
                    size: 'large',
                    fields: [
                        {
                            fieldname: 'search_field',
                            fieldtype: 'Data',
                            label: 'Search Fields',
                            placeholder: 'Type to filter fields...'
                        },
                        {
                            fieldname: 'fields_html',
                            fieldtype: 'HTML'
                        }
                    ]
                });

                // Build responsive field cards
                const buildFieldsHTML = (fields, searchTerm = '') => {
                    const filteredFields = fields.filter(field => {
                        if (!searchTerm) return true;
                        const term = searchTerm.toLowerCase();
                        return field.fieldname.toLowerCase().includes(term) ||
                               (field.label && field.label.toLowerCase().includes(term)) ||
                               field.fieldtype.toLowerCase().includes(term);
                    });

                    if (filteredFields.length === 0) {
                        return '<p class="text-muted text-center">No fields found matching your search.</p>';
                    }

                    return `
                        <div class="row">
                            ${filteredFields.map(field => `
                                <div class="col-md-6 col-lg-4 mb-3">
                                    <div class="card h-100 border-light shadow-sm field-card" data-fieldname="${field.fieldname}" data-fieldtype="${field.fieldtype}" data-label="${field.label}" style="cursor: pointer;">
                                        <div class="card-body p-3">
                                            <h6 class="card-title mb-2">
                                                <code class="text-primary">${field.fieldname}</code>
                                                <i class="fa fa-plus-circle text-success float-right" title="Click to add condition"></i>
                                            </h6>
                                            <p class="card-text mb-1">
                                                <strong>Label:</strong> ${field.label || 'No Label'}
                                            </p>
                                            <p class="card-text mb-1">
                                                <strong>Type:</strong>
                                                <span class="badge badge-info">${field.fieldtype}</span>
                                            </p>
                                            ${field.options ? `
                                                <p class="card-text mb-0">
                                                    <strong>Options:</strong>
                                                    <small class="text-muted">${field.options}</small>
                                                </p>
                                            ` : ''}
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        <div class="mt-3 text-center text-muted">
                            <small>Showing ${filteredFields.length} of ${fields.length} fields</small>
                        </div>
                    `;
                };

                // Initial render
                dialog.fields_dict.fields_html.$wrapper.html(buildFieldsHTML(r.message));

                // Add search functionality
                dialog.fields_dict.search_field.$input.on('input', function() {
                    const searchTerm = $(this).val();
                    dialog.fields_dict.fields_html.$wrapper.html(buildFieldsHTML(r.message, searchTerm));
                    // Re-attach click handlers after re-render
                    attachFieldClickHandlers();
                });

                // Add click functionality to field cards
                function attachFieldClickHandlers() {
                    dialog.fields_dict.fields_html.$wrapper.find('.field-card').off('click').on('click', function() {
                        const fieldname = $(this).data('fieldname');
                        const fieldtype = $(this).data('fieldtype');
                        const label = $(this).data('label');

                        // Add new row to conditions table
                        const conditions_field = frm.get_field('conditions');
                        const new_row = conditions_field.grid.add_new_row();

                        // Set field name
                        frappe.model.set_value(new_row.doctype, new_row.name, 'condition_field', fieldname);

                        // Set default operator based on field type
                        let default_operator = '=';
                        if (fieldtype === 'Check') {
                            default_operator = '=';
                        } else if (fieldtype === 'Text' || fieldtype === 'Data') {
                            default_operator = 'like';
                        } else if (fieldtype === 'Date' || fieldtype === 'Datetime') {
                            default_operator = '>=';
                        }

                        frappe.model.set_value(new_row.doctype, new_row.name, 'operator', default_operator);

                        // Refresh the grid
                        conditions_field.grid.refresh();

                        // Show success message and close dialog
                        frappe.show_alert({
                            message: `Field "${fieldname}" added to conditions`,
                            indicator: 'green'
                        });

                        dialog.hide();
                    });
                }

                // Initial click handler attachment
                attachFieldClickHandlers();

                // Add custom CSS
                dialog.$wrapper.find('.modal-dialog').addClass('modal-lg');
                dialog.$wrapper.find('.fields_html').css({
                    'max-height': '400px',
                    'overflow-y': 'auto',
                    'padding': '10px'
                });

                // Add hover effect CSS
                const hoverCSS = `
                    <style>
                        .field-card:hover {
                            transform: translateY(-2px);
                            transition: transform 0.2s ease;
                            border-color: #007bff !important;
                        }
                        .field-card .fa-plus-circle {
                            opacity: 0.7;
                            transition: opacity 0.2s ease;
                        }
                        .field-card:hover .fa-plus-circle {
                            opacity: 1;
                        }
                    </style>
                `;
                dialog.$wrapper.find('.modal-header').after(hoverCSS);

                dialog.show();
            } else {
                frappe.msgprint(__('No fields found for this DocType'));
            }
        }
    });
}