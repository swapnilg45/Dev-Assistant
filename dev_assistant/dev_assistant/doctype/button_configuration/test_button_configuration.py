# Copyright (c) 2025, Dev Assistant Team and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
import json


class TestButtonConfiguration(FrappeTestCase):
    def setUp(self):
        """Set up test data"""
        # Create test role if doesn't exist
        if not frappe.db.exists("Role", "Test Button Role"):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": "Test Button Role"
            }).insert(ignore_permissions=True)

    def tearDown(self):
        """Clean up test data"""
        # Delete test configurations
        frappe.db.sql("DELETE FROM `tabButton Configuration` WHERE name LIKE 'Test-%'")
        frappe.db.commit()

    def test_button_configuration_creation(self):
        """Test creating a button configuration"""
        config = frappe.get_doc({
            "doctype": "Button Configuration",
            "button_location": "DocType Form",
            "target_doctype": "ToDo",
            "button_type": "Normal",
            "button_label": "Test Button",
            "is_active": 1,
            "conditions": [
                {
                    "condition_field": "status",
                    "operator": "=",
                    "condition_value": "Open",
                    "logical_operator": "AND"
                }
            ],
            "allowed_roles": [
                {
                    "role": "Test Button Role"
                }
            ]
        })
        config.insert()
        self.assertTrue(config.name)

    def test_grouped_button_validation(self):
        """Test that grouped buttons require button_group"""
        config = frappe.get_doc({
            "doctype": "Button Configuration",
            "button_location": "DocType Form",
            "target_doctype": "ToDo",
            "button_type": "Grouped",
            "button_label": "Test Grouped Button",
            "is_active": 1
        })

        # Should throw error without button_group
        with self.assertRaises(frappe.exceptions.ValidationError):
            config.save()

    def test_location_validation(self):
        """Test that correct target fields are required based on location"""
        # Test DocType Form requires target_doctype
        config1 = frappe.get_doc({
            "doctype": "Button Configuration",
            "button_location": "DocType Form",
            "button_type": "Normal",
            "button_label": "Test Button",
            "is_active": 1
        })

        with self.assertRaises(frappe.exceptions.ValidationError):
            config1.save()

        # Test Report requires target_report
        config2 = frappe.get_doc({
            "doctype": "Button Configuration",
            "button_location": "Report",
            "button_type": "Normal",
            "button_label": "Test Button",
            "is_active": 1
        })

        with self.assertRaises(frappe.exceptions.ValidationError):
            config2.save()

    def test_condition_evaluation(self):
        """Test condition evaluation logic"""
        from dev_assistant.api.button_visibility_control import evaluate_single_condition

        # Test equality
        self.assertTrue(evaluate_single_condition("Open", "=", "Open"))
        self.assertFalse(evaluate_single_condition("Closed", "=", "Open"))

        # Test inequality
        self.assertTrue(evaluate_single_condition("Closed", "!=", "Open"))
        self.assertFalse(evaluate_single_condition("Open", "!=", "Open"))

        # Test numeric comparisons
        self.assertTrue(evaluate_single_condition(10, ">", 5))
        self.assertFalse(evaluate_single_condition(5, ">", 10))

        # Test 'in' operator
        self.assertTrue(evaluate_single_condition("Apple", "in", '["Apple", "Banana"]'))
        self.assertFalse(evaluate_single_condition("Orange", "in", '["Apple", "Banana"]'))

        # Test 'is set' and 'is not set'
        self.assertTrue(evaluate_single_condition("Value", "is set", None))
        self.assertFalse(evaluate_single_condition(None, "is set", None))
        self.assertTrue(evaluate_single_condition(None, "is not set", None))

    def test_user_exception(self):
        """Test user exception handling"""
        # Create a configuration with user exception
        config = frappe.get_doc({
            "doctype": "Button Configuration",
            "button_location": "DocType Form",
            "target_doctype": "ToDo",
            "button_type": "Normal",
            "button_label": "Test Exception Button",
            "is_active": 1,
            "user_exceptions": [
                {
                    "user": frappe.session.user,
                    "exception_type": "ALLOW"
                }
            ]
        })
        config.insert()

        # Test exception check
        from dev_assistant.api.button_visibility_control import check_user_exception
        result = check_user_exception(config.name)

        self.assertTrue(result["has_exception"])
        self.assertEqual(result["exception_type"], "ALLOW")

    def test_role_validation(self):
        """Test role validation"""
        # Create configuration with role requirement
        config = frappe.get_doc({
            "doctype": "Button Configuration",
            "button_location": "DocType Form",
            "target_doctype": "ToDo",
            "button_type": "Normal",
            "button_label": "Test Role Button",
            "is_active": 1,
            "allowed_roles": [
                {
                    "role": "System Manager"
                }
            ]
        })
        config.insert()

        # Test role validation
        from dev_assistant.api.button_visibility_control import validate_user_role
        result = validate_user_role(config.name)

        # Result depends on whether current user has System Manager role
        self.assertIn("has_permission", result)
        self.assertIn("user_roles", result)
        self.assertIn("required_roles", result)