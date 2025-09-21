// Enhanced List View for Mandatory Field Controller

frappe.listview_settings['Mandatory Field Controller'] = {
	add_fields: ['enabled', 'priority', 'document_type', 'execution_mode'],

	get_indicator: function(doc) {
		if (doc.enabled) {
			return [__('Active'), 'green'];
		} else {
			return [__('Disabled'), 'gray'];
		}
	},

	formatters: {
		priority: function(value) {
			const priority_colors = {
				'Critical': 'red',
				'High': 'orange',
				'Medium': 'yellow',
				'Low': 'blue'
			};
			const color = priority_colors[value] || 'gray';
			return `<span class="indicator-pill ${color}">${value || 'Not Set'}</span>`;
		},
		document_type: function(value) {
			return value ? `<strong>${value}</strong>` : '<span class="text-muted">Not Set</span>';
		},
		execution_mode: function(value) {
			const mode_icons = {
				'Always': '🔄',
				'Event Based': '⚡',
				'Field Change Based': '🔀',
				'Combined': '🔗'
			};
			const icon = mode_icons[value] || '📋';
			return `${icon} ${value || 'Not Set'}`;
		}
	},

	onload: function(listview) {
		// Add custom buttons
		listview.page.add_inner_button(__('Bulk Enable'), function() {
			bulk_action(listview, 'enable');
		});

		listview.page.add_inner_button(__('Bulk Disable'), function() {
			bulk_action(listview, 'disable');
		});

		listview.page.add_inner_button(__('Import Rules'), function() {
			show_import_dialog(listview);
		});

		listview.page.add_inner_button(__('Analytics Report'), function() {
			frappe.set_route('query-report', 'Mandatory Field Analytics');
		});

		// Quick filters and search help removed for cleaner interface
	},

	refresh: function(listview) {
		// Add status summary
		show_status_summary(listview);
	},

	// Remove invalid button configuration
};

function bulk_action(listview, action) {
	const selected = listview.get_checked_items();
	if (selected.length === 0) {
		frappe.msgprint(__('Please select at least one item'));
		return;
	}

	const names = selected.map(item => item.name);

	frappe.confirm(
		__('Are you sure you want to {0} {1} selected rules?', [action, selected.length]),
		function() {
			frappe.call({
				method: 'dev_assistant.dev_assistant.doctype.mandatory_field_controller.mandatory_field_controller.bulk_update_status',
				args: {
					names: names,
					enabled: action === 'enable'
				},
				callback: function(r) {
					if (r.message) {
						frappe.show_alert({
							message: __('Successfully updated {0} rules', [r.message]),
							indicator: 'green'
						});
						listview.refresh();
					}
				}
			});
		}
	);
}

function show_import_dialog(listview) {
	let d = new frappe.ui.Dialog({
		title: __('Import Validation Rules'),
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'help',
				options: '<p>Upload a JSON file with validation rule configurations</p>'
			},
			{
				fieldtype: 'Attach',
				fieldname: 'import_file',
				label: __('Configuration File (JSON)'),
				reqd: 1
			},
			{
				fieldtype: 'Check',
				fieldname: 'overwrite',
				label: __('Overwrite existing rules with same name')
			}
		],
		primary_action: function(values) {
			import_rules(values.import_file, values.overwrite, listview);
			d.hide();
		},
		primary_action_label: __('Import')
	});
	d.show();
}

function import_rules(file_url, overwrite, listview) {
	frappe.call({
		method: 'dev_assistant.dev_assistant.doctype.mandatory_field_controller.mandatory_field_controller.import_configurations',
		args: {
			file_url: file_url,
			overwrite: overwrite
		},
		callback: function(r) {
			if (r.message) {
				frappe.show_alert({
					message: __('Successfully imported {0} rules', [r.message.imported]),
					indicator: 'green'
				});
				listview.refresh();
			}
		}
	});
}

// Quick filters and search help functions removed for cleaner interface

function show_status_summary(listview) {
	frappe.call({
		method: 'dev_assistant.dev_assistant.doctype.mandatory_field_controller.mandatory_field_controller.get_summary_stats',
		callback: function(r) {
			if (r.message) {
				const stats = r.message;
				const summary_html = `
					<div class="list-stats" style="padding: 10px; background: #f8f9fa; border-radius: 4px; margin-bottom: 15px;">
						<div class="row">
							<div class="col-xs-3 text-center">
								<div class="stat-number" style="font-size: 24px; font-weight: bold; color: #28a745;">
									${stats.active || 0}
								</div>
								<div class="stat-label text-muted">Active Rules</div>
							</div>
							<div class="col-xs-3 text-center">
								<div class="stat-number" style="font-size: 24px; font-weight: bold; color: #dc3545;">
									${stats.critical || 0}
								</div>
								<div class="stat-label text-muted">Critical Priority</div>
							</div>
							<div class="col-xs-3 text-center">
								<div class="stat-number" style="font-size: 24px; font-weight: bold; color: #007bff;">
									${stats.doctypes || 0}
								</div>
								<div class="stat-label text-muted">DocTypes Covered</div>
							</div>
							<div class="col-xs-3 text-center">
								<div class="stat-number" style="font-size: 24px; font-weight: bold; color: #ffc107;">
									${stats.total || 0}
								</div>
								<div class="stat-label text-muted">Total Rules</div>
							</div>
						</div>
					</div>
				`;

				if (!$('.list-stats').length) {
					$(listview.$result).before(summary_html);
				}
			}
		}
	});
}

// Row actions are handled through the onload event instead of prototype override

function test_validation_rule(name) {
	frappe.set_route('Form', 'Mandatory Field Controller', name);
	setTimeout(() => {
		if (cur_frm && cur_frm.doc.name === name) {
			cur_frm.trigger('test_validation');
		}
	}, 1000);
}

function clone_rule(name) {
	frappe.call({
		method: 'frappe.client.get',
		args: {
			doctype: 'Mandatory Field Controller',
			name: name
		},
		callback: function(r) {
			if (r.message) {
				let doc = r.message;
				delete doc.name;
				doc.enabled = 0; // Disable by default
				doc.__newname = doc.document_type + ' Copy';

				frappe.set_route('Form', 'Mandatory Field Controller', 'new-mandatory-field-controller');
				setTimeout(() => {
					if (cur_frm && cur_frm.doctype === 'Mandatory Field Controller') {
						cur_frm.set_value('document_type', doc.document_type);
						cur_frm.set_value('description', doc.description + ' (Copy)');
						cur_frm.set_value('priority', doc.priority);
						cur_frm.set_value('execution_mode', doc.execution_mode);
					}
				}, 500);
			}
		}
	});
}

function view_impact_analysis(name, document_type) {
	frappe.call({
		method: 'dev_assistant.dev_assistant.doctype.mandatory_field_controller.mandatory_field_controller.get_impact_analysis',
		args: {
			controller_name: name,
			document_type: document_type
		},
		callback: function(r) {
			if (r.message) {
				show_impact_dialog(r.message);
			}
		}
	});
}

function show_impact_dialog(data) {
	let d = new frappe.ui.Dialog({
		title: __('Impact Analysis'),
		size: 'large',
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'content',
				options: get_impact_html(data)
			}
		]
	});
	d.show();
}

function get_impact_html(data) {
	return `
		<div style="padding: 15px;">
			<div class="row">
				<div class="col-md-4">
					<div class="stat-card" style="background: #e3f2fd; padding: 15px; border-radius: 8px; text-align: center;">
						<div style="font-size: 32px; font-weight: bold;">${data.total_documents || 0}</div>
						<div style="color: #666;">Total Documents</div>
					</div>
				</div>
				<div class="col-md-4">
					<div class="stat-card" style="background: #fff3e0; padding: 15px; border-radius: 8px; text-align: center;">
						<div style="font-size: 32px; font-weight: bold;">${data.affected_documents || 0}</div>
						<div style="color: #666;">Would Be Affected</div>
					</div>
				</div>
				<div class="col-md-4">
					<div class="stat-card" style="background: #e8f5e9; padding: 15px; border-radius: 8px; text-align: center;">
						<div style="font-size: 32px; font-weight: bold;">${data.compliant_documents || 0}</div>
						<div style="color: #666;">Already Compliant</div>
					</div>
				</div>
			</div>
		</div>
	`;
}
