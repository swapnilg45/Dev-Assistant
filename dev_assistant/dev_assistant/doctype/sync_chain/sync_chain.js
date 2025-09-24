// Copyright (c) 2025, Swapnil and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sync Chain', {
	refresh: function(frm) {
		// Add custom buttons
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__('Test Sync'), function() {
				test_sync_chain(frm);
			});

			frm.add_custom_button(__('View Activity Log'), function() {
				frappe.route_options = {"sync_chain": frm.doc.name};
				frappe.set_route("List", "Sync Activity Log");
			});

			frm.add_custom_button(__('Clone Chain'), function() {
				clone_sync_chain(frm);
			});

			frm.add_custom_button(__('Setup Wizard'), function() {
				open_setup_wizard(frm);
			});
		}

		// Add template creation button
		frm.add_custom_button(__('Create from Template'), function() {
			show_template_dialog(frm);
		});

		// Show sync statistics
		if (!frm.doc.__islocal) {
			show_sync_statistics(frm);
		}
	},

	template_used: function(frm) {
		if (frm.doc.template_used) {
			frm.set_df_property('template_used', 'description',
				`This chain was created from the ${frm.doc.template_used} template`);
		}
	},

	chain_name: function(frm) {
		// Auto-generate description hint based on name
		if (!frm.doc.description && frm.doc.chain_name) {
			const name_lower = frm.doc.chain_name.toLowerCase();
			if (name_lower.includes('lead') && name_lower.includes('sales')) {
				frm.set_value('description', 'Automatically sync lead data through sales process');
			} else if (name_lower.includes('hr') || name_lower.includes('hiring')) {
				frm.set_value('description', 'Automatically sync applicant data through hiring process');
			} else if (name_lower.includes('project')) {
				frm.set_value('description', 'Automatically sync project-related data across modules');
			}
		}
	},

	is_active: function(frm) {
		if (frm.doc.is_active === 0) {
			frappe.msgprint(__('Sync chain is now inactive. No automatic syncing will occur.'));
		}
	}
});

frappe.ui.form.on('Sync Chain Step', {
	doctype_name: function(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.doctype_name) {
			// Auto-update doctype label
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'DocType',
					name: row.doctype_name
				},
				callback: function(r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, 'doctype_label',
							r.message.description || r.message.name);
						frm.refresh_field('chain_steps');
					}
				}
			});

			// Show field mapping button
			show_field_mapping_button(frm, row);
		}
	},

	step_number: function(frm, cdt, cdn) {
		// Auto-sort steps by step number
		setTimeout(() => {
			frm.doc.chain_steps.sort((a, b) => a.step_number - b.step_number);
			frm.refresh_field('chain_steps');
		}, 100);
	}
});

function test_sync_chain(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __('Test Sync Chain'),
		fields: [
			{
				fieldtype: 'Select',
				fieldname: 'test_doctype',
				label: __('Document Type to Test'),
				options: frm.doc.chain_steps.map(step => step.doctype_name).join('\n'),
				reqd: 1
			},
			{
				fieldtype: 'Dynamic Link',
				fieldname: 'test_document',
				label: __('Test Document'),
				options: 'test_doctype',
				reqd: 1
			}
		],
		primary_action: function() {
			const values = dialog.get_values();
			if (values) {
				frappe.call({
					method: 'test_sync_chain',
					doc: frm.doc,
					args: {
						test_doctype: values.test_doctype,
						test_docname: values.test_document
					},
					callback: function(r) {
						dialog.hide();
						if (r.message) {
							if (r.message.success) {
								frappe.msgprint({
									title: __('Test Successful'),
									message: r.message.message,
									indicator: 'green'
								});
							} else {
								frappe.msgprint({
									title: __('Test Failed'),
									message: r.message.message,
									indicator: 'red'
								});
							}
						}
					}
				});
			}
		},
		primary_action_label: __('Run Test')
	});
	dialog.show();
}

function clone_sync_chain(frm) {
	frappe.prompt([
		{
			fieldtype: 'Data',
			fieldname: 'new_name',
			label: __('New Chain Name'),
			reqd: 1
		}
	], function(values) {
		frappe.call({
			method: 'clone_chain',
			doc: frm.doc,
			args: {
				new_name: values.new_name
			},
			callback: function(r) {
				if (r.message && r.message.success) {
					frappe.msgprint({
						title: __('Chain Cloned'),
						message: r.message.message,
						indicator: 'green'
					});
					// Navigate to new chain
					frappe.set_route('Form', 'Sync Chain', r.message.new_chain);
				}
			}
		});
	}, __('Clone Sync Chain'));
}

function show_template_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __('Create from Template'),
		size: 'large',
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'template_selector'
			}
		]
	});

	// Load templates
	frappe.call({
		method: 'dev_assistant.dev_assistant.universal_sync.sync_templates.get_all_templates',
		callback: function(r) {
			if (r.message) {
				render_template_selector(dialog, r.message, frm);
			}
		}
	});

	dialog.show();
}

function render_template_selector(dialog, templates, frm) {
	let template_html = '<div class="template-grid row">';

	Object.keys(templates).forEach(key => {
		const template = templates[key];
		const steps_html = template.steps.map(step => `<li>${step.doctype_label}</li>`).join('');

		template_html += `
			<div class="col-md-4 template-card-wrapper">
				<div class="template-card" data-template="${key}">
					<div class="template-icon text-center">
						<i class="${template.icon} fa-2x text-primary"></i>
					</div>
					<h5 class="text-center">${template.name}</h5>
					<p class="text-muted">${template.description}</p>
					<ul class="template-steps">
						${steps_html}
					</ul>
					<button class="btn btn-primary btn-sm btn-block use-template" data-template="${key}">
						${__('Use This Template')}
					</button>
				</div>
			</div>
		`;
	});

	template_html += `
		<div class="col-md-4 template-card-wrapper">
			<div class="template-card custom-template">
				<div class="template-icon text-center">
					<i class="fa fa-cog fa-2x text-secondary"></i>
				</div>
				<h5 class="text-center">${__('Custom Process')}</h5>
				<p class="text-muted">${__('Build your own process from scratch')}</p>
				<button class="btn btn-secondary btn-sm btn-block" onclick="open_setup_wizard()">
					${__('Start Custom')}
				</button>
			</div>
		</div>
	</div>`;

	dialog.fields_dict.template_selector.$wrapper.html(template_html);

	// Bind events
	dialog.fields_dict.template_selector.$wrapper.on('click', '.use-template', function() {
		const template_key = $(this).data('template');
		create_from_template(template_key, frm, dialog);
	});
}

function create_from_template(template_key, frm, dialog) {
	frappe.prompt([
		{
			fieldtype: 'Data',
			fieldname: 'chain_name',
			label: __('Process Name'),
			reqd: 1,
			default: templates[template_key]?.name || ''
		}
	], function(values) {
		frappe.call({
			method: 'dev_assistant.dev_assistant.universal_sync.sync_templates.create_chain_from_template',
			args: {
				template_name: template_key,
				chain_name: values.chain_name
			},
			callback: function(r) {
				dialog.hide();
				if (r.message && r.message.success) {
					frappe.msgprint({
						title: __('Template Applied'),
						message: r.message.message,
						indicator: 'green'
					});
					// Navigate to new chain or refresh current
					if (frm.doc.__islocal) {
						frm.reload_doc();
					} else {
						frappe.set_route('Form', 'Sync Chain', r.message.chain_name);
					}
				}
			}
		});
	}, __('Create from Template'));
}

function show_sync_statistics(frm) {
	frappe.call({
		method: 'get_sync_statistics',
		doc: frm.doc,
		callback: function(r) {
			if (r.message) {
				const stats = r.message;
				const success_rate = stats.total_syncs > 0 ?
					Math.round((stats.successful_syncs / stats.total_syncs) * 100) : 100;

				const stats_html = `
					<div class="sync-stats row">
						<div class="col-md-3">
							<div class="stat-card">
								<h4>${stats.total_syncs}</h4>
								<p class="text-muted">${__('Total Syncs')}</p>
							</div>
						</div>
						<div class="col-md-3">
							<div class="stat-card">
								<h4 class="text-success">${stats.successful_syncs}</h4>
								<p class="text-muted">${__('Successful')}</p>
							</div>
						</div>
						<div class="col-md-3">
							<div class="stat-card">
								<h4 class="text-danger">${stats.failed_syncs}</h4>
								<p class="text-muted">${__('Failed')}</p>
							</div>
						</div>
						<div class="col-md-3">
							<div class="stat-card">
								<h4 class="text-primary">${success_rate}%</h4>
								<p class="text-muted">${__('Success Rate')}</p>
							</div>
						</div>
					</div>
				`;

				// Add to form
				if (!frm.dashboard.stats_wrapper) {
					frm.dashboard.add_section(stats_html, __('Sync Statistics'));
					frm.dashboard.stats_wrapper = true;
				}
			}
		}
	});
}

function show_field_mapping_button(frm, row) {
	// This will be enhanced with the field mapping interface
	console.log('Field mapping for step:', row.step_number, 'DocType:', row.doctype_name);
}

function open_setup_wizard(frm) {
	// Navigate to setup wizard page
	frappe.set_route('sync-setup-wizard', frm.doc.name || 'new');
}

// CSS for templates
frappe.provide('frappe.ui.form');
frappe.ui.form.sync_chain_css = `
<style>
.template-grid {
	margin-top: 20px;
}
.template-card {
	border: 1px solid #d1d8dd;
	border-radius: 6px;
	padding: 20px;
	margin-bottom: 20px;
	text-align: center;
	transition: all 0.3s ease;
	height: 280px;
	display: flex;
	flex-direction: column;
	justify-content: space-between;
}
.template-card:hover {
	border-color: #007bff;
	box-shadow: 0 2px 10px rgba(0,123,255,0.1);
}
.template-card.custom-template {
	border-style: dashed;
}
.template-steps {
	text-align: left;
	padding-left: 20px;
	font-size: 12px;
	max-height: 80px;
	overflow-y: auto;
}
.sync-stats .stat-card {
	text-align: center;
	padding: 15px;
	border: 1px solid #e9ecef;
	border-radius: 4px;
	margin-bottom: 10px;
}
.sync-stats .stat-card h4 {
	margin: 0;
	font-size: 24px;
	font-weight: bold;
}
.sync-stats .stat-card p {
	margin: 5px 0 0 0;
	font-size: 12px;
}
</style>
`;

$(document).ready(function() {
	if (!$('#sync-chain-css').length) {
		$('head').append('<div id="sync-chain-css">' + frappe.ui.form.sync_chain_css + '</div>');
	}
});