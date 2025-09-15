frappe.ui.form.on('Permission Query Configuration', {
	refresh: function(frm) {
		// Add Test Query button
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__('Test Query'), function() {
				frm.call('test_query').then(r => {
					if (r.message) {
						if (r.message.success) {
							frappe.msgprint({
								title: __('Query Test Successful'),
								message: r.message.message,
								indicator: 'green'
							});
						} else {
							frappe.msgprint({
								title: __('Query Test Failed'),
								message: r.message.message,
								indicator: 'red'
							});
						}
					}
				});
			});

			// Add Global Test button
			frm.add_custom_button(__('Test All Permissions'), function() {
				frappe.call({
					method: 'dev_assistant.dev_assistant.permission_hooks.test_permission_query',
					args: {
						doctype: frm.doc.doctype_name,
						user: frappe.session.user
					},
					callback: function(r) {
						if (r.message) {
							let html = '<div class="permission-test-results">';
							html += `<h4>Permission Test Results for ${r.message.doctype}</h4>`;
							html += `<p><strong>User:</strong> ${r.message.user}</p>`;

							if (r.message.configurations.length === 0) {
								html += '<p class="text-muted">No active permission configurations found.</p>';
							} else {
								r.message.configurations.forEach(config => {
									html += `<div class="permission-config" style="border: 1px solid #ddd; padding: 10px; margin: 10px 0; border-radius: 5px;">`;
									html += `<h5>${config.permission_type} Permission - ${config.config_name}</h5>`;
									html += `<p><strong>Role:</strong> ${config.role} | <strong>Priority:</strong> ${config.priority}</p>`;
									html += `<p><strong>Conditions:</strong> <code>${JSON.stringify(config.conditions)}</code></p>`;
									if (config.sql_conditions) {
										html += `<p><strong>SQL:</strong> <code>${config.sql_conditions}</code></p>`;
									}
									html += `</div>`;
								});
							}
							html += '</div>';

							frappe.msgprint({
								title: __('Permission Test Results'),
								message: html,
								wide: true
							});
						}
					}
				});
			}, __('Actions'));
		}
	},

	filter_method: function(frm) {
		// Clear dependent fields when filter method changes
		if (frm.doc.filter_method === 'Simple Field Match') {
			frm.set_value('custom_query', '');
			frm.set_value('sql_query', '');
		} else if (frm.doc.filter_method === 'Custom Python Query') {
			frm.set_value('sql_query', '');
		} else if (frm.doc.filter_method === 'SQL Query') {
			frm.set_value('custom_query', '');
		}
	},

	doctype_name: function(frm) {
		// Clear field filters when doctype changes
		frm.clear_table('field_filters');
		frm.refresh_field('field_filters');
	},

	onload: function(frm) {
		// Set default values
		if (frm.doc.__islocal) {
			frm.set_value('priority', 1);
			frm.set_value('apply_to_list_view', 1);
			frm.set_value('apply_to_form_view', 1);
			frm.set_value('apply_to_reports', 1);
		}

		// Add helpful tooltips and examples
		if (frm.doc.filter_method === 'Custom Python Query') {
			frm.get_field('custom_query').set_description(`
				<strong>Examples:</strong><br>
				<code># Owner-based filter<br>
				return {'owner': frappe.session.user}</code><br><br>

				<code># Company-based filter<br>
				company = frappe.defaults.get_user_default('Company')<br>
				return {'company': company}</code><br><br>

				<code># Complex conditions<br>
				return [['status', '=', 'Open'], ['priority', 'in', ['High', 'Medium']]]</code>
			`);
		}

		if (frm.doc.filter_method === 'SQL Query') {
			frm.get_field('sql_query').set_description(`
				<strong>Examples:</strong><br>
				<code>tab.owner = '{user}'</code><br>
				<code>tab.company = '{company}'</code><br>
				<code>tab.creation >= '{today}'</code><br><br>
				<strong>Available placeholders:</strong> {user}, {company}, {today}, {now}
			`);
		}
	}
});

// Child table events for field filters
frappe.ui.form.on('Permission Query Field Filter', {
	value_type: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		// Clear value when certain value types are selected
		if (['is set', 'is not set', 'Today', 'Now'].includes(row.value_type)) {
			frappe.model.set_value(cdt, cdn, 'value', '');
		}

		// Set helpful descriptions based on value type
		let descriptions = {
			'Current User': 'Will use the current logged-in user',
			'User Property': 'Enter the user field name (e.g., "company", "department")',
			'Session Value': 'Enter session key (e.g., "user", "company")',
			'Default Value': 'Enter default key (e.g., "Company", "Territory")',
			'Today': 'Will use today\'s date',
			'Now': 'Will use current datetime'
		};

		if (descriptions[row.value_type]) {
			frappe.show_alert({
				message: descriptions[row.value_type],
				indicator: 'blue'
			}, 3);
		}
	},

	operator: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		// Clear value for operators that don't need one
		if (['is set', 'is not set'].includes(row.operator)) {
			frappe.model.set_value(cdt, cdn, 'value', '');
			frappe.model.set_value(cdt, cdn, 'value_type', '');
		}
	}
});