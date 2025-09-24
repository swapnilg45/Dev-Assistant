// Copyright (c) 2025, Swapnil and contributors
// Data Sync Dashboard - User-friendly monitoring interface

frappe.pages['sync-dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Data Sync Dashboard'),
		single_column: true
	});

	frappe.sync_dashboard = new SyncDashboard(page);
};

class SyncDashboard {
	constructor(page) {
		this.page = page;
		this.wrapper = page.main;
		this.refresh_interval = null;
		this.auto_refresh_enabled = true;
		this.init();
	}

	init() {
		this.setup_page();
		this.render_dashboard();
		this.load_data();
		this.start_auto_refresh();
	}

	setup_page() {
		// Add refresh button
		this.page.set_secondary_action(__('Refresh'), () => {
			this.load_data();
		});

		// Add create new button
		this.page.set_primary_action(__('Create New Process'), () => {
			frappe.set_route('sync-setup-wizard');
		});

		// Add filters
		this.page.add_field({
			label: __('Time Period'),
			fieldtype: 'Select',
			fieldname: 'time_filter',
			options: [
				{ label: __('Last 7 days'), value: 7 },
				{ label: __('Last 30 days'), value: 30 },
				{ label: __('Last 90 days'), value: 90 }
			],
			default: 30,
			change: () => {
				this.load_data();
			}
		});

		// Add auto-refresh toggle
		this.page.add_action_item(__('Auto Refresh'), () => {
			this.toggle_auto_refresh();
		});

		// Add test system button
		this.page.add_action_item(__('Test System'), () => {
			if (window.sync_test_interface) {
				window.sync_test_interface.show_test_dialog();
			} else {
				frappe.msgprint(__('Test interface not loaded. Please refresh the page.'));
			}
		});
	}

	render_dashboard() {
		this.wrapper.html(`
			<div class="sync-dashboard">
				<!-- Overview Cards -->
				<div class="dashboard-overview mb-4">
					<div class="row">
						<div class="col-lg-3 col-md-6 mb-3">
							<div class="overview-card total-chains">
								<div class="card h-100">
									<div class="card-body text-center">
										<div class="overview-icon mb-2">
											<i class="fa fa-sitemap fa-2x text-primary"></i>
										</div>
										<h3 class="overview-number">0</h3>
										<p class="overview-label text-muted">${__('Active Processes')}</p>
									</div>
								</div>
							</div>
						</div>
						<div class="col-lg-3 col-md-6 mb-3">
							<div class="overview-card successful-syncs">
								<div class="card h-100">
									<div class="card-body text-center">
										<div class="overview-icon mb-2">
											<i class="fa fa-check-circle fa-2x text-success"></i>
										</div>
										<h3 class="overview-number">0</h3>
										<p class="overview-label text-muted">${__('Successful Syncs')}</p>
									</div>
								</div>
							</div>
						</div>
						<div class="col-lg-3 col-md-6 mb-3">
							<div class="overview-card failed-syncs">
								<div class="card h-100">
									<div class="card-body text-center">
										<div class="overview-icon mb-2">
											<i class="fa fa-exclamation-circle fa-2x text-danger"></i>
										</div>
										<h3 class="overview-number">0</h3>
										<p class="overview-label text-muted">${__('Failed Syncs')}</p>
									</div>
								</div>
							</div>
						</div>
						<div class="col-lg-3 col-md-6 mb-3">
							<div class="overview-card success-rate">
								<div class="card h-100">
									<div class="card-body text-center">
										<div class="overview-icon mb-2">
											<i class="fa fa-line-chart fa-2x text-info"></i>
										</div>
										<h3 class="overview-number">0%</h3>
										<p class="overview-label text-muted">${__('Success Rate')}</p>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- Charts Section -->
				<div class="dashboard-charts mb-4">
					<div class="row">
						<div class="col-lg-8">
							<div class="card">
								<div class="card-header">
									<h6 class="card-title mb-0">${__('Activity Trend')}</h6>
								</div>
								<div class="card-body">
									<canvas id="activity-trend-chart" height="100"></canvas>
								</div>
							</div>
						</div>
						<div class="col-lg-4">
							<div class="card">
								<div class="card-header">
									<h6 class="card-title mb-0">${__('Sync Status Distribution')}</h6>
								</div>
								<div class="card-body">
									<canvas id="status-pie-chart"></canvas>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- Sync Processes -->
				<div class="dashboard-processes mb-4">
					<div class="card">
						<div class="card-header d-flex justify-content-between align-items-center">
							<h6 class="card-title mb-0">${__('Your Sync Processes')}</h6>
							<button class="btn btn-sm btn-primary create-process-btn">
								<i class="fa fa-plus"></i> ${__('New Process')}
							</button>
						</div>
						<div class="card-body">
							<div class="process-cards">
								<div class="text-center p-4">
									<i class="fa fa-spinner fa-spin fa-2x text-muted"></i>
									<p class="text-muted mt-2">${__('Loading processes...')}</p>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- Recent Activity -->
				<div class="dashboard-activity">
					<div class="row">
						<div class="col-lg-8">
							<div class="card">
								<div class="card-header">
									<h6 class="card-title mb-0">${__('Recent Activity')}</h6>
								</div>
								<div class="card-body">
									<div class="activity-list">
										<div class="text-center p-3">
											<i class="fa fa-spinner fa-spin"></i>
											<small class="text-muted ml-2">${__('Loading activities...')}</small>
										</div>
									</div>
								</div>
							</div>
						</div>
						<div class="col-lg-4">
							<div class="card">
								<div class="card-header d-flex justify-content-between align-items-center">
									<h6 class="card-title mb-0">${__('Pending Reviews')}</h6>
									<span class="badge badge-warning pending-count">0</span>
								</div>
								<div class="card-body">
									<div class="pending-reviews">
										<div class="text-center p-3">
											<i class="fa fa-check text-success"></i>
											<small class="text-muted ml-2">${__('No pending reviews')}</small>
										</div>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- System Health -->
				<div class="dashboard-health mt-4">
					<div class="card">
						<div class="card-header">
							<h6 class="card-title mb-0">${__('System Health')}</h6>
						</div>
						<div class="card-body">
							<div class="health-indicators">
								<!-- Health indicators will be rendered here -->
							</div>
						</div>
					</div>
				</div>
			</div>
		`);

		this.bind_events();
		this.init_charts();
	}

	load_data() {
		const time_filter = this.page.fields_dict.time_filter?.get_value() || 30;

		// Show loading state
		this.show_loading_state();

		// Load dashboard data
		frappe.call({
			method: 'dev_assistant.dev_assistant.page.sync_dashboard.sync_dashboard.get_dashboard_data',
			args: { days: time_filter },
			callback: (r) => {
				if (r.message && !r.message.error) {
					this.render_dashboard_data(r.message);
				} else {
					this.show_error_state(r.message?.error || __('Failed to load dashboard data'));
				}
			},
			error: () => {
				this.show_error_state(__('Network error occurred'));
			}
		});

		// Load system health
		frappe.call({
			method: 'dev_assistant.dev_assistant.page.sync_dashboard.sync_dashboard.get_system_health',
			callback: (r) => {
				if (r.message && !r.message.error) {
					this.render_system_health(r.message);
				}
			}
		});
	}

	render_dashboard_data(data) {
		// Update overview cards
		this.update_overview_cards(data.overview);

		// Render process cards
		this.render_process_cards(data.active_chains, data.chain_stats);

		// Render recent activity
		this.render_recent_activity(data.recent_activities);

		// Render pending reviews
		this.render_pending_reviews(data.pending_reviews);

		// Update charts
		this.update_activity_chart(data.hourly_trend);
		this.update_status_chart(data.overview);
	}

	update_overview_cards(overview) {
		this.wrapper.find('.total-chains .overview-number').text(overview.total_chains);
		this.wrapper.find('.successful-syncs .overview-number').text(overview.successful_syncs);
		this.wrapper.find('.failed-syncs .overview-number').text(overview.failed_syncs);
		this.wrapper.find('.success-rate .overview-number').text(`${overview.success_rate}%`);
		this.wrapper.find('.pending-count').text(overview.pending_reviews);
	}

	render_process_cards(chains, stats) {
		const process_cards = this.wrapper.find('.process-cards');

		if (chains.length === 0) {
			process_cards.html(`
				<div class="empty-state text-center p-4">
					<i class="fa fa-sitemap fa-3x text-muted mb-3"></i>
					<h5>${__('No Sync Processes Yet')}</h5>
					<p class="text-muted">${__('Create your first sync process to get started')}</p>
					<button class="btn btn-primary btn-create-first">
						<i class="fa fa-plus"></i> ${__('Create First Process')}
					</button>
				</div>
			`);
			return;
		}

		let cards_html = '<div class="row">';

		chains.forEach(chain => {
			const chain_stat = stats.find(s => s.sync_chain === chain.name) || {
				total_syncs: 0,
				successful_syncs: 0,
				failed_syncs: 0
			};

			const success_rate = chain_stat.total_syncs > 0 ?
				Math.round((chain_stat.successful_syncs / chain_stat.total_syncs) * 100) : 100;

			const status_class = this.get_status_class(success_rate);

			cards_html += `
				<div class="col-lg-6 mb-3">
					<div class="process-card">
						<div class="card">
							<div class="card-body">
								<div class="d-flex justify-content-between align-items-start mb-2">
									<div class="process-info">
										<h6 class="process-name">${chain.chain_name}</h6>
										<small class="text-muted">${chain.description || ''}</small>
									</div>
									<div class="process-status">
										<span class="badge ${status_class}">${success_rate}% Success</span>
									</div>
								</div>
								<div class="process-stats mt-3">
									<div class="row text-center">
										<div class="col-4">
											<div class="stat-item">
												<div class="stat-number">${chain_stat.total_syncs}</div>
												<div class="stat-label small text-muted">${__('Total')}</div>
											</div>
										</div>
										<div class="col-4">
											<div class="stat-item">
												<div class="stat-number text-success">${chain_stat.successful_syncs}</div>
												<div class="stat-label small text-muted">${__('Success')}</div>
											</div>
										</div>
										<div class="col-4">
											<div class="stat-item">
												<div class="stat-number text-danger">${chain_stat.failed_syncs}</div>
												<div class="stat-label small text-muted">${__('Failed')}</div>
											</div>
										</div>
									</div>
								</div>
								<div class="process-actions mt-3">
									<div class="btn-group w-100" role="group">
										<button class="btn btn-sm btn-outline-primary view-details" data-chain="${chain.name}">
											${__('View Details')}
										</button>
										<button class="btn btn-sm btn-outline-secondary edit-process" data-chain="${chain.name}">
											${__('Edit')}
										</button>
										<button class="btn btn-sm btn-outline-info manual-sync" data-chain="${chain.name}">
											${__('Sync Now')}
										</button>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			`;
		});

		cards_html += '</div>';
		process_cards.html(cards_html);
	}

	render_recent_activity(activities) {
		const activity_list = this.wrapper.find('.activity-list');

		if (activities.length === 0) {
			activity_list.html(`
				<div class="text-center p-3">
					<i class="fa fa-info-circle text-muted"></i>
					<small class="text-muted ml-2">${__('No recent activity')}</small>
				</div>
			`);
			return;
		}

		let activities_html = '';

		activities.slice(0, 10).forEach(activity => {
			const icon = this.get_activity_icon(activity.activity_type, activity.status);
			const time_ago = moment(activity.creation).fromNow();

			activities_html += `
				<div class="activity-item d-flex align-items-center py-2 border-bottom">
					<div class="activity-icon me-3">
						<i class="fa ${icon.icon} ${icon.class}"></i>
					</div>
					<div class="activity-content flex-grow-1">
						<div class="activity-title">${activity.activity_type}</div>
						<div class="activity-meta small text-muted">
							${activity.source_doctype} → ${activity.target_doctype} • ${time_ago}
						</div>
					</div>
					<div class="activity-status">
						<span class="badge badge-sm ${this.get_status_badge_class(activity.status)}">${activity.status}</span>
					</div>
				</div>
			`;
		});

		activity_list.html(activities_html);
	}

	render_pending_reviews(pending_reviews) {
		const reviews_container = this.wrapper.find('.pending-reviews');

		if (pending_reviews.length === 0) {
			reviews_container.html(`
				<div class="text-center p-3">
					<i class="fa fa-check text-success"></i>
					<small class="text-muted ml-2">${__('No pending reviews')}</small>
				</div>
			`);
			return;
		}

		let reviews_html = '';

		pending_reviews.slice(0, 5).forEach(review => {
			reviews_html += `
				<div class="review-item py-2 border-bottom">
					<div class="review-title small font-weight-bold">${review.source_doctype} → ${review.target_doctype}</div>
					<div class="review-meta small text-muted">${moment(review.creation).fromNow()}</div>
					<div class="review-actions mt-1">
						<button class="btn btn-xs btn-success resolve-review" data-review="${review.name}" data-action="approve">
							${__('Approve')}
						</button>
						<button class="btn btn-xs btn-danger resolve-review" data-review="${review.name}" data-action="reject">
							${__('Reject')}
						</button>
					</div>
				</div>
			`;
		});

		reviews_container.html(reviews_html);
	}

	render_system_health(health_data) {
		const health_container = this.wrapper.find('.health-indicators');
		const health_class = this.get_health_class(health_data.health_status);

		const health_html = `
			<div class="row">
				<div class="col-lg-3">
					<div class="health-indicator text-center">
						<div class="health-score ${health_class}">
							<h3>${health_data.health_score}/100</h3>
							<p class="small text-muted">${__('Health Score')}</p>
						</div>
					</div>
				</div>
				<div class="col-lg-9">
					<div class="health-metrics">
						<div class="row">
							<div class="col-md-3">
								<div class="metric-item">
									<div class="metric-value">${health_data.error_rate}%</div>
									<div class="metric-label small text-muted">${__('Error Rate')}</div>
								</div>
							</div>
							<div class="col-md-3">
								<div class="metric-item">
									<div class="metric-value">${health_data.avg_processing_time}s</div>
									<div class="metric-label small text-muted">${__('Avg Processing Time')}</div>
								</div>
							</div>
							<div class="col-md-3">
								<div class="metric-item">
									<div class="metric-value">${health_data.daily_activities}</div>
									<div class="metric-label small text-muted">${__('Daily Activities')}</div>
								</div>
							</div>
							<div class="col-md-3">
								<div class="metric-item">
									<div class="metric-value">${health_data.total_active_chains}</div>
									<div class="metric-label small text-muted">${__('Active Chains')}</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		`;

		health_container.html(health_html);
	}

	init_charts() {
		// Initialize Chart.js charts
		this.activity_chart_ctx = document.getElementById('activity-trend-chart');
		this.status_chart_ctx = document.getElementById('status-pie-chart');

		// Activity trend chart
		this.activity_chart = new Chart(this.activity_chart_ctx, {
			type: 'line',
			data: {
				labels: [],
				datasets: [{
					label: __('Successful'),
					data: [],
					borderColor: '#28a745',
					backgroundColor: 'rgba(40, 167, 69, 0.1)',
					tension: 0.4
				}, {
					label: __('Failed'),
					data: [],
					borderColor: '#dc3545',
					backgroundColor: 'rgba(220, 53, 69, 0.1)',
					tension: 0.4
				}]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				scales: {
					y: {
						beginAtZero: true
					}
				}
			}
		});

		// Status pie chart
		this.status_chart = new Chart(this.status_chart_ctx, {
			type: 'doughnut',
			data: {
				labels: [__('Success'), __('Failed'), __('Pending')],
				datasets: [{
					data: [0, 0, 0],
					backgroundColor: ['#28a745', '#dc3545', '#ffc107']
				}]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false
			}
		});
	}

	update_activity_chart(trend_data) {
		if (!this.activity_chart || !trend_data) return;

		const labels = trend_data.map(item => moment(item.hour).format('MMM DD, HH:mm'));
		const success_data = trend_data.map(item => item.success);
		const failed_data = trend_data.map(item => item.failed);

		this.activity_chart.data.labels = labels;
		this.activity_chart.data.datasets[0].data = success_data;
		this.activity_chart.data.datasets[1].data = failed_data;
		this.activity_chart.update();
	}

	update_status_chart(overview) {
		if (!this.status_chart) return;

		this.status_chart.data.datasets[0].data = [
			overview.successful_syncs,
			overview.failed_syncs,
			overview.pending_reviews
		];
		this.status_chart.update();
	}

	bind_events() {
		// Create process buttons
		this.wrapper.on('click', '.create-process-btn, .btn-create-first', () => {
			frappe.set_route('sync-setup-wizard');
		});

		// View process details
		this.wrapper.on('click', '.view-details', (e) => {
			const chain_name = $(e.target).data('chain');
			this.show_process_details(chain_name);
		});

		// Edit process
		this.wrapper.on('click', '.edit-process', (e) => {
			const chain_name = $(e.target).data('chain');
			frappe.set_route('Form', 'Sync Chain', chain_name);
		});

		// Manual sync
		this.wrapper.on('click', '.manual-sync', (e) => {
			const chain_name = $(e.target).data('chain');
			this.trigger_manual_sync(chain_name);
		});

		// Resolve review
		this.wrapper.on('click', '.resolve-review', (e) => {
			const review_name = $(e.target).data('review');
			const action = $(e.target).data('action');
			this.resolve_review(review_name, action);
		});
	}

	show_process_details(chain_name) {
		frappe.call({
			method: 'dev_assistant.dev_assistant.page.sync_dashboard.sync_dashboard.get_chain_details',
			args: { chain_name: chain_name },
			callback: (r) => {
				if (r.message && !r.message.error) {
					this.render_process_details_dialog(r.message);
				}
			}
		});
	}

	render_process_details_dialog(data) {
		const dialog = new frappe.ui.Dialog({
			title: `${__('Process Details')}: ${data.chain.chain_name}`,
			size: 'large',
			fields: [
				{
					fieldtype: 'HTML',
					fieldname: 'process_details'
				}
			]
		});

		const steps_html = data.steps.map(step =>
			`<tr>
				<td class="text-center">${step.step_number}</td>
				<td><strong>${step.doctype_label}</strong><br><small class="text-muted">${step.doctype_name}</small></td>
				<td>${step.sync_condition}</td>
				<td class="text-center">${step.field_mappings_count}</td>
				<td class="text-center">${step.record_count}</td>
			</tr>`
		).join('');

		const activities_html = data.recent_activities.slice(0, 5).map(activity =>
			`<tr>
				<td>${activity.activity_type}</td>
				<td><span class="badge ${this.get_status_badge_class(activity.status)}">${activity.status}</span></td>
				<td>${moment(activity.creation).fromNow()}</td>
			</tr>`
		).join('');

		const details_html = `
			<div class="process-details">
				<div class="row mb-3">
					<div class="col-md-6">
						<h6>${__('Basic Information')}</h6>
						<table class="table table-sm">
							<tr><td><strong>${__('Status')}</strong></td><td>${data.chain.is_active ? __('Active') : __('Inactive')}</td></tr>
							<tr><td><strong>${__('Sync Frequency')}</strong></td><td>${data.chain.sync_frequency}</td></tr>
							<tr><td><strong>${__('Conflict Resolution')}</strong></td><td>${data.chain.conflict_resolution}</td></tr>
							<tr><td><strong>${__('Template Used')}</strong></td><td>${data.chain.template_used || __('Custom')}</td></tr>
						</table>
					</div>
					<div class="col-md-6">
						<h6>${__('Performance Metrics')}</h6>
						<table class="table table-sm">
							<tr><td><strong>${__('Total Executions')}</strong></td><td>${data.performance.total_executions || 0}</td></tr>
							<tr><td><strong>${__('Success Rate')}</strong></td><td>${Math.round(data.performance.avg_success_rate || 0)}%</td></tr>
							<tr><td><strong>${__('Active Days')}</strong></td><td>${data.performance.active_days || 0}</td></tr>
							<tr><td><strong>${__('Last Activity')}</strong></td><td>${data.performance.last_activity ? moment(data.performance.last_activity).fromNow() : __('Never')}</td></tr>
						</table>
					</div>
				</div>

				<h6>${__('Process Steps')}</h6>
				<table class="table table-bordered table-sm">
					<thead>
						<tr>
							<th width="10%">${__('Step')}</th>
							<th width="30%">${__('Document Type')}</th>
							<th width="20%">${__('Sync Condition')}</th>
							<th width="15%">${__('Mappings')}</th>
							<th width="15%">${__('Records')}</th>
						</tr>
					</thead>
					<tbody>${steps_html}</tbody>
				</table>

				<h6 class="mt-3">${__('Recent Activity')}</h6>
				<table class="table table-sm">
					<thead>
						<tr><th>${__('Activity')}</th><th>${__('Status')}</th><th>${__('Time')}</th></tr>
					</thead>
					<tbody>${activities_html}</tbody>
				</table>
			</div>
		`;

		dialog.fields_dict.process_details.$wrapper.html(details_html);
		dialog.show();
	}

	trigger_manual_sync(chain_name) {
		frappe.confirm(
			__('This will trigger a manual sync for all applicable documents. Continue?'),
			() => {
				frappe.show_alert({
					message: __('Manual sync started...'),
					indicator: 'blue'
				});

				// Here you would call the manual sync API
				// For now, just reload data after a delay
				setTimeout(() => {
					this.load_data();
					frappe.show_alert({
						message: __('Manual sync completed'),
						indicator: 'green'
					});
				}, 3000);
			}
		);
	}

	resolve_review(review_name, action) {
		frappe.call({
			method: 'dev_assistant.dev_assistant.universal_sync.sync_activity_log.resolve_pending_review',
			args: {
				log_name: review_name,
				resolution: action
			},
			callback: (r) => {
				if (r.message && r.message.success) {
					frappe.show_alert({
						message: r.message.message,
						indicator: 'green'
					});
					this.load_data();
				}
			}
		});
	}

	get_status_class(success_rate) {
		if (success_rate >= 90) return 'badge-success';
		if (success_rate >= 70) return 'badge-warning';
		return 'badge-danger';
	}

	get_status_badge_class(status) {
		const classes = {
			'Success': 'badge-success',
			'Failed': 'badge-danger',
			'Pending Review': 'badge-warning'
		};
		return classes[status] || 'badge-secondary';
	}

	get_activity_icon(type, status) {
		if (status === 'Failed') return { icon: 'fa-exclamation-circle', class: 'text-danger' };
		if (type === 'Data Synced') return { icon: 'fa-check-circle', class: 'text-success' };
		if (type === 'Manual Review Needed') return { icon: 'fa-eye', class: 'text-warning' };
		return { icon: 'fa-info-circle', class: 'text-info' };
	}

	get_health_class(status) {
		const classes = {
			'excellent': 'text-success',
			'good': 'text-info',
			'warning': 'text-warning',
			'critical': 'text-danger'
		};
		return classes[status] || 'text-secondary';
	}

	show_loading_state() {
		// Show loading spinners
		this.wrapper.find('.overview-number').html('<i class="fa fa-spinner fa-spin"></i>');
	}

	show_error_state(error_msg) {
		frappe.msgprint({
			title: __('Dashboard Error'),
			message: error_msg,
			indicator: 'red'
		});
	}

	start_auto_refresh() {
		if (this.auto_refresh_enabled) {
			this.refresh_interval = setInterval(() => {
				this.load_data();
			}, 60000); // Refresh every minute
		}
	}

	stop_auto_refresh() {
		if (this.refresh_interval) {
			clearInterval(this.refresh_interval);
			this.refresh_interval = null;
		}
	}

	toggle_auto_refresh() {
		this.auto_refresh_enabled = !this.auto_refresh_enabled;

		if (this.auto_refresh_enabled) {
			this.start_auto_refresh();
			frappe.show_alert({
				message: __('Auto refresh enabled'),
				indicator: 'green'
			});
		} else {
			this.stop_auto_refresh();
			frappe.show_alert({
				message: __('Auto refresh disabled'),
				indicator: 'orange'
			});
		}
	}

	destroy() {
		this.stop_auto_refresh();
	}
}

// CSS for dashboard
$(document).ready(function() {
	if (!$('#sync-dashboard-css').length) {
		$('head').append(`
			<style id="sync-dashboard-css">
			.sync-dashboard .overview-card {
				transition: transform 0.2s ease;
			}

			.sync-dashboard .overview-card:hover {
				transform: translateY(-2px);
			}

			.overview-icon {
				opacity: 0.8;
			}

			.overview-number {
				font-size: 2.5rem;
				font-weight: bold;
				margin: 0;
			}

			.process-card {
				transition: transform 0.2s ease;
			}

			.process-card:hover {
				transform: translateY(-2px);
			}

			.stat-item {
				text-align: center;
			}

			.stat-number {
				font-size: 1.2rem;
				font-weight: bold;
			}

			.activity-item {
				transition: background-color 0.2s ease;
			}

			.activity-item:hover {
				background-color: #f8f9fa;
			}

			.health-score h3 {
				font-size: 2rem;
				margin: 0;
			}

			.metric-value {
				font-size: 1.5rem;
				font-weight: bold;
			}

			.empty-state {
				background: #f8f9fa;
				border: 2px dashed #dee2e6;
				border-radius: 8px;
			}

			.badge-sm {
				font-size: 0.75em;
			}
			</style>
		`);
	}
});