
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
        });
    }
    
    function applyFieldConfiguration(frm, fieldConfig) {
        console.log('🔧 applyFieldConfiguration called:', fieldConfig);
        
        if (!fieldConfig.fieldname || !fieldConfig.action_type) {
            console.log('❌ Invalid field config - missing fieldname or action_type');
            return;
        }
        
        // Check if this is a child table field
        if (fieldConfig.is_child_table_field) {
            console.log('👶 Applying child table field configuration:', fieldConfig);
            applyChildTableFieldConfiguration(frm, fieldConfig);
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
    
    function applyChildTableFieldConfiguration(frm, fieldConfig) {
        console.log('👶 applyChildTableFieldConfiguration called:', fieldConfig);
        
        const parentField = fieldConfig.parent_field;
        const childFieldname = fieldConfig.child_fieldname;
        const actionType = fieldConfig.action_type;
        
        // Apply to existing child table rows
        if (frm.doc[parentField]) {
            frm.doc[parentField].forEach(function(childRow, index) {
                applyChildTableRowFieldControl(frm, parentField, index, childFieldname, actionType);
            });
        }
        
        // Listen for new child table rows
        frm.fields_dict[parentField].grid.wrapper.on('row_added', function() {
            setTimeout(function() {
                const lastIndex = frm.doc[parentField].length - 1;
                applyChildTableRowFieldControl(frm, parentField, lastIndex, childFieldname, actionType);
            }, 100);
        });
    }
    
    function applyChildTableRowFieldControl(frm, parentField, rowIndex, childFieldname, actionType) {
        console.log('👶👶 applyChildTableRowFieldControl:', parentField, rowIndex, childFieldname, actionType);
        
        try {
            const grid = frm.fields_dict[parentField].grid;
            const row = grid.grid_rows[rowIndex];
            
            if (!row) {
                console.log('❌ Row not found for index:', rowIndex);
                return;
            }
            
            const fieldWrapper = row.wrapper.find(`[data-fieldname="${childFieldname}"]`);
            
            if (fieldWrapper.length === 0) {
                console.log('❌ Child field not found:', childFieldname);
                return;
            }
            
            switch (actionType) {
                case 'Hide':
                    console.log('🙈 Hiding child table field:', childFieldname);
                    fieldWrapper.hide();
                    break;
                    
                case 'Read Only':
                    console.log('🔒 Making child table field readonly:', childFieldname);
                    const input = fieldWrapper.find('input, select, textarea');
                    if (input.length > 0) {
                        input.prop('readonly', true).addClass('read-only');
                    }
                    break;
                    
                default:
                    console.log('❌ Unknown action type for child table field:', actionType);
            }
        } catch (error) {
            console.log('❌ Error applying child table field control:', error);
        }
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
        $(document).on('form_loaded', function(e, frm) {
            console.log('📋 Form loaded event:', frm.doctype, 'docname:', frm.docname);
            if (frm && frm.doctype) {
                setTimeout(function() {
                    window.applyFieldHiding(frm.doctype, frm.docname);
                }, 100);
            }
        });
        
        $(document).on('form_refresh', function(e, frm) {
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
