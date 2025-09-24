# Copyright (c) 2025, Swapnil and contributors
# Test runner for Universal Sync System

import frappe
from frappe import _
from .test_system import SyncSystemValidator


@frappe.whitelist()
def run_complete_validation():
	"""Run complete system validation and return results"""
	try:
		validator = SyncSystemValidator()
		results = validator.run_all_tests()

		# Format results for display
		formatted_results = {
			"success": True,
			"overall_status": "pass" if all(r["passed"] for r in results) else "fail",
			"total_tests": len(results),
			"passed_tests": sum(1 for r in results if r["passed"]),
			"failed_tests": sum(1 for r in results if not r["passed"]),
			"detailed_results": results
		}

		# Log results
		frappe.log_error(
			f"Sync System Validation completed: {formatted_results['passed_tests']}/{formatted_results['total_tests']} tests passed",
			"Sync System Validation"
		)

		return formatted_results

	except Exception as e:
		frappe.log_error(f"Validation failed: {str(e)}", "Sync System Validation Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def run_specific_test(test_name):
	"""Run a specific test by name"""
	try:
		validator = SyncSystemValidator()

		# Map test names to methods
		test_methods = {
			"doctype_structure": validator.test_doctype_structure,
			"permissions": validator.test_permissions,
			"pages": validator.test_pages,
			"field_mapping": validator.test_field_mapping,
			"templates": validator.test_templates,
			"sync_engine": validator.test_sync_engine,
			"notifications": validator.test_notifications,
			"wizard": validator.test_wizard_functionality,
			"data_integrity": validator.test_data_integrity,
			"error_handling": validator.test_error_handling
		}

		if test_name not in test_methods:
			return {
				"success": False,
				"error": f"Unknown test: {test_name}"
			}

		result = test_methods[test_name]()
		return {
			"success": True,
			"result": result
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_test_summary():
	"""Get summary of available tests"""
	return {
		"success": True,
		"available_tests": [
			{
				"name": "doctype_structure",
				"title": "DocType Structure Validation",
				"description": "Validates all required DocTypes and their structure"
			},
			{
				"name": "permissions",
				"title": "Permission System",
				"description": "Tests role-based permissions and access control"
			},
			{
				"name": "pages",
				"title": "Page Functionality",
				"description": "Validates dashboard and wizard pages"
			},
			{
				"name": "field_mapping",
				"title": "Field Mapping System",
				"description": "Tests intelligent field mapping and suggestions"
			},
			{
				"name": "templates",
				"title": "Template System",
				"description": "Validates pre-built templates and customization"
			},
			{
				"name": "sync_engine",
				"title": "Sync Engine",
				"description": "Tests core synchronization functionality"
			},
			{
				"name": "notifications",
				"title": "Notification System",
				"description": "Validates multi-channel notification system"
			},
			{
				"name": "wizard",
				"title": "Setup Wizard",
				"description": "Tests wizard functionality and user experience"
			},
			{
				"name": "data_integrity",
				"title": "Data Integrity",
				"description": "Validates data consistency and integrity checks"
			},
			{
				"name": "error_handling",
				"title": "Error Handling",
				"description": "Tests error handling and recovery mechanisms"
			}
		]
	}


@frappe.whitelist()
def create_test_data():
	"""Create sample test data for validation"""
	try:
		# Create test sync chain
		if not frappe.db.exists("Sync Chain", "TEST-0001"):
			test_chain = frappe.get_doc({
				"doctype": "Sync Chain",
				"chain_name": "Test CRM Process",
				"description": "Test chain for validation",
				"is_active": 0,  # Keep inactive during testing
				"template_used": "crm_process",
				"sync_frequency": "Real-time",
				"conflict_resolution": "source_wins",
				"chain_steps": [
					{
						"step_name": "Lead to Customer",
						"source_doctype": "Lead",
						"target_doctype": "Customer",
						"mapping_config": '{"lead_name": "customer_name", "email_id": "customer_primary_contact"}',
						"sync_direction": "source_to_target",
						"step_order": 1
					}
				]
			})
			test_chain.insert()

		# Create test activity log
		if not frappe.db.exists("Sync Activity Log", {"sync_chain": "TEST-0001"}):
			activity_log = frappe.get_doc({
				"doctype": "Sync Activity Log",
				"sync_chain": "TEST-0001",
				"activity_type": "Test",
				"status": "Success",
				"source_document": "Test Document",
				"target_document": "Test Target",
				"processing_time": 0.5,
				"records_processed": 1,
				"records_success": 1,
				"records_failed": 0,
				"activity_details": "Test activity for validation"
			})
			activity_log.insert()

		return {
			"success": True,
			"message": "Test data created successfully"
		}

	except Exception as e:
		frappe.log_error(f"Test data creation failed: {str(e)}", "Test Data Creation")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def cleanup_test_data():
	"""Clean up test data after validation"""
	try:
		# Delete test records
		test_records = [
			("Sync Chain", "TEST-0001"),
			("Sync Activity Log", {"sync_chain": "TEST-0001"})
		]

		for doctype, filters in test_records:
			if isinstance(filters, str):
				# Single document name
				if frappe.db.exists(doctype, filters):
					frappe.delete_doc(doctype, filters)
			else:
				# Filter dict
				docs = frappe.get_all(doctype, filters=filters)
				for doc in docs:
					frappe.delete_doc(doctype, doc.name)

		return {
			"success": True,
			"message": "Test data cleaned up successfully"
		}

	except Exception as e:
		frappe.log_error(f"Test data cleanup failed: {str(e)}", "Test Data Cleanup")
		return {
			"success": False,
			"error": str(e)
		}


def generate_validation_report():
	"""Generate comprehensive validation report"""
	try:
		validator = SyncSystemValidator()
		results = validator.run_all_tests()

		# Generate markdown report
		report_lines = [
			"# Universal Sync System Validation Report",
			f"**Generated:** {frappe.utils.now()}",
			f"**System:** {frappe.local.site}",
			""
		]

		# Summary
		passed = sum(1 for r in results if r["passed"])
		total = len(results)
		status = "✅ PASS" if passed == total else "❌ FAIL"

		report_lines.extend([
			"## Summary",
			f"**Overall Status:** {status}",
			f"**Tests Passed:** {passed}/{total}",
			""
		])

		# Detailed results
		report_lines.append("## Detailed Results")
		for result in results:
			status_icon = "✅" if result["passed"] else "❌"
			report_lines.extend([
				f"### {status_icon} {result['test_name']}",
				f"**Status:** {'PASS' if result['passed'] else 'FAIL'}",
				""
			])

			if result["details"]:
				report_lines.append("**Details:**")
				for detail in result["details"]:
					report_lines.append(f"- {detail}")
				report_lines.append("")

			if result.get("errors"):
				report_lines.append("**Errors:**")
				for error in result["errors"]:
					report_lines.append(f"- {error}")
				report_lines.append("")

		return "\n".join(report_lines)

	except Exception as e:
		return f"Error generating report: {str(e)}"