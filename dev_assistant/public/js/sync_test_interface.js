/**
 * Sync Test Interface
 * Provides testing and validation UI for the Universal Sync System
 * @author Claude Code Assistant
 */

class SyncTestInterface {
	constructor() {
		this.test_results = {};
		this.running_tests = new Set();
	}

	/**
	 * Create test interface dialog
	 */
	show_test_dialog() {
		this.dialog = new frappe.ui.Dialog({
			title: __('Universal Sync System - Test & Validation'),
			fields: [
				{
					fieldtype: 'HTML',
					fieldname: 'test_intro',
					options: `
						<div class="test-intro">
							<p><strong>System Validation</strong></p>
							<p>Run comprehensive tests to validate the Universal Sync System installation and functionality.</p>
						</div>
					`
				},
				{
					fieldtype: 'Section Break'
				},
				{
					fieldtype: 'HTML',
					fieldname: 'test_buttons',
					options: this.get_test_buttons_html()
				},
				{
					fieldtype: 'Section Break'
				},
				{
					fieldtype: 'HTML',
					fieldname: 'test_results',
					options: '<div id="test-results-container"></div>'
				}
			],
			size: 'large',
			primary_action: () => {
				this.run_all_tests();
			},
			primary_action_label: __('Run All Tests'),
			secondary_action: () => {
				this.create_test_data();
			},
			secondary_action_label: __('Setup Test Data')
		});

		this.dialog.show();
		this.setup_test_event_handlers();
	}

	/**
	 * Generate HTML for individual test buttons
	 */
	get_test_buttons_html() {
		const tests = [
			{ name: 'doctype_structure', title: 'DocType Structure', icon: 'file-text' },
			{ name: 'permissions', title: 'Permissions', icon: 'lock' },
			{ name: 'pages', title: 'Pages', icon: 'layout' },
			{ name: 'field_mapping', title: 'Field Mapping', icon: 'link' },
			{ name: 'templates', title: 'Templates', icon: 'copy' },
			{ name: 'sync_engine', title: 'Sync Engine', icon: 'refresh-cw' },
			{ name: 'notifications', title: 'Notifications', icon: 'bell' },
			{ name: 'wizard', title: 'Setup Wizard', icon: 'zap' },
			{ name: 'data_integrity', title: 'Data Integrity', icon: 'shield' },
			{ name: 'error_handling', title: 'Error Handling', icon: 'alert-triangle' }
		];

		let html = '<div class="test-buttons-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 15px 0;">';

		tests.forEach(test => {
			html += `
				<button class="btn btn-default test-btn" data-test="${test.name}" style="padding: 10px; text-align: left;">
					<i class="fa fa-${test.icon}" style="margin-right: 8px;"></i>
					${test.title}
					<span class="test-status" data-test="${test.name}" style="float: right;"></span>
				</button>
			`;
		});

		html += '</div>';
		return html;
	}

	/**
	 * Setup event handlers for test buttons
	 */
	setup_test_event_handlers() {
		// Individual test buttons
		this.dialog.$wrapper.find('.test-btn').on('click', (e) => {
			const test_name = $(e.currentTarget).data('test');
			this.run_single_test(test_name);
		});

		// Cleanup button
		this.dialog.$wrapper.find('.cleanup-btn').on('click', () => {
			this.cleanup_test_data();
		});
	}

	/**
	 * Run all tests sequentially
	 */
	async run_all_tests() {
		this.dialog.set_primary_action_label(__('Running Tests...'));
		this.dialog.disable_primary_action();

		try {
			const response = await frappe.call({
				method: 'dev_assistant.dev_assistant.universal_sync.run_tests.run_complete_validation'
			});

			if (response.message.success) {
				this.display_all_test_results(response.message);
			} else {
				this.show_error('Failed to run tests: ' + response.message.error);
			}
		} catch (error) {
			this.show_error('Error running tests: ' + error.message);
		} finally {
			this.dialog.set_primary_action_label(__('Run All Tests'));
			this.dialog.enable_primary_action();
		}
	}

	/**
	 * Run individual test
	 */
	async run_single_test(test_name) {
		if (this.running_tests.has(test_name)) {
			return;
		}

		this.running_tests.add(test_name);
		this.update_test_status(test_name, 'running');

		try {
			const response = await frappe.call({
				method: 'dev_assistant.dev_assistant.universal_sync.run_tests.run_specific_test',
				args: { test_name: test_name }
			});

			if (response.message.success) {
				this.test_results[test_name] = response.message.result;
				this.update_test_status(test_name, response.message.result.passed ? 'pass' : 'fail');
				this.display_single_test_result(test_name, response.message.result);
			} else {
				this.update_test_status(test_name, 'error');
				this.show_error(`Test ${test_name} failed: ${response.message.error}`);
			}
		} catch (error) {
			this.update_test_status(test_name, 'error');
			this.show_error(`Error running test ${test_name}: ${error.message}`);
		} finally {
			this.running_tests.delete(test_name);
		}
	}

	/**
	 * Update test status indicator
	 */
	update_test_status(test_name, status) {
		const status_element = this.dialog.$wrapper.find(`[data-test="${test_name}"].test-status`);

		status_element.removeClass('text-success text-danger text-warning text-muted');

		switch (status) {
			case 'running':
				status_element.html('<i class="fa fa-spinner fa-spin"></i>');
				status_element.addClass('text-warning');
				break;
			case 'pass':
				status_element.html('<i class="fa fa-check"></i>');
				status_element.addClass('text-success');
				break;
			case 'fail':
				status_element.html('<i class="fa fa-times"></i>');
				status_element.addClass('text-danger');
				break;
			case 'error':
				status_element.html('<i class="fa fa-exclamation"></i>');
				status_element.addClass('text-danger');
				break;
			default:
				status_element.html('');
				status_element.addClass('text-muted');
		}
	}

	/**
	 * Display results for all tests
	 */
	display_all_test_results(results) {
		const container = this.dialog.$wrapper.find('#test-results-container');

		let html = `
			<div class="test-summary" style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px;">
				<h4>Test Summary</h4>
				<p><strong>Overall Status:</strong> <span class="badge badge-${results.overall_status === 'pass' ? 'success' : 'danger'}">${results.overall_status.toUpperCase()}</span></p>
				<p><strong>Tests Passed:</strong> ${results.passed_tests}/${results.total_tests}</p>
			</div>
			<div class="test-details">
		`;

		results.detailed_results.forEach(result => {
			const status_class = result.passed ? 'success' : 'danger';
			const status_icon = result.passed ? 'check' : 'times';

			html += `
				<div class="test-result-item" style="margin: 10px 0; padding: 10px; border: 1px solid #dee2e6; border-radius: 5px;">
					<h5>
						<i class="fa fa-${status_icon} text-${status_class}"></i>
						${result.test_name}
						<span class="badge badge-${status_class} float-right">${result.passed ? 'PASS' : 'FAIL'}</span>
					</h5>
			`;

			if (result.details && result.details.length > 0) {
				html += '<ul>';
				result.details.forEach(detail => {
					html += `<li>${detail}</li>`;
				});
				html += '</ul>';
			}

			if (result.errors && result.errors.length > 0) {
				html += '<div class="text-danger"><strong>Errors:</strong><ul>';
				result.errors.forEach(error => {
					html += `<li>${error}</li>`;
				});
				html += '</ul></div>';
			}

			html += '</div>';
		});

		html += '</div>';
		container.html(html);

		// Update individual test status indicators
		results.detailed_results.forEach(result => {
			this.update_test_status(result.test_name.replace(' ', '_').toLowerCase(), result.passed ? 'pass' : 'fail');
		});
	}

	/**
	 * Display single test result
	 */
	display_single_test_result(test_name, result) {
		const container = this.dialog.$wrapper.find('#test-results-container');
		const status_class = result.passed ? 'success' : 'danger';
		const status_icon = result.passed ? 'check' : 'times';

		let html = `
			<div class="single-test-result" style="margin: 15px 0; padding: 15px; border: 1px solid #dee2e6; border-radius: 5px;">
				<h5>
					<i class="fa fa-${status_icon} text-${status_class}"></i>
					${test_name.replace('_', ' ').toUpperCase()}
					<span class="badge badge-${status_class} float-right">${result.passed ? 'PASS' : 'FAIL'}</span>
				</h5>
		`;

		if (result.details && result.details.length > 0) {
			html += '<div><strong>Details:</strong><ul>';
			result.details.forEach(detail => {
				html += `<li>${detail}</li>`;
			});
			html += '</ul></div>';
		}

		if (result.errors && result.errors.length > 0) {
			html += '<div class="text-danger"><strong>Errors:</strong><ul>';
			result.errors.forEach(error => {
				html += `<li>${error}</li>`;
			});
			html += '</ul></div>';
		}

		html += '</div>';
		container.html(html);
	}

	/**
	 * Create test data
	 */
	async create_test_data() {
		this.dialog.set_secondary_action_label(__('Creating...'));

		try {
			const response = await frappe.call({
				method: 'dev_assistant.dev_assistant.universal_sync.run_tests.create_test_data'
			});

			if (response.message.success) {
				frappe.show_alert({
					message: __('Test data created successfully'),
					indicator: 'green'
				});
			} else {
				this.show_error('Failed to create test data: ' + response.message.error);
			}
		} catch (error) {
			this.show_error('Error creating test data: ' + error.message);
		} finally {
			this.dialog.set_secondary_action_label(__('Setup Test Data'));
		}
	}

	/**
	 * Clean up test data
	 */
	async cleanup_test_data() {
		try {
			const response = await frappe.call({
				method: 'dev_assistant.dev_assistant.universal_sync.run_tests.cleanup_test_data'
			});

			if (response.message.success) {
				frappe.show_alert({
					message: __('Test data cleaned up successfully'),
					indicator: 'green'
				});
			} else {
				this.show_error('Failed to cleanup test data: ' + response.message.error);
			}
		} catch (error) {
			this.show_error('Error cleaning up test data: ' + error.message);
		}
	}

	/**
	 * Show error message
	 */
	show_error(message) {
		frappe.msgprint({
			title: __('Error'),
			message: message,
			indicator: 'red'
		});
	}

	/**
	 * Generate and download validation report
	 */
	async generate_report() {
		try {
			const response = await frappe.call({
				method: 'dev_assistant.dev_assistant.universal_sync.run_tests.generate_validation_report'
			});

			if (response.message) {
				// Create downloadable file
				const blob = new Blob([response.message], { type: 'text/markdown' });
				const url = URL.createObjectURL(blob);
				const a = document.createElement('a');
				a.href = url;
				a.download = `sync_validation_report_${frappe.datetime.get_today()}.md`;
				document.body.appendChild(a);
				a.click();
				document.body.removeChild(a);
				URL.revokeObjectURL(url);

				frappe.show_alert({
					message: __('Validation report downloaded'),
					indicator: 'green'
				});
			}
		} catch (error) {
			this.show_error('Error generating report: ' + error.message);
		}
	}
}

// Global instance for easy access
window.sync_test_interface = new SyncTestInterface();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
	module.exports = SyncTestInterface;
}