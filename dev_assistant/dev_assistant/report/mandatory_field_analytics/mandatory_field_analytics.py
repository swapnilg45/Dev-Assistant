# Copyright (c) 2024, Swapnil and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import datetime, timedelta


def execute(filters=None):
	"""Generate Mandatory Field Analytics Report."""
	columns = get_columns()
	data = get_data(filters)
	charts = get_charts(data)
	summary = get_summary(data)

	return columns, data, None, charts, summary


def get_columns():
	"""Define report columns."""
	return [
		{
			"label": _("Controller Name"),
			"fieldname": "name",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"label": _("Document Type"),
			"fieldname": "document_type",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Priority"),
			"fieldname": "priority",
			"fieldtype": "Select",
			"options": "Low\nMedium\nHigh\nCritical",
			"width": 100
		},
		{
			"label": _("Execution Mode"),
			"fieldname": "execution_mode",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("Status"),
			"fieldname": "enabled",
			"fieldtype": "Data",
			"width": 80
		},
		{
			"label": _("Conditions"),
			"fieldname": "condition_count",
			"fieldtype": "Int",
			"width": 90
		},
		{
			"label": _("Mandatory Fields"),
			"fieldname": "field_count",
			"fieldtype": "Int",
			"width": 120
		},
		{
			"label": _("Created By"),
			"fieldname": "owner",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Created On"),
			"fieldname": "creation",
			"fieldtype": "Datetime",
			"width": 150
		},
		{
			"label": _("Last Modified"),
			"fieldname": "modified",
			"fieldtype": "Datetime",
			"width": 150
		}
	]


def get_data(filters):
	"""Fetch report data based on filters."""
	conditions = build_conditions(filters)

	data = frappe.db.sql("""
		SELECT
			mfc.name,
			mfc.document_type,
			mfc.priority,
			mfc.execution_mode,
			IF(mfc.enabled, 'Active', 'Disabled') as enabled,
			(SELECT COUNT(*) FROM `tabMandatory Field Condition` WHERE parent = mfc.name) as condition_count,
			(SELECT COUNT(*) FROM `tabMandatory Field Detail` WHERE parent = mfc.name) as field_count,
			mfc.owner,
			mfc.creation,
			mfc.modified
		FROM
			`tabMandatory Field Controller` mfc
		WHERE
			{conditions}
		ORDER BY
			mfc.priority DESC, mfc.modified DESC
	""".format(conditions=conditions), as_dict=1)

	return data


def build_conditions(filters):
	"""Build SQL conditions from filters."""
	conditions = ["1=1"]

	if filters:
		if filters.get("document_type"):
			conditions.append(f"mfc.document_type = '{filters['document_type']}'")

		if filters.get("priority"):
			conditions.append(f"mfc.priority = '{filters['priority']}'")

		if filters.get("execution_mode"):
			conditions.append(f"mfc.execution_mode = '{filters['execution_mode']}'")

		if filters.get("enabled"):
			enabled_value = 1 if filters["enabled"] == "Active" else 0
			conditions.append(f"mfc.enabled = {enabled_value}")

		if filters.get("owner"):
			conditions.append(f"mfc.owner = '{filters['owner']}'")

		if filters.get("from_date"):
			conditions.append(f"DATE(mfc.creation) >= '{filters['from_date']}'")

		if filters.get("to_date"):
			conditions.append(f"DATE(mfc.creation) <= '{filters['to_date']}'")

	return " AND ".join(conditions)


def get_charts(data):
	"""Generate chart configurations."""
	charts = []

	# Priority Distribution Chart
	priority_data = {}
	for row in data:
		priority = row.get("priority", "Not Set")
		priority_data[priority] = priority_data.get(priority, 0) + 1

	charts.append({
		"title": _("Rules by Priority"),
		"data": {
			"labels": list(priority_data.keys()),
			"datasets": [{
				"values": list(priority_data.values())
			}]
		},
		"type": "donut",
		"height": 300
	})

	# Document Type Distribution
	doctype_data = {}
	for row in data:
		doctype = row.get("document_type", "Not Set")
		doctype_data[doctype] = doctype_data.get(doctype, 0) + 1

	# Get top 10 doctypes
	sorted_doctypes = sorted(doctype_data.items(), key=lambda x: x[1], reverse=True)[:10]

	if sorted_doctypes:
		charts.append({
			"title": _("Top 10 Document Types"),
			"data": {
				"labels": [d[0] for d in sorted_doctypes],
				"datasets": [{
					"name": "Rules",
					"values": [d[1] for d in sorted_doctypes]
				}]
			},
			"type": "bar",
			"height": 300
		})

	# Timeline Chart - Rules created over time
	timeline_data = {}
	for row in data:
		date_key = row.get("creation").date() if row.get("creation") else None
		if date_key:
			timeline_data[str(date_key)] = timeline_data.get(str(date_key), 0) + 1

	if timeline_data:
		sorted_timeline = sorted(timeline_data.items())
		charts.append({
			"title": _("Rules Created Over Time"),
			"data": {
				"labels": [d[0] for d in sorted_timeline],
				"datasets": [{
					"name": "Rules Created",
					"values": [d[1] for d in sorted_timeline]
				}]
			},
			"type": "line",
			"height": 300
		})

	return charts


def get_summary(data):
	"""Generate summary statistics."""
	if not data:
		# Show helpful cards when no data
		return [
			{
				"value": 0,
				"label": _("Total Rules"),
				"datatype": "Int",
				"color": "blue"
			},
			{
				"value": "Get Started",
				"label": _("Create your first Mandatory Field Rule"),
				"datatype": "Data",
				"color": "green"
			},
			{
				"value": "Documentation",
				"label": _("Check help for setup guide"),
				"datatype": "Data",
				"color": "orange"
			}
		]

	total_rules = len(data)
	active_rules = len([d for d in data if d.get("enabled") == "Active"])
	critical_rules = len([d for d in data if d.get("priority") == "Critical"])

	# Calculate average conditions and fields
	total_conditions = sum([d.get("condition_count", 0) for d in data])
	total_fields = sum([d.get("field_count", 0) for d in data])
	avg_conditions = round(total_conditions / total_rules, 1) if total_rules else 0
	avg_fields = round(total_fields / total_rules, 1) if total_rules else 0

	# Get unique document types
	unique_doctypes = len(set([d.get("document_type") for d in data if d.get("document_type")]))

	summary = [
		{
			"value": total_rules,
			"label": _("Total Rules"),
			"datatype": "Int",
			"color": "blue"
		},
		{
			"value": active_rules,
			"label": _("Active Rules"),
			"datatype": "Int",
			"color": "green"
		},
		{
			"value": critical_rules,
			"label": _("Critical Priority"),
			"datatype": "Int",
			"color": "red"
		},
		{
			"value": unique_doctypes,
			"label": _("Document Types"),
			"datatype": "Int",
			"color": "orange"
		},
		{
			"value": avg_conditions,
			"label": _("Avg Conditions/Rule"),
			"datatype": "Float",
			"color": "purple"
		},
		{
			"value": avg_fields,
			"label": _("Avg Fields/Rule"),
			"datatype": "Float",
			"color": "yellow"
		}
	]

	return summary