// Copyright (c) 2025, Swapnil and contributors
// Visual Workflow Builder for Universal Sync System

frappe.provide('frappe.ui');

frappe.ui.VisualWorkflowBuilder = class VisualWorkflowBuilder {
	constructor(opts) {
		this.wrapper = opts.wrapper;
		this.chain_data = opts.chain_data || {};
		this.callback = opts.callback;
		this.steps = opts.steps || [];
		this.is_readonly = opts.readonly || false;
		this.doctypes = [];
		this.make();
	}

	make() {
		this.wrapper.html(`
			<div class="visual-workflow-builder">
				<div class="builder-header d-flex justify-content-between align-items-center mb-3">
					<h6 class="mb-0">${__('Visual Workflow Builder')}</h6>
					<div class="builder-actions">
						${!this.is_readonly ? `
						<button class="btn btn-sm btn-primary add-step-btn">
							<i class="fa fa-plus"></i> ${__('Add Step')}
						</button>
						<button class="btn btn-sm btn-secondary auto-arrange-btn">
							<i class="fa fa-magic"></i> ${__('Auto Arrange')}
						</button>
						` : ''}
					</div>
				</div>

				<div class="builder-content">
					<div class="row">
						${!this.is_readonly ? `
						<div class="col-md-3">
							<div class="doctype-palette">
								<h6 class="text-muted mb-3">${__('Available Document Types')}</h6>
								<div class="doctype-search mb-2">
									<input type="text" class="form-control form-control-sm"
										   placeholder="${__('Search document types...')}"
										   id="doctype-search">
								</div>
								<div class="draggable-doctypes" style="max-height: 400px; overflow-y: auto;">
									<div class="text-center p-3">
										<i class="fa fa-spinner fa-spin"></i><br>
										<small class="text-muted">${__('Loading...')}</small>
									</div>
								</div>
							</div>
						</div>
						` : ''}

						<div class="${this.is_readonly ? 'col-12' : 'col-md-9'}">
							<div class="workflow-canvas">
								<div class="canvas-header d-flex justify-content-between align-items-center mb-2">
									<h6 class="text-muted mb-0">${__('Process Flow')}</h6>
									<div class="canvas-tools">
										<button class="btn btn-sm btn-outline-secondary zoom-out">
											<i class="fa fa-search-minus"></i>
										</button>
										<button class="btn btn-sm btn-outline-secondary zoom-in">
											<i class="fa fa-search-plus"></i>
										</button>
										<button class="btn btn-sm btn-outline-secondary fit-to-screen">
											<i class="fa fa-expand"></i>
										</button>
									</div>
								</div>
								<div class="workflow-canvas-area" style="min-height: 400px; position: relative;">
									<div class="drop-zone">
										${this.steps.length === 0 ? `
										<div class="empty-canvas text-center">
											<i class="fa fa-sitemap fa-3x text-muted mb-3"></i>
											<p class="text-muted">
												${this.is_readonly ?
													__('No workflow steps configured') :
													__('Drag document types here to build your process flow')
												}
											</p>
											${!this.is_readonly ? `
											<button class="btn btn-primary btn-start-building">
												${__('Start Building')}
											</button>
											` : ''}
										</div>
										` : ''}
									</div>
									<svg class="connection-lines" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1;">
										<!-- Connection lines will be drawn here -->
									</svg>
								</div>
							</div>
						</div>
					</div>
				</div>

				<div class="builder-footer mt-3" style="display: ${this.steps.length > 0 ? 'block' : 'none'};">
					<div class="workflow-summary">
						<div class="row">
							<div class="col-md-8">
								<div class="flow-summary">
									<strong>${__('Process Flow')}:</strong>
									<span class="flow-path"></span>
								</div>
							</div>
							<div class="col-md-4 text-end">
								<small class="text-muted">
									${__('Steps')}: <span class="step-count">0</span> |
									${__('Connections')}: <span class="connection-count">0</span>
								</small>
							</div>
						</div>
					</div>
				</div>
			</div>
		`);

		this.load_doctypes();
		this.render_workflow();
		this.bind_events();
		this.add_css();
	}

	load_doctypes() {
		if (this.is_readonly) return;

		frappe.call({
			method: 'dev_assistant.dev_assistant.universal_sync.wizard.get_wizard_doctype_suggestions',
			callback: (r) => {
				if (r.message) {
					this.doctypes = r.message;
					this.render_doctype_palette();
				}
			}
		});
	}

	render_doctype_palette() {
		const palette = this.wrapper.find('.draggable-doctypes');
		let doctypes_html = '';

		this.doctypes.forEach(doctype => {
			const is_used = this.steps.some(step => step.doctype_name === doctype.name);

			doctypes_html += `
				<div class="doctype-item ${is_used ? 'used' : ''}"
					 data-doctype="${doctype.name}"
					 title="${doctype.usage_hint || doctype.description || doctype.name}">
					<div class="doctype-content">
						<div class="doctype-icon">
							<i class="fa ${this.get_doctype_icon(doctype.name)}"></i>
						</div>
						<div class="doctype-info">
							<div class="doctype-name">${doctype.name}</div>
							<div class="doctype-module small text-muted">${doctype.module}</div>
						</div>
					</div>
					${is_used ? '<div class="used-indicator"><i class="fa fa-check"></i></div>' : ''}
				</div>
			`;
		});

		palette.html(doctypes_html);
		this.make_doctypes_draggable();
	}

	make_doctypes_draggable() {
		this.wrapper.find('.doctype-item:not(.used)').draggable({
			helper: 'clone',
			revert: 'invalid',
			containment: this.wrapper,
			cursor: 'move',
			opacity: 0.7,
			start: (event, ui) => {
				ui.helper.css('z-index', 1000);
			}
		});
	}

	render_workflow() {
		const canvas = this.wrapper.find('.drop-zone');

		if (this.steps.length === 0) {
			this.wrapper.find('.builder-footer').hide();
			return;
		}

		// Show footer
		this.wrapper.find('.builder-footer').show();

		// Clear existing content
		canvas.empty();

		// Render steps
		this.steps.forEach((step, index) => {
			this.render_workflow_step(step, index);
		});

		// Make canvas droppable
		this.make_canvas_droppable();

		// Draw connections
		setTimeout(() => this.draw_connections(), 100);

		// Update summary
		this.update_workflow_summary();
	}

	render_workflow_step(step, index) {
		const canvas = this.wrapper.find('.drop-zone');

		// Calculate position (simple grid layout)
		const cols = 3;
		const row = Math.floor(index / cols);
		const col = index % cols;
		const x = 50 + (col * 300);
		const y = 50 + (row * 120);

		const step_html = `
			<div class="workflow-step-node"
				 data-step-index="${index}"
				 data-doctype="${step.doctype_name}"
				 style="position: absolute; left: ${x}px; top: ${y}px; z-index: 2;">
				<div class="step-node">
					<div class="step-header">
						<div class="step-number">${step.step_number}</div>
						<div class="step-title">${step.doctype_label || step.doctype_name}</div>
						${!this.is_readonly ? `
						<div class="step-actions">
							<button class="btn btn-xs btn-secondary edit-step" title="${__('Edit Step')}">
								<i class="fa fa-edit"></i>
							</button>
							<button class="btn btn-xs btn-danger remove-step" title="${__('Remove Step')}">
								<i class="fa fa-trash"></i>
							</button>
						</div>
						` : ''}
					</div>
					<div class="step-body">
						<div class="step-icon">
							<i class="fa ${this.get_doctype_icon(step.doctype_name)} fa-2x"></i>
						</div>
						<div class="step-details">
							<div class="sync-condition">
								<small class="text-muted">${__('Sync')}: ${step.sync_condition}</small>
							</div>
							${step.field_mappings ? `
							<div class="mapping-info">
								<small class="text-success">
									<i class="fa fa-link"></i> ${Object.keys(JSON.parse(step.field_mappings)).length} ${__('mappings')}
								</small>
							</div>
							` : ''}
						</div>
					</div>
				</div>
			</div>
		`;

		canvas.append(step_html);

		// Make step draggable if not readonly
		if (!this.is_readonly) {
			this.wrapper.find(`[data-step-index="${index}"]`).draggable({
				containment: canvas,
				cursor: 'move',
				stop: () => {
					setTimeout(() => this.draw_connections(), 50);
				}
			});
		}
	}

	make_canvas_droppable() {
		if (this.is_readonly) return;

		this.wrapper.find('.workflow-canvas-area').droppable({
			accept: '.doctype-item',
			tolerance: 'pointer',
			drop: (event, ui) => {
				const doctype_name = ui.draggable.data('doctype');
				const drop_position = {
					x: ui.offset.left - $(event.target).offset().left,
					y: ui.offset.top - $(event.target).offset().top
				};
				this.add_step_at_position(doctype_name, drop_position);
			}
		});
	}

	add_step_at_position(doctype_name, position) {
		// Check if DocType is already used
		const existing_step = this.steps.find(step => step.doctype_name === doctype_name);
		if (existing_step) {
			frappe.show_alert({
				message: __('Document type already added to workflow'),
				indicator: 'orange'
			});
			return;
		}

		// Create new step
		const new_step = {
			step_number: this.steps.length + 1,
			doctype_name: doctype_name,
			doctype_label: this.get_doctype_label(doctype_name),
			sync_condition: 'Always'
		};

		this.steps.push(new_step);
		this.render_workflow();
		this.render_doctype_palette(); // Update palette to show used state

		if (this.callback) {
			this.callback(this.steps);
		}

		frappe.show_alert({
			message: __('Step added to workflow'),
			indicator: 'green'
		});
	}

	get_doctype_label(doctype_name) {
		const doctype_info = this.doctypes.find(dt => dt.name === doctype_name);
		return doctype_info ? doctype_info.name : doctype_name;
	}

	get_doctype_icon(doctype_name) {
		const icon_map = {
			'Lead': 'fa-user-plus',
			'Customer': 'fa-users',
			'Opportunity': 'fa-handshake-o',
			'Quotation': 'fa-file-text-o',
			'Sales Order': 'fa-shopping-cart',
			'Purchase Order': 'fa-shopping-bag',
			'Sales Invoice': 'fa-file-invoice',
			'Purchase Invoice': 'fa-file-invoice-dollar',
			'Employee': 'fa-user',
			'Job Applicant': 'fa-user-circle',
			'Project': 'fa-project-diagram',
			'Task': 'fa-tasks',
			'Item': 'fa-cube',
			'Stock Entry': 'fa-boxes',
			'Work Order': 'fa-industry',
			'Timesheet': 'fa-clock-o'
		};

		return icon_map[doctype_name] || 'fa-file-text';
	}

	draw_connections() {
		const svg = this.wrapper.find('.connection-lines');
		svg.empty();

		if (this.steps.length < 2) return;

		// Draw connections between sequential steps
		for (let i = 0; i < this.steps.length - 1; i++) {
			const source_node = this.wrapper.find(`[data-step-index="${i}"] .step-node`);
			const target_node = this.wrapper.find(`[data-step-index="${i + 1}"] .step-node`);

			if (source_node.length && target_node.length) {
				this.draw_connection_line(svg[0], source_node[0], target_node[0]);
			}
		}
	}

	draw_connection_line(svg, source_element, target_element) {
		const canvas_rect = this.wrapper.find('.workflow-canvas-area')[0].getBoundingClientRect();
		const source_rect = source_element.getBoundingClientRect();
		const target_rect = target_element.getBoundingClientRect();

		// Calculate connection points
		const source_x = source_rect.right - canvas_rect.left;
		const source_y = source_rect.top + (source_rect.height / 2) - canvas_rect.top;
		const target_x = target_rect.left - canvas_rect.left;
		const target_y = target_rect.top + (target_rect.height / 2) - canvas_rect.top;

		// Create SVG path
		const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
		const control_x = source_x + (target_x - source_x) / 2;

		const path_data = `M ${source_x} ${source_y} Q ${control_x} ${source_y} ${control_x} ${(source_y + target_y) / 2} Q ${control_x} ${target_y} ${target_x} ${target_y}`;

		path.setAttribute('d', path_data);
		path.setAttribute('stroke', '#007bff');
		path.setAttribute('stroke-width', '2');
		path.setAttribute('fill', 'none');
		path.setAttribute('marker-end', 'url(#arrowhead)');

		// Add arrow marker
		const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
		const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
		marker.setAttribute('id', 'arrowhead');
		marker.setAttribute('markerWidth', '10');
		marker.setAttribute('markerHeight', '7');
		marker.setAttribute('refX', '9');
		marker.setAttribute('refY', '3.5');
		marker.setAttribute('orient', 'auto');

		const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
		polygon.setAttribute('points', '0 0, 10 3.5, 0 7');
		polygon.setAttribute('fill', '#007bff');

		marker.appendChild(polygon);
		defs.appendChild(marker);
		svg.appendChild(defs);
		svg.appendChild(path);
	}

	update_workflow_summary() {
		// Update step count
		this.wrapper.find('.step-count').text(this.steps.length);

		// Update connection count
		const connections = Math.max(0, this.steps.length - 1);
		this.wrapper.find('.connection-count').text(connections);

		// Update flow path
		const flow_path = this.steps.map(step => step.doctype_label || step.doctype_name).join(' → ');
		this.wrapper.find('.flow-path').text(flow_path);
	}

	show_step_edit_dialog(step_index) {
		const step = this.steps[step_index];

		const dialog = new frappe.ui.Dialog({
			title: __('Edit Step: {0}', [step.doctype_name]),
			fields: [
				{
					fieldtype: 'Data',
					fieldname: 'doctype_label',
					label: __('Display Name'),
					default: step.doctype_label
				},
				{
					fieldtype: 'Select',
					fieldname: 'sync_condition',
					label: __('Sync When'),
					options: 'Always\nStatus Changes\nSpecific Field Changes\nManual Trigger',
					default: step.sync_condition,
					reqd: 1
				},
				{
					fieldtype: 'Section Break'
				},
				{
					fieldtype: 'HTML',
					fieldname: 'field_mapping_info',
					options: `<p class="text-muted">${__('Field mappings can be configured in the next step of the wizard.')}</p>`
				}
			],
			primary_action: (values) => {
				this.update_step(step_index, values);
				dialog.hide();
			},
			primary_action_label: __('Update Step')
		});

		dialog.show();
	}

	update_step(step_index, values) {
		this.steps[step_index].doctype_label = values.doctype_label;
		this.steps[step_index].sync_condition = values.sync_condition;

		this.render_workflow();

		if (this.callback) {
			this.callback(this.steps);
		}

		frappe.show_alert({
			message: __('Step updated'),
			indicator: 'green'
		});
	}

	remove_step(step_index) {
		if (confirm(__('Are you sure you want to remove this step?'))) {
			this.steps.splice(step_index, 1);

			// Renumber remaining steps
			this.steps.forEach((step, index) => {
				step.step_number = index + 1;
			});

			this.render_workflow();
			this.render_doctype_palette(); // Update palette

			if (this.callback) {
				this.callback(this.steps);
			}

			frappe.show_alert({
				message: __('Step removed'),
				indicator: 'green'
			});
		}
	}

	auto_arrange_steps() {
		// Simple auto-arrangement in a flow layout
		this.steps.forEach((step, index) => {
			const step_node = this.wrapper.find(`[data-step-index="${index}"]`);
			const x = 50 + (index * 250);
			const y = 100;

			step_node.css({
				left: `${x}px`,
				top: `${y}px`
			});
		});

		setTimeout(() => this.draw_connections(), 100);

		frappe.show_alert({
			message: __('Steps auto-arranged'),
			indicator: 'green'
		});
	}

	bind_events() {
		// Add step button
		this.wrapper.on('click', '.add-step-btn, .btn-start-building', () => {
			this.show_add_step_dialog();
		});

		// Auto arrange button
		this.wrapper.on('click', '.auto-arrange-btn', () => {
			this.auto_arrange_steps();
		});

		// Edit step
		this.wrapper.on('click', '.edit-step', (e) => {
			const step_index = parseInt($(e.target).closest('.workflow-step-node').data('step-index'));
			this.show_step_edit_dialog(step_index);
		});

		// Remove step
		this.wrapper.on('click', '.remove-step', (e) => {
			const step_index = parseInt($(e.target).closest('.workflow-step-node').data('step-index'));
			this.remove_step(step_index);
		});

		// DocType search
		this.wrapper.on('keyup', '#doctype-search', (e) => {
			this.filter_doctypes($(e.target).val());
		});

		// Canvas zoom
		this.wrapper.on('click', '.zoom-in', () => this.zoom_canvas(1.2));
		this.wrapper.on('click', '.zoom-out', () => this.zoom_canvas(0.8));
		this.wrapper.on('click', '.fit-to-screen', () => this.fit_canvas_to_screen());

		// Canvas resize
		$(window).on('resize', () => {
			setTimeout(() => this.draw_connections(), 100);
		});
	}

	show_add_step_dialog() {
		const used_doctypes = this.steps.map(step => step.doctype_name);
		const available_doctypes = this.doctypes.filter(dt => !used_doctypes.includes(dt.name));

		if (available_doctypes.length === 0) {
			frappe.msgprint(__('All available document types are already in use.'));
			return;
		}

		const dialog = new frappe.ui.Dialog({
			title: __('Add Process Step'),
			fields: [
				{
					fieldtype: 'Autocomplete',
					fieldname: 'doctype_name',
					label: __('Document Type'),
					options: available_doctypes.map(dt => dt.name),
					reqd: 1
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
			step_number: this.steps.length + 1,
			doctype_name: step_data.doctype_name,
			doctype_label: this.get_doctype_label(step_data.doctype_name),
			sync_condition: step_data.sync_condition
		};

		this.steps.push(new_step);
		this.render_workflow();
		this.render_doctype_palette();

		if (this.callback) {
			this.callback(this.steps);
		}

		frappe.show_alert({
			message: __('Step added to workflow'),
			indicator: 'green'
		});
	}

	filter_doctypes(search_term) {
		const doctype_items = this.wrapper.find('.doctype-item');

		doctype_items.each(function() {
			const doctype_name = $(this).data('doctype').toLowerCase();
			if (doctype_name.includes(search_term.toLowerCase()) || search_term === '') {
				$(this).show();
			} else {
				$(this).hide();
			}
		});
	}

	zoom_canvas(factor) {
		// Simple zoom implementation
		const canvas = this.wrapper.find('.workflow-canvas-area');
		let current_scale = parseFloat(canvas.data('scale') || 1);
		current_scale *= factor;
		current_scale = Math.max(0.5, Math.min(2, current_scale)); // Limit zoom range

		canvas.css('transform', `scale(${current_scale})`);
		canvas.data('scale', current_scale);

		setTimeout(() => this.draw_connections(), 100);
	}

	fit_canvas_to_screen() {
		const canvas = this.wrapper.find('.workflow-canvas-area');
		canvas.css('transform', 'scale(1)');
		canvas.data('scale', 1);
		setTimeout(() => this.draw_connections(), 100);
	}

	get_steps() {
		return this.steps;
	}

	set_steps(steps) {
		this.steps = steps || [];
		this.render_workflow();
		if (!this.is_readonly) {
			this.render_doctype_palette();
		}
	}

	add_css() {
		if (!$('#visual-workflow-css').length) {
			$('head').append(`
				<style id="visual-workflow-css">
				.visual-workflow-builder {
					border: 1px solid #e9ecef;
					border-radius: 6px;
					background: #f8f9fa;
				}

				.builder-header, .builder-footer {
					padding: 15px 20px;
					background: white;
				}

				.builder-header {
					border-bottom: 1px solid #e9ecef;
					border-radius: 6px 6px 0 0;
				}

				.builder-footer {
					border-top: 1px solid #e9ecef;
					border-radius: 0 0 6px 6px;
				}

				.builder-content {
					padding: 20px;
				}

				.doctype-palette {
					background: white;
					border: 1px solid #e9ecef;
					border-radius: 4px;
					padding: 15px;
					height: 500px;
				}

				.doctype-item {
					border: 1px solid #e9ecef;
					border-radius: 4px;
					padding: 10px;
					margin-bottom: 8px;
					cursor: grab;
					transition: all 0.2s ease;
					background: white;
					position: relative;
				}

				.doctype-item:hover {
					border-color: #007bff;
					box-shadow: 0 1px 3px rgba(0,123,255,0.1);
				}

				.doctype-item.used {
					opacity: 0.5;
					cursor: not-allowed;
				}

				.doctype-item.used .used-indicator {
					position: absolute;
					top: 5px;
					right: 5px;
					color: #28a745;
				}

				.doctype-content {
					display: flex;
					align-items: center;
				}

				.doctype-icon {
					margin-right: 10px;
					color: #6c757d;
					min-width: 20px;
				}

				.doctype-name {
					font-weight: 500;
					font-size: 13px;
				}

				.doctype-module {
					font-size: 11px;
				}

				.workflow-canvas {
					background: white;
					border: 1px solid #e9ecef;
					border-radius: 4px;
					min-height: 500px;
				}

				.canvas-header {
					padding: 10px 15px;
					border-bottom: 1px solid #e9ecef;
					background: #f8f9fa;
				}

				.workflow-canvas-area {
					position: relative;
					background-image:
						linear-gradient(90deg, #f0f0f0 1px, transparent 1px),
						linear-gradient(180deg, #f0f0f0 1px, transparent 1px);
					background-size: 20px 20px;
				}

				.drop-zone {
					width: 100%;
					height: 100%;
					min-height: 400px;
					position: relative;
				}

				.empty-canvas {
					position: absolute;
					top: 50%;
					left: 50%;
					transform: translate(-50%, -50%);
				}

				.workflow-step-node {
					position: absolute;
					z-index: 2;
				}

				.step-node {
					width: 200px;
					background: white;
					border: 2px solid #007bff;
					border-radius: 8px;
					box-shadow: 0 2px 8px rgba(0,0,0,0.1);
					transition: all 0.2s ease;
					cursor: grab;
				}

				.step-node:hover {
					box-shadow: 0 4px 12px rgba(0,0,0,0.15);
					transform: translateY(-2px);
				}

				.step-header {
					background: #007bff;
					color: white;
					padding: 8px 12px;
					border-radius: 6px 6px 0 0;
					display: flex;
					justify-content: space-between;
					align-items: center;
				}

				.step-number {
					background: white;
					color: #007bff;
					width: 20px;
					height: 20px;
					border-radius: 50%;
					display: flex;
					align-items: center;
					justify-content: center;
					font-size: 11px;
					font-weight: bold;
				}

				.step-title {
					font-weight: 500;
					font-size: 12px;
					margin-left: 8px;
					flex: 1;
					text-overflow: ellipsis;
					overflow: hidden;
					white-space: nowrap;
				}

				.step-actions {
					display: none;
				}

				.step-node:hover .step-actions {
					display: flex;
					gap: 4px;
				}

				.step-body {
					padding: 12px;
					display: flex;
					align-items: center;
				}

				.step-icon {
					margin-right: 12px;
					color: #007bff;
				}

				.step-details {
					flex: 1;
					font-size: 11px;
				}

				.sync-condition {
					margin-bottom: 4px;
				}

				.mapping-info {
					margin-top: 4px;
				}

				.connection-lines {
					pointer-events: none;
					z-index: 1;
				}

				.workflow-summary {
					background: #e3f2fd;
					padding: 15px;
					border-radius: 4px;
				}

				.flow-summary {
					font-size: 13px;
				}

				.flow-path {
					color: #007bff;
					font-family: monospace;
					background: white;
					padding: 4px 8px;
					border-radius: 4px;
					margin-left: 8px;
				}
				</style>
			`);
		}
	}
};