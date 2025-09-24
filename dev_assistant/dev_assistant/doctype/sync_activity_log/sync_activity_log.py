# Copyright (c) 2025, Swapnil and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now


class SyncActivityLog(Document):
	def before_insert(self):
		"""Set default values before inserting"""
		if not self.sync_timestamp:
			self.sync_timestamp = now()

	def validate(self):
		"""Validate sync activity log"""
		self.validate_documents()

	def validate_documents(self):
		"""Validate source and target document references"""
		# Validate source document
		if self.source_document and self.source_doctype:
			if not frappe.db.exists(self.source_doctype, self.source_document):
				frappe.msgprint(f"Warning: Source document {self.source_doctype} {self.source_document} does not exist")

		# Validate target document
		if self.target_document and self.target_doctype:
			if not frappe.db.exists(self.target_doctype, self.target_document):
				frappe.msgprint(f"Warning: Target document {self.target_doctype} {self.target_document} does not exist")

	@frappe.whitelist()
	def retry_sync(self):
		"""Retry failed sync operation"""
		if self.status != "Failed":
			frappe.throw("Only failed sync operations can be retried")

		from dev_assistant.dev_assistant.universal_sync.sync_engine import SimpleSyncEngine

		try:
			# Get source document
			source_doc = frappe.get_doc(self.source_doctype, self.source_document)

			# Initialize sync engine
			sync_engine = SimpleSyncEngine(self.sync_chain)

			# Execute sync
			result = sync_engine.execute_sync(source_doc, self.source_doctype, "manual")

			if result and result.get("status") == "success":
				# Update this log entry
				self.status = "Success"
				self.activity_type = "Data Synced"
				self.message = "Retry successful"
				self.error_details = ""
				self.sync_timestamp = now()
				self.save()

				return {
					"success": True,
					"message": "Sync retry completed successfully"
				}
			else:
				return {
					"success": False,
					"message": f"Sync retry failed: {result.get('error', 'Unknown error')}"
				}

		except Exception as e:
			frappe.log_error(f"Sync retry failed: {str(e)}", "Sync Activity Log")
			return {
				"success": False,
				"message": f"Sync retry failed: {str(e)}"
			}

	def get_formatted_duration(self):
		"""Get formatted duration since sync timestamp"""
		if self.sync_timestamp:
			return frappe.utils.pretty_date(self.sync_timestamp)
		return "Unknown"

	def get_status_indicator(self):
		"""Get status indicator for UI display"""
		status_map = {
			"Success": {"color": "green", "icon": "fa-check-circle"},
			"Failed": {"color": "red", "icon": "fa-exclamation-circle"},
			"Pending Review": {"color": "orange", "icon": "fa-clock"}
		}
		return status_map.get(self.status, {"color": "gray", "icon": "fa-question"})


@frappe.whitelist()
def create_sync_activity_log(sync_chain, activity_type, status="Success",
							  source_doc=None, target_doc=None, message=None, error_details=None):
	"""Create a sync activity log entry"""
	log = frappe.new_doc("Sync Activity Log")
	log.sync_chain = sync_chain
	log.activity_type = activity_type
	log.status = status
	log.message = message or ""
	log.sync_timestamp = now()

	if source_doc:
		log.source_document = source_doc.name
		log.source_doctype = source_doc.doctype

	if target_doc:
		log.target_document = target_doc.name
		log.target_doctype = target_doc.doctype

	if error_details:
		log.error_details = error_details

	log.insert(ignore_permissions=True)
	return log


@frappe.whitelist()
def get_sync_activity_summary(sync_chain=None, days=30):
	"""Get sync activity summary for dashboard"""
	conditions = ["sal.creation >= DATE_SUB(NOW(), INTERVAL %s DAY)"]
	values = [days]

	if sync_chain:
		conditions.append("sal.sync_chain = %s")
		values.append(sync_chain)

	condition_str = " AND ".join(conditions)

	summary = frappe.db.sql(f"""
		SELECT
			sal.sync_chain,
			sc.chain_name,
			COUNT(*) as total_activities,
			SUM(CASE WHEN sal.status = 'Success' THEN 1 ELSE 0 END) as successful,
			SUM(CASE WHEN sal.status = 'Failed' THEN 1 ELSE 0 END) as failed,
			SUM(CASE WHEN sal.status = 'Pending Review' THEN 1 ELSE 0 END) as pending_review,
			MAX(sal.sync_timestamp) as last_activity
		FROM `tabSync Activity Log` sal
		LEFT JOIN `tabSync Chain` sc ON sal.sync_chain = sc.name
		WHERE {condition_str}
		GROUP BY sal.sync_chain
		ORDER BY last_activity DESC
	""", values, as_dict=True)

	return summary


@frappe.whitelist()
def get_recent_activities(limit=20, sync_chain=None):
	"""Get recent sync activities"""
	filters = {}
	if sync_chain:
		filters["sync_chain"] = sync_chain

	activities = frappe.get_all("Sync Activity Log",
		filters=filters,
		fields=[
			"name", "sync_chain", "activity_type", "status", "sync_timestamp",
			"source_document", "source_doctype", "target_document", "target_doctype",
			"message"
		],
		order_by="sync_timestamp desc",
		limit=limit
	)

	# Add sync chain names
	for activity in activities:
		if activity.sync_chain:
			chain_doc = frappe.get_cached_value("Sync Chain", activity.sync_chain, "chain_name")
			activity["chain_name"] = chain_doc or activity.sync_chain

	return activities


@frappe.whitelist()
def cleanup_old_logs(days_to_keep=90):
	"""Cleanup old sync activity logs"""
	if not frappe.has_permission("Sync Activity Log", "delete"):
		frappe.throw("Insufficient permissions to cleanup logs")

	cutoff_date = frappe.utils.add_days(frappe.utils.nowdate(), -days_to_keep)

	deleted_count = frappe.db.sql("""
		DELETE FROM `tabSync Activity Log`
		WHERE creation < %s
		AND status = 'Success'
	""", cutoff_date)

	frappe.msgprint(f"Cleaned up {deleted_count} old sync activity logs")
	return deleted_count


@frappe.whitelist()
def resolve_pending_review(log_name, resolution, notes=None):
	"""Resolve a pending review activity"""
	log = frappe.get_doc("Sync Activity Log", log_name)

	if log.status != "Pending Review":
		frappe.throw("Only pending review activities can be resolved")

	if resolution == "approve":
		log.status = "Success"
		log.activity_type = "Data Synced"
		log.message = f"Manual review approved. {notes or ''}"
	elif resolution == "reject":
		log.status = "Failed"
		log.activity_type = "Error Occurred"
		log.message = f"Manual review rejected. {notes or ''}"
	else:
		frappe.throw("Invalid resolution. Use 'approve' or 'reject'")

	log.sync_timestamp = now()
	log.save()

	return {
		"success": True,
		"message": f"Review resolved successfully"
	}