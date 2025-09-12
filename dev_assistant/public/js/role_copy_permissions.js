frappe.ui.form.on('Role', {
    refresh: function(frm) {
        // Only show button for custom roles and not for standard roles
        if (!frm.doc.disabled) {
            frm.add_custom_button(__('Copy Permissions'), function() {
                show_copy_permissions_dialog(frm);
            }).addClass('btn-primary');
        }
    }
});

function show_copy_permissions_dialog(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Copy Permissions'),
        fields: [
            {
                label: __('Source Role'),
                fieldname: 'source_role',
                fieldtype: 'Link',
                options: 'Role',
                reqd: 1,
                get_query: function() {
                    return {
                        filters: {
                            'name': ['!=', frm.doc.name], // Exclude current role
                            'disabled': 0
                        }
                    };
                }
            },
            {
                label: __('Overwrite Existing Permissions'),
                fieldname: 'overwrite',
                fieldtype: 'Check',
                default: 0,
                description: __('If checked, existing permissions will be overwritten')
            }
        ],
        primary_action_label: __('Copy Permissions'),
        primary_action: function(values) {
            copy_permissions(frm, values);
            dialog.hide();
        }
    });
    
    dialog.show();
}

function copy_permissions(frm, values) {
    frappe.call({
        method: 'dev_assistant.dev_assistant.utils.copy_role_permissions',
        args: {
            source_role: values.source_role,
            target_role: frm.doc.name,
            overwrite_existing: values.overwrite
        },
        callback: function(r) {
            if (r.message) {
                frappe.show_alert({
                    message: __('Permissions copied successfully!'),
                    indicator: 'green'
                });
                // Refresh the form to show updated permissions
                frm.reload_doc();
            }
        },
        error: function(r) {
            frappe.msgprint(__('Error copying permissions: ') + r.message);
        }
    });
}
