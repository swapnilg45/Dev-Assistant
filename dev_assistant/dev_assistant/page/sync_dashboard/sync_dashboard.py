# Copyright (c) 2025, Swapnil and contributors
# Dashboard API methods for Universal Sync System

import frappe
from frappe import _
from datetime import datetime, timedelta


@frappe.whitelist()
def get_dashboard_data(days=30):
	"""Get comprehensive dashboard data for sync monitoring"""
	try:
		# Convert days to int
		days = int(days)

		# Get active sync chains
		active_chains = frappe.get_all("Sync Chain",
			filters={"is_active": 1},
			fields=["name", "chain_name", "description", "template_used", "creation", "sync_frequency"]
		)

		# Get recent activity summary
		cutoff_date = frappe.utils.add_days(frappe.utils.nowdate(), -days)
		recent_activities = frappe.get_all("Sync Activity Log",
			filters={"creation": [">=", cutoff_date]},
			fields=[
				"name", "activity_type", "status", "sync_chain", "creation",
				"source_doctype", "target_doctype", "message"
			],
			order_by="creation desc",
			limit=50
		)

		# Get success/failure stats by chain
		chain_stats = frappe.db.sql("""
			SELECT
				sync_chain,
				COUNT(*) as total_syncs,
				SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) as successful_syncs,
				SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed_syncs,
				SUM(CASE WHEN status = 'Pending Review' THEN 1 ELSE 0 END) as pending_syncs,
				MAX(sync_timestamp) as last_sync
			FROM `tabSync Activity Log`
			WHERE creation >= %s
			GROUP BY sync_chain
			ORDER BY total_syncs DESC
		""", cutoff_date, as_dict=True)

		# Get pending reviews
		pending_reviews = frappe.get_all("Sync Activity Log",
			filters={"status": "Pending Review"},
			fields=[
				"name", "sync_chain", "source_document", "source_doctype",
				"target_document", "target_doctype", "creation", "message"
			],
			order_by="creation desc"
		)

		# Calculate overall statistics
		total_chains = len(active_chains)
		total_activities = len(recent_activities)
		total_success = sum(stat['successful_syncs'] for stat in chain_stats)
		total_failed = sum(stat['failed_syncs'] for stat in chain_stats)
		total_pending = sum(stat['pending_syncs'] for stat in chain_stats)

		# Calculate success rate
		success_rate = 0
		if total_activities > 0:
			success_rate = round((total_success / (total_success + total_failed + total_pending)) * 100, 1)

		# Get hourly activity trend for charts
		hourly_trend = get_hourly_activity_trend(days)

		# Get chain health status
		chain_health = calculate_chain_health(chain_stats)

		return {
			"overview": {
				"total_chains": total_chains,
				"total_activities": total_activities,
				"successful_syncs": total_success,
				"failed_syncs": total_failed,
				"pending_reviews": len(pending_reviews),
				"success_rate": success_rate
			},
			"active_chains": active_chains,
			"recent_activities": recent_activities,
			"chain_stats": chain_stats,
			"pending_reviews": pending_reviews,
			"hourly_trend": hourly_trend,
			"chain_health": chain_health
		}

	except Exception as e:
		frappe.log_error(f"Dashboard data fetch failed: {str(e)}", "Sync Dashboard")
		return {"error": str(e)}


@frappe.whitelist()
def get_chain_details(chain_name):
	"""Get detailed information about a specific sync chain"""
	try:
		chain_doc = frappe.get_doc("Sync Chain", chain_name)

		# Get step details
		steps = []
		for step in chain_doc.chain_steps:
			step_info = {
				"step_number": step.step_number,
				"doctype_name": step.doctype_name,
				"doctype_label": step.doctype_label or step.doctype_name,
				"sync_condition": step.sync_condition,
				"field_mappings_count": len(frappe.parse_json(step.field_mappings or "{}"))
			}

			# Get record count for this DocType
			try:
				step_info["record_count"] = frappe.db.count(step.doctype_name)
			except:
				step_info["record_count"] = "N/A"

			steps.append(step_info)

		# Get recent activity for this chain
		recent_activities = frappe.get_all("Sync Activity Log",
			filters={"sync_chain": chain_name},
			fields=["activity_type", "status", "message", "creation", "source_doctype", "target_doctype"],
			order_by="creation desc",
			limit=20
		)

		# Get performance metrics
		performance_metrics = get_chain_performance_metrics(chain_name)

		return {
			"chain": {
				"name": chain_doc.name,
				"chain_name": chain_doc.chain_name,
				"description": chain_doc.description,
				"is_active": chain_doc.is_active,
				"template_used": chain_doc.template_used,
				"sync_frequency": chain_doc.sync_frequency,
				"conflict_resolution": chain_doc.conflict_resolution,
				"creation": chain_doc.creation
			},
			"steps": steps,
			"recent_activities": recent_activities,
			"performance": performance_metrics
		}

	except Exception as e:
		frappe.log_error(f"Chain details fetch failed: {str(e)}", "Sync Dashboard")
		return {"error": str(e)}


def get_hourly_activity_trend(days):
	"""Get hourly activity trend data for charts"""
	try:
		cutoff_date = frappe.utils.add_days(frappe.utils.nowdate(), -days)

		activities = frappe.db.sql("""
			SELECT
				DATE_FORMAT(creation, '%%Y-%%m-%%d %%H:00:00') as hour,
				COUNT(*) as total,
				SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) as success,
				SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed
			FROM `tabSync Activity Log`
			WHERE creation >= %s
			GROUP BY DATE_FORMAT(creation, '%%Y-%%m-%%d %%H:00:00')
			ORDER BY hour
		""", cutoff_date, as_dict=True)

		return activities

	except Exception as e:
		frappe.log_error(f"Hourly trend calculation failed: {str(e)}", "Sync Dashboard")
		return []


def calculate_chain_health(chain_stats):
	"""Calculate health status for each chain"""
	health_data = []

	for stat in chain_stats:
		total = stat['total_syncs']
		success = stat['successful_syncs']
		failed = stat['failed_syncs']

		if total == 0:
			health_status = "inactive"
			health_score = 0
		else:
			success_rate = (success / total) * 100
			if success_rate >= 95:
				health_status = "excellent"
				health_score = 100
			elif success_rate >= 85:
				health_status = "good"
				health_score = 85
			elif success_rate >= 70:
				health_status = "warning"
				health_score = 70
			else:
				health_status = "critical"
				health_score = success_rate

		health_data.append({
			"sync_chain": stat['sync_chain'],
			"health_status": health_status,
			"health_score": round(health_score, 1),
			"success_rate": round((success / total * 100) if total > 0 else 0, 1),
			"last_sync": stat['last_sync']
		})

	return health_data


def get_chain_performance_metrics(chain_name):
	"""Get performance metrics for a specific chain"""
	try:
		# Get metrics for last 30 days
		cutoff_date = frappe.utils.add_days(frappe.utils.nowdate(), -30)

		metrics = frappe.db.sql("""
			SELECT
				COUNT(*) as total_executions,
				AVG(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) * 100 as avg_success_rate,
				COUNT(DISTINCT DATE(creation)) as active_days,
				MIN(creation) as first_activity,
				MAX(creation) as last_activity
			FROM `tabSync Activity Log`
			WHERE sync_chain = %s AND creation >= %s
		""", [chain_name, cutoff_date], as_dict=True)

		if metrics:
			return metrics[0]
		else:
			return {
				"total_executions": 0,
				"avg_success_rate": 0,
				"active_days": 0,
				"first_activity": None,
				"last_activity": None
			}

	except Exception as e:
		frappe.log_error(f"Performance metrics calculation failed: {str(e)}", "Sync Dashboard")
		return {}


@frappe.whitelist()
def get_system_health():
	"""Get overall system health metrics"""
	try:
		# Get system-wide metrics
		total_chains = frappe.db.count("Sync Chain", {"is_active": 1})
		total_logs_today = frappe.db.count("Sync Activity Log", {
			"creation": [">=", frappe.utils.today()]
		})

		# Get error rate for last 24 hours
		error_count = frappe.db.count("Sync Activity Log", {
			"creation": [">=", frappe.utils.add_hours(frappe.utils.now(), -24)],
			"status": "Failed"
		})

		total_count = frappe.db.count("Sync Activity Log", {
			"creation": [">=", frappe.utils.add_hours(frappe.utils.now(), -24)]
		})

		error_rate = (error_count / total_count * 100) if total_count > 0 else 0

		# Get resource usage (simplified)
		avg_processing_time = frappe.db.sql("""
			SELECT AVG(TIMESTAMPDIFF(SECOND, creation, modified)) as avg_time
			FROM `tabSync Activity Log`
			WHERE creation >= %s AND status = 'Success'
		""", frappe.utils.add_hours(frappe.utils.now(), -24))

		processing_time = avg_processing_time[0][0] if avg_processing_time and avg_processing_time[0][0] else 0

		# System health score
		health_score = 100
		if error_rate > 10:
			health_score -= 30
		elif error_rate > 5:
			health_score -= 15

		if processing_time > 10:
			health_score -= 20
		elif processing_time > 5:
			health_score -= 10

		health_status = "excellent"
		if health_score < 70:
			health_status = "critical"
		elif health_score < 85:
			health_status = "warning"
		elif health_score < 95:
			health_status = "good"

		return {
			"total_active_chains": total_chains,
			"daily_activities": total_logs_today,
			"error_rate": round(error_rate, 1),
			"avg_processing_time": round(processing_time, 2),
			"health_score": round(health_score, 1),
			"health_status": health_status,
			"last_updated": frappe.utils.now()
		}

	except Exception as e:
		frappe.log_error(f"System health calculation failed: {str(e)}", "Sync Dashboard")
		return {"error": str(e)}


@frappe.whitelist()
def get_template_usage_stats():
	"""Get template usage statistics"""
	try:
		stats = frappe.db.sql("""
			SELECT
				template_used,
				COUNT(*) as usage_count,
				AVG(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) * 100 as active_rate
			FROM `tabSync Chain`
			WHERE template_used IS NOT NULL AND template_used != ''
			GROUP BY template_used
			ORDER BY usage_count DESC
		""", as_dict=True)

		return stats

	except Exception as e:
		frappe.log_error(f"Template usage stats failed: {str(e)}", "Sync Dashboard")
		return []


@frappe.whitelist()
def export_dashboard_data(format_type="json", days=30):
	"""Export dashboard data for reporting"""
	try:
		dashboard_data = get_dashboard_data(days)

		if format_type == "csv":
			# Convert to CSV format
			import csv
			import io

			output = io.StringIO()
			writer = csv.writer(output)

			# Write chain statistics
			writer.writerow(["Chain Name", "Total Syncs", "Successful", "Failed", "Success Rate"])
			for stat in dashboard_data.get("chain_stats", []):
				success_rate = 0
				if stat["total_syncs"] > 0:
					success_rate = round((stat["successful_syncs"] / stat["total_syncs"]) * 100, 1)

				writer.writerow([
					stat["sync_chain"],
					stat["total_syncs"],
					stat["successful_syncs"],
					stat["failed_syncs"],
					f"{success_rate}%"
				])

			return {
				"success": True,
				"data": output.getvalue(),
				"filename": f"sync_dashboard_{frappe.utils.today()}.csv"
			}

		else:
			# Return JSON format
			return {
				"success": True,
				"data": dashboard_data,
				"filename": f"sync_dashboard_{frappe.utils.today()}.json"
			}

	except Exception as e:
		return {"success": False, "error": str(e)}