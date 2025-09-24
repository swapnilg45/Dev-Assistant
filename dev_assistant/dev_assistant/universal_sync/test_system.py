# Copyright (c) 2025, Swapnil and contributors
# Test and validation utilities for Universal Sync System

import frappe
from frappe import _
import json
import traceback
from typing import Dict, List, Any


class SyncSystemValidator:
	"""Comprehensive validation and testing system for Universal Sync"""

	def __init__(self):
		self.test_results = []
		self.warnings = []
		self.errors = []

	def run_all_tests(self) -> Dict[str, Any]:
		"""Run comprehensive system validation"""
		print("Starting Universal Sync System validation...")

		try:
			# Infrastructure tests
			self.test_doctype_structure()
			self.test_permissions()
			self.test_pages_and_routes()

			# Core functionality tests
			self.test_field_mapping_system()
			self.test_template_system()
			self.test_sync_engine()

			# Integration tests
			self.test_notification_system()
			self.test_wizard_functionality()

			# Performance and safety tests
			self.test_data_integrity()
			self.test_error_handling()

			# Generate final report
			return self.generate_test_report()

		except Exception as e:
			self.errors.append(f"Critical test failure: {str(e)}")
			return self.generate_test_report()

	def test_doctype_structure(self):
		"""Test DocType definitions and structure"""
		print("Testing DocType structure...")

		required_doctypes = [
			"Sync Chain",
			"Sync Chain Step",
			"Sync Activity Log"
		]

		for doctype in required_doctypes:
			try:
				# Check if DocType exists
				if not frappe.db.exists("DocType", doctype):
					self.errors.append(f"DocType {doctype} is missing")
					continue

				# Check DocType structure
				meta = frappe.get_meta(doctype)

				# Validate basic structure
				if doctype == "Sync Chain":
					self.validate_sync_chain_structure(meta)
				elif doctype == "Sync Chain Step":
					self.validate_sync_step_structure(meta)
				elif doctype == "Sync Activity Log":
					self.validate_activity_log_structure(meta)

				self.test_results.append(f"✓ DocType {doctype} structure is valid")

			except Exception as e:
				self.errors.append(f"DocType {doctype} validation failed: {str(e)}")

	def validate_sync_chain_structure(self, meta):
		"""Validate Sync Chain DocType structure"""
		required_fields = [
			"chain_name", "description", "is_active", "template_used",
			"chain_steps", "sync_frequency", "conflict_resolution"
		]

		for field in required_fields:
			if not any(f.fieldname == field for f in meta.fields):
				self.errors.append(f"Sync Chain missing required field: {field}")

		# Check child table link
		steps_field = next((f for f in meta.fields if f.fieldname == "chain_steps"), None)
		if steps_field and steps_field.options != "Sync Chain Step":
			self.errors.append("chain_steps field should link to Sync Chain Step")

	def validate_sync_step_structure(self, meta):
		"""Validate Sync Chain Step DocType structure"""
		required_fields = [
			"step_number", "doctype_name", "doctype_label",
			"sync_condition", "field_mappings"
		]

		for field in required_fields:
			if not any(f.fieldname == field for f in meta.fields):
				self.errors.append(f"Sync Chain Step missing required field: {field}")

		# Check if it's a child table
		if not meta.istable:
			self.errors.append("Sync Chain Step should be a child table (istable=1)")

	def validate_activity_log_structure(self, meta):
		"""Validate Sync Activity Log DocType structure"""
		required_fields = [
			"sync_chain", "activity_type", "status", "source_document",
			"target_document", "message", "sync_timestamp"
		]

		for field in required_fields:
			if not any(f.fieldname == field for f in meta.fields):
				self.errors.append(f"Sync Activity Log missing required field: {field}")

	def test_permissions(self):
		"""Test permission setup"""
		print("Testing permissions...")

		try:
			# Test System Manager permissions
			system_manager_perms = frappe.get_all("DocPerm", {
				"parent": "Sync Chain",
				"role": "System Manager"
			})

			if not system_manager_perms:
				self.warnings.append("No System Manager permissions found for Sync Chain")

			self.test_results.append("✓ Permissions structure validated")

		except Exception as e:
			self.errors.append(f"Permission test failed: {str(e)}")

	def test_pages_and_routes(self):
		"""Test page accessibility"""
		print("Testing pages and routes...")

		required_pages = [
			"sync-dashboard",
			"sync-setup-wizard"
		]

		for page_name in required_pages:
			try:
				page_doc = frappe.get_doc("Page", page_name)
				if page_doc:
					self.test_results.append(f"✓ Page {page_name} exists")
				else:
					self.errors.append(f"Page {page_name} is missing")

			except frappe.DoesNotExistError:
				self.errors.append(f"Page {page_name} does not exist")
			except Exception as e:
				self.errors.append(f"Page {page_name} test failed: {str(e)}")

	def test_field_mapping_system(self):
		"""Test field mapping functionality"""
		print("Testing field mapping system...")

		try:
			from dev_assistant.dev_assistant.universal_sync.field_mapper import SmartFieldMapper

			mapper = SmartFieldMapper()

			# Test basic field mapping
			test_mappings = mapper.get_field_suggestions("Lead", "Customer")

			if test_mappings:
				self.test_results.append("✓ Field mapping system working")
			else:
				self.warnings.append("Field mapping returned no suggestions")

			# Test field compatibility
			mappable_fields = mapper.get_mappable_fields("Lead")
			if mappable_fields:
				self.test_results.append("✓ Mappable fields detection working")
			else:
				self.warnings.append("No mappable fields found for Lead")

		except ImportError as e:
			self.errors.append(f"Field mapper import failed: {str(e)}")
		except Exception as e:
			self.errors.append(f"Field mapping test failed: {str(e)}")

	def test_template_system(self):
		"""Test template system"""
		print("Testing template system...")

		try:
			from dev_assistant.dev_assistant.universal_sync.sync_templates import get_all_templates, get_template

			# Test template loading
			templates = get_all_templates()

			if templates:
				self.test_results.append(f"✓ Template system loaded {len(templates)} templates")

				# Test specific template
				crm_template = get_template("crm_process")
				if crm_template:
					self.test_results.append("✓ CRM template loaded successfully")
				else:
					self.warnings.append("CRM template not found")

			else:
				self.errors.append("No templates loaded")

		except ImportError as e:
			self.errors.append(f"Template system import failed: {str(e)}")
		except Exception as e:
			self.errors.append(f"Template system test failed: {str(e)}")

	def test_sync_engine(self):
		"""Test sync engine functionality"""
		print("Testing sync engine...")

		try:
			from dev_assistant.dev_assistant.universal_sync.sync_engine import SimpleSyncEngine

			# Create a test sync chain
			test_chain = self.create_test_sync_chain()

			if test_chain:
				# Initialize sync engine
				sync_engine = SimpleSyncEngine(test_chain.name)

				# Test basic engine initialization
				if sync_engine.chain_doc:
					self.test_results.append("✓ Sync engine initialization successful")
				else:
					self.errors.append("Sync engine initialization failed")

				# Test field mapping parsing
				if hasattr(sync_engine, 'get_field_mappings'):
					self.test_results.append("✓ Sync engine methods available")

			else:
				self.warnings.append("Could not create test sync chain for engine testing")

		except ImportError as e:
			self.errors.append(f"Sync engine import failed: {str(e)}")
		except Exception as e:
			self.errors.append(f"Sync engine test failed: {str(e)}")

	def test_notification_system(self):
		"""Test notification system"""
		print("Testing notification system...")

		try:
			from dev_assistant.dev_assistant.universal_sync.notification_system import SyncNotificationSystem

			notification_system = SyncNotificationSystem()

			# Test notification channels
			if hasattr(notification_system, 'channels'):
				self.test_results.append(f"✓ Notification system has {len(notification_system.channels)} channels")

			# Test notification content generation
			test_chain = self.create_minimal_chain_object()
			test_data = {"source_doctype": "Lead", "target_doctype": "Customer"}

			try:
				subject, message = notification_system.get_email_content("sync_success", test_chain, test_data)
				if subject and message:
					self.test_results.append("✓ Notification content generation working")
			except Exception as e:
				self.warnings.append(f"Notification content generation warning: {str(e)}")

		except ImportError as e:
			self.errors.append(f"Notification system import failed: {str(e)}")
		except Exception as e:
			self.errors.append(f"Notification system test failed: {str(e)}")

	def test_wizard_functionality(self):
		"""Test wizard backend functionality"""
		print("Testing wizard functionality...")

		try:
			from dev_assistant.dev_assistant.universal_sync import wizard

			# Test wizard helper functions
			if hasattr(wizard, 'get_wizard_doctype_suggestions'):
				suggestions = wizard.get_wizard_doctype_suggestions()
				if suggestions:
					self.test_results.append("✓ Wizard DocType suggestions working")
				else:
					self.warnings.append("Wizard returned no DocType suggestions")

		except ImportError as e:
			self.errors.append(f"Wizard module import failed: {str(e)}")
		except Exception as e:
			self.errors.append(f"Wizard functionality test failed: {str(e)}")

	def test_data_integrity(self):
		"""Test data integrity and validation"""
		print("Testing data integrity...")

		try:
			# Test sync chain validation
			test_chain = self.create_test_sync_chain()

			if test_chain:
				# Test chain validation
				try:
					test_chain.save()
					self.test_results.append("✓ Sync chain validation working")
				except Exception as e:
					self.warnings.append(f"Sync chain validation issue: {str(e)}")

				# Cleanup test chain
				test_chain.delete()

		except Exception as e:
			self.errors.append(f"Data integrity test failed: {str(e)}")

	def test_error_handling(self):
		"""Test error handling mechanisms"""
		print("Testing error handling...")

		try:
			# Test sync engine with invalid data
			from dev_assistant.dev_assistant.universal_sync.sync_engine import SimpleSyncEngine

			try:
				# This should fail gracefully
				invalid_engine = SimpleSyncEngine("NON_EXISTENT_CHAIN")
				self.warnings.append("Invalid sync chain should have failed")
			except Exception:
				self.test_results.append("✓ Sync engine error handling working")

			# Test field mapper with invalid data
			from dev_assistant.dev_assistant.universal_sync.field_mapper import SmartFieldMapper

			mapper = SmartFieldMapper()
			try:
				# This should fail gracefully
				invalid_mappings = mapper.get_field_suggestions("NON_EXISTENT_DOCTYPE", "ANOTHER_NON_EXISTENT")
				if not invalid_mappings:
					self.test_results.append("✓ Field mapper error handling working")
			except Exception as e:
				self.test_results.append("✓ Field mapper properly raises exceptions")

		except Exception as e:
			self.errors.append(f"Error handling test failed: {str(e)}")

	def create_test_sync_chain(self):
		"""Create a test sync chain for testing"""
		try:
			test_chain = frappe.new_doc("Sync Chain")
			test_chain.chain_name = "Test Sync Chain"
			test_chain.description = "Test chain for validation"
			test_chain.is_active = 0  # Keep inactive
			test_chain.sync_frequency = "Manual Only"
			test_chain.conflict_resolution = "Use Latest Data"

			# Add a test step
			step = test_chain.append("chain_steps")
			step.step_number = 1
			step.doctype_name = "Lead"
			step.doctype_label = "Lead"
			step.sync_condition = "Always"
			step.field_mappings = '{"lead_name": "customer_name"}'

			test_chain.insert()
			return test_chain

		except Exception as e:
			self.warnings.append(f"Could not create test sync chain: {str(e)}")
			return None

	def create_minimal_chain_object(self):
		"""Create minimal chain object for testing"""
		class MinimalChain:
			def __init__(self):
				self.name = "TEST-CHAIN"
				self.chain_name = "Test Chain"
				self.description = "Test description"
				self.owner = frappe.session.user
				self.chain_steps = []

		return MinimalChain()

	def generate_test_report(self) -> Dict[str, Any]:
		"""Generate comprehensive test report"""
		total_tests = len(self.test_results) + len(self.warnings) + len(self.errors)
		passed_tests = len(self.test_results)
		warning_count = len(self.warnings)
		error_count = len(self.errors)

		# Determine overall status
		if error_count == 0 and warning_count == 0:
			overall_status = "EXCELLENT"
		elif error_count == 0:
			overall_status = "GOOD"
		elif error_count < 3:
			overall_status = "NEEDS_ATTENTION"
		else:
			overall_status = "CRITICAL"

		report = {
			"overall_status": overall_status,
			"summary": {
				"total_tests": total_tests,
				"passed": passed_tests,
				"warnings": warning_count,
				"errors": error_count,
				"success_rate": round((passed_tests / total_tests * 100) if total_tests > 0 else 0, 1)
			},
			"results": {
				"passed": self.test_results,
				"warnings": self.warnings,
				"errors": self.errors
			},
			"recommendations": self.generate_recommendations(),
			"next_steps": self.generate_next_steps()
		}

		return report

	def generate_recommendations(self) -> List[str]:
		"""Generate recommendations based on test results"""
		recommendations = []

		if self.errors:
			recommendations.append("❌ Critical errors found - system may not function properly")
			recommendations.append("🔧 Review and fix all errors before production use")

		if self.warnings:
			recommendations.append("⚠️ Warnings found - system will work but may have limitations")
			recommendations.append("📋 Review warnings and consider improvements")

		if not self.errors and not self.warnings:
			recommendations.append("✅ System is in excellent condition")
			recommendations.append("🚀 Ready for production use")

		# Specific recommendations
		if any("permission" in error.lower() for error in self.errors):
			recommendations.append("🔐 Review and set up proper role-based permissions")

		if any("template" in error.lower() for error in self.errors):
			recommendations.append("📄 Check template system configuration")

		return recommendations

	def generate_next_steps(self) -> List[str]:
		"""Generate next steps based on test results"""
		next_steps = []

		if self.errors:
			next_steps.append("1. Fix all critical errors listed above")
			next_steps.append("2. Re-run validation tests")
		else:
			next_steps.append("1. System validation passed!")

		if not self.errors and self.warnings:
			next_steps.append("2. Review and address warnings")
			next_steps.append("3. Run user acceptance testing")
		elif not self.errors and not self.warnings:
			next_steps.append("2. Proceed with user training")
			next_steps.append("3. Deploy to production environment")

		next_steps.append("4. Monitor system performance after deployment")
		next_steps.append("5. Collect user feedback and iterate")

		return next_steps


@frappe.whitelist()
def run_system_validation():
	"""API endpoint to run system validation"""
	try:
		validator = SyncSystemValidator()
		report = validator.run_all_tests()

		return {
			"success": True,
			"report": report,
			"message": f"Validation completed - {report['overall_status']}"
		}

	except Exception as e:
		frappe.log_error(f"System validation failed: {str(e)}", "System Validation")
		return {
			"success": False,
			"error": str(e),
			"message": "System validation failed"
		}


@frappe.whitelist()
def run_quick_health_check():
	"""Quick health check for monitoring"""
	try:
		health_checks = {
			"doctypes_exist": check_doctypes_exist(),
			"pages_accessible": check_pages_accessible(),
			"active_chains": count_active_chains(),
			"recent_activities": count_recent_activities(),
			"system_errors": check_recent_errors()
		}

		# Overall health score
		healthy_checks = sum(1 for check in health_checks.values() if check.get("status") == "healthy")
		total_checks = len(health_checks)
		health_score = round((healthy_checks / total_checks) * 100, 1)

		return {
			"success": True,
			"health_score": health_score,
			"status": "healthy" if health_score >= 80 else "needs_attention" if health_score >= 60 else "critical",
			"checks": health_checks,
			"timestamp": frappe.utils.now()
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e),
			"health_score": 0,
			"status": "critical"
		}


def check_doctypes_exist():
	"""Check if core DocTypes exist"""
	required = ["Sync Chain", "Sync Chain Step", "Sync Activity Log"]
	existing = [dt for dt in required if frappe.db.exists("DocType", dt)]

	return {
		"status": "healthy" if len(existing) == len(required) else "critical",
		"details": f"{len(existing)}/{len(required)} DocTypes exist",
		"missing": [dt for dt in required if dt not in existing]
	}


def check_pages_accessible():
	"""Check if pages are accessible"""
	required_pages = ["sync-dashboard", "sync-setup-wizard"]
	accessible = []

	for page in required_pages:
		try:
			frappe.get_doc("Page", page)
			accessible.append(page)
		except:
			pass

	return {
		"status": "healthy" if len(accessible) == len(required_pages) else "needs_attention",
		"details": f"{len(accessible)}/{len(required_pages)} pages accessible"
	}


def count_active_chains():
	"""Count active sync chains"""
	try:
		count = frappe.db.count("Sync Chain", {"is_active": 1})
		return {
			"status": "healthy",
			"details": f"{count} active sync chains",
			"count": count
		}
	except:
		return {
			"status": "critical",
			"details": "Cannot access sync chains"
		}


def count_recent_activities():
	"""Count recent sync activities"""
	try:
		cutoff = frappe.utils.add_days(frappe.utils.now(), -1)
		count = frappe.db.count("Sync Activity Log", {"creation": [">=", cutoff]})

		return {
			"status": "healthy",
			"details": f"{count} activities in last 24h",
			"count": count
		}
	except:
		return {
			"status": "needs_attention",
			"details": "Cannot access activity logs"
		}


def check_recent_errors():
	"""Check for recent errors"""
	try:
		cutoff = frappe.utils.add_days(frappe.utils.now(), -1)
		error_count = frappe.db.count("Sync Activity Log", {
			"creation": [">=", cutoff],
			"status": "Failed"
		})

		if error_count == 0:
			status = "healthy"
		elif error_count < 5:
			status = "needs_attention"
		else:
			status = "critical"

		return {
			"status": status,
			"details": f"{error_count} errors in last 24h",
			"count": error_count
		}
	except:
		return {
			"status": "critical",
			"details": "Cannot check error logs"
		}