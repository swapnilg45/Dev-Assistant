
// Copyright (c) 2025, Hybrowlabs and contributors
// For license information, please see license.txt

// Simple role-based field control using Frappe's existing methods
// This file handles automatic field hiding/readonly on all forms

// Chrome compatibility fix - ensure script loads
(function() {
    'use strict';
    
    console.log('🔧 Field Access Control System Loaded');
    console.log('🌐 Browser detected:', navigator.userAgent);
    
    // Function to apply field hiding to any form using Frappe's existing methods
    window.applyFieldHiding = function(doctype_name, docname) {
        console.log('🎯 applyFieldHiding called for doctype:', doctype_name, 'docname:', docname);
        
        if (!doctype_name) {
            console.log('❌ No doctype name provided');
            return;
        }
        
        // Get active configurations for this doctype and docname
        frappe.call({
            method: 'dev_assistant.dev_assistant.doctype.field_access_control.field_access_control.get_active_configurations',
            args: {
                doctype_name: doctype_name,
                docname: docname
            },
            callback: function(r) {
                console.log('📡 Server response:', r);
                if (!r.exc && r.message && r.message.length > 0) {
                    console.log('✅ Configurations found:', r.message.length, 'configs');
                    // Apply configurations to current form
                    applyConfigurationsToCurrentForm(r.message);
                } else {
                    console.log('❌ No configurations found or error:', r.exc);
                }
            }
        });
    };
    
    function applyConfigurationsToCurrentForm(configurations) {
        console.log('🔧 applyConfigurationsToCurrentForm called with:', configurations);
        
        if (!cur_frm) {
            console.log('❌ No current form found');
            return;
        }
        
        // Get user's roles
        var userRoles = frappe.user_roles || [];
        console.log('👤 User roles:', userRoles);

        // Process each configuration
        configurations.forEach(function(config, index) {
            console.log('📋 Processing config ' + (index + 1) + ':', config);

            // Check if configuration applies to user's role
            if (config.role && userRoles.indexOf(config.role) === -1 && !config.apply_to_all_roles) {
                console.log('❌ Config skipped - user doesn\'t have role: ' + config.role);
                return;
            }

            console.log('✅ Config applies to user - role: ' + config.role + ', apply_to_all_roles: ' + config.apply_to_all_roles);

            // Apply field configurations
            if (config.field_configurations) {
                console.log('🔧 Applying ' + config.field_configurations.length + ' field configurations');
                config.field_configurations.forEach(function(fieldConfig, fieldIndex) {
                    console.log('📝 Field config ' + (fieldIndex + 1) + ':', fieldConfig);
                    applyFieldConfiguration(cur_frm, fieldConfig);
                });
            } else {
                console.log('❌ No field configurations found in this config');
            }

            // Apply child table button configurations
            if (config.child_table_configurations) {
                console.log('🔧 Applying ' + config.child_table_configurations.length + ' child table configurations');
                config.child_table_configurations.forEach(function(tableConfig, tableIndex) {
                    console.log('📝 Table config ' + (tableIndex + 1) + ':', tableConfig);
                    applyChildTableConfiguration(cur_frm, tableConfig);
                });
            } else {
                console.log('❌ No child table configurations found in this config');
            }
        });
    }
    
    function applyFieldConfiguration(frm, fieldConfig) {
        console.log('🔧 applyFieldConfiguration called:', fieldConfig);
        
        if (!fieldConfig.fieldname || !fieldConfig.action_type) {
            console.log('❌ Invalid field config - missing fieldname or action_type');
            return;
        }
        
        // Use Frappe's existing methods for field control
        switch (fieldConfig.action_type) {
            case 'Hide':
                console.log('🙈 Hiding field: ' + fieldConfig.fieldname);
                // Use Frappe's hide_field function
                if (typeof hide_field === 'function') {
                    hide_field(fieldConfig.fieldname);
                    console.log('✅ hide_field() called for: ' + fieldConfig.fieldname);
                } else {
                    // Fallback to set_df_property
                    console.log('🔄 Using set_df_property fallback for: ' + fieldConfig.fieldname);
                    frm.set_df_property(fieldConfig.fieldname, 'hidden', 1);
                }
                break;
                
            case 'Read Only':
                console.log('🔒 Making field readonly: ' + fieldConfig.fieldname);
                // Use Frappe's set_df_property for read-only
                frm.set_df_property(fieldConfig.fieldname, 'read_only', 1);
                break;
                
            default:
                console.log('❌ Unknown action type: ' + fieldConfig.action_type);
        }
    }

    // Function to apply child table configuration dynamically
    function applyChildTableConfiguration(frm, tableConfig) {
        console.log('🔧 applyChildTableConfiguration called:', tableConfig);

        if (!tableConfig.table_fieldname || !tableConfig.is_active) {
            console.log('❌ Table config inactive or missing table_fieldname:', tableConfig);
            return;
        }

        setTimeout(function() {
            var grid_field = frm.get_field(tableConfig.table_fieldname);
            if (grid_field && grid_field.grid) {
                console.log('📋 Processing table: ' + tableConfig.table_fieldname +
                           ', hide_add: ' + tableConfig.hide_add_button +
                           ', hide_delete: ' + tableConfig.hide_delete_button +
                           ', is_active: ' + tableConfig.is_active);

                // Handle add button hiding - only if explicitly enabled
                if (tableConfig.hide_add_button === 1) {
                    console.log('🙈 Hiding add buttons for table: ' + tableConfig.table_fieldname);

                    // Hide specific add-related buttons only
                    grid_field.grid.wrapper.find('.grid-add-row').hide();
                    grid_field.grid.wrapper.find('button:contains("Add Row")').hide();
                    grid_field.grid.wrapper.find('button:contains("Add Multiple")').hide();
                    grid_field.grid.wrapper.find('[data-action="add"]').hide();
                    grid_field.grid.wrapper.find('[data-action="add_multiple"]').hide();

                    // Set Frappe property to disable add functionality
                    frm.set_df_property(tableConfig.table_fieldname, 'cannot_add_rows', 1);
                    grid_field.grid.cannot_add_rows = true;
                    grid_field.grid.df.cannot_add_rows = true;
                } else {
                    console.log('✅ Add buttons allowed for table: ' + tableConfig.table_fieldname);
                    // Ensure add functionality is enabled
                    frm.set_df_property(tableConfig.table_fieldname, 'cannot_add_rows', 0);
                    grid_field.grid.cannot_add_rows = false;
                    grid_field.grid.df.cannot_add_rows = false;
                }

                // Handle delete button hiding - only if explicitly enabled
                if (tableConfig.hide_delete_button === 1) {
                    console.log('🙈 Hiding delete buttons for table: ' + tableConfig.table_fieldname);

                    // Hide specific delete-related buttons only
                    grid_field.grid.wrapper.find('.grid-delete-row').hide();
                    grid_field.grid.wrapper.find('.grid-remove-rows').hide();
                    grid_field.grid.wrapper.find('button:contains("Delete")').hide();
                    grid_field.grid.wrapper.find('button:contains("Delete All")').hide();
                    grid_field.grid.wrapper.find('[data-action="delete"]').hide();
                    grid_field.grid.wrapper.find('[data-action="delete_all"]').hide();

                    // Set Frappe property to disable delete functionality
                    frm.set_df_property(tableConfig.table_fieldname, 'cannot_delete_rows', 1);
                    grid_field.grid.cannot_delete_rows = true;
                    grid_field.grid.df.cannot_delete_rows = true;
                } else {
                    console.log('✅ Delete buttons allowed for table: ' + tableConfig.table_fieldname);
                    // Ensure delete functionality is enabled
                    frm.set_df_property(tableConfig.table_fieldname, 'cannot_delete_rows', 0);
                    grid_field.grid.cannot_delete_rows = false;
                    grid_field.grid.df.cannot_delete_rows = false;
                }

                // Refresh the field to apply changes
                frm.refresh_field(tableConfig.table_fieldname);

                console.log('✅ Child table configuration applied successfully for: ' + tableConfig.table_fieldname);
            } else {
                console.log('❌ Grid field not found for: ' + tableConfig.table_fieldname);
            }
        }, 100);
    }
    
    // Chrome-specific initialization
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('📄 DOM Content Loaded - Chrome compatibility');
            setupFieldAccessControl();
        });
    } else {
        console.log('📄 DOM already loaded - Chrome compatibility');
        setupFieldAccessControl();
    }
    
    function setupFieldAccessControl() {
        console.log('🔧 Setting up field access control...');
        
        // Listen for form events
        $(document).on('form_loaded', function(_event, frm) {
            console.log('📋 Form loaded event:', frm.doctype, 'docname:', frm.docname);
            if (frm && frm.doctype) {
                setTimeout(function() {
                    window.applyFieldHiding(frm.doctype, frm.docname);
                }, 100);
            }
        });

        $(document).on('form_refresh', function(_event, frm) {
            console.log('🔄 Form refresh event:', frm.doctype, 'docname:', frm.docname);
            if (frm && frm.doctype) {
                setTimeout(function() {
                    window.applyFieldHiding(frm.doctype, frm.docname);
                }, 100);
            }
        });
        
        // Override Frappe's form setup for Chrome compatibility
        var originalSetup = frappe.ui.form.Form.prototype.setup;
        frappe.ui.form.Form.prototype.setup = function() {
            console.log('🔧 Form setup override called for: ' + this.doctype + ' docname: ' + this.docname);
            originalSetup.apply(this, arguments);
            
            // Apply field hiding after form setup
            setTimeout(function() {
                console.log('⏰ Applying field hiding after form setup delay');
                window.applyFieldHiding(this.doctype, this.docname);
            }.bind(this), 200);
        };
        
        console.log('✅ Field Access Control System Setup Complete');
    }
    
})();
