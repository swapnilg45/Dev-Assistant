import frappe
from frappe import _
import operator


def validate_mandatory_fields(doc, method=None):
    """
    Validate mandatory fields based on Mandatory Field Controller rules
    """
    if doc.doctype in ["Mandatory Field Controller", "Mandatory Field Condition", "Mandatory Field Detail"]:
        return

    # Get active rules for this doctype
    rules = frappe.get_all(
        "Mandatory Field Controller",
        filters={
            "document_type": doc.doctype,
            "disabled": 0
        },
        fields=["name", "priority"],
        order_by="priority desc, creation desc"
    )

    if not rules:
        return

    # Process rules in order of priority
    for rule in rules:
        rule_doc = frappe.get_doc("Mandatory Field Controller", rule.name)

        # Check if conditions are met
        if _check_conditions(doc, rule_doc.conditions):
            # Make fields mandatory
            _validate_mandatory_fields(doc, rule_doc.mandatory_fields)


def _check_conditions(doc, conditions):
    """
    Check if all conditions in the rule are met
    """
    if not conditions:
        return True

    operators_map = {
        "=": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "in": lambda x, y: x in str(y).split(","),
        "not in": lambda x, y: x not in str(y).split(",")
    }

    for condition in conditions:
        field_value = getattr(doc, condition.field, None)
        condition_op = operators_map.get(condition.condition)

        if not condition_op:
            continue

        try:
            # Convert values for comparison
            if condition.condition in ["in", "not in"]:
                result = condition_op(str(field_value) if field_value else "", condition.value)
            else:
                # Try to convert to appropriate types for comparison
                if field_value is None:
                    field_value = ""
                if isinstance(field_value, (int, float)) and condition.value.isdigit():
                    result = condition_op(field_value, float(condition.value))
                else:
                    result = condition_op(str(field_value), str(condition.value))

            if not result:
                return False

        except (ValueError, TypeError, AttributeError):
            return False

    return True


def _validate_mandatory_fields(doc, mandatory_fields):
    """
    Validate that mandatory fields have values
    """
    errors = []

    for field in mandatory_fields:
        field_value = getattr(doc, field.field_name, None)

        # Check if field is empty (handle different data types properly)
        is_empty = False

        if field_value is None:
            is_empty = True
        elif isinstance(field_value, str) and field_value.strip() == "":
            is_empty = True
        elif isinstance(field_value, (int, float)) and field_value == 0:
            # For checkbox fields (0 = unchecked, 1 = checked)
            is_empty = True
        elif isinstance(field_value, list) and len(field_value) == 0:
            is_empty = True

        if is_empty:
            if field.custom_error_message:
                error_message = field.custom_error_message
            else:
                field_label = field.field_label or field.field_name.replace('_', ' ').title()
                error_message = f"Please fill the <strong>{field_label}</strong> field"

            errors.append(error_message)

    if errors:
        error_html = "<div style='text-align: left;'>"
        error_html += "<ul style='margin: 10px 0; padding-left: 20px;'>"
        for error in errors:
            error_html += f"<li style='margin: 5px 0;'>{error}</li>"
        error_html += "</ul></div>"

        frappe.throw(
            error_html,
            title="⚠️ Required Fields Missing",
            exc=frappe.ValidationError
        )