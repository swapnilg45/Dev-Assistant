# Copyright (c) 2025, Swapnil and contributors
# Pre-built sync templates for common business processes

import frappe
from frappe import _
import json


# Pre-built sync templates for common business workflows
SYNC_TEMPLATES = {
	"crm_process": {
		"name": "CRM Sales Process",
		"description": "Lead → Opportunity → Quotation → Sales Order",
		"icon": "fa fa-users",
		"category": "Sales & Marketing",
		"steps": [
			{
				"step_number": 1,
				"doctype_name": "Lead",
				"doctype_label": "Lead",
				"sync_condition": "Status Changes",
				"field_mappings": {
					"lead_name": "customer_name",
					"email_id": "contact_email",
					"phone": "contact_phone",
					"company": "company",
					"lead_owner": "contact_person",
					"source": "source",
					"industry": "industry"
				}
			},
			{
				"step_number": 2,
				"doctype_name": "Opportunity",
				"doctype_label": "Opportunity",
				"sync_condition": "Status Changes",
				"field_mappings": {
					"customer_name": "party_name",
					"contact_email": "contact_email",
					"contact_phone": "contact_mobile",
					"opportunity_amount": "opportunity_amount",
					"company": "company",
					"source": "source",
					"contact_person": "contact_person"
				}
			},
			{
				"step_number": 3,
				"doctype_name": "Quotation",
				"doctype_label": "Quotation",
				"sync_condition": "Always",
				"field_mappings": {
					"party_name": "customer_name",
					"contact_email": "contact_email",
					"contact_mobile": "contact_mobile",
					"opportunity_amount": "grand_total",
					"company": "company"
				}
			},
			{
				"step_number": 4,
				"doctype_name": "Sales Order",
				"doctype_label": "Sales Order",
				"sync_condition": "Always",
				"field_mappings": {
					"customer_name": "customer",
					"grand_total": "grand_total",
					"contact_email": "contact_email",
					"contact_mobile": "contact_mobile",
					"company": "company"
				}
			}
		],
		"benefits": [
			"Automatically track leads through entire sales funnel",
			"Reduce data entry across sales documents",
			"Maintain consistent customer information",
			"Track conversion rates and sales performance"
		]
	},

	"hr_process": {
		"name": "HR Hiring Process",
		"description": "Job Applicant → Interview → Employee → Onboarding",
		"icon": "fa fa-user-plus",
		"category": "Human Resources",
		"steps": [
			{
				"step_number": 1,
				"doctype_name": "Job Applicant",
				"doctype_label": "Job Applicant",
				"sync_condition": "Status Changes",
				"field_mappings": {
					"applicant_name": "employee_name",
					"email_id": "personal_email",
					"phone_number": "cell_number",
					"designation": "designation",
					"department": "department",
					"date_of_birth": "date_of_birth",
					"gender": "gender"
				}
			},
			{
				"step_number": 2,
				"doctype_name": "Interview",
				"doctype_label": "Interview",
				"sync_condition": "Always",
				"field_mappings": {
					"job_applicant": "job_applicant",
					"interview_date": "scheduled_on",
					"designation": "designation",
					"department": "department"
				}
			},
			{
				"step_number": 3,
				"doctype_name": "Employee",
				"doctype_label": "Employee",
				"sync_condition": "Always",
				"field_mappings": {
					"employee_name": "employee_name",
					"personal_email": "personal_email",
					"cell_number": "cell_number",
					"designation": "designation",
					"department": "department",
					"date_of_birth": "date_of_birth",
					"gender": "gender",
					"date_of_joining": "date_of_joining"
				}
			},
			{
				"step_number": 4,
				"doctype_name": "Employee Onboarding",
				"doctype_label": "Onboarding",
				"sync_condition": "Always",
				"field_mappings": {
					"employee": "employee",
					"date_of_joining": "date_of_joining",
					"designation": "designation",
					"department": "department"
				}
			}
		],
		"benefits": [
			"Streamline hiring process from application to onboarding",
			"Maintain consistent employee data across HR modules",
			"Reduce manual data entry during hiring",
			"Track hiring metrics and process efficiency"
		]
	},

	"project_process": {
		"name": "Project Management Process",
		"description": "Lead → Project → Task → Timesheet",
		"icon": "fa fa-project-diagram",
		"category": "Project Management",
		"steps": [
			{
				"step_number": 1,
				"doctype_name": "Lead",
				"doctype_label": "Lead",
				"sync_condition": "Status Changes",
				"field_mappings": {
					"lead_name": "customer",
					"email_id": "contact_email",
					"phone": "contact_phone",
					"company": "company"
				}
			},
			{
				"step_number": 2,
				"doctype_name": "Project",
				"doctype_label": "Project",
				"sync_condition": "Always",
				"field_mappings": {
					"customer": "customer",
					"contact_email": "contact_email",
					"contact_phone": "contact_phone",
					"project_name": "project_name",
					"company": "company"
				}
			},
			{
				"step_number": 3,
				"doctype_name": "Task",
				"doctype_label": "Task",
				"sync_condition": "Always",
				"field_mappings": {
					"project": "project",
					"subject": "subject",
					"company": "company"
				}
			},
			{
				"step_number": 4,
				"doctype_name": "Timesheet",
				"doctype_label": "Timesheet",
				"sync_condition": "Always",
				"field_mappings": {
					"project": "project_name",
					"task": "task",
					"company": "company"
				}
			}
		],
		"benefits": [
			"Connect leads directly to project delivery",
			"Maintain project hierarchy and relationships",
			"Track time and resources across project lifecycle",
			"Improve project profitability analysis"
		]
	},

	"purchase_process": {
		"name": "Purchase to Payment Process",
		"description": "Material Request → Purchase Order → Receipt → Invoice",
		"icon": "fa fa-shopping-cart",
		"category": "Procurement",
		"steps": [
			{
				"step_number": 1,
				"doctype_name": "Material Request",
				"doctype_label": "Material Request",
				"sync_condition": "Status Changes",
				"field_mappings": {
					"company": "company",
					"schedule_date": "required_date"
				}
			},
			{
				"step_number": 2,
				"doctype_name": "Purchase Order",
				"doctype_label": "Purchase Order",
				"sync_condition": "Always",
				"field_mappings": {
					"company": "company",
					"required_date": "schedule_date",
					"supplier": "supplier",
					"grand_total": "grand_total"
				}
			},
			{
				"step_number": 3,
				"doctype_name": "Purchase Receipt",
				"doctype_label": "Purchase Receipt",
				"sync_condition": "Always",
				"field_mappings": {
					"company": "company",
					"supplier": "supplier",
					"grand_total": "grand_total",
					"purchase_order": "purchase_order"
				}
			},
			{
				"step_number": 4,
				"doctype_name": "Purchase Invoice",
				"doctype_label": "Purchase Invoice",
				"sync_condition": "Always",
				"field_mappings": {
					"company": "company",
					"supplier": "supplier",
					"grand_total": "grand_total",
					"purchase_order": "purchase_order",
					"purchase_receipt": "purchase_receipt"
				}
			}
		],
		"benefits": [
			"Streamline procurement process from request to payment",
			"Maintain accurate purchase order tracking",
			"Ensure proper invoice matching and approval",
			"Improve procurement analytics and cost control"
		]
	},

	"manufacturing_process": {
		"name": "Manufacturing Process",
		"description": "Sales Order → Work Order → Job Card → Stock Entry",
		"icon": "fa fa-industry",
		"category": "Manufacturing",
		"steps": [
			{
				"step_number": 1,
				"doctype_name": "Sales Order",
				"doctype_label": "Sales Order",
				"sync_condition": "Status Changes",
				"field_mappings": {
					"customer": "customer",
					"company": "company",
					"delivery_date": "planned_start_date"
				}
			},
			{
				"step_number": 2,
				"doctype_name": "Work Order",
				"doctype_label": "Work Order",
				"sync_condition": "Always",
				"field_mappings": {
					"customer": "customer",
					"company": "company",
					"planned_start_date": "planned_start_date",
					"sales_order": "sales_order"
				}
			},
			{
				"step_number": 3,
				"doctype_name": "Job Card",
				"doctype_label": "Job Card",
				"sync_condition": "Always",
				"field_mappings": {
					"work_order": "work_order",
					"company": "company"
				}
			},
			{
				"step_number": 4,
				"doctype_name": "Stock Entry",
				"doctype_label": "Stock Entry",
				"sync_condition": "Always",
				"field_mappings": {
					"work_order": "work_order",
					"company": "company"
				}
			}
		],
		"benefits": [
			"Connect sales orders directly to manufacturing execution",
			"Track production progress in real-time",
			"Maintain accurate work order status",
			"Improve manufacturing efficiency and planning"
		]
	}
}


def get_template(template_name):
	"""Get template configuration by name"""
	return SYNC_TEMPLATES.get(template_name, {})


def get_all_templates():
	"""Get all available templates"""
	return SYNC_TEMPLATES


def get_templates_by_category():
	"""Get templates organized by category"""
	categories = {}
	for template_key, template in SYNC_TEMPLATES.items():
		category = template.get('category', 'Other')
		if category not in categories:
			categories[category] = []
		categories[category].append({
			'key': template_key,
			'template': template
		})
	return categories


def create_chain_from_template(template_name, chain_name=None):
	"""Create a new Sync Chain from template"""
	template = get_template(template_name)
	if not template:
		frappe.throw(_("Template '{}' not found").format(template_name))

	# Create new sync chain document
	chain_doc = frappe.new_doc("Sync Chain")
	chain_doc.chain_name = chain_name or template["name"]
	chain_doc.description = template["description"]
	chain_doc.template_used = template_name
	chain_doc.is_active = 1

	# Add steps from template
	for step_data in template["steps"]:
		step_row = chain_doc.append("chain_steps")
		step_row.step_number = step_data["step_number"]
		step_row.doctype_name = step_data["doctype_name"]
		step_row.doctype_label = step_data["doctype_label"]
		step_row.sync_condition = step_data["sync_condition"]
		step_row.field_mappings = json.dumps(step_data["field_mappings"], indent=2)

	# Save the chain
	chain_doc.insert()

	return chain_doc


def customize_template(template_name, customizations):
	"""Create a customized version of a template"""
	template = get_template(template_name)
	if not template:
		frappe.throw(_("Template '{}' not found").format(template_name))

	# Apply customizations
	customized_template = template.copy()

	if 'name' in customizations:
		customized_template['name'] = customizations['name']

	if 'description' in customizations:
		customized_template['description'] = customizations['description']

	if 'steps' in customizations:
		# Merge step customizations
		for step_custom in customizations['steps']:
			step_number = step_custom.get('step_number')
			for i, step in enumerate(customized_template['steps']):
				if step['step_number'] == step_number:
					customized_template['steps'][i].update(step_custom)
					break

	return customized_template


def validate_template_compatibility(template_name):
	"""Validate if template DocTypes are available in current system"""
	template = get_template(template_name)
	if not template:
		return {"valid": False, "errors": [f"Template '{template_name}' not found"]}

	errors = []
	warnings = []

	for step in template["steps"]:
		doctype_name = step["doctype_name"]

		# Check if DocType exists
		if not frappe.db.exists("DocType", doctype_name):
			errors.append(f"DocType '{doctype_name}' not found in system")
			continue

		# Check if DocType is accessible
		try:
			meta = frappe.get_meta(doctype_name)
			if meta.issingle:
				warnings.append(f"DocType '{doctype_name}' is a single DocType (may not be suitable for sync)")
		except frappe.PermissionError:
			warnings.append(f"No permission to access DocType '{doctype_name}'")

		# Validate field mappings
		if "field_mappings" in step:
			try:
				meta = frappe.get_meta(doctype_name)
				valid_fields = {field.fieldname for field in meta.fields}

				for field_name in step["field_mappings"].keys():
					if field_name not in valid_fields:
						warnings.append(f"Field '{field_name}' not found in {doctype_name}")
			except Exception:
				warnings.append(f"Could not validate fields for {doctype_name}")

	return {
		"valid": len(errors) == 0,
		"errors": errors,
		"warnings": warnings
	}


@frappe.whitelist()
def get_all_templates_api():
	"""API endpoint to get all templates"""
	return get_all_templates()


@frappe.whitelist()
def get_templates_by_category_api():
	"""API endpoint to get templates by category"""
	return get_templates_by_category()


@frappe.whitelist()
def get_template_api(template_name):
	"""API endpoint to get specific template"""
	template = get_template(template_name)
	if not template:
		frappe.throw(_("Template not found"))
	return template


@frappe.whitelist()
def create_chain_from_template_api(template_name, chain_name=None):
	"""API endpoint to create sync chain from template"""
	try:
		# Validate template compatibility first
		validation = validate_template_compatibility(template_name)
		if not validation["valid"]:
			frappe.throw(_("Template validation failed: {}").format(", ".join(validation["errors"])))

		chain_doc = create_chain_from_template(template_name, chain_name)

		return {
			"success": True,
			"chain_name": chain_doc.name,
			"chain_title": chain_doc.chain_name,
			"message": _("Sync chain created successfully from {} template").format(template_name),
			"warnings": validation.get("warnings", [])
		}
	except Exception as e:
		frappe.log_error(f"Template creation failed: {str(e)}", "Sync Chain Template")
		return {
			"success": False,
			"message": _("Failed to create chain from template: {}").format(str(e))
		}


@frappe.whitelist()
def validate_template_compatibility_api(template_name):
	"""API endpoint to validate template compatibility"""
	return validate_template_compatibility(template_name)


@frappe.whitelist()
def preview_template_api(template_name):
	"""API endpoint to preview template before creation"""
	template = get_template(template_name)
	if not template:
		frappe.throw(_("Template not found"))

	validation = validate_template_compatibility(template_name)

	return {
		"template": template,
		"validation": validation,
		"step_count": len(template.get("steps", [])),
		"estimated_setup_time": "5-10 minutes"
	}


@frappe.whitelist()
def get_template_usage_stats():
	"""Get usage statistics for templates"""
	stats = {}

	# Get usage count for each template
	for template_name in SYNC_TEMPLATES.keys():
		count = frappe.db.count("Sync Chain", {"template_used": template_name})
		stats[template_name] = {
			"usage_count": count,
			"template_info": SYNC_TEMPLATES[template_name]
		}

	# Sort by usage
	sorted_stats = dict(sorted(stats.items(), key=lambda x: x[1]["usage_count"], reverse=True))

	return sorted_stats


def install_sample_templates():
	"""Install sample sync chains for demonstration"""
	sample_templates = ["crm_process", "hr_process"]

	for template_name in sample_templates:
		chain_name = f"Sample {SYNC_TEMPLATES[template_name]['name']}"

		# Check if sample already exists
		if frappe.db.exists("Sync Chain", {"chain_name": chain_name}):
			continue

		try:
			chain_doc = create_chain_from_template(template_name, chain_name)
			chain_doc.is_active = 0  # Keep samples inactive
			chain_doc.description = f"Sample template: {chain_doc.description}"
			chain_doc.save()

			frappe.logger().info(f"Created sample sync chain: {chain_name}")
		except Exception as e:
			frappe.logger().error(f"Failed to create sample chain {chain_name}: {str(e)}")


@frappe.whitelist()
def export_template(sync_chain_name):
	"""Export existing sync chain as a template"""
	try:
		chain_doc = frappe.get_doc("Sync Chain", sync_chain_name)

		template = {
			"name": f"Custom {chain_doc.chain_name}",
			"description": chain_doc.description or f"Custom template from {chain_doc.chain_name}",
			"icon": "fa fa-cog",
			"category": "Custom",
			"steps": []
		}

		for step in chain_doc.chain_steps:
			step_data = {
				"step_number": step.step_number,
				"doctype_name": step.doctype_name,
				"doctype_label": step.doctype_label or step.doctype_name,
				"sync_condition": step.sync_condition,
				"field_mappings": json.loads(step.field_mappings or "{}")
			}
			template["steps"].append(step_data)

		return template

	except Exception as e:
		frappe.throw(_("Failed to export template: {}").format(str(e)))