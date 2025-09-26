# Copyright (c) 2025, Dev Assistant Team and contributors
# For license information, please see license.txt

"""
Dynamic Button Visibility Control API

This module provides APIs for managing button visibility configurations
and evaluating button visibility based on conditions, roles, and user exceptions.
"""

import frappe
from frappe import _
import json
from typing import Dict, List, Any, Optional


@frappe.whitelist()
def get_button_configs(location: str, target_name: str) -> List[Dict[str, Any]]:
    """
    Get all active button configurations for a location (DocType or Report)

    Args:
        location (str): Button location ('DocType Form' or 'Report')
        target_name (str): Target DocType or Report name

    Returns:
        list: Button configurations with conditions and roles
    """
    if not location or not target_name:
        return []

    # Build filters based on location
    filters = {
        "button_location": location,
        "is_active": 1
    }

    if location == "DocType Form":
        filters["target_doctype"] = target_name
    elif location == "Report":
        filters["target_report"] = target_name
    else:
        return []

    # Get button configurations
    button_configs = frappe.get_all(
        "Button Configuration",
        filters=filters,
        fields=["name"]
    )

    # Get full configuration details for each
    configs = []
    for config in button_configs:
        doc = frappe.get_doc("Button Configuration", config.name)
        configs.append(doc.get_configuration_details())

    return configs


@frappe.whitelist()
def evaluate_button_visibility(
    location: str,
    target_name: str,
    context_data: str,
    button_config: str
) -> Dict[str, Any]:
    """
    Evaluate if a button should be visible for a specific context

    Args:
        location (str): Button location ('DocType Form' or 'Report')
        target_name (str): Target DocType or Report name
        context_data (str): JSON string of context data (document data for forms, filters for reports)
        button_config (str): Button configuration name

    Returns:
        dict: {visible: bool, reason: str, details: dict}
    """
    try:
        context_data = json.loads(context_data) if isinstance(context_data, str) else context_data
    except json.JSONDecodeError:
        return {
            "visible": False,
            "reason": "Invalid context data",
            "details": {}
        }

    # Get button configuration
    if not frappe.db.exists("Button Configuration", button_config):
        return {
            "visible": False,
            "reason": "Button configuration not found",
            "details": {}
        }

    config_doc = frappe.get_doc("Button Configuration", button_config)

    # Check if configuration is active
    if not config_doc.is_active:
        return {
            "visible": False,
            "reason": "Button configuration is inactive",
            "details": {}
        }

    # Check user exceptions first (highest priority)
    user_exception_result = check_user_exception(button_config)
    if user_exception_result["has_exception"]:
        return {
            "visible": user_exception_result["exception_type"] == "ALLOW",
            "reason": f"User has {user_exception_result['exception_type']} exception",
            "details": {"user_exception": user_exception_result}
        }

    # Check role permissions
    role_check_result = validate_user_role(button_config)
    if not role_check_result["has_permission"]:
        return {
            "visible": False,
            "reason": "User does not have required role",
            "details": {"role_check": role_check_result}
        }

    # Evaluate conditions based on location
    if location == "DocType Form":
        condition_result = evaluate_form_conditions(config_doc, context_data)
    elif location == "Report":
        condition_result = evaluate_report_conditions(config_doc, context_data)
    else:
        condition_result = {"passed": False, "reason": "Invalid location"}

    return {
        "visible": condition_result["passed"],
        "reason": condition_result.get("reason", "Conditions evaluated"),
        "details": {
            "condition_results": condition_result.get("results", []),
            "role_check": role_check_result
        }
    }


@frappe.whitelist()
def check_user_exception(button_config: str) -> Dict[str, Any]:
    """
    Check if current user has exception for this button

    Args:
        button_config (str): Button configuration name

    Returns:
        dict: {has_exception: bool, exception_type: str or None}
    """
    current_user = frappe.session.user

    # Get button configuration
    config_doc = frappe.get_doc("Button Configuration", button_config)

    # Check user exceptions
    for exception in config_doc.user_exceptions:
        if exception.user == current_user:
            return {
                "has_exception": True,
                "exception_type": exception.exception_type
            }

    return {
        "has_exception": False,
        "exception_type": None
    }


@frappe.whitelist()
def validate_user_role(button_config: str) -> Dict[str, Any]:
    """
    Check if current user has required role for button

    Args:
        button_config (str): Button configuration name

    Returns:
        dict: {has_permission: bool, user_roles: list, required_roles: list}
    """
    current_user = frappe.session.user

    # Get button configuration
    config_doc = frappe.get_doc("Button Configuration", button_config)

    # If no roles specified, button is available to all
    if not config_doc.allowed_roles:
        return {
            "has_permission": True,
            "user_roles": frappe.get_roles(current_user),
            "required_roles": []
        }

    # Get user roles
    user_roles = frappe.get_roles(current_user)

    # Check if user has any of the required roles
    required_roles = [role.role for role in config_doc.allowed_roles]
    has_role = any(role in user_roles for role in required_roles)

    return {
        "has_permission": has_role,
        "user_roles": user_roles,
        "required_roles": required_roles
    }


def evaluate_form_conditions(config_doc, context_data: Dict) -> Dict[str, Any]:
    """
    Evaluate conditions for form buttons

    Args:
        config_doc: Button Configuration document
        context_data (dict): Form document data

    Returns:
        dict: {passed: bool, reason: str, results: list}
    """
    if not config_doc.conditions:
        return {"passed": True, "reason": "No conditions defined", "results": []}

    # Get document data
    doc_data = context_data.get("doc", {})
    if not doc_data:
        return {"passed": False, "reason": "No document data provided", "results": []}

    results = []
    all_conditions_passed = True
    use_or_logic = False

    for condition in config_doc.conditions:
        # Get field value
        field_value = doc_data.get(condition.condition_field)

        # Evaluate condition
        condition_passed = evaluate_single_condition(
            field_value,
            condition.operator,
            condition.condition_value
        )

        results.append({
            "field": condition.condition_field,
            "operator": condition.operator,
            "expected": condition.condition_value,
            "actual": field_value,
            "passed": condition_passed
        })

        # Handle logical operators
        if condition.logical_operator == "OR":
            use_or_logic = True
            if condition_passed:
                # For OR logic, if any condition passes, overall passes
                all_conditions_passed = True
                break
        else:  # AND logic
            if not condition_passed:
                all_conditions_passed = False
                if not use_or_logic:
                    # For AND logic, if any condition fails, overall fails
                    break

    reason = "All conditions met" if all_conditions_passed else "Conditions not met"
    return {
        "passed": all_conditions_passed,
        "reason": reason,
        "results": results
    }


def evaluate_report_conditions(config_doc, context_data: Dict) -> Dict[str, Any]:
    """
    Evaluate conditions for report buttons

    Args:
        config_doc: Button Configuration document
        context_data (dict): Report filters and data

    Returns:
        dict: {passed: bool, reason: str, results: list}
    """
    if not config_doc.conditions:
        return {"passed": True, "reason": "No conditions defined", "results": []}

    # Get filter data
    filters = context_data.get("filters", {})

    results = []
    all_conditions_passed = True

    for condition in config_doc.conditions:
        # Get filter value
        field_value = filters.get(condition.condition_field)

        # Evaluate condition
        condition_passed = evaluate_single_condition(
            field_value,
            condition.operator,
            condition.condition_value
        )

        results.append({
            "field": condition.condition_field,
            "operator": condition.operator,
            "expected": condition.condition_value,
            "actual": field_value,
            "passed": condition_passed
        })

        # Handle logical operators
        if condition.logical_operator == "OR":
            if condition_passed:
                all_conditions_passed = True
                break
        else:  # AND logic
            if not condition_passed:
                all_conditions_passed = False
                break

    reason = "All conditions met" if all_conditions_passed else "Conditions not met"
    return {
        "passed": all_conditions_passed,
        "reason": reason,
        "results": results
    }


def evaluate_single_condition(
    field_value: Any,
    operator: str,
    expected_value: Any
) -> bool:
    """
    Evaluate a single condition

    Args:
        field_value: Actual field value
        operator: Comparison operator
        expected_value: Expected value

    Returns:
        bool: True if condition passes
    """
    # Handle 'is set' and 'is not set' operators
    if operator == "is set":
        return field_value is not None and field_value != ""
    elif operator == "is not set":
        return field_value is None or field_value == ""

    # Handle other operators
    if operator == "=":
        return str(field_value) == str(expected_value) if field_value is not None else False
    elif operator == "!=":
        return str(field_value) != str(expected_value) if field_value is not None else True
    elif operator == ">":
        try:
            return float(field_value) > float(expected_value)
        except (ValueError, TypeError):
            return False
    elif operator == ">=":
        try:
            return float(field_value) >= float(expected_value)
        except (ValueError, TypeError):
            return False
    elif operator == "<":
        try:
            return float(field_value) < float(expected_value)
        except (ValueError, TypeError):
            return False
    elif operator == "<=":
        try:
            return float(field_value) <= float(expected_value)
        except (ValueError, TypeError):
            return False
    elif operator == "like":
        return expected_value in str(field_value) if field_value is not None else False
    elif operator == "not like":
        return expected_value not in str(field_value) if field_value is not None else True
    elif operator in ["in", "not in"]:
        try:
            # Parse expected value as JSON array
            expected_list = json.loads(expected_value) if isinstance(expected_value, str) else expected_value
            if not isinstance(expected_list, list):
                expected_list = [expected_list]

            if operator == "in":
                return str(field_value) in [str(v) for v in expected_list]
            else:  # not in
                return str(field_value) not in [str(v) for v in expected_list]
        except (json.JSONDecodeError, TypeError):
            return False

    return False


@frappe.whitelist()
def get_doctype_fields(doctype: str) -> List[Dict[str, str]]:
    """
    Get all fields for a DocType (for condition builder)

    Args:
        doctype (str): DocType name

    Returns:
        list: Field definitions with types and options
    """
    if not frappe.db.exists("DocType", doctype):
        frappe.throw(_("DocType {0} does not exist").format(doctype))

    fields = frappe.get_meta(doctype).fields

    field_list = []
    for field in fields:
        if field.fieldtype not in ["Section Break", "Column Break", "HTML", "Button"]:
            field_list.append({
                "fieldname": field.fieldname,
                "label": field.label,
                "fieldtype": field.fieldtype,
                "options": field.options
            })

    return field_list


@frappe.whitelist()
def test_condition(doctype: str, docname: str, conditions: str) -> Dict[str, Any]:
    """
    Test condition evaluation for debugging

    Args:
        doctype (str): DocType name
        docname (str): Document name
        conditions (str): JSON string of conditions

    Returns:
        dict: Evaluation results and debug info
    """
    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(_("No permission to read {0} {1}").format(doctype, docname))

    try:
        conditions = json.loads(conditions) if isinstance(conditions, str) else conditions
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid conditions JSON"
        }

    # Get document
    doc = frappe.get_doc(doctype, docname)

    results = []
    for condition in conditions:
        field_value = doc.get(condition.get("condition_field"))
        condition_passed = evaluate_single_condition(
            field_value,
            condition.get("operator"),
            condition.get("condition_value")
        )

        results.append({
            "field": condition.get("condition_field"),
            "operator": condition.get("operator"),
            "expected": condition.get("condition_value"),
            "actual": field_value,
            "passed": condition_passed
        })

    return {
        "success": True,
        "results": results
    }