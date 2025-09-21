// Copyright (c) 2024, Swapnil and contributors
// For license information, please see license.txt

frappe.query_reports["Mandatory Field Analytics"] = {
	"filters": [
		{
			"fieldname": "document_type",
			"label": __("Document Type"),
			"fieldtype": "Data"
		},
		{
			"fieldname": "enabled",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nActive\nDisabled"
		}
	],

	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname == "priority") {
			const priority_colors = {
				"Critical": "red",
				"High": "orange",
				"Medium": "yellow",
				"Low": "blue"
			};
			const color = priority_colors[data.priority] || "gray";
			value = `<span class="indicator-pill ${color}">${value}</span>`;
		}

		if (column.fieldname == "enabled") {
			if (data.enabled === "Active") {
				value = `<span class="indicator-pill green">${value}</span>`;
			} else {
				value = `<span class="indicator-pill gray">${value}</span>`;
			}
		}

		if (column.fieldname == "condition_count" || column.fieldname == "field_count") {
			if (parseInt(value) > 0) {
				value = `<strong>${value}</strong>`;
			}
		}

		return value;
	},

	"onload": function(report) {
		// Add custom buttons
		report.page.add_inner_button(__("Refresh"), function() {
			report.refresh();
		});

		report.page.add_inner_button(__("Export All"), function() {
			export_all_configurations();
		});

		report.page.add_inner_button(__("Create Rule"), function() {
			frappe.new_doc("Mandatory Field Controller");
		});

		report.page.add_inner_button(__("View List"), function() {
			frappe.set_route("List", "Mandatory Field Controller");
		});

		// Add help text
		add_help_section(report);
	},

	// Removed after_datatable_render to avoid conflicts

	"get_datatable_options": function(options) {
		return Object.assign(options, {
			checkboxColumn: true,
			dynamicRowHeight: true
		});
	}
};

function export_all_configurations() {
	frappe.call({
		method: "dev_assistant.dev_assistant.doctype.mandatory_field_controller.mandatory_field_controller.export_all_configurations",
		callback: function(r) {
			if (r.message) {
				const json_str = JSON.stringify(r.message, null, 2);
				const blob = new Blob([json_str], { type: "application/json" });
				const url = URL.createObjectURL(blob);
				const a = document.createElement("a");
				a.href = url;
				a.download = `mandatory_field_configurations_${frappe.datetime.nowdate()}.json`;
				a.click();

				frappe.show_alert({
					message: __("Configurations exported successfully"),
					indicator: "green"
				});
			}
		}
	});
}

function add_help_section(report) {
	// Simplified help section to avoid conflicts
	frappe.show_alert({
		message: __('Mandatory Field Analytics Report loaded successfully. Use filters to analyze your validation rules.'),
		indicator: 'blue'
	});
}

function show_empty_state(datatable_obj) {
	// Create a nice empty state
	const empty_html = `
		<div class="empty-state" style="text-align: center; padding: 60px 20px;">
			<div style="font-size: 48px; color: #d1d8dd; margin-bottom: 20px;">
				📋
			</div>
			<h3 style="color: #555; margin-bottom: 15px;">No Mandatory Field Rules Found</h3>
			<p style="color: #888; margin-bottom: 30px;">
				Get started by creating your first mandatory field validation rule.<br>
				Use rules to ensure important fields are filled before saving documents.
			</p>
			<div style="margin-bottom: 20px;">
				<button class="btn btn-primary btn-create-rule" style="margin-right: 10px;">
					<i class="fa fa-plus"></i> Create Your First Rule
				</button>
				<button class="btn btn-default btn-view-docs">
					<i class="fa fa-book"></i> View Documentation
				</button>
			</div>
			<div class="quick-start-tips" style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 30px; text-align: left; max-width: 600px; margin-left: auto; margin-right: auto;">
				<h5>Quick Start Tips:</h5>
				<ul style="margin: 0;">
					<li>Choose a document type (e.g., Sales Order, Customer)</li>
					<li>Select fields that must be filled</li>
					<li>Set conditions when validation should apply</li>
					<li>Test with sample data before enabling</li>
				</ul>
			</div>
		</div>
	`;

	// Replace the datatable content
	$(datatable_obj.wrapper).html(empty_html);

	// Add click handlers
	$(datatable_obj.wrapper).find('.btn-create-rule').on('click', function() {
		frappe.new_doc("Mandatory Field Controller");
	});

	$(datatable_obj.wrapper).find('.btn-view-docs').on('click', function() {
		frappe.msgprint({
			title: __('Getting Started'),
			message: `
				<h5>Creating Mandatory Field Rules</h5>
				<ol>
					<li><strong>Select Document Type:</strong> Choose which form/document to validate</li>
					<li><strong>Add Conditions:</strong> Define when validation should apply (optional)</li>
					<li><strong>Select Fields:</strong> Choose which fields must be filled</li>
					<li><strong>Test & Enable:</strong> Test with sample data, then enable the rule</li>
				</ol>
				<p><strong>Pro Tip:</strong> Start with simple rules on important documents like Sales Orders or Customers.</p>
			`,
			indicator: 'blue'
		});
	});
}