// Mandatory Field Controller Dashboard

frappe.pages['mandatory-field-dashboard'].on_page_load = function(wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Mandatory Field Controller Dashboard',
		single_column: true
	});

	// Add custom CSS
	add_dashboard_styles();

	// Create dashboard container
	let dashboard = new MandatoryFieldDashboard(page);
	dashboard.init();
};

class MandatoryFieldDashboard {
	constructor(page) {
		this.page = page;
		this.charts = {};
		this.filters = {};
	}

	init() {
		this.setup_filters();
		this.setup_layout();
		this.load_data();
		this.setup_refresh();
	}

	setup_filters() {
		// Add date range filter
		this.filters.date_range = this.page.add_field({
			fieldname: 'date_range',
			label: __('Date Range'),
			fieldtype: 'Select',
			options: [
				{ label: 'Last 7 Days', value: '7' },
				{ label: 'Last 30 Days', value: '30' },
				{ label: 'Last 3 Months', value: '90' },
				{ label: 'Last Year', value: '365' },
				{ label: 'All Time', value: 'all' }
			],
			default: '30',
			change: () => this.refresh_dashboard()
		});

		// Add DocType filter
		this.filters.document_type = this.page.add_field({
			fieldname: 'document_type',
			label: __('Document Type'),
			fieldtype: 'Link',
			options: 'DocType',
			change: () => this.refresh_dashboard()
		});

		// Add priority filter
		this.filters.priority = this.page.add_field({
			fieldname: 'priority',
			label: __('Priority'),
			fieldtype: 'Select',
			options: [
				{ label: 'All', value: '' },
				{ label: 'Critical', value: 'Critical' },
				{ label: 'High', value: 'High' },
				{ label: 'Medium', value: 'Medium' },
				{ label: 'Low', value: 'Low' }
			],
			change: () => this.refresh_dashboard()
		});

		// Add refresh button
		this.page.set_primary_action(__('Refresh'), () => {
			this.refresh_dashboard();
		}, 'refresh');

		// Add export button
		this.page.set_secondary_action(__('Export Report'), () => {
			this.export_report();
		});
	}

	setup_layout() {
		let html = `
			<div class="dashboard-container">
				<!-- Summary Cards -->
				<div class="row dashboard-stats">
					<div class="col-lg-3 col-md-6">
						<div class="stat-card" id="total-rules">
							<div class="stat-icon"><i class="fa fa-list"></i></div>
							<div class="stat-content">
								<div class="stat-number">0</div>
								<div class="stat-label">Total Rules</div>
							</div>
						</div>
					</div>
					<div class="col-lg-3 col-md-6">
						<div class="stat-card" id="active-rules">
							<div class="stat-icon"><i class="fa fa-check-circle"></i></div>
							<div class="stat-content">
								<div class="stat-number">0</div>
								<div class="stat-label">Active Rules</div>
							</div>
						</div>
					</div>
					<div class="col-lg-3 col-md-6">
						<div class="stat-card" id="triggered-today">
							<div class="stat-icon"><i class="fa fa-bolt"></i></div>
							<div class="stat-content">
								<div class="stat-number">0</div>
								<div class="stat-label">Triggered Today</div>
							</div>
						</div>
					</div>
					<div class="col-lg-3 col-md-6">
						<div class="stat-card" id="error-rate">
							<div class="stat-icon"><i class="fa fa-exclamation-triangle"></i></div>
							<div class="stat-content">
								<div class="stat-number">0%</div>
								<div class="stat-label">Error Rate</div>
							</div>
						</div>
					</div>
				</div>

				<!-- Charts Row 1 -->
				<div class="row">
					<div class="col-lg-6">
						<div class="chart-container">
							<h4>Rules by Priority</h4>
							<div id="priority-chart"></div>
						</div>
					</div>
					<div class="col-lg-6">
						<div class="chart-container">
							<h4>Rules by DocType</h4>
							<div id="doctype-chart"></div>
						</div>
					</div>
				</div>

				<!-- Charts Row 2 -->
				<div class="row">
					<div class="col-lg-8">
						<div class="chart-container">
							<h4>Validation Triggers Over Time</h4>
							<div id="timeline-chart"></div>
						</div>
					</div>
					<div class="col-lg-4">
						<div class="chart-container">
							<h4>Execution Modes</h4>
							<div id="execution-mode-chart"></div>
						</div>
					</div>
				</div>

				<!-- Performance Metrics -->
				<div class="row">
					<div class="col-lg-12">
						<div class="chart-container">
							<h4>Performance Metrics</h4>
							<div id="performance-table"></div>
						</div>
					</div>
				</div>

				<!-- Recent Activity -->
				<div class="row">
					<div class="col-lg-6">
						<div class="chart-container">
							<h4>Most Active Rules</h4>
							<div id="active-rules-list"></div>
						</div>
					</div>
					<div class="col-lg-6">
						<div class="chart-container">
							<h4>Recent Errors</h4>
							<div id="error-log"></div>
						</div>
					</div>
				</div>
			</div>
		`;

		$(this.page.body).html(html);
	}

	load_data() {
		// Load summary statistics
		this.load_summary_stats();

		// Load charts data
		this.load_priority_chart();
		this.load_doctype_chart();
		this.load_timeline_chart();
		this.load_execution_mode_chart();
		this.load_performance_metrics();
		this.load_active_rules();
		this.load_error_log();
	}

	load_summary_stats() {
		frappe.call({
			method: 'dev_assistant.dev_assistant.doctype.mandatory_field_controller.mandatory_field_controller.get_dashboard_stats',
			args: {
				filters: this.get_filters()
			},
			callback: (r) => {
				if (r.message) {
					this.update_stat_cards(r.message);
				}
			}
		});
	}

	update_stat_cards(stats) {
		$('#total-rules .stat-number').text(stats.total_rules || 0);
		$('#active-rules .stat-number').text(stats.active_rules || 0);
		$('#triggered-today .stat-number').text(stats.triggered_today || 0);
		$('#error-rate .stat-number').text((stats.error_rate || 0) + '%');

		// Add color coding based on values
		if (stats.error_rate > 10) {
			$('#error-rate .stat-card').addClass('alert-danger');
		} else if (stats.error_rate > 5) {
			$('#error-rate .stat-card').addClass('alert-warning');
		}
	}

	load_priority_chart() {
		// Mock data - replace with actual API call
		const data = {
			labels: ['Critical', 'High', 'Medium', 'Low'],
			datasets: [{
				values: [5, 15, 25, 10]
			}]
		};

		this.charts.priority = new frappe.Chart('#priority-chart', {
			data: data,
			type: 'donut',
			height: 300,
			colors: ['#dc3545', '#fd7e14', '#ffc107', '#0dcaf0']
		});
	}

	load_doctype_chart() {
		// Mock data - replace with actual API call
		const data = {
			labels: ['Sales Order', 'Purchase Order', 'Employee', 'Customer', 'Supplier'],
			datasets: [{
				name: 'Rules',
				values: [12, 8, 6, 5, 4]
			}]
		};

		this.charts.doctype = new frappe.Chart('#doctype-chart', {
			data: data,
			type: 'bar',
			height: 300,
			colors: ['#5e64ff']
		});
	}

	load_timeline_chart() {
		// Mock data - replace with actual API call
		const dates = [];
		const values = [];

		for (let i = 29; i >= 0; i--) {
			const date = frappe.datetime.add_days(frappe.datetime.get_today(), -i);
			dates.push(date);
			values.push(Math.floor(Math.random() * 100) + 20);
		}

		const data = {
			labels: dates,
			datasets: [{
				name: 'Validations Triggered',
				values: values
			}]
		};

		this.charts.timeline = new frappe.Chart('#timeline-chart', {
			data: data,
			type: 'line',
			height: 300,
			colors: ['#28a745'],
			lineOptions: {
				regionFill: 1
			}
		});
	}

	load_execution_mode_chart() {
		// Mock data - replace with actual API call
		const data = {
			labels: ['Always', 'Event Based', 'Field Change', 'Combined'],
			datasets: [{
				values: [20, 15, 10, 5]
			}]
		};

		this.charts.execution_mode = new frappe.Chart('#execution-mode-chart', {
			data: data,
			type: 'pie',
			height: 300
		});
	}

	load_performance_metrics() {
		const html = `
			<table class="table table-bordered">
				<thead>
					<tr>
						<th>Metric</th>
						<th>Value</th>
						<th>Trend</th>
						<th>Status</th>
					</tr>
				</thead>
				<tbody>
					<tr>
						<td>Average Execution Time</td>
						<td>45ms</td>
						<td><i class="fa fa-arrow-down text-success"></i> -12%</td>
						<td><span class="badge badge-success">Good</span></td>
					</tr>
					<tr>
						<td>Success Rate</td>
						<td>98.5%</td>
						<td><i class="fa fa-arrow-up text-success"></i> +2%</td>
						<td><span class="badge badge-success">Excellent</span></td>
					</tr>
					<tr>
						<td>Cache Hit Rate</td>
						<td>85%</td>
						<td><i class="fa fa-arrow-up text-success"></i> +5%</td>
						<td><span class="badge badge-success">Good</span></td>
					</tr>
					<tr>
						<td>Rules Evaluated/Second</td>
						<td>250</td>
						<td><i class="fa fa-arrow-right text-muted"></i> 0%</td>
						<td><span class="badge badge-info">Normal</span></td>
					</tr>
				</tbody>
			</table>
		`;

		$('#performance-table').html(html);
	}

	load_active_rules() {
		const html = `
			<div class="list-group">
				<div class="list-group-item">
					<div class="d-flex justify-content-between align-items-center">
						<div>
							<strong>Sales Order - High Value Validation</strong>
							<small class="text-muted d-block">Triggered 234 times today</small>
						</div>
						<span class="badge badge-primary">234</span>
					</div>
				</div>
				<div class="list-group-item">
					<div class="d-flex justify-content-between align-items-center">
						<div>
							<strong>Purchase Order - Budget Approval</strong>
							<small class="text-muted d-block">Triggered 156 times today</small>
						</div>
						<span class="badge badge-primary">156</span>
					</div>
				</div>
				<div class="list-group-item">
					<div class="d-flex justify-content-between align-items-center">
						<div>
							<strong>Employee - Onboarding Checklist</strong>
							<small class="text-muted d-block">Triggered 89 times today</small>
						</div>
						<span class="badge badge-primary">89</span>
					</div>
				</div>
			</div>
		`;

		$('#active-rules-list').html(html);
	}

	load_error_log() {
		const html = `
			<div class="list-group">
				<div class="list-group-item list-group-item-danger">
					<small class="text-muted">2 hours ago</small>
					<div><strong>Field not found error</strong></div>
					<small>Sales Order - custom_field_xyz not found</small>
				</div>
				<div class="list-group-item list-group-item-warning">
					<small class="text-muted">5 hours ago</small>
					<div><strong>Condition evaluation timeout</strong></div>
					<small>Purchase Order - Complex condition took >5s</small>
				</div>
				<div class="list-group-item">
					<small class="text-muted">1 day ago</small>
					<div><strong>Permission denied</strong></div>
					<small>User lacks permission for Employee doctype</small>
				</div>
			</div>
		`;

		$('#error-log').html(html);
	}

	get_filters() {
		return {
			date_range: this.filters.date_range.get_value(),
			document_type: this.filters.document_type.get_value(),
			priority: this.filters.priority.get_value()
		};
	}

	refresh_dashboard() {
		frappe.show_alert({ message: __('Refreshing dashboard...'), indicator: 'blue' });
		this.load_data();
	}

	setup_refresh() {
		// Auto-refresh every 30 seconds
		setInterval(() => {
			this.load_summary_stats();
			this.load_active_rules();
			this.load_error_log();
		}, 30000);
	}

	export_report() {
		frappe.call({
			method: 'dev_assistant.dev_assistant.doctype.mandatory_field_controller.mandatory_field_controller.export_dashboard_report',
			args: {
				filters: this.get_filters()
			},
			callback: (r) => {
				if (r.message) {
					const csv = this.generate_csv(r.message);
					this.download_csv(csv, 'mandatory_field_dashboard_report.csv');
				}
			}
		});
	}

	generate_csv(data) {
		// Convert data to CSV format
		let csv = 'Metric,Value,Date\n';
		// Add data rows
		return csv;
	}

	download_csv(csv, filename) {
		const blob = new Blob([csv], { type: 'text/csv' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = filename;
		a.click();
	}
}

function add_dashboard_styles() {
	const style = `
		<style>
			.dashboard-container {
				padding: 20px;
			}

			.dashboard-stats {
				margin-bottom: 30px;
			}

			.stat-card {
				background: white;
				border-radius: 8px;
				padding: 20px;
				box-shadow: 0 2px 4px rgba(0,0,0,0.1);
				margin-bottom: 20px;
				display: flex;
				align-items: center;
				transition: transform 0.3s, box-shadow 0.3s;
			}

			.stat-card:hover {
				transform: translateY(-2px);
				box-shadow: 0 4px 8px rgba(0,0,0,0.15);
			}

			.stat-icon {
				font-size: 32px;
				color: #5e64ff;
				margin-right: 20px;
			}

			.stat-content {
				flex: 1;
			}

			.stat-number {
				font-size: 32px;
				font-weight: bold;
				color: #333;
			}

			.stat-label {
				color: #666;
				font-size: 14px;
				margin-top: 5px;
			}

			.chart-container {
				background: white;
				border-radius: 8px;
				padding: 20px;
				box-shadow: 0 2px 4px rgba(0,0,0,0.1);
				margin-bottom: 20px;
			}

			.chart-container h4 {
				margin-top: 0;
				margin-bottom: 20px;
				color: #333;
				font-size: 18px;
				font-weight: 500;
			}

			.list-group-item {
				border-left: 3px solid transparent;
				transition: all 0.3s;
			}

			.list-group-item:hover {
				background-color: #f8f9fa;
				border-left-color: #5e64ff;
			}

			.alert-danger {
				border-left: 4px solid #dc3545;
			}

			.alert-warning {
				border-left: 4px solid #ffc107;
			}

			.badge {
				padding: 5px 10px;
				border-radius: 12px;
			}

			.badge-success {
				background-color: #28a745;
				color: white;
			}

			.badge-info {
				background-color: #17a2b8;
				color: white;
			}

			.badge-primary {
				background-color: #5e64ff;
				color: white;
			}
		</style>
	`;

	$('head').append(style);
}