// Copyright (c) 2025, Swapnil and contributors
// Template Selector for Universal Sync System

frappe.provide('frappe.ui');

frappe.ui.TemplateSelector = class TemplateSelector {
	constructor(opts) {
		this.wrapper = opts.wrapper;
		this.callback = opts.callback;
		this.show_custom = opts.show_custom !== false; // Default true
		this.templates = {};
		this.make();
	}

	make() {
		this.wrapper.html(`
			<div class="template-selector">
				<div class="template-header mb-3">
					<h5 class="mb-2">${__('Choose a Template')}</h5>
					<p class="text-muted">
						${__('Select a pre-built template to quickly set up your sync process, or create a custom process from scratch.')}
					</p>
				</div>

				<div class="template-categories">
					<ul class="nav nav-pills mb-3" role="tablist">
						<li class="nav-item" role="presentation">
							<button class="nav-link active" data-category="all" type="button">
								${__('All Templates')}
							</button>
						</li>
					</ul>
				</div>

				<div class="template-grid">
					<div class="row">
						<div class="col-12 text-center p-4">
							<i class="fa fa-spinner fa-spin fa-2x text-muted"></i>
							<p class="text-muted mt-2">${__('Loading templates...')}</p>
						</div>
					</div>
				</div>

				${this.show_custom ? `
				<div class="custom-option mt-4">
					<div class="custom-template-card">
						<div class="row align-items-center">
							<div class="col-md-2 text-center">
								<i class="fa fa-cog fa-3x text-secondary"></i>
							</div>
							<div class="col-md-8">
								<h5 class="mb-1">${__('Custom Process')}</h5>
								<p class="text-muted mb-1">${__('Build your own sync process from scratch with full control over steps and field mappings.')}</p>
								<small class="text-muted">
									<i class="fa fa-clock-o"></i> ${__('Setup time')}: 10-15 ${__('minutes')}
								</small>
							</div>
							<div class="col-md-2 text-end">
								<button class="btn btn-secondary create-custom">
									${__('Start Custom')}
								</button>
							</div>
						</div>
					</div>
				</div>
				` : ''}
			</div>
		`);

		this.load_templates();
		this.bind_events();
	}

	load_templates() {
		frappe.call({
			method: 'dev_assistant.dev_assistant.universal_sync.sync_templates.get_templates_by_category_api',
			callback: (r) => {
				if (r.message) {
					this.templates = r.message;
					this.render_categories();
					this.render_templates('all');
				}
			},
			error: () => {
				this.show_error(__('Failed to load templates. Please try again.'));
			}
		});
	}

	render_categories() {
		const categories_nav = this.wrapper.find('.nav-pills');

		// Add category tabs
		Object.keys(this.templates).forEach(category => {
			categories_nav.append(`
				<li class="nav-item" role="presentation">
					<button class="nav-link" data-category="${category}" type="button">
						${__(category)}
					</button>
				</li>
			`);
		});
	}

	render_templates(selected_category = 'all') {
		const template_grid = this.wrapper.find('.template-grid .row');
		let templates_html = '';

		if (selected_category === 'all') {
			// Show all templates
			Object.keys(this.templates).forEach(category => {
				this.templates[category].forEach(item => {
					templates_html += this.create_template_card(item.key, item.template);
				});
			});
		} else {
			// Show templates from selected category
			if (this.templates[selected_category]) {
				this.templates[selected_category].forEach(item => {
					templates_html += this.create_template_card(item.key, item.template);
				});
			}
		}

		if (templates_html === '') {
			templates_html = `
				<div class="col-12 text-center p-4">
					<i class="fa fa-folder-open fa-2x text-muted"></i>
					<p class="text-muted mt-2">${__('No templates found in this category.')}</p>
				</div>
			`;
		}

		template_grid.html(templates_html);
	}

	create_template_card(template_key, template) {
		const steps_html = template.steps.slice(0, 4).map(step =>
			`<li class="step-item">
				<i class="fa fa-arrow-right text-muted me-1"></i>
				${step.doctype_label}
			</li>`
		).join('');

		const more_steps = template.steps.length > 4 ?
			`<li class="step-item text-muted">+${template.steps.length - 4} more steps</li>` : '';

		return `
			<div class="col-lg-6 col-md-6 mb-4">
				<div class="template-card" data-template="${template_key}">
					<div class="card h-100">
						<div class="card-header d-flex align-items-center">
							<div class="template-icon me-3">
								<i class="${template.icon} fa-2x text-primary"></i>
							</div>
							<div class="flex-grow-1">
								<h5 class="card-title mb-1">${template.name}</h5>
								<small class="text-muted">${template.category}</small>
							</div>
						</div>
						<div class="card-body">
							<p class="card-text text-muted mb-3">${template.description}</p>

							<div class="template-steps mb-3">
								<h6 class="small text-muted mb-2">${__('Process Flow')}:</h6>
								<ol class="step-list">
									${steps_html}
									${more_steps}
								</ol>
							</div>

							${template.benefits ? `
							<div class="template-benefits mb-3">
								<h6 class="small text-muted mb-2">${__('Benefits')}:</h6>
								<ul class="benefit-list">
									${template.benefits.slice(0, 2).map(benefit =>
										`<li class="benefit-item small text-success">
											<i class="fa fa-check me-1"></i>${benefit}
										</li>`
									).join('')}
								</ul>
							</div>
							` : ''}
						</div>
						<div class="card-footer d-flex justify-content-between align-items-center">
							<small class="text-muted">
								<i class="fa fa-clock-o"></i> 5-10 ${__('mins setup')}
							</small>
							<div class="template-actions">
								<button class="btn btn-sm btn-outline-primary preview-template me-2"
										data-template="${template_key}">
									${__('Preview')}
								</button>
								<button class="btn btn-sm btn-primary use-template"
										data-template="${template_key}">
									${__('Use Template')}
								</button>
							</div>
						</div>
					</div>
				</div>
			</div>
		`;
	}

	show_template_preview(template_key) {
		frappe.call({
			method: 'dev_assistant.dev_assistant.universal_sync.sync_templates.preview_template_api',
			args: { template_name: template_key },
			callback: (r) => {
				if (r.message) {
					this.render_preview_dialog(r.message);
				}
			}
		});
	}

	render_preview_dialog(preview_data) {
		const template = preview_data.template;
		const validation = preview_data.validation;

		const dialog = new frappe.ui.Dialog({
			title: `${__('Template Preview')}: ${template.name}`,
			size: 'large',
			fields: [
				{
					fieldtype: 'HTML',
					fieldname: 'preview_content'
				}
			],
			primary_action: () => {
				dialog.hide();
				this.use_template(template_key);
			},
			primary_action_label: __('Use This Template')
		});

		const steps_html = template.steps.map((step, index) => `
			<tr>
				<td class="text-center">${step.step_number}</td>
				<td>
					<strong>${step.doctype_label}</strong>
					<br><small class="text-muted">${step.doctype_name}</small>
				</td>
				<td>
					<span class="badge badge-sm ${this.get_condition_badge_class(step.sync_condition)}">
						${step.sync_condition}
					</span>
				</td>
				<td class="text-center">
					${Object.keys(step.field_mappings || {}).length} ${__('fields')}
				</td>
			</tr>
		`).join('');

		const warnings_html = validation.warnings.length > 0 ? `
			<div class="alert alert-warning">
				<h6>${__('Warnings')}:</h6>
				<ul class="mb-0">
					${validation.warnings.map(warning => `<li>${warning}</li>`).join('')}
				</ul>
			</div>
		` : '';

		const errors_html = validation.errors.length > 0 ? `
			<div class="alert alert-danger">
				<h6>${__('Errors')}:</h6>
				<ul class="mb-0">
					${validation.errors.map(error => `<li>${error}</li>`).join('')}
				</ul>
			</div>
		` : '';

		const preview_html = `
			<div class="template-preview">
				<div class="row">
					<div class="col-md-8">
						<h6>${__('Process Flow')}</h6>
						<table class="table table-sm table-bordered">
							<thead>
								<tr>
									<th width="10%">${__('Step')}</th>
									<th width="40%">${__('Document Type')}</th>
									<th width="25%">${__('Sync Condition')}</th>
									<th width="25%">${__('Field Mappings')}</th>
								</tr>
							</thead>
							<tbody>
								${steps_html}
							</tbody>
						</table>
					</div>
					<div class="col-md-4">
						<div class="template-info">
							<h6>${__('Template Information')}</h6>
							<p><strong>${__('Description')}:</strong><br>${template.description}</p>
							<p><strong>${__('Category')}:</strong> ${template.category}</p>
							<p><strong>${__('Steps')}:</strong> ${template.steps.length}</p>
							<p><strong>${__('Estimated Setup Time')}:</strong> ${preview_data.estimated_setup_time}</p>
						</div>

						${template.benefits ? `
						<div class="template-benefits mt-3">
							<h6>${__('Benefits')}</h6>
							<ul class="small">
								${template.benefits.map(benefit => `<li>${benefit}</li>`).join('')}
							</ul>
						</div>
						` : ''}
					</div>
				</div>

				${errors_html}
				${warnings_html}

				${!validation.valid ? `
				<div class="alert alert-info">
					<strong>${__('Note')}:</strong> ${__('This template cannot be used because some required DocTypes are missing from your system. Please contact your system administrator.')}
				</div>
				` : ''}
			</div>
		`;

		dialog.fields_dict.preview_content.$wrapper.html(preview_html);

		// Disable primary action if template is not valid
		if (!validation.valid) {
			dialog.set_primary_action(__('Template Not Available'));
			dialog.get_primary_btn().prop('disabled', true);
		}

		dialog.show();
	}

	use_template(template_key, template_name = null) {
		const template_info = this.get_template_info(template_key);

		frappe.prompt([
			{
				fieldtype: 'Data',
				fieldname: 'chain_name',
				label: __('Process Name'),
				reqd: 1,
				default: template_name || (template_info ? template_info.name : ''),
				description: __('Enter a name for your sync process')
			}
		], (values) => {
			this.create_from_template(template_key, values.chain_name);
		}, __('Create Sync Process'));
	}

	create_from_template(template_key, chain_name) {
		frappe.call({
			method: 'dev_assistant.dev_assistant.universal_sync.sync_templates.create_chain_from_template_api',
			args: {
				template_name: template_key,
				chain_name: chain_name
			},
			callback: (r) => {
				if (r.message && r.message.success) {
					frappe.show_alert({
						message: r.message.message,
						indicator: 'green'
					});

					// Show warnings if any
					if (r.message.warnings && r.message.warnings.length > 0) {
						frappe.msgprint({
							title: __('Template Applied with Warnings'),
							message: r.message.warnings.join('<br>'),
							indicator: 'orange'
						});
					}

					if (this.callback) {
						this.callback({
							success: true,
							chain_name: r.message.chain_name,
							chain_title: r.message.chain_title,
							template_key: template_key
						});
					}
				} else {
					frappe.msgprint({
						title: __('Template Creation Failed'),
						message: r.message?.message || __('Unknown error occurred'),
						indicator: 'red'
					});
				}
			}
		});
	}

	get_template_info(template_key) {
		for (const category in this.templates) {
			const template_item = this.templates[category].find(item => item.key === template_key);
			if (template_item) {
				return template_item.template;
			}
		}
		return null;
	}

	get_condition_badge_class(condition) {
		const classes = {
			'Always': 'badge-success',
			'Status Changes': 'badge-info',
			'Specific Field Changes': 'badge-warning',
			'Manual Trigger': 'badge-secondary'
		};
		return classes[condition] || 'badge-light';
	}

	show_error(message) {
		this.wrapper.find('.template-grid .row').html(`
			<div class="col-12 text-center p-4">
				<i class="fa fa-exclamation-triangle fa-2x text-danger"></i>
				<p class="text-danger mt-2">${message}</p>
			</div>
		`);
	}

	bind_events() {
		// Category navigation
		this.wrapper.on('click', '.nav-link', (e) => {
			const category = $(e.target).data('category');

			// Update active state
			this.wrapper.find('.nav-link').removeClass('active');
			$(e.target).addClass('active');

			// Render templates for selected category
			this.render_templates(category);
		});

		// Use template button
		this.wrapper.on('click', '.use-template', (e) => {
			const template_key = $(e.target).data('template');
			this.use_template(template_key);
		});

		// Preview template button
		this.wrapper.on('click', '.preview-template', (e) => {
			const template_key = $(e.target).data('template');
			this.show_template_preview(template_key);
		});

		// Custom process button
		this.wrapper.on('click', '.create-custom', () => {
			if (this.callback) {
				this.callback({
					success: true,
					template_key: 'custom',
					custom: true
				});
			}
		});

		// Template card hover effects
		this.wrapper.on('mouseenter', '.template-card', function() {
			$(this).find('.card').addClass('border-primary shadow-sm');
		});

		this.wrapper.on('mouseleave', '.template-card', function() {
			$(this).find('.card').removeClass('border-primary shadow-sm');
		});
	}
};

// CSS for template selector
frappe.provide('frappe.ui.template_selector_css');
frappe.ui.template_selector_css = `
<style>
.template-selector {
	font-size: 14px;
}

.template-card .card {
	transition: all 0.2s ease;
	border: 1px solid #dee2e6;
}

.template-card:hover .card {
	transform: translateY(-2px);
}

.template-icon {
	min-width: 50px;
}

.step-list {
	list-style: none;
	padding: 0;
	margin: 0;
	font-size: 12px;
}

.step-item {
	padding: 2px 0;
	color: #6c757d;
}

.benefit-list {
	list-style: none;
	padding: 0;
	margin: 0;
}

.benefit-item {
	padding: 1px 0;
}

.custom-template-card {
	border: 2px dashed #dee2e6;
	border-radius: 8px;
	padding: 20px;
	transition: all 0.2s ease;
}

.custom-template-card:hover {
	border-color: #6c757d;
	background-color: #f8f9fa;
}

.nav-pills .nav-link {
	color: #6c757d;
	background-color: transparent;
	border-radius: 20px;
	padding: 8px 16px;
	margin-right: 8px;
	transition: all 0.2s ease;
}

.nav-pills .nav-link.active {
	background-color: #007bff;
	color: white;
}

.nav-pills .nav-link:hover {
	background-color: #e9ecef;
	color: #495057;
}

.nav-pills .nav-link.active:hover {
	background-color: #0056b3;
	color: white;
}

.template-preview table th {
	background-color: #f8f9fa;
	font-size: 12px;
}

.template-preview table td {
	font-size: 12px;
	vertical-align: middle;
}

.badge-sm {
	font-size: 10px;
	padding: 2px 6px;
}
</style>
`;

// Inject CSS
$(document).ready(function() {
	if (!$('#template-selector-css').length) {
		$('head').append('<div id="template-selector-css">' + frappe.ui.template_selector_css + '</div>');
	}
});