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
                // Create a dialog to show fields
                const fields_html = r.message.map(field => {
                    return `
                        <tr>
                            <td><code>${field.fieldname}</code></td>
                            <td>${field.label}</td>
                            <td>${field.fieldtype}</td>
                            <td>${field.options || '-'}</td>
                        </tr>
                    `;
                }).join('');

                const message = `
                    <h5>Available Fields for ${frm.doc.target_doctype}</h5>
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>Field Name</th>
                                <th>Label</th>
                                <th>Type</th>
                                <th>Options</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${fields_html}
                        </tbody>
                    </table>
                `;

                frappe.msgprint({
                    title: __('DocType Fields'),
                    message: message,
                    wide: true
                });
            } else {
                frappe.msgprint(__('No fields found for this DocType'));
            }
        }
    });
}