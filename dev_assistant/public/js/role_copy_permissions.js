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
        title: __('Enhanced Copy Permissions'),
        size: 'large',
        fields: [
            {
                fieldname: 'operation_mode',
                fieldtype: 'Select',
                label: __('Operation Mode'),
                options: ['Local Site', 'Cross-Site'],
                default: 'Local Site',
                onchange: function() {
                    toggle_site_mode(dialog, frm);
                }
            },
            {
                fieldname: 'cross_site_section',
                fieldtype: 'Section Break',
                label: __('Remote Site Configuration'),
                depends_on: 'eval:doc.operation_mode=="Cross-Site"'
            },
            {
                fieldname: 'remote_site_url',
                fieldtype: 'Data',
                label: __('Remote Site URL'),
                placeholder: 'https://remote-site.domain.com',
                depends_on: 'eval:doc.operation_mode=="Cross-Site"'
            },
            {
                fieldname: 'remote_username',
                fieldtype: 'Data',
                label: __('Username'),
                depends_on: 'eval:doc.operation_mode=="Cross-Site"'
            },
            {
                fieldname: 'remote_password',
                fieldtype: 'Password',
                label: __('Password'),
                depends_on: 'eval:doc.operation_mode=="Cross-Site"'
            },
            {
                fieldname: 'authenticate_btn',
                fieldtype: 'Button',
                label: __('Authenticate & Fetch Roles'),
                depends_on: 'eval:doc.operation_mode=="Cross-Site"',
                click: function() {
                    authenticate_remote_site(dialog, frm);
                }
            },
            {
                fieldname: 'auth_status',
                fieldtype: 'HTML',
                depends_on: 'eval:doc.operation_mode=="Cross-Site"'
            },
            {
                fieldname: 'source_section',
                fieldtype: 'Section Break',
                label: __('Source Role Configuration')
            },
            {
                label: __('Source Role'),
                fieldname: 'source_role_local',
                fieldtype: 'Link',
                options: 'Role',
                reqd: 0,  // Not always required
                default: '',
                hidden: 0,
                get_query: function() {
                    return {
                        filters: {
                            'name': ['!=', frm.doc.name],
                            'disabled': 0
                        }
                    };
                }
            },
            {
                label: __('Source Role (Remote)'),
                fieldname: 'source_role_remote',
                fieldtype: 'Select',
                options: '',
                reqd: 0,  // Not always required
                default: '',
                hidden: 1
            },
            {
                fieldname: 'doctype_selection_section',
                fieldtype: 'Section Break',
                label: __('DocType Selection (Optional)')
            },
            {
                fieldname: 'copy_mode',
                fieldtype: 'Select',
                label: __('Copy Mode'),
                options: ['All DocTypes', 'Selected DocTypes Only'],
                default: 'All DocTypes',
                onchange: function() {
                    toggle_doctype_selection(dialog);
                }
            },
            {
                fieldname: 'select_doctypes_btn',
                fieldtype: 'Button',
                label: __('Select DocTypes'),
                depends_on: 'eval:doc.copy_mode=="Selected DocTypes Only"',
                click: function() {
                    show_doctype_selector(dialog);
                }
            },
            {
                fieldname: 'selected_doctypes_display',
                fieldtype: 'HTML',
                depends_on: 'eval:doc.copy_mode=="Selected DocTypes Only"'
            },
            {
                fieldname: 'options_section',
                fieldtype: 'Section Break',
                label: __('Copy Options')
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
            execute_permission_copy(frm, dialog, values);
        }
    });

    // Initialize dialog state
    dialog.selected_doctypes = [];
    dialog.authenticated_site_data = null;

    dialog.show();
}

function copy_permissions(frm, values) {
    frappe.call({
        method: 'dev_assistant.api.copy_roles_functionality.copy_role_permissions',
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

// NEW ENHANCED FUNCTIONS

function toggle_site_mode(dialog, frm) {
    let mode = dialog.get_value('operation_mode');

    if (mode === 'Cross-Site') {
        dialog.fields_dict.auth_status.$wrapper.html('');
        dialog.authenticated_site_data = null;

        // Hide local field, show remote field
        dialog.fields_dict.source_role_local.df.hidden = 1;
        dialog.fields_dict.source_role_local.$wrapper.hide();
        dialog.fields_dict.source_role_local.set_value('');

        dialog.fields_dict.source_role_remote.df.hidden = 0;
        dialog.fields_dict.source_role_remote.$wrapper.show();
        dialog.fields_dict.source_role_remote.df.options = '';
        dialog.fields_dict.source_role_remote.set_value('');
        dialog.fields_dict.source_role_remote.refresh();
    } else {
        // Local Site mode - show local field, hide remote field
        dialog.fields_dict.source_role_local.df.hidden = 0;
        dialog.fields_dict.source_role_local.$wrapper.show();
        dialog.fields_dict.source_role_local.set_value('');
        dialog.fields_dict.source_role_local.refresh();

        dialog.fields_dict.source_role_remote.df.hidden = 1;
        dialog.fields_dict.source_role_remote.$wrapper.hide();
        dialog.fields_dict.source_role_remote.set_value('');
    }

    dialog.refresh();
}


function authenticate_remote_site(dialog, frm) {
    let site_url = dialog.get_value('remote_site_url');
    let username = dialog.get_value('remote_username');
    let password = dialog.get_value('remote_password');

    if (!site_url || !username || !password) {
        frappe.msgprint(__('Please fill all remote site credentials'));
        return;
    }

    dialog.fields_dict.auth_status.$wrapper.html(
        '<div class="alert alert-info">🔄 Authenticating with remote site...</div>'
    );

    frappe.call({
        method: 'dev_assistant.api.copy_roles_functionality.authenticate_remote_site',
        args: {
            site_url: site_url,
            username: username,
            password: password
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                dialog.authenticated_site_data = r.message;
                dialog.fields_dict.auth_status.$wrapper.html(
                    `<div class="alert alert-success">✅ Authenticated as: ${r.message.user}</div>`
                );

                // Fetch remote roles
                fetch_remote_roles(dialog);
            } else {
                dialog.fields_dict.auth_status.$wrapper.html(
                    `<div class="alert alert-danger">❌ Authentication failed: ${r.message.error}</div>`
                );
            }
        },
        error: function(r) {
            dialog.fields_dict.auth_status.$wrapper.html(
                '<div class="alert alert-danger">❌ Error connecting to remote site</div>'
            );
        }
    });
}

function fetch_remote_roles(dialog) {
    if (!dialog.authenticated_site_data) return;

    frappe.call({
        method: 'dev_assistant.api.copy_roles_functionality.get_remote_roles',
        args: {
            site_url: dialog.authenticated_site_data.site_url,
            session_cookies: dialog.authenticated_site_data.session_cookies
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                console.log('🌐 Fetched remote roles:', r.message.roles.length, 'roles');

                // Update remote source role field with roles
                let remote_role_field = dialog.fields_dict.source_role_remote;
                remote_role_field.df.options = r.message.roles.join('\n');
                remote_role_field.set_value('');
                remote_role_field.refresh();

                frappe.show_alert({
                    message: __(`${r.message.roles.length} remote roles fetched successfully!`),
                    indicator: 'green'
                });
            } else {
                frappe.show_alert({
                    message: __('Failed to fetch remote roles: ') + (r.message.error || 'Unknown error'),
                    indicator: 'red'
                });
            }
        },
        error: function(r) {
            frappe.show_alert({
                message: __('Error fetching remote roles'),
                indicator: 'red'
            });
        }
    });
}

function toggle_doctype_selection(dialog) {
    let copy_mode = dialog.get_value('copy_mode');

    if (copy_mode === 'Selected DocTypes Only') {
        update_selected_doctypes_display(dialog);
    } else {
        dialog.selected_doctypes = [];
    }

    dialog.refresh();
}

function show_doctype_selector(dialog) {
    // First get the doctype list
    frappe.call({
        method: 'dev_assistant.api.copy_roles_functionality.get_doctype_list',
        callback: function(r) {
            if (r.message && r.message.success) {
                show_doctype_selection_dialog(dialog, r.message.doctypes);
            }
        }
    });
}

function show_doctype_selection_dialog(parent_dialog, doctypes) {
    let selector_dialog = new frappe.ui.Dialog({
        title: __('Select DocTypes'),
        size: 'large',
        fields: [
            {
                fieldname: 'search',
                fieldtype: 'Data',
                label: __('Search DocTypes'),
                placeholder: __('Type to search...'),
                onchange: function() {
                    filter_doctypes(selector_dialog, doctypes);
                }
            },
            {
                fieldname: 'category_filter',
                fieldtype: 'Select',
                label: __('Category'),
                options: ['All', 'Core DocTypes', 'Custom DocTypes'],
                default: 'All',
                onchange: function() {
                    filter_doctypes(selector_dialog, doctypes);
                }
            },
            {
                fieldname: 'preset_buttons',
                fieldtype: 'HTML',
                options: `
                    <div class="row">
                        <div class="col-md-12">
                            <button class="btn btn-sm btn-default" onclick="select_preset('core')">Select Core Only</button>
                            <button class="btn btn-sm btn-default" onclick="select_preset('custom')">Select Custom Only</button>
                            <button class="btn btn-sm btn-default" onclick="select_preset('hr')">HR Module</button>
                            <button class="btn btn-sm btn-default" onclick="select_preset('accounting')">Accounting</button>
                            <button class="btn btn-sm btn-default" onclick="clear_all_selection()">Clear All</button>
                        </div>
                    </div>
                `
            },
            {
                fieldname: 'doctype_list',
                fieldtype: 'HTML'
            },
            {
                fieldname: 'selected_count',
                fieldtype: 'HTML'
            }
        ],
        primary_action_label: __('Apply Selection'),
        primary_action: function(values) {
            parent_dialog.selected_doctypes = get_selected_doctypes_from_checkboxes();
            update_selected_doctypes_display(parent_dialog);
            selector_dialog.hide();
        }
    });

    // Store reference for preset functions
    window.current_selector_dialog = selector_dialog;
    window.current_doctypes = doctypes;

    selector_dialog.show();
    render_doctype_checkboxes(selector_dialog, doctypes);
}

function render_doctype_checkboxes(dialog, doctypes) {
    let html = '<div class="doctype-selector-grid">';

    // Core DocTypes
    if (doctypes.core && doctypes.core.length > 0) {
        html += '<h5>🔹 Core DocTypes</h5>';
        html += '<div class="checkbox-group">';
        doctypes.core.forEach(dt => {
            html += `
                <label class="checkbox-label" data-category="core" data-module="${dt.module}">
                    <input type="checkbox" value="${dt.name}" class="doctype-checkbox"> ${dt.name}
                    <small class="text-muted"> (${dt.module})</small>
                </label>
            `;
        });
        html += '</div><br>';
    }

    // Custom DocTypes
    if (doctypes.custom && doctypes.custom.length > 0) {
        html += '<h5>⭐ Custom DocTypes</h5>';
        html += '<div class="checkbox-group">';
        doctypes.custom.forEach(dt => {
            html += `
                <label class="checkbox-label" data-category="custom" data-module="${dt.module}">
                    <input type="checkbox" value="${dt.name}" class="doctype-checkbox"> ${dt.name}
                    <small class="text-muted"> (${dt.module})</small>
                </label>
            `;
        });
        html += '</div>';
    }

    html += '</div>';

    html += `
        <style>
            .doctype-selector-grid {
                max-height: 400px;
                overflow-y: auto;
                border: 1px solid #ddd;
                padding: 15px;
                border-radius: 4px;
            }
            .checkbox-group {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 8px;
                margin-bottom: 15px;
            }
            .checkbox-label {
                display: flex;
                align-items: center;
                padding: 5px;
                margin: 0;
                cursor: pointer;
            }
            .checkbox-label:hover {
                background-color: #f8f9fa;
                border-radius: 3px;
            }
            .doctype-checkbox {
                margin-right: 8px;
            }
        </style>
    `;

    dialog.fields_dict.doctype_list.$wrapper.html(html);

    // Add event listeners
    dialog.$wrapper.find('.doctype-checkbox').on('change', function() {
        update_selection_count(dialog);
    });

    update_selection_count(dialog);
}

function filter_doctypes(dialog, doctypes) {
    let search = dialog.get_value('search') || '';
    let category = dialog.get_value('category_filter') || 'All';

    dialog.$wrapper.find('.checkbox-label').each(function() {
        let label = $(this);
        let doctype_name = label.find('.doctype-checkbox').val().toLowerCase();
        let label_category = label.data('category');

        let show = true;

        // Filter by search
        if (search && !doctype_name.includes(search.toLowerCase())) {
            show = false;
        }

        // Filter by category
        if (category !== 'All') {
            if (category === 'Core DocTypes' && label_category !== 'core') {
                show = false;
            } else if (category === 'Custom DocTypes' && label_category !== 'custom') {
                show = false;
            }
        }

        if (show) {
            label.show();
        } else {
            label.hide();
        }
    });
}

function update_selection_count(dialog) {
    let selected = dialog.$wrapper.find('.doctype-checkbox:checked').length;
    dialog.fields_dict.selected_count.$wrapper.html(
        `<div class="alert alert-info">📊 Selected: ${selected} DocTypes</div>`
    );
}

function get_selected_doctypes_from_checkboxes() {
    let selected = [];
    window.current_selector_dialog.$wrapper.find('.doctype-checkbox:checked').each(function() {
        selected.push($(this).val());
    });
    return selected;
}

function update_selected_doctypes_display(dialog) {
    let count = dialog.selected_doctypes.length;
    let html = '';

    if (count > 0) {
        html = `
            <div class="alert alert-success">
                ✅ ${count} DocTypes selected
                <br><small>${dialog.selected_doctypes.slice(0, 5).join(', ')}
                ${count > 5 ? ' and ' + (count - 5) + ' more...' : ''}</small>
            </div>
        `;
    } else {
        html = '<div class="alert alert-warning">⚠️ No DocTypes selected</div>';
    }

    dialog.fields_dict.selected_doctypes_display.$wrapper.html(html);
}

// Global preset functions
window.select_preset = function(type) {
    let doctypes = window.current_doctypes;
    let checkboxes = window.current_selector_dialog.$wrapper.find('.doctype-checkbox');

    // Clear all first
    checkboxes.prop('checked', false);

    if (type === 'core') {
        window.current_selector_dialog.$wrapper.find('[data-category="core"] .doctype-checkbox').prop('checked', true);
    } else if (type === 'custom') {
        window.current_selector_dialog.$wrapper.find('[data-category="custom"] .doctype-checkbox').prop('checked', true);
    } else if (type === 'hr') {
        window.current_selector_dialog.$wrapper.find('[data-module="HR"] .doctype-checkbox').prop('checked', true);
    } else if (type === 'accounting') {
        window.current_selector_dialog.$wrapper.find('[data-module="Accounting"] .doctype-checkbox, [data-module="Accounts"] .doctype-checkbox').prop('checked', true);
    }

    update_selection_count(window.current_selector_dialog);
};

window.clear_all_selection = function() {
    window.current_selector_dialog.$wrapper.find('.doctype-checkbox').prop('checked', false);
    update_selection_count(window.current_selector_dialog);
};

function execute_permission_copy(frm, dialog, values) {
    let operation_mode = values.operation_mode;
    let copy_mode = values.copy_mode;

    // Get the correct source role based on operation mode
    let source_role = '';
    if (operation_mode === 'Local Site') {
        source_role = values.source_role_local;
    } else {
        source_role = values.source_role_remote;
    }

    if (!source_role) {
        frappe.msgprint(__('Please select a source role'));
        return;
    }

    // Add source role to values for compatibility with existing functions
    values.source_role = source_role;

    if (copy_mode === 'All DocTypes') {
        // Use original method for all DocTypes
        if (operation_mode === 'Local Site') {
            copy_permissions(frm, values);
        } else {
            copy_cross_site_permissions(frm, dialog, values);
        }
    } else {
        // Use selective copy method
        if (dialog.selected_doctypes.length === 0) {
            frappe.msgprint(__('Please select at least one DocType'));
            return;
        }
        copy_selective_permissions(frm, dialog, values);
    }

    dialog.hide();
}

function copy_cross_site_permissions(frm, dialog, values) {
    if (!dialog.authenticated_site_data) {
        frappe.msgprint(__('Please authenticate with remote site first'));
        return;
    }

    // Use selective permissions method for cross-site with all DocTypes
    frappe.call({
        method: 'dev_assistant.api.copy_roles_functionality.copy_selective_permissions',
        args: {
            source_role: values.source_role,
            target_role: frm.doc.name,
            selected_doctypes: JSON.stringify([]), // Empty array means all DocTypes
            overwrite_existing: values.overwrite,
            source_site_url: dialog.authenticated_site_data.site_url,
            session_cookies: JSON.stringify(dialog.authenticated_site_data.session_cookies)
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __('Cross-site permissions copied successfully!'),
                    indicator: 'green'
                });

                // Show detailed results
                frappe.msgprint({
                    title: __('Cross-Site Copy Results'),
                    message: `
                        <div>
                            <p><strong>📊 Summary:</strong></p>
                            <ul>
                                <li>✅ Copied: ${r.message.copied_count} permissions</li>
                                <li>⏭️ Skipped: ${r.message.skipped_count} existing permissions</li>
                                <li>🌐 Source: Remote site</li>
                            </ul>
                        </div>
                    `,
                    indicator: 'green'
                });

                frm.reload_doc();
            } else {
                frappe.msgprint(__('Error copying cross-site permissions: ') + (r.message && r.message.error ? r.message.error : 'Unknown error'));
            }
        },
        error: function(r) {
            frappe.msgprint(__('Error copying cross-site permissions: ') + (r.message || 'Unknown error'));
        }
    });
}

function copy_selective_permissions(frm, dialog, values) {
    let site_data = null;
    let session_cookies = null;

    if (values.operation_mode === 'Cross-Site') {
        if (!dialog.authenticated_site_data) {
            frappe.msgprint(__('Please authenticate with remote site first'));
            return;
        }
        site_data = dialog.authenticated_site_data.site_url;
        session_cookies = JSON.stringify(dialog.authenticated_site_data.session_cookies);
    }

    // Show progress
    frappe.show_alert({
        message: __('Copying permissions for selected DocTypes...'),
        indicator: 'blue'
    });

    frappe.call({
        method: 'dev_assistant.api.copy_roles_functionality.copy_selective_permissions',
        args: {
            source_role: values.source_role,
            target_role: frm.doc.name,
            selected_doctypes: JSON.stringify(dialog.selected_doctypes),
            overwrite_existing: values.overwrite,
            source_site_url: site_data,
            session_cookies: session_cookies
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: r.message.message || __('Selective permissions copied successfully!'),
                    indicator: 'green'
                });

                // Show detailed results
                frappe.msgprint({
                    title: __('Copy Results'),
                    message: `
                        <div>
                            <p><strong>📊 Summary:</strong></p>
                            <ul>
                                <li>✅ Copied: ${r.message.copied_count} permissions</li>
                                <li>⏭️ Skipped: ${r.message.skipped_count} existing permissions</li>
                                <li>📁 DocTypes: ${dialog.selected_doctypes.length} selected</li>
                            </ul>
                        </div>
                    `,
                    indicator: 'green'
                });

                frm.reload_doc();
            }
        },
        error: function(r) {
            frappe.msgprint(__('Error copying selective permissions: ') + (r.message || 'Unknown error'));
        }
    });
}
