# Copyright (c) 2025, Swapnil and contributors
# Simplified Synchronization Engine for Universal Sync System

import frappe
from frappe import _
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class SimpleSyncEngine:
	"""Simplified synchronization engine for non-technical users"""

	def __init__(self, sync_chain_name: str):
		self.chain_name = sync_chain_name
		self.chain_doc = frappe.get_doc("Sync Chain", sync_chain_name)
		self.current_user = frappe.session.user

	def execute_sync(self, source_doc, source_doctype: str, trigger_event: str = None) -> Dict[str, Any]:
		"""Execute synchronization for a document"""
		try:
			# Check if chain is active
			if not self.chain_doc.is_active:
				return {"status": "skipped", "message": "Sync chain is inactive"}

			# Find current step and next step
			current_step = self.find_step_by_doctype(source_doctype)
			if not current_step:
				return {"status": "skipped", "message": f"No sync step found for {source_doctype}"}

			next_step = self.get_next_step(current_step)
			if not next_step:
				return {"status": "completed", "message": "Reached end of sync chain"}

			# Check sync condition
			if not self.should_sync(current_step, source_doc, trigger_event):
				return {"status": "skipped", "message": f"Sync condition not met: {current_step.sync_condition}"}

			# Perform synchronization
			result = self.sync_to_next_step(source_doc, current_step, next_step)

			# Log activity
			self.log_sync_activity(source_doc, result, current_step, next_step)

			return result

		except Exception as e:
			error_msg = str(e)
			self.log_sync_error(source_doc, error_msg, current_step if 'current_step' in locals() else None)
			frappe.log_error(f"Sync Error in {self.chain_name}: {error_msg}", "Universal Sync System")
			return {"status": "error", "error": error_msg}

	def find_step_by_doctype(self, doctype: str):
		"""Find step configuration for a DocType"""
		for step in self.chain_doc.chain_steps:
			if step.doctype_name == doctype:
				return step
		return None

	def get_next_step(self, current_step):
		"""Get the next step in the chain"""
		next_step_number = current_step.step_number + 1
		for step in self.chain_doc.chain_steps:
			if step.step_number == next_step_number:
				return step
		return None

	def get_previous_step(self, current_step):
		"""Get the previous step in the chain (for bi-directional sync)"""
		prev_step_number = current_step.step_number - 1
		for step in self.chain_doc.chain_steps:
			if step.step_number == prev_step_number:
				return step
		return None

	def should_sync(self, step, source_doc, trigger_event: str) -> bool:
		"""Check if synchronization should happen based on conditions"""
		condition = step.sync_condition

		if condition == "Always":
			return trigger_event in ["on_update", "on_submit", "on_update_after_submit", "manual"]
		elif condition == "Status Changes":
			return trigger_event in ["on_update", "on_update_after_submit", "on_submit"]
		elif condition == "Specific Field Changes":
			# Enhanced field change detection could be implemented here
			return trigger_event in ["on_update", "on_update_after_submit"]
		elif condition == "Manual Trigger":
			return trigger_event == "manual"

		return False

	def sync_to_next_step(self, source_doc, current_step, next_step) -> Dict[str, Any]:
		"""Sync data to the next DocType in the chain"""
		try:
			# Parse field mappings
			field_mappings = self.get_field_mappings(next_step)
			if not field_mappings:
				return {"status": "warning", "message": "No field mappings configured"}

			# Find or create target document
			target_doc = self.find_or_create_target_doc(source_doc, next_step, field_mappings)

			# Map fields
			changes_made = self.map_fields(source_doc, target_doc, field_mappings)

			if not changes_made:
				return {"status": "skipped", "message": "No changes to sync"}

			# Handle conflicts if target already exists
			if not target_doc.is_new():
				conflict_result = self.handle_conflicts(target_doc, field_mappings, source_doc)
				if conflict_result.get("status") == "review_needed":
					return conflict_result

			# Save target document
			if target_doc.is_new():
				target_doc.insert(ignore_permissions=True)
			else:
				target_doc.save(ignore_permissions=True)

			return {
				"status": "success",
				"target_doc": target_doc.name,
				"target_doctype": next_step.doctype_name,
				"changes_count": changes_made
			}

		except Exception as e:
			return {"status": "error", "error": str(e)}

	def get_field_mappings(self, step) -> Dict[str, str]:
		"""Get field mappings from step configuration"""
		if not step.field_mappings:
			return {}

		try:
			return json.loads(step.field_mappings)
		except json.JSONDecodeError:
			frappe.log_error(f"Invalid field mappings JSON in step {step.step_number}", "Sync Engine")
			return {}

	def find_or_create_target_doc(self, source_doc, target_step, field_mappings):
		"""Find existing target document or create new one"""
		target_doctype = target_step.doctype_name

		# Strategy 1: Look for existing document with same source reference
		existing_doc = self.find_linked_document(source_doc, target_doctype, field_mappings)
		if existing_doc:
			return frappe.get_doc(target_doctype, existing_doc)

		# Strategy 2: Look for document with matching key fields
		key_matches = self.find_by_key_fields(source_doc, target_doctype, field_mappings)
		if key_matches:
			return frappe.get_doc(target_doctype, key_matches[0])

		# Strategy 3: Create new document
		return frappe.new_doc(target_doctype)

	def find_linked_document(self, source_doc, target_doctype, field_mappings):
		"""Find document linked via sync activity log"""
		activities = frappe.get_all("Sync Activity Log",
			filters={
				"sync_chain": self.chain_name,
				"source_document": source_doc.name,
				"source_doctype": source_doc.doctype,
				"target_doctype": target_doctype,
				"status": "Success"
			},
			fields=["target_document"],
			order_by="creation desc",
			limit=1
		)

		if activities and activities[0].target_document:
			# Verify the linked document still exists
			if frappe.db.exists(target_doctype, activities[0].target_document):
				return activities[0].target_document

		return None

	def find_by_key_fields(self, source_doc, target_doctype, field_mappings):
		"""Find document by matching key fields"""
		key_fields = self.identify_key_fields(target_doctype, field_mappings)
		if not key_fields:
			return None

		# Build filters from key field mappings
		filters = {}
		for source_field, target_field in field_mappings.items():
			if target_field in key_fields:
				source_value = getattr(source_doc, source_field, None)
				if source_value:
					filters[target_field] = source_value

		if not filters:
			return None

		# Search for matching documents
		try:
			matches = frappe.get_all(target_doctype, filters=filters, limit=2)
			return [match.name for match in matches] if matches else None
		except Exception:
			return None

	def identify_key_fields(self, target_doctype, field_mappings) -> List[str]:
		"""Identify key fields that uniquely identify documents"""
		try:
			meta = frappe.get_meta(target_doctype)
			key_fields = []

			# Priority 1: Required fields that are being mapped
			for field in meta.fields:
				if field.reqd and field.fieldname in field_mappings.values():
					key_fields.append(field.fieldname)

			# Priority 2: Unique fields
			for field in meta.fields:
				if field.unique and field.fieldname in field_mappings.values():
					key_fields.append(field.fieldname)

			# Priority 3: Common identifier fields
			common_keys = ['email', 'email_id', 'phone', 'mobile', 'customer', 'supplier', 'employee']
			for target_field in field_mappings.values():
				if any(key in target_field.lower() for key in common_keys):
					key_fields.append(target_field)

			return list(set(key_fields))  # Remove duplicates

		except Exception:
			return []

	def map_fields(self, source_doc, target_doc, field_mappings) -> int:
		"""Map fields from source to target document"""
		changes_count = 0

		for source_field, target_field in field_mappings.items():
			if not hasattr(source_doc, source_field):
				continue

			if not hasattr(target_doc, target_field):
				continue

			source_value = getattr(source_doc, source_field)

			# Skip if source value is empty and target already has a value
			if not source_value and getattr(target_doc, target_field, None):
				continue

			# Get current target value
			current_target_value = getattr(target_doc, target_field, None)

			# Check if change is needed
			if self.values_are_different(source_value, current_target_value):
				# Apply field type conversion if needed
				converted_value = self.convert_field_value(source_value, target_field, target_doc.doctype)
				setattr(target_doc, target_field, converted_value)
				changes_count += 1

		return changes_count

	def values_are_different(self, value1, value2) -> bool:
		"""Check if two values are different (handling None, empty strings, etc.)"""
		# Normalize values
		def normalize(val):
			if val is None:
				return ""
			if isinstance(val, str):
				return val.strip()
			return val

		return normalize(value1) != normalize(value2)

	def convert_field_value(self, value, target_field, target_doctype):
		"""Convert field value to match target field type"""
		try:
			meta = frappe.get_meta(target_doctype)
			target_field_info = next((f for f in meta.fields if f.fieldname == target_field), None)

			if not target_field_info:
				return value

			target_fieldtype = target_field_info.fieldtype

			# Basic type conversions
			if target_fieldtype == "Int" and value is not None:
				return int(float(value)) if str(value).replace('.', '').replace('-', '').isdigit() else 0
			elif target_fieldtype == "Float" and value is not None:
				return float(value) if str(value).replace('.', '').replace('-', '').isdigit() else 0.0
			elif target_fieldtype == "Currency" and value is not None:
				return float(value) if str(value).replace('.', '').replace('-', '').isdigit() else 0.0
			elif target_fieldtype == "Check":
				return 1 if value in [1, '1', True, 'true', 'True', 'yes', 'Yes'] else 0
			elif target_fieldtype in ["Data", "Small Text", "Text", "Text Editor"]:
				return str(value) if value is not None else ""

			return value

		except Exception:
			return value

	def handle_conflicts(self, target_doc, field_mappings, source_doc) -> Dict[str, Any]:
		"""Handle data conflicts based on chain configuration"""
		resolution_strategy = self.chain_doc.conflict_resolution

		if resolution_strategy == "Use Latest Data":
			# Always overwrite - no conflict handling needed
			return {"status": "resolved", "method": "overwrite"}

		elif resolution_strategy == "Keep Original Data":
			# Don't overwrite existing values
			return {"status": "resolved", "method": "preserve"}

		elif resolution_strategy == "Ask Me to Review":
			# Create review task
			return self.create_review_task(target_doc, field_mappings, source_doc)

		return {"status": "resolved", "method": "default"}

	def create_review_task(self, target_doc, field_mappings, source_doc) -> Dict[str, Any]:
		"""Create review task for manual conflict resolution"""
		# Log activity with pending review status
		activity_log = frappe.new_doc("Sync Activity Log")
		activity_log.sync_chain = self.chain_name
		activity_log.activity_type = "Manual Review Needed"
		activity_log.status = "Pending Review"
		activity_log.source_document = source_doc.name
		activity_log.source_doctype = source_doc.doctype
		activity_log.target_document = target_doc.name
		activity_log.target_doctype = target_doc.doctype
		activity_log.message = f"Data conflict detected. Manual review required before sync."
		activity_log.insert(ignore_permissions=True)

		# Create notification
		self.create_conflict_notification(activity_log, target_doc, source_doc)

		return {
			"status": "review_needed",
			"message": "Manual review required for data conflict",
			"review_log": activity_log.name
		}

	def create_conflict_notification(self, activity_log, target_doc, source_doc):
		"""Create notification for conflict review"""
		try:
			# Create notification for chain owner or system manager
			recipients = [self.chain_doc.owner]

			# Add system managers as fallback
			system_managers = frappe.get_all("Has Role",
				filters={"role": "System Manager"},
				fields=["parent"]
			)
			recipients.extend([sm.parent for sm in system_managers])

			for recipient in set(recipients):  # Remove duplicates
				frappe.get_doc({
					"doctype": "Notification Log",
					"for_user": recipient,
					"type": "Alert",
					"document_type": "Sync Activity Log",
					"document_name": activity_log.name,
					"subject": f"Sync Conflict: {source_doc.doctype} → {target_doc.doctype}",
					"email_content": f"A data conflict has been detected in sync chain '{self.chain_doc.chain_name}'. Please review and resolve.",
				}).insert(ignore_permissions=True)

		except Exception as e:
			frappe.log_error(f"Failed to create conflict notification: {str(e)}", "Sync Engine")

	def log_sync_activity(self, source_doc, result, current_step, next_step):
		"""Log synchronization activity"""
		from dev_assistant.dev_assistant.doctype.sync_activity_log.sync_activity_log import create_sync_activity_log

		activity_type = "Data Synced"
		status = "Success"
		message = f"Successfully synced from {current_step.doctype_name} to {next_step.doctype_name}"

		if result["status"] == "error":
			activity_type = "Error Occurred"
			status = "Failed"
			message = f"Sync failed: {result.get('error', 'Unknown error')}"
		elif result["status"] == "skipped":
			activity_type = "Process Completed"
			status = "Success"
			message = result.get("message", "Sync skipped")
		elif result["status"] == "warning":
			activity_type = "Error Occurred"
			status = "Failed"
			message = result.get("message", "Sync warning")
		elif result["status"] == "review_needed":
			activity_type = "Manual Review Needed"
			status = "Pending Review"
			message = result.get("message", "Manual review required")

		# Get target doc if available
		target_doc = None
		if result.get("target_doc") and result.get("target_doctype"):
			try:
				target_doc = frappe.get_doc(result["target_doctype"], result["target_doc"])
			except Exception:
				pass

		create_sync_activity_log(
			sync_chain=self.chain_name,
			activity_type=activity_type,
			status=status,
			source_doc=source_doc,
			target_doc=target_doc,
			message=message,
			error_details=result.get("error") if result["status"] == "error" else None
		)

	def log_sync_error(self, source_doc, error_msg, current_step=None):
		"""Log sync error"""
		from dev_assistant.dev_assistant.doctype.sync_activity_log.sync_activity_log import create_sync_activity_log

		create_sync_activity_log(
			sync_chain=self.chain_name,
			activity_type="Error Occurred",
			status="Failed",
			source_doc=source_doc,
			message=f"Sync error: {error_msg}",
			error_details=error_msg
		)

	def execute_bi_directional_sync(self, source_doc, source_doctype: str, trigger_event: str = None) -> Dict[str, Any]:
		"""Execute bi-directional synchronization"""
		results = []

		# Forward sync
		forward_result = self.execute_sync(source_doc, source_doctype, trigger_event)
		results.append({
			"direction": "forward",
			"result": forward_result
		})

		# Backward sync if forward was successful and there's a previous step
		if forward_result["status"] == "success":
			current_step = self.find_step_by_doctype(source_doctype)
			if current_step:
				prev_step = self.get_previous_step(current_step)
				if prev_step:
					backward_result = self.execute_sync(source_doc, source_doctype, trigger_event)
					results.append({
						"direction": "backward",
						"result": backward_result
					})

		return {
			"status": "completed",
			"bi_directional": True,
			"results": results
		}


# Hook functions for document events
def sync_on_document_event(doc, method):
	"""Hook function to trigger sync on document events"""
	# Skip if sync is already in progress (prevent infinite loops)
	if hasattr(frappe.local, 'sync_in_progress') and frappe.local.sync_in_progress:
		return

	try:
		# Check if sync tables exist (for migration safety)
		if not frappe.db.table_exists("tabSync Chain") or not frappe.db.table_exists("tabSync Chain Step"):
			return

		frappe.local.sync_in_progress = True

		# Find all sync chains that include this DocType
		chains = frappe.get_all("Sync Chain Step",
			filters={"doctype_name": doc.doctype},
			fields=["parent"]
		)

		# Execute sync for each chain
		for chain in chains:
			# Check if chain is active
			chain_doc = frappe.get_cached_doc("Sync Chain", chain.parent)
			if not chain_doc.is_active:
				continue

			try:
				sync_engine = SimpleSyncEngine(chain.parent)
				sync_engine.execute_sync(doc, doc.doctype, method)
			except Exception as e:
				frappe.log_error(f"Chain sync failed for {chain.parent}: {str(e)}", "Document Event Sync")

	finally:
		frappe.local.sync_in_progress = False


@frappe.whitelist()
def manual_sync(docname: str, doctype: str, sync_chain: str):
	"""Manual sync trigger"""
	try:
		doc = frappe.get_doc(doctype, docname)
		sync_engine = SimpleSyncEngine(sync_chain)
		result = sync_engine.execute_sync(doc, doctype, "manual")

		return {
			"success": True,
			"result": result,
			"message": _("Manual sync completed")
		}

	except Exception as e:
		frappe.log_error(f"Manual sync failed: {str(e)}", "Manual Sync")
		return {
			"success": False,
			"error": str(e),
			"message": _("Manual sync failed: {0}").format(str(e))
		}


@frappe.whitelist()
def bulk_sync(filters: Dict[str, Any], sync_chain: str, limit: int = 100):
	"""Bulk sync multiple documents"""
	try:
		# Get chain configuration
		chain_doc = frappe.get_doc("Sync Chain", sync_chain)
		if not chain_doc.is_active:
			return {"success": False, "message": "Sync chain is inactive"}

		# Get first step DocType
		first_step = None
		for step in chain_doc.chain_steps:
			if step.step_number == 1:
				first_step = step
				break

		if not first_step:
			return {"success": False, "message": "No starting step found in sync chain"}

		# Get documents to sync
		if isinstance(filters, str):
			filters = json.loads(filters)

		documents = frappe.get_all(first_step.doctype_name, filters=filters, limit=limit)

		# Initialize sync engine
		sync_engine = SimpleSyncEngine(sync_chain)

		# Process documents
		results = {
			"total": len(documents),
			"success": 0,
			"failed": 0,
			"skipped": 0,
			"errors": []
		}

		for doc_ref in documents:
			try:
				doc = frappe.get_doc(first_step.doctype_name, doc_ref.name)
				result = sync_engine.execute_sync(doc, first_step.doctype_name, "manual")

				if result["status"] == "success":
					results["success"] += 1
				elif result["status"] in ["skipped", "completed"]:
					results["skipped"] += 1
				else:
					results["failed"] += 1
					results["errors"].append(f"{doc_ref.name}: {result.get('error', 'Unknown error')}")

			except Exception as e:
				results["failed"] += 1
				results["errors"].append(f"{doc_ref.name}: {str(e)}")

		return {
			"success": True,
			"results": results,
			"message": f"Bulk sync completed. Success: {results['success']}, Failed: {results['failed']}, Skipped: {results['skipped']}"
		}

	except Exception as e:
		frappe.log_error(f"Bulk sync failed: {str(e)}", "Bulk Sync")
		return {
			"success": False,
			"error": str(e),
			"message": f"Bulk sync failed: {str(e)}"
		}


@frappe.whitelist()
def get_sync_status(sync_chain: str, days: int = 7):
	"""Get sync status for monitoring"""
	try:
		# Get recent activities
		activities = frappe.get_all("Sync Activity Log",
			filters={
				"sync_chain": sync_chain,
				"creation": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -days)]
			},
			fields=["activity_type", "status", "creation", "source_doctype", "target_doctype"],
			order_by="creation desc",
			limit=100
		)

		# Calculate statistics
		stats = {
			"total_activities": len(activities),
			"success_count": len([a for a in activities if a.status == "Success"]),
			"failed_count": len([a for a in activities if a.status == "Failed"]),
			"pending_count": len([a for a in activities if a.status == "Pending Review"]),
			"last_activity": activities[0].creation if activities else None
		}

		# Success rate
		if stats["total_activities"] > 0:
			stats["success_rate"] = round((stats["success_count"] / stats["total_activities"]) * 100, 1)
		else:
			stats["success_rate"] = 0

		# Group activities by hour for trend analysis
		hourly_stats = {}
		for activity in activities:
			hour = activity.creation.strftime("%Y-%m-%d %H:00")
			if hour not in hourly_stats:
				hourly_stats[hour] = {"success": 0, "failed": 0}

			if activity.status == "Success":
				hourly_stats[hour]["success"] += 1
			elif activity.status == "Failed":
				hourly_stats[hour]["failed"] += 1

		return {
			"success": True,
			"stats": stats,
			"hourly_trend": hourly_stats,
			"recent_activities": activities[:10]  # Latest 10 activities
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


# Scheduled tasks
def scheduled_sync():
	"""Process scheduled sync chains (hourly)"""
	try:
		# Get chains with hourly sync frequency
		hourly_chains = frappe.get_all("Sync Chain",
			filters={
				"is_active": 1,
				"sync_frequency": "Every Hour"
			}
		)

		for chain in hourly_chains:
			try:
				process_scheduled_chain(chain.name, "hourly")
			except Exception as e:
				frappe.log_error(f"Hourly sync failed for chain {chain.name}: {str(e)}", "Scheduled Sync")

	except Exception as e:
		frappe.log_error(f"Scheduled sync processing failed: {str(e)}", "Scheduled Sync")


def daily_sync_cleanup():
	"""Daily sync maintenance tasks"""
	try:
		# Cleanup old activity logs (keep only 90 days)
		cutoff_date = frappe.utils.add_days(frappe.utils.nowdate(), -90)

		deleted_count = frappe.db.sql("""
			DELETE FROM `tabSync Activity Log`
			WHERE creation < %s AND status = 'Success'
		""", cutoff_date)

		if deleted_count:
			frappe.log_error(f"Cleaned up {deleted_count} old sync activity logs", "Daily Sync Cleanup")

		# Process daily sync chains
		daily_chains = frappe.get_all("Sync Chain",
			filters={
				"is_active": 1,
				"sync_frequency": "Daily"
			}
		)

		for chain in daily_chains:
			try:
				process_scheduled_chain(chain.name, "daily")
			except Exception as e:
				frappe.log_error(f"Daily sync failed for chain {chain.name}: {str(e)}", "Scheduled Sync")

	except Exception as e:
		frappe.log_error(f"Daily sync cleanup failed: {str(e)}", "Daily Sync Cleanup")


def process_scheduled_chain(chain_name: str, frequency: str):
	"""Process a scheduled sync chain"""
	chain_doc = frappe.get_doc("Sync Chain", chain_name)

	# Get first step DocType
	first_step = None
	for step in chain_doc.chain_steps:
		if step.step_number == 1:
			first_step = step
			break

	if not first_step:
		return

	# Get documents modified since last sync
	last_sync_time = get_last_sync_time(chain_name, frequency)

	filters = {
		"modified": [">=", last_sync_time]
	}

	documents = frappe.get_all(first_step.doctype_name, filters=filters, limit=1000)

	if not documents:
		return

	# Initialize sync engine
	sync_engine = SimpleSyncEngine(chain_name)

	# Process documents
	processed = 0
	for doc_ref in documents:
		try:
			doc = frappe.get_doc(first_step.doctype_name, doc_ref.name)
			sync_engine.execute_sync(doc, first_step.doctype_name, "scheduled")
			processed += 1

			# Commit every 50 documents to avoid timeout
			if processed % 50 == 0:
				frappe.db.commit()

		except Exception as e:
			frappe.log_error(f"Scheduled sync failed for {doc_ref.name}: {str(e)}", "Scheduled Chain Sync")

	# Update last sync time
	set_last_sync_time(chain_name, frequency)

	frappe.log_error(f"Scheduled sync completed for {chain_name}: {processed} documents processed", "Scheduled Sync")


def get_last_sync_time(chain_name: str, frequency: str) -> datetime:
	"""Get last sync time for scheduled processing"""
	cache_key = f"last_sync_time_{chain_name}_{frequency}"
	last_time = frappe.cache().get_value(cache_key)

	if last_time:
		return frappe.utils.get_datetime(last_time)

	# Default: 24 hours ago for daily, 1 hour ago for hourly
	if frequency == "daily":
		return frappe.utils.add_hours(frappe.utils.now_datetime(), -24)
	else:
		return frappe.utils.add_hours(frappe.utils.now_datetime(), -1)


def set_last_sync_time(chain_name: str, frequency: str):
	"""Set last sync time for scheduled processing"""
	cache_key = f"last_sync_time_{chain_name}_{frequency}"
	frappe.cache().set_value(cache_key, frappe.utils.now(), expires_in_sec=7 * 24 * 3600)  # 7 days