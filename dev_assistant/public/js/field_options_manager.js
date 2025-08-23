// Copyright (c) 2025, Dev Assistant and contributors
// For license information, please see license.txt

// Dynamic Field Options Manager
// This file handles automatic field options population on all forms

(function() {
    'use strict';
    
    console.log('🔧 Field Options Manager System Loaded');
    
    // Function to apply dynamic options to any form
    window.applyDynamicFieldOptions = function(doctype_name, docname) {
        console.log('🎯 applyDynamicFieldOptions called for doctype:', doctype_name, 'docname:', docname);
        
        if (!doctype_name) {
            console.log('❌ No doctype name provided');
            return;
        }
        
        // Get active configurations for this doctype
        frappe.call({
            method: 'dev_assistant.dev_assistant.doctype.field_options_manager.field_options_manager.get_active_configurations',
            args: {
                doctype_name: doctype_name,
                docname: docname
            },
            callback: function(r) {
                console.log('📡 Server response:', r);
                if (!r.exc && r.message && r.message.length > 0) {
                    console.log('✅ Configurations found:', r.message.length, 'configs');
                    // Apply configurations to current form
                    applyConfigurationsToCurrentForm(r.message, doctype_name, docname);
                } else {
                    console.log('❌ No configurations found or error:', r.exc);
                }
            }
        });
    };
    
    function applyConfigurationsToCurrentForm(configurations, doctype_name, docname) {
        console.log('🔧 applyConfigurationsToCurrentForm called with:', configurations);
        
        if (!cur_frm) {
            console.log('❌ No current form found');
            return;
        }
        
        // Get current document values for condition evaluation
        var docValues = {};
        if (cur_frm.doc) {
            docValues = cur_frm.doc;
        }
        
        // Process each configuration
        configurations.forEach(function(config, index) {
            console.log('📋 Processing config ' + (index + 1) + ':', config);
            
            // Check if configuration applies to current field
            if (config.field_name && config.field_name !== 'All') {
                applyOptionsToField(config, docValues);
            } else if (config.apply_to_all_fields) {
                // Apply to all fields that can have options
                applyToAllFields(config, docValues);
            }
        });
    }
    
    function applyOptionsToField(config, docValues) {
        console.log('🔧 applyOptionsToField called for field:', config.field_name);
        
        // Check if field exists in current form
        if (!cur_frm.fields_dict[config.field_name]) {
            console.log('❌ Field not found in form:', config.field_name);
            return;
        }
        
        // Get options for this configuration
        frappe.call({
            method: 'dev_assistant.dev_assistant.doctype.field_options_manager.field_options_manager.get_field_options',
            args: {
                doctype_name: config.doctype_name,
                field_name: config.field_name,
                docname: cur_frm.docname
            },
            callback: function(r) {
                if (!r.exc && r.message && r.message.length > 0) {
                    console.log('✅ Options received for field:', config.field_name, r.message);
                    setFieldOptions(config.field_name, r.message);
                } else {
                    console.log('❌ No options received for field:', config.field_name);
                }
            }
        });
    }
    
    function applyToAllFields(config, docValues) {
        console.log('🔧 applyToAllFields called');
        
        // Get all fields that can have options
        var optionFields = ['Link', 'Select', 'MultiSelect', 'Dynamic Link'];
        
        Object.keys(cur_frm.fields_dict).forEach(function(fieldname) {
            var field = cur_frm.fields_dict[fieldname];
            if (field && field.df && optionFields.includes(field.df.fieldtype)) {
                console.log('🔧 Applying options to field:', fieldname);
                applyOptionsToField(config, docValues);
            }
        });
    }
    
    function setFieldOptions(fieldname, options) {
        console.log('🔧 setFieldOptions called for field:', fieldname, 'options:', options);
        
        var field = cur_frm.fields_dict[fieldname];
        if (!field) {
            console.log('❌ Field not found:', fieldname);
            return;
        }
        
        // Set options based on field type
        if (field.df.fieldtype === 'Select') {
            // For Select fields, update the options
            field.df.options = options.join('\n');
            field.refresh();
            console.log('✅ Select field options updated:', fieldname);
        } else if (field.df.fieldtype === 'Link') {
            // For Link fields, we need to update the options dynamically
            // This is more complex and may require custom handling
            console.log('⚠️ Link field options update not implemented yet:', fieldname);
        } else if (field.df.fieldtype === 'MultiSelect') {
            // For MultiSelect fields
            field.df.options = options.join('\n');
            field.refresh();
            console.log('✅ MultiSelect field options updated:', fieldname);
        }
    }
    
    // Chrome-specific initialization
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('📄 DOM Content Loaded - Chrome compatibility');
            setupFieldOptionsManager();
        });
    } else {
        console.log('📄 DOM already loaded - Chrome compatibility');
        setupFieldOptionsManager();
    }
    
    function setupFieldOptionsManager() {
        console.log('🔧 Setting up field options manager...');
        
        // Listen for form events
        $(document).on('form_loaded', function(e, frm) {
            console.log('📋 Form loaded event:', frm.doctype, 'docname:', frm.docname);
            if (frm && frm.doctype) {
                setTimeout(function() {
                    window.applyDynamicFieldOptions(frm.doctype, frm.docname);
                }, 100);
            }
        });
        
        $(document).on('form_refresh', function(e, frm) {
            console.log('🔄 Form refresh event:', frm.doctype, 'docname:', frm.docname);
            if (frm && frm.doctype) {
                setTimeout(function() {
                    window.applyDynamicFieldOptions(frm.doctype, frm.docname);
                }, 100);
            }
        });
        
        // Override Frappe's form setup for Chrome compatibility
        var originalSetup = frappe.ui.form.Form.prototype.setup;
        frappe.ui.form.Form.prototype.setup = function() {
            console.log('🔧 Form setup override called for: ' + this.doctype + ' docname: ' + this.docname);
            originalSetup.apply(this, arguments);
            
            // Apply field options after form setup
            setTimeout(function() {
                console.log('⏰ Applying field options after form setup delay');
                window.applyDynamicFieldOptions(this.doctype, this.docname);
            }.bind(this), 200);
        };
        
        console.log('✅ Field Options Manager System Setup Complete');
    }
    
})();

