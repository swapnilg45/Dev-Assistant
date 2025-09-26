/**
 * Simple Button Control Script
 * Hide/Show existing buttons based on Button Configuration
 */

// Chrome compatibility fix - ensure script loads
(function() {
    'use strict';

    console.log('🔥🔥🔥 BUTTON CONTROL SCRIPT LOADED 🔥🔥🔥');
    console.log('🌐 Browser detected:', navigator.userAgent);

    // Main function to control buttons
    window.control_buttons = function(frm) {
        console.log(`🎯 Button Control: Starting for ${frm.doc.doctype} - ${frm.doc.name}`);

        frappe.call({
            method: 'dev_assistant.dev_assistant.doctype.button_configuration.button_configuration.get_button_configurations',
            args: { doctype: frm.doc.doctype },
            callback: function(r) {
                console.log(`📡 API Response:`, r.message);

                if (r.message && r.message.configurations) {
                    let buttons_to_remove = [];
                    let processed = 0;
                    let total = r.message.configurations.length;

                    console.log(`🔍 Found ${total} button configurations to check`);

                    r.message.configurations.forEach(function(config) {
                        const timeout = config.timeout_ms || 500;
                        console.log(`⏰ Processing button "${config.button_label}" with ${timeout}ms timeout`);

                        setTimeout(() => {
                            // Check visibility
                            frappe.call({
                                method: 'dev_assistant.dev_assistant.doctype.button_configuration.button_configuration.evaluate_button_visibility',
                                args: {
                                    button_name: config.name,
                                    doc_data: JSON.stringify(frm.doc)
                                },
                                callback: function(result) {
                                    processed++;
                                    console.log(`✅ Evaluated "${config.button_label}": visible=${result.message?.visible}, reason=${result.message?.reason}`);

                                    if (result.message && !result.message.visible) {
                                        buttons_to_remove.push({
                                            label: config.button_label,
                                            group: config.button_group,
                                            type: config.button_type
                                        });
                                        console.log(`➕ Added to remove list: "${config.button_label}"`);
                                    }

                                    // When all processed, remove buttons
                                    if (processed === total) {
                                        console.log(`🏁 All ${total} buttons evaluated. Processing removal...`);
                                        remove_buttons(frm, buttons_to_remove);
                                    }
                                }
                            });
                        }, timeout);
                    });
                } else {
                    console.log(`❌ No configurations found for ${frm.doc.doctype}`);
                }
            }
        });
    };

    // Remove all buttons in one go
    window.remove_buttons = function(frm, buttons_to_remove) {
        console.log(`Button Control: Removing ${buttons_to_remove.length} buttons from ${frm.doc.doctype}`);

        buttons_to_remove.forEach(function(btn) {
            console.log(`- Removing button "${btn.label}" ${btn.type === "Grouped" ? `from group "${btn.group}"` : ""}`);

            if (btn.type === "Normal") {
                frm.remove_custom_button(btn.label);
            } else {
                frm.remove_custom_button(btn.label, btn.group);
            }
        });
    };

    // Store configured doctypes
    let configured_doctypes = [];

    // Chrome-specific initialization
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('📄 DOM Content Loaded - Chrome compatibility');
            setupButtonControl();
        });
    } else {
        console.log('📄 DOM already loaded - Chrome compatibility');
        setupButtonControl();
    }

    function setupButtonControl() {
        console.log(`🚀 Button Control System: Initializing...`);

        frappe.call({
            method: 'dev_assistant.dev_assistant.doctype.button_configuration.button_configuration.get_configured_doctypes',
            callback: function(r) {
                if (r.message) {
                    console.log(`📝 Configured DocTypes loaded:`, r.message);
                    configured_doctypes = r.message;

                    // Register handler for each configured doctype
                    r.message.forEach(function(doctype) {
                        console.log(`🔗 Registering handler for: ${doctype}`);

                        frappe.ui.form.on(doctype, {
                            refresh: function(frm) {
                                console.log(`📋 Form refresh: ${frm.doc.doctype} - ${frm.doc.name || 'New'}`);
                                console.log(`✅ Starting button control for configured DocType: ${frm.doc.doctype}`);
                                setTimeout(function() {
                                    window.control_buttons(frm);
                                }, 100);
                            }
                        });
                    });

                    console.log('✅ Button Control System Setup Complete');
                } else {
                    console.log(`⚠️ No configured DocTypes found`);
                }
            }
        });
    }

})();