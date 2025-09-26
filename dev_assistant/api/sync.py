import frappe
from frappe import _
import json


@frappe.whitelist()
def test_sync_api():
    """Test endpoint to check if API is working"""
    try:
        return {
            "success": True,
            "message": "API is working!",
            "site": frappe.local.site,
            "user": frappe.session.user
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist(allow_guest=True, methods=['POST'])
def create_sync_chain_from_wizard():
    """Create sync chain from wizard data"""
    try:
        # Try to get data from request directly
        import json
        from frappe import request

        # Check if we have form data
        if hasattr(request, 'form'):
            process_data = request.form.get('process_data')
            activate_immediately = request.form.get('activate_immediately', True)

            frappe.logger().info(f"From request.form - process_data: {process_data}")
            frappe.logger().info(f"From request.form - activate_immediately: {activate_immediately}")
        else:
            # Fall back to form_dict
            form_data = frappe.form_dict
            process_data = form_data.get('process_data')
            activate_immediately = form_data.get('activate_immediately', True)

            frappe.logger().info(f"From form_dict - process_data: {process_data}")

        if not process_data:
            frappe.throw(f"Process data is required. Check request form data.")

        # Parse process data if it's a string
        if isinstance(process_data, str):
            process_data = json.loads(process_data)

        # Create new sync chain document
        chain_doc = frappe.new_doc("Sync Chain")
        chain_doc.chain_name = process_data.get("processName", "New Sync Process")
        chain_doc.description = process_data.get("description", "")
        chain_doc.is_active = 1 if activate_immediately else 0

        # Set template reference
        template_key = process_data.get("templateKey")
        if template_key and template_key != "custom":
            chain_doc.template_used = template_key

        # Process steps data to create chain_steps
        steps = process_data.get("steps", [])
        field_mappings = process_data.get("fieldMappings", {})

        if not steps:
            frappe.throw("At least one process step is required")

        for i, step in enumerate(steps):
            step_doc = {
                "step_number": step.get("stepNumber", i + 1),
                "doctype_name": step.get("doctypeName", step.get("doctype", "")),
                "sync_condition": step.get("syncCondition", "Always")
            }

            # Add field mappings if available for this step
            step_index = str(i)  # Use string index to match frontend data
            if field_mappings and step_index in field_mappings:
                step_doc["field_mappings"] = json.dumps(field_mappings[step_index])

            chain_doc.append("chain_steps", step_doc)

        # Save the document
        chain_doc.save()

        return {
            "success": True,
            "message": f"Sync Chain '{chain_doc.chain_name}' created successfully!",
            "chain_id": chain_doc.name,
            "status": "created"
        }

    except Exception as e:
        error_msg = str(e)
        frappe.logger().error(f"Sync Chain Creation Failed: {error_msg}")
        frappe.log_error(message=error_msg, title="Sync Chain Creation Failed")

        # Return error response
        frappe.local.response["http_status_code"] = 400
        return {
            "success": False,
            "message": f"Failed to create sync process: {error_msg}",
            "error": error_msg
        }