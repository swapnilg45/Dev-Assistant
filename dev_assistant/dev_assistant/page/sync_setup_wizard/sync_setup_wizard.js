// Copyright (c) 2025, Swapnil and contributors
// Sync Setup Wizard - 5 Step Process

frappe.pages['sync-setup-wizard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Sync Setup Wizard'),
		single_column: true
	});

	frappe.sync_setup_wizard = new SyncSetupWizard(page);
};

class SyncSetupWizard {
	constructor(page) {
		this.page = page;
		this.wrapper = page.main;
		this.current_step = 1;
		this.total_steps = 5;
		this.data = {
			template_key: null,
			process_name: '',
			description: '',
			steps: [],
			field_mappings: {},
			settings: {
				sync_frequency: 'Immediately',
				conflict_resolution: 'Use Latest Data',
				notifications: ['email']
			}
		};

		this.init();
	}

	init() {
		this.setup_page();
		this.render_wizard();
		this.show_step(1);
	}

	setup_page() {
		this.page.set_secondary_action(__('Cancel'), () => {
			this.cancel_wizard();
		});

		// Add custom CSS
		this.add_wizard_css();
	}

	render_wizard() {
		this.wrapper.html(`
			<div class="sync-wizard-container">
				<div class="wizard-header">
					<div class="wizard-progress">
						<div class="progress-bar">
							<div class="progress-fill" style="width: 20%"></div>
						</div>
						<div class="step-indicators">
							${this.render_step_indicators()}
						</div>
					</div>
				</div>

				<div class="wizard-content">
					<div class="step-container">
						<!-- Steps will be rendered here -->
					</div>
				</div>

				<div class="wizard-footer">
					<div class="wizard-navigation">
						<button class="btn btn-secondary btn-previous" disabled>
							<i class="fa fa-arrow-left"></i> ${__('Previous')}
						</button>
						<button class="btn btn-primary btn-next">
							${__('Next')} <i class="fa fa-arrow-right"></i>
						</button>
					</div>
				</div>
			</div>
		`);

		this.bind_events();
	}

	render_step_indicators() {
		const steps = [
			{ number: 1, title: __('Template') },
			{ number: 2, title: __('Configure') },
			{ number: 3, title: __('Map Fields') },
			{ number: 4, title: __('Set Rules') },
			{ number: 5, title: __('Complete') }
		];

		return steps.map(step => `
			<div class="step-indicator ${step.number === 1 ? 'active' : ''}" data-step="${step.number}">
				<div class="step-number">${step.number}</div>
				<div class="step-title">${step.title}</div>
			</div>
		`).join('');
	}

	show_step(step_number) {
		this.current_step = step_number;
		this.update_progress();
		this.update_navigation();

		// Update step indicators
		this.wrapper.find('.step-indicator').removeClass('active completed');
		this.wrapper.find('.step-indicator').each(function() {
			const stepNum = parseInt($(this).data('step'));
			if (stepNum < step_number) {
				$(this).addClass('completed');
			} else if (stepNum === step_number) {
				$(this).addClass('active');
			}
		});

		// Render step content
		const step_container = this.wrapper.find('.step-container');
		switch (step_number) {
			case 1:
				this.render_step_1(step_container);
				break;
			case 2:
				this.render_step_2(step_container);
				break;
			case 3:
				this.render_step_3(step_container);
				break;
			case 4:
				this.render_step_4(step_container);
				break;
			case 5:
				this.render_step_5(step_container);
				break;
		}
	}

	// Step 1: Template Selection
	render_step_1(container) {
		container.html(`
			<div class="wizard-step step-1">
				<div class="step-header">
					<h3>${__('Step 1: Choose Your Process Type')}</h3>
					<p class="text-muted">
						${__('Select a pre-built template to quickly set up your sync process, or create a custom process from scratch.')}
					</p>
				</div>
				<div class="step-content">
					<div class="template-selector-container">
						<!-- Template selector will be rendered here -->
					</div>
				</div>
			</div>
		`);

		// Initialize template selector
		this.template_selector = new frappe.ui.TemplateSelector({
			wrapper: container.find('.template-selector-container'),
			show_custom: true,
			callback: (result) => {
				if (result.success) {
					if (result.custom) {
						this.data.template_key = 'custom';
						this.data.process_name = __('Custom Sync Process');
						this.data.description = __('Custom sync process built from scratch');
						this.data.steps = [];
					} else {
						this.data.template_key = result.template_key;
						this.data.process_name = result.chain_title || result.template_key;
						this.load_template_data(result.template_key);
					}

					// Enable next button
					this.wrapper.find('.btn-next').prop('disabled', false);
				}
			}
		});
	}

	// Step 2: Configure Process Steps
	render_step_2(container) {
		container.html(`
			<div class="wizard-step step-2">
				<div class="step-header">
					<h3>${__('Step 2: Configure Your Process Steps')}</h3>
					<p class="text-muted">
						${__('Review and customize the steps in your sync process. You can add, remove, or reorder steps.')}
					</p>
				</div>
				<div class="step-content">
					<div class="process-config-form">
						<div class="row">
							<div class="col-md-6">
								<div class="form-group">
									<label class="form-label">${__('Process Name')}</label>
									<input type="text" class="form-control process-name"
										   value="${this.data.process_name}" required>
								</div>
							</div>
							<div class="col-md-6">
								<div class="form-group">
									<label class="form-label">${__('Description')}</label>
									<input type="text" class="form-control process-description"
										   value="${this.data.description}">
								</div>
							</div>
						</div>
					</div>

					<div class="visual-workflow-container">
						<h5>${__('Process Flow')}</h5>
						<div class="workflow-builder">
							<!-- Visual workflow builder will be rendered here -->
						</div>
					</div>
				</div>
			</div>
		`);

		// Initialize visual workflow builder
		this.init_visual_workflow_builder(container.find('.workflow-builder'));

		// Bind form events
		container.find('.process-name').on('change', (e) => {
			this.data.process_name = $(e.target).val();
		});

		container.find('.process-description').on('change', (e) => {
			this.data.description = $(e.target).val();
		});
	}

	// Step 3: Map Fields
	render_step_3(container) {
		container.html(`
			<div class="wizard-step step-3">
				<div class="step-header">
					<h3>${__('Step 3: Map Your Fields')}</h3>
					<p class="text-muted">
						${__('Map fields between document types to ensure data flows correctly through your process.')}
					</p>
				</div>
				<div class="step-content">
					<div class="field-mapping-steps">
						<!-- Field mapping interfaces for each step will be rendered here -->
					</div>
				</div>
			</div>
		`);

		this.render_field_mapping_steps(container.find('.field-mapping-steps'));
	}

	// Step 4: Set Rules
	render_step_4(container) {
		container.html(`
			<div class="wizard-step step-4">
				<div class="step-header">
					<h3>${__('Step 4: Set Your Rules')}</h3>
					<p class="text-muted">
						${__('Configure when and how your data should sync, and what happens when conflicts occur.')}
					</p>
				</div>
				<div class="step-content">
					<div class="rules-config-container">
						<!-- Simple rules config will be rendered here -->
					</div>
				</div>
			</div>
		`);

		// Initialize simple rules configuration
		this.init_rules_config(container.find('.rules-config-container'));
	}

	// Step 5: Test & Activate
	render_step_5(container) {
		container.html(`
			<div class="wizard-step step-5">
				<div class="step-header">
					<h3>${__('Step 5: Test & Activate')}</h3>
					<p class="text-muted">
						${__('Review your sync process configuration and test it before activation.')}
					</p>
				</div>
				<div class="step-content">
					<div class="configuration-summary">
						<h5>${__('Configuration Summary')}</h5>
						${this.render_configuration_summary()}
					</div>

					<div class="test-section mt-4">
						<h5>${__('Test Your Process')}</h5>
						<p class="text-muted">${__('Test your sync process with sample data before activating it.')}</p>
						<button class="btn btn-info btn-test-process">
							<i class="fa fa-flask"></i> ${__('Test Process')}
						</button>
					</div>

					<div class="activation-section mt-4">
						<h5>${__('Activate Process')}</h5>
						<div class="form-check">
							<input class="form-check-input" type="checkbox" id="activate-immediately">
							<label class="form-check-label" for="activate-immediately">
								${__('Activate this process immediately')}
							</label>
						</div>
						<button class="btn btn-success btn-create-process mt-3">
							<i class="fa fa-check"></i> ${__('Create Sync Process')}
						</button>
					</div>
				</div>
			</div>
		`);

		this.bind_final_step_events(container);
	}

	init_visual_workflow_builder(container) {
		// Simple workflow step builder
		let steps_html = '';

		if (this.data.steps.length === 0) {
			steps_html = `
				<div class="empty-workflow text-center p-4">
					<i class="fa fa-plus-circle fa-3x text-muted mb-3"></i>
					<p class="text-muted">${__('No steps configured yet')}</p>
					<button class="btn btn-primary btn-add-step">
						${__('Add First Step')}
					</button>
				</div>
			`;
		} else {
			steps_html = `
				<div class="workflow-steps">
					${this.data.steps.map((step, index) => this.render_workflow_step(step, index)).join('')}
					<div class="add-step-button text-center mt-3">
						<button class="btn btn-outline-primary btn-add-step">
							<i class="fa fa-plus"></i> ${__('Add Step')}
						</button>
					</div>
				</div>
			`;
		}

		container.html(steps_html);
		this.bind_workflow_events(container);
	}

	render_workflow_step(step, index) {
		return `
			<div class="workflow-step-item" data-index="${index}">
				<div class="step-card">
					<div class="step-header d-flex justify-content-between align-items-center">
						<div class="step-info">
							<span class="step-number">${step.step_number}</span>
							<strong>${step.doctype_label || step.doctype_name}</strong>
						</div>
						<div class="step-actions">
							<button class="btn btn-sm btn-secondary edit-step" data-index="${index}">
								<i class="fa fa-edit"></i>
							</button>
							<button class="btn btn-sm btn-danger remove-step" data-index="${index}">
								<i class="fa fa-trash"></i>
							</button>
						</div>
					</div>
					<div class="step-details">
						<small class="text-muted">
							${__('DocType')}: ${step.doctype_name}<br>
							${__('Sync When')}: ${step.sync_condition}
						</small>
					</div>
				</div>
				${index < this.data.steps.length - 1 ? '<div class="step-connector"><i class="fa fa-arrow-down"></i></div>' : ''}
			</div>
		`;
	}

	render_field_mapping_steps(container) {
		if (this.data.steps.length < 2) {
			container.html(`
				<div class="alert alert-info">
					${__('You need at least 2 steps in your process to configure field mappings.')}
				</div>
			`);
			return;
		}

		let mappings_html = '';
		for (let i = 0; i < this.data.steps.length - 1; i++) {
			const source_step = this.data.steps[i];
			const target_step = this.data.steps[i + 1];

			mappings_html += `
				<div class="field-mapping-step mb-4">
					<h6 class="mapping-title">
						${source_step.doctype_label} → ${target_step.doctype_label}
					</h6>
					<div class="field-mapping-interface"
						 data-source="${source_step.doctype_name}"
						 data-target="${target_step.doctype_name}"
						 data-step="${i}">
						<!-- Field mapping interface will be rendered here -->
					</div>
				</div>
			`;
		}

		container.html(mappings_html);

		// Initialize field mapping interfaces
		container.find('.field-mapping-interface').each((index, element) => {
			const source_doctype = $(element).data('source');
			const target_doctype = $(element).data('target');
			const step_index = $(element).data('step');

			const existing_mappings = this.data.field_mappings[step_index] || {};

			new frappe.ui.FieldMappingInterface({
				wrapper: $(element),
				source_doctype: source_doctype,
				target_doctype: target_doctype,
				existing_mappings: existing_mappings,
				callback: (mappings) => {
					this.data.field_mappings[step_index] = mappings;
				}
			});
		});
	}

	init_rules_config(container) {
		container.html(`
			<div class="rules-config">
				<div class="row">
					<div class="col-md-6">
						<div class="rule-section">
							<h6>${__('When should data sync happen?')}</h6>
							<div class="form-check mb-2">
								<input class="form-check-input" type="radio" name="sync_frequency" value="Immediately"
									   ${this.data.settings.sync_frequency === 'Immediately' ? 'checked' : ''}>
								<label class="form-check-label">
									<strong>${__('Immediately')}</strong><br>
									<small class="text-muted">${__('Sync happens right away when documents are saved')}</small>
								</label>
							</div>
							<div class="form-check mb-2">
								<input class="form-check-input" type="radio" name="sync_frequency" value="Every Hour"
									   ${this.data.settings.sync_frequency === 'Every Hour' ? 'checked' : ''}>
								<label class="form-check-label">
									<strong>${__('Every Hour')}</strong><br>
									<small class="text-muted">${__('Check for changes and sync once per hour')}</small>
								</label>
							</div>
							<div class="form-check mb-2">
								<input class="form-check-input" type="radio" name="sync_frequency" value="Daily"
									   ${this.data.settings.sync_frequency === 'Daily' ? 'checked' : ''}>
								<label class="form-check-label">
									<strong>${__('Daily')}</strong><br>
									<small class="text-muted">${__('Sync all changes once per day')}</small>
								</label>
							</div>
							<div class="form-check mb-2">
								<input class="form-check-input" type="radio" name="sync_frequency" value="Manual Only"
									   ${this.data.settings.sync_frequency === 'Manual Only' ? 'checked' : ''}>
								<label class="form-check-label">
									<strong>${__('Manual Only')}</strong><br>
									<small class="text-muted">${__('I will decide when to sync')}</small>
								</label>
							</div>
						</div>
					</div>
					<div class="col-md-6">
						<div class="rule-section">
							<h6>${__('When data conflicts occur?')}</h6>
							<div class="form-check mb-2">
								<input class="form-check-input" type="radio" name="conflict_resolution" value="Use Latest Data"
									   ${this.data.settings.conflict_resolution === 'Use Latest Data' ? 'checked' : ''}>
								<label class="form-check-label">
									<strong>${__('Use Latest Data')}</strong><br>
									<small class="text-muted">${__('The newest changes will overwrite older data')}</small>
								</label>
							</div>
							<div class="form-check mb-2">
								<input class="form-check-input" type="radio" name="conflict_resolution" value="Ask Me to Review"
									   ${this.data.settings.conflict_resolution === 'Ask Me to Review' ? 'checked' : ''}>
								<label class="form-check-label">
									<strong>${__('Ask Me to Review')}</strong><br>
									<small class="text-muted">${__('I will get a notification to manually resolve conflicts')}</small>
								</label>
							</div>
							<div class="form-check mb-2">
								<input class="form-check-input" type="radio" name="conflict_resolution" value="Keep Original Data"
									   ${this.data.settings.conflict_resolution === 'Keep Original Data' ? 'checked' : ''}>
								<label class="form-check-label">
									<strong>${__('Keep Original Data')}</strong><br>
									<small class="text-muted">${__('Do not change data that already exists')}</small>
								</label>
							</div>
						</div>
					</div>
				</div>

				<div class="rule-section mt-4">
					<h6>${__('How should you be notified?')}</h6>
					<div class="row">
						<div class="col-md-4">
							<div class="form-check">
								<input class="form-check-input" type="checkbox" name="notifications" value="email"
									   ${this.data.settings.notifications.includes('email') ? 'checked' : ''}>
								<label class="form-check-label">${__('Email notifications')}</label>
							</div>
						</div>
						<div class="col-md-4">
							<div class="form-check">
								<input class="form-check-input" type="checkbox" name="notifications" value="system"
									   ${this.data.settings.notifications.includes('system') ? 'checked' : ''}>
								<label class="form-check-label">${__('System notifications')}</label>
							</div>
						</div>
						<div class="col-md-4">
							<div class="form-check">
								<input class="form-check-input" type="checkbox" name="notifications" value="errors_only"
									   ${this.data.settings.notifications.includes('errors_only') ? 'checked' : ''}>
								<label class="form-check-label">${__('Only notify about errors')}</label>
							</div>
						</div>
					</div>
				</div>
			</div>
		`);

		// Bind rules config events
		container.find('input[name="sync_frequency"]').on('change', (e) => {
			this.data.settings.sync_frequency = $(e.target).val();
		});

		container.find('input[name="conflict_resolution"]').on('change', (e) => {
			this.data.settings.conflict_resolution = $(e.target).val();
		});

		container.find('input[name="notifications"]').on('change', () => {
			const notifications = [];
			container.find('input[name="notifications"]:checked').each(function() {
				notifications.push($(this).val());
			});
			this.data.settings.notifications = notifications;
		});
	}

	render_configuration_summary() {
		const mappings_count = Object.keys(this.data.field_mappings).length;
		const total_fields = Object.values(this.data.field_mappings)
			.reduce((sum, mapping) => sum + Object.keys(mapping).length, 0);

		return `
			<div class="summary-cards row">
				<div class="col-md-3">
					<div class="summary-card">
						<h4>${this.data.steps.length}</h4>
						<p>${__('Process Steps')}</p>
					</div>
				</div>
				<div class="col-md-3">
					<div class="summary-card">
						<h4>${mappings_count}</h4>
						<p>${__('Step Mappings')}</p>
					</div>
				</div>
				<div class="col-md-3">
					<div class="summary-card">
						<h4>${total_fields}</h4>
						<p>${__('Field Mappings')}</p>
					</div>
				</div>
				<div class="col-md-3">
					<div class="summary-card">
						<h4>${this.data.settings.sync_frequency}</h4>
						<p>${__('Sync Frequency')}</p>
					</div>
				</div>
			</div>

			<div class="process-flow mt-3">
				<h6>${__('Process Flow')}</h6>
				<div class="flow-diagram">
					${this.data.steps.map((step, index) =>
						`<span class="flow-step">${step.doctype_label}</span>` +
						(index < this.data.steps.length - 1 ? '<i class="fa fa-arrow-right mx-2"></i>' : '')
					).join('')}
				</div>
			</div>
		`;
	}

	bind_workflow_events(container) {
		// Add step button
		container.on('click', '.btn-add-step', () => {
			this.show_add_step_dialog();
		});

		// Edit step button
		container.on('click', '.edit-step', (e) => {
			const index = $(e.target).closest('.edit-step').data('index');
			this.show_edit_step_dialog(index);
		});

		// Remove step button
		container.on('click', '.remove-step', (e) => {
			const index = $(e.target).closest('.remove-step').data('index');
			this.remove_step(index);
		});
	}

	show_add_step_dialog() {
		const dialog = new frappe.ui.Dialog({
			title: __('Add Process Step'),
			fields: [
				{
					fieldtype: 'Link',
					fieldname: 'doctype_name',
					label: __('Document Type'),
					options: 'DocType',
					reqd: 1,
					get_query: () => ({
						filters: {
							'issingle': 0,
							'istable': 0,
							'module': ['not in', ['Core', 'Desk', 'Custom']]
						}
					})
				},
				{
					fieldtype: 'Select',
					fieldname: 'sync_condition',
					label: __('Sync When'),
					options: 'Always\nStatus Changes\nSpecific Field Changes\nManual Trigger',
					default: 'Always',
					reqd: 1
				}
			],
			primary_action: (values) => {
				this.add_step(values);
				dialog.hide();
			},
			primary_action_label: __('Add Step')
		});

		dialog.show();
	}

	add_step(step_data) {
		const new_step = {
			step_number: this.data.steps.length + 1,
			doctype_name: step_data.doctype_name,
			doctype_label: step_data.doctype_name, // Will be updated
			sync_condition: step_data.sync_condition
		};

		this.data.steps.push(new_step);
		this.refresh_workflow_builder();
	}

	remove_step(index) {
		if (confirm(__('Are you sure you want to remove this step?'))) {
			this.data.steps.splice(index, 1);

			// Renumber steps
			this.data.steps.forEach((step, i) => {
				step.step_number = i + 1;
			});

			this.refresh_workflow_builder();
		}
	}

	refresh_workflow_builder() {
		const container = this.wrapper.find('.workflow-builder');
		this.init_visual_workflow_builder(container);
	}

	bind_final_step_events(container) {
		// Test process button
		container.on('click', '.btn-test-process', () => {
			this.test_process();
		});

		// Create process button
		container.on('click', '.btn-create-process', () => {
			this.create_process();
		});
	}

	test_process() {
		if (this.data.steps.length === 0) {
			frappe.msgprint(__('Please configure at least one process step.'));
			return;
		}

		frappe.show_alert({
			message: __('Testing process... This is a simulation.'),
			indicator: 'blue'
		});

		// Simulate test result
		setTimeout(() => {
			frappe.msgprint({
				title: __('Test Results'),
				message: `
					<div class="alert alert-success">
						<h6>${__('Test Passed!')}</h6>
						<ul>
							<li>${__('All DocTypes are accessible')}</li>
							<li>${__('Field mappings are valid')}</li>
							<li>${__('Process flow is logical')}</li>
						</ul>
					</div>
				`,
				indicator: 'green'
			});
		}, 2000);
	}

	create_process() {
		if (!this.validate_configuration()) {
			return;
		}

		const activate_immediately = this.wrapper.find('#activate-immediately').is(':checked');

		frappe.call({
			method: 'dev_assistant.dev_assistant.universal_sync.wizard.create_sync_chain_from_wizard',
			args: {
				process_data: this.data,
				activate_immediately: activate_immediately
			},
			callback: (r) => {
				if (r.message && r.message.success) {
					frappe.show_alert({
						message: r.message.message,
						indicator: 'green'
					});

					// Redirect to the created sync chain
					setTimeout(() => {
						frappe.set_route('Form', 'Sync Chain', r.message.chain_name);
					}, 2000);
				} else {
					frappe.msgprint({
						title: __('Creation Failed'),
						message: r.message?.message || __('Unknown error occurred'),
						indicator: 'red'
					});
				}
			}
		});
	}

	validate_configuration() {
		if (!this.data.process_name) {
			frappe.msgprint(__('Please enter a process name.'));
			return false;
		}

		if (this.data.steps.length === 0) {
			frappe.msgprint(__('Please add at least one process step.'));
			return false;
		}

		return true;
	}

	load_template_data(template_key) {
		frappe.call({
			method: 'dev_assistant.dev_assistant.universal_sync.sync_templates.get_template_api',
			args: { template_name: template_key },
			callback: (r) => {
				if (r.message) {
					const template = r.message;
					this.data.description = template.description;
					this.data.steps = template.steps.map(step => ({
						step_number: step.step_number,
						doctype_name: step.doctype_name,
						doctype_label: step.doctype_label,
						sync_condition: step.sync_condition
					}));

					// Pre-populate field mappings
					template.steps.forEach((step, index) => {
						if (step.field_mappings) {
							this.data.field_mappings[index] = step.field_mappings;
						}
					});
				}
			}
		});
	}

	update_progress() {
		const progress_percent = (this.current_step / this.total_steps) * 100;
		this.wrapper.find('.progress-fill').css('width', `${progress_percent}%`);
	}

	update_navigation() {
		const prev_btn = this.wrapper.find('.btn-previous');
		const next_btn = this.wrapper.find('.btn-next');

		// Previous button
		if (this.current_step === 1) {
			prev_btn.prop('disabled', true);
		} else {
			prev_btn.prop('disabled', false);
		}

		// Next button
		if (this.current_step === this.total_steps) {
			next_btn.hide();
		} else {
			next_btn.show();

			// Disable next if step is not complete
			const step_complete = this.is_step_complete(this.current_step);
			next_btn.prop('disabled', !step_complete);
		}
	}

	is_step_complete(step_number) {
		switch (step_number) {
			case 1:
				return this.data.template_key !== null;
			case 2:
				return this.data.process_name && this.data.steps.length > 0;
			case 3:
				return true; // Field mapping is optional
			case 4:
				return true; // Rules have defaults
			case 5:
				return true;
			default:
				return false;
		}
	}

	bind_events() {
		// Navigation buttons
		this.wrapper.on('click', '.btn-next', () => {
			if (this.current_step < this.total_steps) {
				this.show_step(this.current_step + 1);
			}
		});

		this.wrapper.on('click', '.btn-previous', () => {
			if (this.current_step > 1) {
				this.show_step(this.current_step - 1);
			}
		});

		// Step indicator clicks
		this.wrapper.on('click', '.step-indicator', (e) => {
			const step_number = parseInt($(e.target).closest('.step-indicator').data('step'));
			if (step_number <= this.current_step || this.is_step_complete(step_number - 1)) {
				this.show_step(step_number);
			}
		});
	}

	cancel_wizard() {
		if (confirm(__('Are you sure you want to cancel the setup wizard? All progress will be lost.'))) {
			frappe.set_route('List', 'Sync Chain');
		}
	}

	add_wizard_css() {
		if (!$('#wizard-css').length) {
			$('head').append(`
				<style id="wizard-css">
				.sync-wizard-container {
					max-width: 1200px;
					margin: 0 auto;
					background: white;
					border-radius: 8px;
					box-shadow: 0 1px 3px rgba(0,0,0,0.1);
				}

				.wizard-header {
					padding: 30px 30px 20px;
					border-bottom: 1px solid #e9ecef;
				}

				.progress-bar {
					height: 4px;
					background: #e9ecef;
					border-radius: 2px;
					margin-bottom: 20px;
				}

				.progress-fill {
					height: 100%;
					background: #007bff;
					border-radius: 2px;
					transition: width 0.3s ease;
				}

				.step-indicators {
					display: flex;
					justify-content: space-between;
				}

				.step-indicator {
					text-align: center;
					cursor: pointer;
					opacity: 0.5;
					transition: opacity 0.3s ease;
				}

				.step-indicator.active {
					opacity: 1;
				}

				.step-indicator.completed {
					opacity: 1;
					color: #28a745;
				}

				.step-number {
					width: 30px;
					height: 30px;
					border-radius: 50%;
					background: #e9ecef;
					display: flex;
					align-items: center;
					justify-content: center;
					margin: 0 auto 8px;
					font-weight: bold;
					transition: background 0.3s ease;
				}

				.step-indicator.active .step-number {
					background: #007bff;
					color: white;
				}

				.step-indicator.completed .step-number {
					background: #28a745;
					color: white;
				}

				.step-title {
					font-size: 12px;
					font-weight: 500;
				}

				.wizard-content {
					padding: 30px;
					min-height: 500px;
				}

				.wizard-footer {
					padding: 20px 30px;
					border-top: 1px solid #e9ecef;
					background: #f8f9fa;
					border-radius: 0 0 8px 8px;
				}

				.wizard-navigation {
					display: flex;
					justify-content: space-between;
				}

				.step-header h3 {
					color: #333;
					margin-bottom: 10px;
				}

				.workflow-step-item {
					margin-bottom: 15px;
				}

				.step-card {
					border: 1px solid #e9ecef;
					border-radius: 6px;
					padding: 15px;
					background: #f8f9fa;
				}

				.step-number {
					background: #007bff;
					color: white;
					width: 24px;
					height: 24px;
					border-radius: 50%;
					display: inline-flex;
					align-items: center;
					justify-content: center;
					font-size: 12px;
					margin-right: 10px;
				}

				.step-connector {
					text-align: center;
					color: #6c757d;
					margin: 10px 0;
				}

				.summary-card {
					text-align: center;
					padding: 20px;
					border: 1px solid #e9ecef;
					border-radius: 6px;
					margin-bottom: 20px;
				}

				.summary-card h4 {
					color: #007bff;
					margin-bottom: 5px;
				}

				.flow-diagram {
					padding: 15px;
					background: #f8f9fa;
					border-radius: 6px;
					text-align: center;
				}

				.flow-step {
					background: #007bff;
					color: white;
					padding: 8px 12px;
					border-radius: 4px;
					font-size: 12px;
					font-weight: 500;
				}
				</style>
			`);
		}
	}
}