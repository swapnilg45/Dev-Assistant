// Copyright (c) 2025, Swapnil and contributors
// Field Mapping Interface for Universal Sync System

frappe.provide('frappe.ui');

frappe.ui.FieldMappingInterface = class FieldMappingInterface {
	constructor(opts) {
		this.wrapper = opts.wrapper;
		this.source_doctype = opts.source_doctype;
		this.target_doctype = opts.target_doctype;
		this.callback = opts.callback;
		this.mappings = opts.existing_mappings || {};
		this.suggestions = [];
		this.source_fields = [];
		this.target_fields = [];
		this.make();
	}

	make() {
		this.wrapper.html(`
			<div class="field-mapping-interface">
				<div class="mapping-header d-flex justify-content-between align-items-center mb-3">
					<h5 class="mb-0">${__('Map Fields')}: ${this.source_doctype} → ${this.target_doctype}</h5>
					<div class="mapping-actions">
						<button class="btn btn-sm btn-primary auto-map-btn me-2">
							<i class="fa fa-magic"></i> ${__('Auto-Map Similar Fields')}
						</button>
						<button class="btn btn-sm btn-secondary preview-btn">
							<i class="fa fa-eye"></i> ${__('Preview')}
						</button>
					</div>
				</div>

				<div class="mapping-container row">
					<div class="col-md-5">
						<div class="source-fields-panel">
							<h6 class="text-muted">${__('From')}: ${this.source_doctype}</h6>
							<div class="field-search mb-2">
								<input type="text" class="form-control form-control-sm source-search"
									   placeholder="${__('Search source fields...')}">
							</div>
							<div class="field-list source-list" style="max-height: 400px; overflow-y: auto;">
								<div class="text-center text-muted p-3">
									<i class="fa fa-spinner fa-spin"></i> ${__('Loading fields...')}
								</div>
							</div>
						</div>
					</div>

					<div class="col-md-2">
						<div class="mapping-area text-center" style="height: 400px; position: relative;">
							<div class="mapping-lines"></div>
							<div class="d-flex flex-column justify-content-center h-100">
								<i class="fa fa-arrows-h fa-2x text-muted"></i>
								<small class="text-muted mt-2">${__('Drag to map')}</small>
							</div>
						</div>
					</div>

					<div class="col-md-5">
						<div class="target-fields-panel">
							<h6 class="text-muted">${__('To')}: ${this.target_doctype}</h6>
							<div class="field-search mb-2">
								<input type="text" class="form-control form-control-sm target-search"
									   placeholder="${__('Search target fields...')}">
							</div>
							<div class="field-list target-list" style="max-height: 400px; overflow-y: auto;">
								<div class="text-center text-muted p-3">
									<i class="fa fa-spinner fa-spin"></i> ${__('Loading fields...')}
								</div>
							</div>
						</div>
					</div>
				</div>

				<div class="mapping-preview mt-3">
					<h6>${__('Current Mappings')}</h6>
					<div class="mapping-list">
						<div class="text-muted">${__('No mappings yet. Use drag & drop or auto-map to create mappings.')}</div>
					</div>
				</div>

				<div class="mapping-suggestions mt-3" style="display: none;">
					<h6 class="text-success">${__('Smart Suggestions')}</h6>
					<div class="suggestions-list"></div>
				</div>
			</div>
		`);

		this.load_fields();
		this.bind_events();
	}

	load_fields() {
		// Load source fields
		frappe.call({
			method: 'dev_assistant.dev_assistant.universal_sync.field_mapper.get_mappable_fields',
			args: { doctype: this.source_doctype },
			callback: (r) => {
				if (r.message) {
					this.source_fields = r.message;
					this.render_source_fields(r.message);
				}
			}
		});

		// Load target fields
		frappe.call({
			method: 'dev_assistant.dev_assistant.universal_sync.field_mapper.get_mappable_fields',
			args: { doctype: this.target_doctype },
			callback: (r) => {
				if (r.message) {
					this.target_fields = r.message;
					this.render_target_fields(r.message);
				}
			}
		});

		// Load auto-mapping suggestions
		this.load_suggestions();
	}

	render_source_fields(fields) {
		const source_list = this.wrapper.find('.source-list');
		let fields_html = '';

		fields.forEach(field => {
			const is_mapped = this.mappings.hasOwnProperty(field.fieldname);
			const confidence_class = this.get_confidence_class(field.fieldname);

			fields_html += `
				<div class="field-item source-field ${confidence_class} ${is_mapped ? 'mapped' : ''}"
					 data-fieldname="${field.fieldname}"
					 data-fieldtype="${field.fieldtype}"
					 data-label="${field.label}"
					 title="${field.description || field.label}">
					<div class="field-content d-flex justify-content-between align-items-center">
						<div class="field-info">
							<div class="field-label fw-bold">${field.label}</div>
							<div class="field-name text-muted small">${field.fieldname}</div>
							<span class="badge badge-sm badge-secondary">${field.fieldtype}</span>
							${field.reqd ? '<span class="badge badge-sm badge-danger">Required</span>' : ''}
						</div>
						<div class="field-actions">
							<i class="fa fa-grip-vertical text-muted drag-handle"></i>
						</div>
					</div>
				</div>
			`;
		});

		source_list.html(fields_html);
		this.make_source_draggable();
	}

	render_target_fields(fields) {
		const target_list = this.wrapper.find('.target-list');
		let fields_html = '';

		fields.forEach(field => {
			const is_mapped = Object.values(this.mappings).includes(field.fieldname);
			const confidence_class = this.get_target_confidence_class(field.fieldname);

			fields_html += `
				<div class="field-item target-field ${confidence_class} ${is_mapped ? 'mapped' : ''}"
					 data-fieldname="${field.fieldname}"
					 data-fieldtype="${field.fieldtype}"
					 data-label="${field.label}"
					 title="${field.description || field.label}">
					<div class="field-content d-flex justify-content-between align-items-center">
						<div class="field-info">
							<div class="field-label fw-bold">${field.label}</div>
							<div class="field-name text-muted small">${field.fieldname}</div>
							<span class="badge badge-sm badge-secondary">${field.fieldtype}</span>
							${field.reqd ? '<span class="badge badge-sm badge-danger">Required</span>' : ''}
						</div>
						<div class="field-actions">
							<i class="fa fa-bullseye text-muted drop-target"></i>
						</div>
					</div>
				</div>
			`;
		});

		target_list.html(fields_html);
		this.make_target_droppable();
	}

	make_source_draggable() {
		if (typeof $ !== 'undefined' && $.fn.draggable) {
			this.wrapper.find('.source-field').draggable({
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
	}

	make_target_droppable() {
		if (typeof $ !== 'undefined' && $.fn.droppable) {
			this.wrapper.find('.target-field').droppable({
				accept: '.source-field',
				hoverClass: 'drop-hover',
				tolerance: 'pointer',
				drop: (event, ui) => {
					const source_field = ui.draggable.data('fieldname');
					const target_field = $(event.target).closest('.target-field').data('fieldname');
					this.add_mapping(source_field, target_field);
				}
			});
		}
	}

	load_suggestions() {
		frappe.call({
			method: 'dev_assistant.dev_assistant.universal_sync.field_mapper.get_field_mapping_suggestions',
			args: {
				source_doctype: this.source_doctype,
				target_doctype: this.target_doctype
			},
			callback: (r) => {
				if (r.message) {
					this.suggestions = r.message;
					this.show_suggestions();
					this.highlight_suggested_fields();
				}
			}
		});
	}

	show_suggestions() {
		if (this.suggestions.length === 0) return;

		const suggestions_list = this.wrapper.find('.suggestions-list');
		const suggestions_section = this.wrapper.find('.mapping-suggestions');
		let suggestions_html = '';

		this.suggestions.slice(0, 5).forEach(suggestion => {
			if (suggestion.target_suggestions.length > 0) {
				const best_match = suggestion.target_suggestions[0];
				const confidence_percent = Math.round(suggestion.confidence * 100);

				suggestions_html += `
					<div class="suggestion-item d-flex justify-content-between align-items-center p-2 mb-2 border rounded">
						<div class="suggestion-info">
							<strong>${suggestion.source_field.label}</strong>
							<i class="fa fa-arrow-right mx-2"></i>
							<strong>${best_match.field.label}</strong>
							<div class="small text-muted">
								${suggestion.source_field.fieldname} → ${best_match.field.fieldname}
								<span class="badge badge-success ms-2">${confidence_percent}% match</span>
							</div>
						</div>
						<button class="btn btn-sm btn-primary apply-suggestion"
								data-source="${suggestion.source_field.fieldname}"
								data-target="${best_match.field.fieldname}">
							${__('Apply')}
						</button>
					</div>
				`;
			}
		});

		suggestions_list.html(suggestions_html);
		suggestions_section.show();
	}

	highlight_suggested_fields() {
		this.suggestions.forEach(suggestion => {
			if (suggestion.confidence > 0.8) {
				const source_elem = this.wrapper.find(`[data-fieldname="${suggestion.source_field.fieldname}"]`);
				source_elem.addClass('high-confidence-suggestion');

				if (suggestion.target_suggestions.length > 0) {
					const target_elem = this.wrapper.find(`[data-fieldname="${suggestion.target_suggestions[0].field.fieldname}"]`);
					target_elem.addClass('high-confidence-suggestion');
				}
			}
		});
	}

	get_confidence_class(fieldname) {
		const suggestion = this.suggestions.find(s => s.source_field.fieldname === fieldname);
		if (!suggestion) return '';

		if (suggestion.confidence > 0.9) return 'confidence-high';
		if (suggestion.confidence > 0.7) return 'confidence-medium';
		return 'confidence-low';
	}

	get_target_confidence_class(fieldname) {
		for (const suggestion of this.suggestions) {
			const match = suggestion.target_suggestions.find(ts => ts.field.fieldname === fieldname);
			if (match) {
				if (match.confidence > 0.9) return 'confidence-high';
				if (match.confidence > 0.7) return 'confidence-medium';
				return 'confidence-low';
			}
		}
		return '';
	}

	auto_map_fields() {
		frappe.call({
			method: 'dev_assistant.dev_assistant.universal_sync.field_mapper.auto_map_fields',
			args: {
				source_doctype: this.source_doctype,
				target_doctype: this.target_doctype,
				confidence_threshold: 0.8
			},
			callback: (r) => {
				if (r.message) {
					Object.assign(this.mappings, r.message);
					this.update_mapping_preview();
					this.update_field_states();

					frappe.show_alert({
						message: `${Object.keys(r.message).length} ${__('fields auto-mapped')}`,
						indicator: 'green'
					});

					if (this.callback) {
						this.callback(this.mappings);
					}
				}
			}
		});
	}

	add_mapping(source_field, target_field) {
		// Remove existing mapping for this source field
		const existing_target = this.mappings[source_field];
		if (existing_target) {
			delete this.mappings[source_field];
		}

		// Add new mapping
		this.mappings[source_field] = target_field;

		this.update_mapping_preview();
		this.update_field_states();
		this.draw_connection_line(source_field, target_field);

		if (this.callback) {
			this.callback(this.mappings);
		}

		frappe.show_alert({
			message: `${__('Mapped')}: ${source_field} → ${target_field}`,
			indicator: 'green'
		});
	}

	remove_mapping(source_field) {
		if (this.mappings[source_field]) {
			delete this.mappings[source_field];
			this.update_mapping_preview();
			this.update_field_states();

			if (this.callback) {
				this.callback(this.mappings);
			}
		}
	}

	update_mapping_preview() {
		const mapping_list = this.wrapper.find('.mapping-list');

		if (Object.keys(this.mappings).length === 0) {
			mapping_list.html('<div class="text-muted">' + __('No mappings yet. Use drag & drop or auto-map to create mappings.') + '</div>');
			return;
		}

		let mappings_html = '<div class="row">';

		Object.entries(this.mappings).forEach(([source, target]) => {
			const source_field = this.source_fields.find(f => f.fieldname === source);
			const target_field = this.target_fields.find(f => f.fieldname === target);

			mappings_html += `
				<div class="col-md-6 mb-2">
					<div class="mapping-item p-2 border rounded d-flex justify-content-between align-items-center">
						<div class="mapping-content">
							<div class="fw-bold">${source_field?.label || source}</div>
							<div class="text-muted small">
								<i class="fa fa-arrow-right mx-1"></i>
								${target_field?.label || target}
							</div>
						</div>
						<button class="btn btn-sm btn-link text-danger remove-mapping"
								data-source="${source}" title="${__('Remove mapping')}">
							<i class="fa fa-times"></i>
						</button>
					</div>
				</div>
			`;
		});

		mappings_html += '</div>';
		mapping_list.html(mappings_html);
	}

	update_field_states() {
		// Update source field states
		this.wrapper.find('.source-field').removeClass('mapped');
		Object.keys(this.mappings).forEach(source_field => {
			this.wrapper.find(`[data-fieldname="${source_field}"]`).addClass('mapped');
		});

		// Update target field states
		this.wrapper.find('.target-field').removeClass('mapped');
		Object.values(this.mappings).forEach(target_field => {
			this.wrapper.find(`[data-fieldname="${target_field}"]`).addClass('mapped');
		});
	}

	draw_connection_line(source_field, target_field) {
		// Visual connection lines could be implemented here
		// For now, we'll rely on the mapping preview list
	}

	show_preview() {
		frappe.call({
			method: 'dev_assistant.dev_assistant.universal_sync.field_mapper.get_mapping_preview',
			args: {
				source_doctype: this.source_doctype,
				target_doctype: this.target_doctype,
				field_mappings: this.mappings
			},
			callback: (r) => {
				if (r.message && !r.message.error) {
					this.show_preview_dialog(r.message);
				} else {
					frappe.msgprint({
						title: __('Preview Not Available'),
						message: r.message?.error || __('No sample data available'),
						indicator: 'orange'
					});
				}
			}
		});
	}

	show_preview_dialog(preview_data) {
		const dialog = new frappe.ui.Dialog({
			title: __('Field Mapping Preview'),
			size: 'large',
			fields: [
				{
					fieldtype: 'HTML',
					fieldname: 'preview_content'
				}
			]
		});

		let preview_html = `
			<div class="mapping-preview-content">
				<div class="alert alert-info">
					<strong>${__('Sample Document')}:</strong> ${preview_data.sample_doc}
				</div>
				<table class="table table-bordered">
					<thead>
						<tr>
							<th>${__('Source Field')}</th>
							<th>${__('Target Field')}</th>
							<th>${__('Sample Value')}</th>
						</tr>
					</thead>
					<tbody>
		`;

		preview_data.preview_data.forEach(item => {
			preview_html += `
				<tr>
					<td><code>${item.source_field}</code></td>
					<td><code>${item.target_field}</code></td>
					<td>${item.formatted_value || '<em>Empty</em>'}</td>
				</tr>
			`;
		});

		preview_html += `
					</tbody>
				</table>
			</div>
		`;

		dialog.fields_dict.preview_content.$wrapper.html(preview_html);
		dialog.show();
	}

	bind_events() {
		// Auto-map button
		this.wrapper.on('click', '.auto-map-btn', () => {
			this.auto_map_fields();
		});

		// Preview button
		this.wrapper.on('click', '.preview-btn', () => {
			this.show_preview();
		});

		// Remove mapping button
		this.wrapper.on('click', '.remove-mapping', (e) => {
			const source_field = $(e.target).closest('.remove-mapping').data('source');
			this.remove_mapping(source_field);
		});

		// Apply suggestion button
		this.wrapper.on('click', '.apply-suggestion', (e) => {
			const source_field = $(e.target).data('source');
			const target_field = $(e.target).data('target');
			this.add_mapping(source_field, target_field);
		});

		// Search functionality
		this.wrapper.on('keyup', '.source-search', (e) => {
			this.filter_fields('source', $(e.target).val());
		});

		this.wrapper.on('keyup', '.target-search', (e) => {
			this.filter_fields('target', $(e.target).val());
		});

		// Field click to show details
		this.wrapper.on('click', '.field-item', (e) => {
			const field_elem = $(e.target).closest('.field-item');
			this.show_field_details(field_elem);
		});
	}

	filter_fields(type, search_term) {
		const field_items = this.wrapper.find(`.${type}-field`);

		field_items.each(function() {
			const field = $(this);
			const fieldname = field.data('fieldname').toLowerCase();
			const label = field.data('label').toLowerCase();

			if (fieldname.includes(search_term.toLowerCase()) ||
				label.includes(search_term.toLowerCase())) {
				field.show();
			} else {
				field.hide();
			}
		});
	}

	show_field_details(field_elem) {
		const fieldname = field_elem.data('fieldname');
		const fieldtype = field_elem.data('fieldtype');
		const label = field_elem.data('label');

		frappe.show_alert({
			message: `<strong>${label}</strong><br>Field: ${fieldname}<br>Type: ${fieldtype}`,
			indicator: 'blue'
		}, 5);
	}

	get_mappings() {
		return this.mappings;
	}

	set_mappings(mappings) {
		this.mappings = mappings;
		this.update_mapping_preview();
		this.update_field_states();
	}
};

// CSS for field mapping interface
frappe.provide('frappe.ui.field_mapping_css');
frappe.ui.field_mapping_css = `
<style>
.field-mapping-interface {
	font-size: 13px;
}

.field-item {
	border: 1px solid #e9ecef;
	border-radius: 4px;
	margin-bottom: 8px;
	padding: 10px;
	cursor: pointer;
	transition: all 0.2s ease;
	background: #fff;
}

.field-item:hover {
	border-color: #007bff;
	box-shadow: 0 1px 3px rgba(0,123,255,0.1);
}

.field-item.mapped {
	border-color: #28a745;
	background-color: #f8fff9;
}

.field-item.confidence-high {
	border-left: 4px solid #28a745;
}

.field-item.confidence-medium {
	border-left: 4px solid #ffc107;
}

.field-item.confidence-low {
	border-left: 4px solid #6c757d;
}

.field-item.high-confidence-suggestion {
	animation: pulse-green 2s infinite;
}

@keyframes pulse-green {
	0% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.4); }
	70% { box-shadow: 0 0 0 10px rgba(40, 167, 69, 0); }
	100% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0); }
}

.field-item.drop-hover {
	border-color: #007bff;
	background-color: #e3f2fd;
}

.drag-handle {
	cursor: grab;
}

.drag-handle:active {
	cursor: grabbing;
}

.mapping-item {
	background: #f8f9fa;
}

.suggestion-item {
	background: #fff3cd;
}

.badge {
	font-size: 10px;
}

.field-search input {
	border-radius: 4px;
}

.mapping-lines {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	pointer-events: none;
}
</style>
`;

// Inject CSS
$(document).ready(function() {
	if (!$('#field-mapping-css').length) {
		$('head').append('<div id="field-mapping-css">' + frappe.ui.field_mapping_css + '</div>');
	}
});