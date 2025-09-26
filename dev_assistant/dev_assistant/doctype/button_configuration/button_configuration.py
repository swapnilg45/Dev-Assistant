# Copyright (c) 2025, Dev Assistant Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json


class ButtonConfiguration(Document):
    """DocType for managing dynamic button visibility configurations"""

    def validate(self):
        """Validate button configuration"""
        self.validate_target()
        self.validate_button_group()
        self.validate_conditions()
        self.validate_roles()
        self.validate_user_exceptions()

    def validate_target(self):
        """Validate that either target_doctype or target_report is specified"""
        if self.button_location == "DocType Form":
            if not self.target_doctype:
                frappe.throw("Target DocType is required for DocType Form location")
            # Clear report field
            self.target_report = None
        elif self.button_location == "Report":
            if not self.target_report:
                frappe.throw("Target Report is required for Report location")
            # Clear doctype field
            self.target_doctype = None

    def validate_button_group(self):
        """Validate that button_group is provided for grouped buttons"""
        if self.button_type == "Grouped" and not self.button_group:
            frappe.throw("Button Group is required for Grouped buttons")
        elif self.button_type == "Normal":
            # Clear button_group for normal buttons
            self.button_group = None

    def validate_conditions(self):
        """Validate condition configurations"""
        if self.conditions:
            for idx, condition in enumerate(self.conditions):
                if not condition.condition_field:
                    frappe.throw(f"Condition field is required in row {idx + 1}")
                if not condition.operator:
                    frappe.throw(f"Operator is required in row {idx + 1}")

                # Validate that value is provided for operators that need it
                if condition.operator not in ["is set", "is not set"] and not condition.condition_value:
                    frappe.throw(f"Condition value is required for operator '{condition.operator}' in row {idx + 1}")

                # For 'in' and 'not in' operators, validate JSON format
                if condition.operator in ["in", "not in"] and condition.condition_value:
                    try:
                        json.loads(condition.condition_value)
                    except json.JSONDecodeError:
                        frappe.throw(f"Condition value must be valid JSON array for 'in' operator in row {idx + 1}")

    def validate_roles(self):
        """Validate role configurations"""
        if self.allowed_roles:
            role_names = []
            for role_config in self.allowed_roles:
                if not role_config.role:
                    frappe.throw("Role is required in Allowed Roles")

                # Check for duplicate roles
                if role_config.role in role_names:
                    frappe.throw(f"Duplicate role '{role_config.role}' in Allowed Roles")
                role_names.append(role_config.role)

                # Validate role exists
                if not frappe.db.exists("Role", role_config.role):
                    frappe.throw(f"Role '{role_config.role}' does not exist")

    def validate_user_exceptions(self):
        """Validate user exception configurations"""
        if self.user_exceptions:
            user_emails = []
            for exception in self.user_exceptions:
                if not exception.user:
                    frappe.throw("User is required in User Exceptions")
                if not exception.exception_type:
                    frappe.throw("Exception Type is required in User Exceptions")

                # Check for duplicate users
                if exception.user in user_emails:
                    frappe.throw(f"Duplicate user '{exception.user}' in User Exceptions")
                user_emails.append(exception.user)

                # Validate user exists
                if not frappe.db.exists("User", exception.user):
                    frappe.throw(f"User '{exception.user}' does not exist")

    def get_configuration_details(self):
        """Get complete configuration details including child tables"""
        return {
            "name": self.name,
            "button_location": self.button_location,
            "target_doctype": self.target_doctype,
            "target_report": self.target_report,
            "button_type": self.button_type,
            "button_label": self.button_label,
            "button_group": self.button_group,
            "callback_function": self.callback_function,
            "timeout_ms": self.timeout_ms or 500,
            "is_active": self.is_active,
            "conditions": [
                {
                    "condition_field": c.condition_field,
                    "operator": c.operator,
                    "condition_value": c.condition_value,
                    "logical_operator": c.logical_operator
                }
                for c in self.conditions
            ],
            "allowed_roles": [
                {
                    "role": r.role,
                    "conditions": r.conditions if hasattr(r, 'conditions') else None,
                    "logical_operator": r.logical_operator if hasattr(r, 'logical_operator') else "AND"
                }
                for r in self.allowed_roles
            ],
            "user_exceptions": [
                {
                    "user": u.user,
                    "exception_type": u.exception_type
                }
                for u in self.user_exceptions
            ]
        }


@frappe.whitelist()
def get_button_configurations(doctype=None, report=None):
    """
    Get all active button configurations for a DocType or Report.

    Args:
        doctype: Name of the DocType (for form buttons)
        report: Name of the Report (for report buttons)

    Returns:
        Dictionary containing button configurations with visibility rules
    """
    if not doctype and not report:
        return {"configurations": []}

    filters = {"is_active": 1}

    if doctype:
        filters["button_location"] = "DocType Form"
        filters["target_doctype"] = doctype
    elif report:
        filters["button_location"] = "Report"
        filters["target_report"] = report

    configurations = frappe.get_all(
        "Button Configuration",
        filters=filters,
        fields=["name", "button_label", "button_group", "button_type", "timeout_ms", "force_hide", "enable_user_expections", "role_permission"]
    )

    result = []
    current_user = frappe.session.user
    user_roles = frappe.get_roles(current_user)

    for config in configurations:
        doc = frappe.get_doc("Button Configuration", config.name)

        # Check user exceptions first (only if enabled)
        user_exception = None
        if doc.enable_user_expections:
            user_exception = _check_user_exception(doc, current_user)

        if user_exception is not None:
            config_data = {
                "name": doc.name,
                "button_label": doc.button_label,
                "button_type": doc.button_type,
                "button_group": doc.button_group,
                "callback_function": doc.callback_function,
                "timeout_ms": doc.timeout_ms or 500,
                "force_hide": doc.force_hide or 0,
                "enable_user_expections": doc.enable_user_expections or 0,
                "role_permission": doc.role_permission or 0,
                "visible": user_exception,
                "reason": "user_exception"
            }
            result.append(config_data)
            continue

        # Check role-based access (only if enabled)
        has_role_access = True  # Default to True if role permission is disabled
        if doc.role_permission:
            has_role_access = _check_role_access(doc, user_roles)

        # Get conditions to be evaluated on client side
        conditions = []
        if doc.conditions:
            for condition in doc.conditions:
                conditions.append({
                    "field": condition.condition_field,
                    "operator": condition.operator,
                    "value": condition.condition_value,
                    "logical_operator": condition.logical_operator
                })

        config_data = {
            "name": doc.name,
            "button_label": doc.button_label,
            "button_type": doc.button_type,
            "button_group": doc.button_group,
            "callback_function": doc.callback_function,
            "timeout_ms": doc.timeout_ms or 500,
            "force_hide": doc.force_hide or 0,
            "enable_user_expections": doc.enable_user_expections or 0,
            "role_permission": doc.role_permission or 0,
            "has_role_access": has_role_access,
            "conditions": conditions,
            "visible": has_role_access  # Initial visibility based on role
        }

        result.append(config_data)

    return {"configurations": result}


def _check_user_exception(doc, user):
    """
    Check if user has an exception rule.

    Returns:
        True if user should see button (ALLOW exception)
        False if user should not see button (DENY exception)
        None if no exception exists
    """
    if not doc.user_exceptions:
        return None

    for exception in doc.user_exceptions:
        if exception.user == user:
            return exception.exception_type == "ALLOW"

    return None


def _check_role_access(doc, user_roles):
    """
    Check if user has role-based access to the button.

    Returns:
        True if user has at least one allowed role or no roles are specified
        False otherwise
    """
    if not doc.allowed_roles:
        # If no roles specified, button is visible to all
        return True

    for role_condition in doc.allowed_roles:
        if role_condition.role in user_roles:
            return True

    return False


@frappe.whitelist()
def evaluate_button_visibility(button_name, doc_data=None):
    """
    Evaluate button visibility for a specific document instance.

    Args:
        button_name: Name of the Button Configuration
        doc_data: Current document data for condition evaluation

    Returns:
        Dictionary with visibility status and reason
    """
    if isinstance(doc_data, str):
        doc_data = json.loads(doc_data)

    try:
        config = frappe.get_doc("Button Configuration", button_name)
    except frappe.DoesNotExistError:
        return {"visible": True, "reason": "no_configuration"}

    if not config.is_active:
        return {"visible": True, "reason": "configuration_inactive"}

    current_user = frappe.session.user

    # Check user exception first (highest priority, only if enabled)
    if config.enable_user_expections:
        user_exception = _check_user_exception(config, current_user)
        if user_exception is not None:
            return {
                "visible": user_exception,
                "reason": "user_exception"
            }

    # Check role access (only if enabled)
    if config.role_permission:
        user_roles = frappe.get_roles(current_user)
        has_role = _check_role_access(config, user_roles)

        if not has_role:
            return {
                "visible": False,
                "reason": "no_role_access"
            }

    # Evaluate field conditions if doc_data provided
    if doc_data and config.conditions:
        conditions_met = _evaluate_conditions(config.conditions, doc_data)
        return {
            "visible": conditions_met,
            "reason": "conditions_evaluated"
        }

    return {
        "visible": True,
        "reason": "default_visible"
    }


def _evaluate_conditions(conditions, doc_data):
    """
    Evaluate field conditions against document data.

    Args:
        conditions: List of condition objects
        doc_data: Current document data

    Returns:
        True if conditions are met, False otherwise
    """
    if not conditions:
        return True

    results = []
    logical_operators = []

    for condition in conditions:
        field_value = doc_data.get(condition.condition_field)
        operator = condition.operator
        compare_value = condition.condition_value

        # Handle different operators
        result = False

        if operator == "is set":
            result = field_value is not None and field_value != ""
        elif operator == "is not set":
            result = field_value is None or field_value == ""
        elif operator == "=":
            result = str(field_value) == str(compare_value)
        elif operator == "!=":
            result = str(field_value) != str(compare_value)
        elif operator in [">", ">=", "<", "<="]:
            try:
                field_val = float(field_value) if field_value else 0
                compare_val = float(compare_value) if compare_value else 0

                if operator == ">":
                    result = field_val > compare_val
                elif operator == ">=":
                    result = field_val >= compare_val
                elif operator == "<":
                    result = field_val < compare_val
                elif operator == "<=":
                    result = field_val <= compare_val
            except (ValueError, TypeError):
                result = False
        elif operator == "in":
            try:
                values_list = json.loads(compare_value) if isinstance(compare_value, str) else compare_value
                result = field_value in values_list
            except (json.JSONDecodeError, TypeError):
                result = False
        elif operator == "not in":
            try:
                values_list = json.loads(compare_value) if isinstance(compare_value, str) else compare_value
                result = field_value not in values_list
            except (json.JSONDecodeError, TypeError):
                result = True
        elif operator == "like":
            result = compare_value in str(field_value) if field_value else False
        elif operator == "not like":
            result = compare_value not in str(field_value) if field_value else True

        results.append(result)
        if condition.logical_operator:
            logical_operators.append(condition.logical_operator)

    # Combine results with logical operators
    if not results:
        return True

    final_result = results[0]
    for i, operator in enumerate(logical_operators):
        if i + 1 < len(results):
            if operator == "AND":
                final_result = final_result and results[i + 1]
            elif operator == "OR":
                final_result = final_result or results[i + 1]

    return final_result


@frappe.whitelist()
def get_doctype_fields(doctype):
    """
    Get all fields for a DocType to help with configuration.

    Args:
        doctype: Name of the DocType

    Returns:
        List of field dictionaries with fieldname and label
    """
    if not frappe.has_permission(doctype, "read"):
        frappe.throw(f"Insufficient permissions to read {doctype}")

    meta = frappe.get_meta(doctype)
    fields = []

    for field in meta.fields:
        if field.fieldtype not in ["Section Break", "Column Break", "HTML", "Button"]:
            fields.append({
                "fieldname": field.fieldname,
                "label": field.label or field.fieldname,
                "fieldtype": field.fieldtype,
                "options": field.options
            })

    return fields


@frappe.whitelist()
def get_configured_doctypes():
    """
    Get all unique DocTypes that have active button configurations

    Returns:
        List of DocType names
    """
    doctypes = frappe.db.sql("""
        SELECT DISTINCT target_doctype
        FROM `tabButton Configuration`
        WHERE is_active = 1
        AND button_location = 'DocType Form'
        AND target_doctype IS NOT NULL
    """, as_dict=True)

    return [d.target_doctype for d in doctypes]