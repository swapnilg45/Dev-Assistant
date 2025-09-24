# Copyright (c) 2025, Swapnil and contributors
# Installation and setup utilities for Universal Sync System

import frappe
from frappe import _


def after_install():
	"""Setup after installing the universal sync system"""
	try:
		# Create custom roles
		create_sync_roles()

		# Set up permissions
		setup_sync_permissions()

		# Create sample templates (if requested)
		# install_sample_templates()

		# Clear cache to refresh everything
		frappe.cache().delete_key("*")

		print("Universal Sync System installed successfully!")

	except Exception as e:
		frappe.log_error(f"Universal Sync installation failed: {str(e)}", "Sync Installation")


def create_sync_roles():
	"""Create custom roles for sync system"""
	roles_to_create = [
		{
			"role_name": "Sync Manager",
			"description": "Can create and manage sync processes"
		},
		{
			"role_name": "Sync User",
			"description": "Can view sync processes and activity"
		}
	]

	for role_info in roles_to_create:
		if not frappe.db.exists("Role", role_info["role_name"]):
			role_doc = frappe.get_doc({
				"doctype": "Role",
				"role_name": role_info["role_name"],
				"description": role_info["description"]
			})
			role_doc.insert()
			print(f"Created role: {role_info['role_name']}")


def setup_sync_permissions():
	"""Set up permissions for sync DocTypes"""

	# Define permission matrix
	permissions = [
		# Sync Chain permissions
		{
			"doctype": "Sync Chain",
			"role": "System Manager",
			"perms": ["read", "write", "create", "delete", "submit", "cancel", "amend"]
		},
		{
			"doctype": "Sync Chain",
			"role": "Sync Manager",
			"perms": ["read", "write", "create", "delete"]
		},
		{
			"doctype": "Sync Chain",
			"role": "Sync User",
			"perms": ["read"]
		},

		# Sync Activity Log permissions
		{
			"doctype": "Sync Activity Log",
			"role": "System Manager",
			"perms": ["read", "write", "create", "delete"]
		},
		{
			"doctype": "Sync Activity Log",
			"role": "Sync Manager",
			"perms": ["read", "write", "create"]
		},
		{
			"doctype": "Sync Activity Log",
			"role": "Sync User",
			"perms": ["read"]
		},

		# All users can read their own sync activities
		{
			"doctype": "Sync Activity Log",
			"role": "All",
			"perms": ["read"]
		}
	]

	for perm in permissions:
		create_doctype_permissions(
			perm["doctype"],
			perm["role"],
			perm["perms"]
		)


def create_doctype_permissions(doctype, role, permissions):
	"""Create permissions for a DocType and role"""
	try:
		# Check if permission already exists
		existing = frappe.db.exists("Custom DocPerm", {
			"parent": doctype,
			"role": role
		})

		if existing:
			return

		# Create permission doc
		perm_doc = {
			"doctype": "Custom DocPerm",
			"parent": doctype,
			"parenttype": "DocType",
			"parentfield": "permissions",
			"role": role,
			"read": 1 if "read" in permissions else 0,
			"write": 1 if "write" in permissions else 0,
			"create": 1 if "create" in permissions else 0,
			"delete": 1 if "delete" in permissions else 0,
			"submit": 1 if "submit" in permissions else 0,
			"cancel": 1 if "cancel" in permissions else 0,
			"amend": 1 if "amend" in permissions else 0,
			"report": 1 if "read" in permissions else 0,
			"export": 1 if "read" in permissions else 0,
			"print": 1 if "read" in permissions else 0,
			"email": 1 if "read" in permissions else 0,
			"share": 1 if "write" in permissions else 0
		}

		frappe.get_doc(perm_doc).insert()
		print(f"Created permissions for {role} on {doctype}")

	except Exception as e:
		frappe.log_error(f"Permission creation failed for {role} on {doctype}: {str(e)}", "Permission Setup")


def install_sample_templates():
	"""Install sample sync chains for demonstration"""
	from .sync_templates import create_chain_from_template

	sample_templates = [
		{
			"template_key": "crm_process",
			"chain_name": "Sample CRM Process",
			"activate": False
		}
	]

	for template in sample_templates:
		try:
			# Check if sample already exists
			if frappe.db.exists("Sync Chain", {"chain_name": template["chain_name"]}):
				continue

			chain_doc = create_chain_from_template(
				template["template_key"],
				template["chain_name"]
			)

			chain_doc.is_active = template["activate"]
			chain_doc.description = f"Sample template: {chain_doc.description}"
			chain_doc.save()

			print(f"Installed sample template: {template['chain_name']}")

		except Exception as e:
			frappe.log_error(f"Sample template installation failed: {str(e)}", "Sample Template")


def before_uninstall():
	"""Cleanup before uninstalling"""
	try:
		# Deactivate all sync chains
		chains = frappe.get_all("Sync Chain", filters={"is_active": 1})
		for chain in chains:
			chain_doc = frappe.get_doc("Sync Chain", chain.name)
			chain_doc.is_active = 0
			chain_doc.save()

		print("Deactivated all sync chains before uninstall")

	except Exception as e:
		frappe.log_error(f"Uninstall cleanup failed: {str(e)}", "Sync Uninstall")


@frappe.whitelist()
def create_demo_data():
	"""Create demo data for testing"""
	try:
		# This would create sample leads, customers, etc. for testing
		# For now, just return success
		return {
			"success": True,
			"message": "Demo data creation is not implemented yet"
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def check_system_health():
	"""Check if sync system is properly configured"""
	try:
		health_checks = []

		# Check if required DocTypes exist
		required_doctypes = ["Sync Chain", "Sync Chain Step", "Sync Activity Log"]
		for doctype in required_doctypes:
			exists = frappe.db.exists("DocType", doctype)
			health_checks.append({
				"check": f"DocType {doctype} exists",
				"status": "pass" if exists else "fail",
				"message": "OK" if exists else f"DocType {doctype} is missing"
			})

		# Check if roles exist
		required_roles = ["Sync Manager", "Sync User"]
		for role in required_roles:
			exists = frappe.db.exists("Role", role)
			health_checks.append({
				"check": f"Role {role} exists",
				"status": "pass" if exists else "warn",
				"message": "OK" if exists else f"Role {role} is missing (optional)"
			})

		# Check if pages are accessible
		try:
			frappe.get_doc("Page", "sync-dashboard")
			health_checks.append({
				"check": "Sync Dashboard page exists",
				"status": "pass",
				"message": "OK"
			})
		except:
			health_checks.append({
				"check": "Sync Dashboard page exists",
				"status": "fail",
				"message": "Dashboard page is missing"
			})

		# Overall status
		failed_checks = [c for c in health_checks if c["status"] == "fail"]
		overall_status = "fail" if failed_checks else "pass"

		return {
			"success": True,
			"overall_status": overall_status,
			"checks": health_checks,
			"summary": f"{len(health_checks) - len(failed_checks)}/{len(health_checks)} checks passed"
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}