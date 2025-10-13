/**
 * Field Access Control - Realtime Cache Management
 *
 * Listens for field access configuration changes and automatically
 * refreshes forms without requiring manual page reload.
 */

(function() {
    'use strict';

    // Store field access update timestamps
    window.field_access_updates = window.field_access_updates || {};

    // Listen for field access configuration changes
    frappe.realtime.on('field_access_config_changed', (data) => {
        console.log('🔄 Field Access Config Changed:', data.doctype, data.timestamp);

        // Store update timestamp
        window.field_access_updates[data.doctype] = data.timestamp;

        // Clear ALL meta caches aggressively
        clearMetaCache(data.doctype);

        // Check if current form is the affected doctype OR has it as a child table
        let should_reload = false;
        let reload_reason = '';

        if (cur_frm && cur_frm.doctype === data.doctype) {
            should_reload = true;
            reload_reason = 'Current form doctype matches';
        } else if (cur_frm && cur_frm.meta) {
            // Check if the changed doctype is a child table in current form
            const child_tables = cur_frm.meta.fields.filter(f => f.fieldtype === 'Table');
            for (let child_field of child_tables) {
                if (child_field.options === data.doctype) {
                    should_reload = true;
                    reload_reason = `Child table ${data.doctype} config changed`;
                    break;
                }
            }
        }

        if (should_reload) {
            console.log('🔃 Reloading current form:', cur_frm.doctype, '-', reload_reason);

            // Show message to user
            frappe.show_alert({
                message: __('Field permissions updated. Reloading form...'),
                indicator: 'blue'
            }, 3);

            // Force reload with cache bypass
            setTimeout(() => {
                // Clear parent form's meta too
                if (cur_frm.meta) {
                    cur_frm.meta = null;
                }
                clearMetaCache(cur_frm.doctype);

                // Reload the document
                cur_frm.reload_doc();
            }, 500);
        }
    });

    // Function to clear all meta caches for a doctype
    function clearMetaCache(doctype) {
        // Clear from frappe.model.meta_map
        if (frappe.model && frappe.model.meta_map) {
            delete frappe.model.meta_map[doctype];
        }

        // Clear from frappe.meta.docfield_map
        if (frappe.meta && frappe.meta.docfield_map) {
            delete frappe.meta.docfield_map[doctype];
        }

        // Clear from frappe.model.docinfo
        if (frappe.model && frappe.model.docinfo) {
            delete frappe.model.docinfo[doctype];
        }

        // Clear from locals
        if (window.locals && window.locals.DocType) {
            delete window.locals.DocType[doctype];
        }

        console.log('✅ Cleared all meta caches for:', doctype);
    }

    // Override frappe.model.with_doctype to always fetch fresh meta
    // if we know it was recently updated
    const original_with_doctype = frappe.model.with_doctype;
    frappe.model.with_doctype = function(doctype, callback) {
        // Check if this doctype was recently updated
        if (window.field_access_updates && window.field_access_updates[doctype]) {
            console.log('🔄 Forcing fresh meta fetch for:', doctype, window.field_access_updates[doctype]);

            // Clear meta before fetching
            clearMetaCache(doctype);

            // Force fresh fetch (third parameter = true forces cache bypass)
            return original_with_doctype.call(this, doctype, callback, true);
        }

        return original_with_doctype.apply(this, arguments);
    };

    console.log('✅ Field Access Control - Realtime updates active');
})();
