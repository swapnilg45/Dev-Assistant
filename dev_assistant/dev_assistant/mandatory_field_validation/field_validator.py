# Copyright (c) 2025, Swapnil and contributors
# For license information, please see license.txt

"""
Field Validator for Enhanced Mandatory Field Controller
Validates fields based on different validation types and patterns
"""

import frappe
from frappe import _
from frappe.utils import cint, cstr, flt
import re
from typing import Any, Optional, Dict


class FieldValidator:
	"""
	Validates mandatory fields with support for different validation types
	including required, conditional, format, and custom validation.
	"""

	def __init__(self):
		"""Initialize field validator."""
		self._validation_cache = {}

	def validate_field(
		self,
		doc: frappe.model.document.Document,
		field_config: Any
	) -> Optional[str]:
		"""
		Validate a single field based on configuration.

		Args:
			doc: Document containing the field
			field_config: Field configuration object

		Returns:
			Error message if validation fails, None if valid
		"""
		field_name = field_config.field_name
		if not field_name:
			return None

		# Get field value using Frappe's safe_getattr
		field_value = frappe.utils.safe_getattr(doc, field_name, None)

		# Get validation type
		validation_type = getattr(field_config, 'validation_type', 'Required')

		# Perform validation based on type
		if validation_type == "Required":
			return self._validate_required(field_value, field_config)
		elif validation_type == "Conditionally Required":
			return self._validate_conditionally_required(doc, field_value, field_config)
		elif validation_type == "Format Validation":
			return self._validate_format(field_value, field_config)
		elif validation_type == "Custom Validation":
			return self._validate_custom(doc, field_value, field_config)
		else:
			# Default to required validation for backward compatibility
			return self._validate_required(field_value, field_config)

	def _validate_required(
		self,
		field_value: Any,
		field_config: Any
	) -> Optional[str]:
		"""
		Validate that field has a value.

		Args:
			field_value: Field value to validate
			field_config: Field configuration

		Returns:
			Error message if empty, None if valid
		"""
		if self._is_empty(field_value):
			return self._get_error_message(field_config, "is required")

		return None

	def _validate_conditionally_required(
		self,
		doc: frappe.model.document.Document,
		field_value: Any,
		field_config: Any
	) -> Optional[str]:
		"""
		Validate field is required based on conditions.

		Args:
			doc: Document context
			field_value: Field value to validate
			field_config: Field configuration

		Returns:
			Error message if validation fails, None if valid
		"""
		# For now, treat as regular required
		# In future, can add condition evaluation here
		if self._is_empty(field_value):
			return self._get_error_message(field_config, "is conditionally required")

		return None

	def _validate_format(
		self,
		field_value: Any,
		field_config: Any
	) -> Optional[str]:
		"""
		Validate field format using pattern and length constraints.

		Args:
			field_value: Field value to validate
			field_config: Field configuration

		Returns:
			Error message if format invalid, None if valid
		"""
		if self._is_empty(field_value):
			# Empty values might be allowed for format validation
			# Check if field is also required
			if hasattr(field_config, 'required') and field_config.required:
				return self._get_error_message(field_config, "is required")
			return None

		value_str = cstr(field_value)

		# Check minimum length
		min_length = getattr(field_config, 'min_length', None)
		if min_length and len(value_str) < min_length:
			return self._get_error_message(
				field_config,
				f"must be at least {min_length} characters long"
			)

		# Check maximum length
		max_length = getattr(field_config, 'max_length', None)
		if max_length and len(value_str) > max_length:
			return self._get_error_message(
				field_config,
				f"must not exceed {max_length} characters"
			)

		# Check format pattern
		format_pattern = getattr(field_config, 'format_pattern', None)
		if format_pattern:
			try:
				if not re.match(format_pattern, value_str):
					return self._get_error_message(
						field_config,
						f"does not match the required format"
					)
			except re.error as e:
				frappe.log_error(
					f"Invalid regex pattern: {format_pattern} - {str(e)}",
					"Mandatory Field Controller"
				)

		return None

	def _validate_custom(
		self,
		doc: frappe.model.document.Document,
		field_value: Any,
		field_config: Any
	) -> Optional[str]:
		"""
		Validate field using custom Python script.

		Args:
			doc: Document context
			field_value: Field value to validate
			field_config: Field configuration

		Returns:
			Error message if validation fails, None if valid
		"""
		validation_script = getattr(field_config, 'validation_script', None)
		if not validation_script:
			# No script means validation passes
			return None

		try:
			# Create execution context
			context = {
				"value": field_value,
				"doc": doc,
				"user": frappe.session.user,
				"frappe": frappe,
				"_": _,
				"cint": cint,
				"cstr": cstr,
				"flt": flt
			}

			# Execute validation script
			result = frappe.safe_eval(
				validation_script,
				eval_globals=context,
				eval_locals=context
			)

			# Script should return True if valid
			if not result:
				return self._get_error_message(
					field_config,
					"does not meet custom validation requirements"
				)

			return None

		except Exception as e:
			frappe.log_error(
				f"Custom validation script error: {str(e)}",
				"Mandatory Field Controller"
			)
			# On error, don't block but log
			return None

	def _is_empty(self, value: Any) -> bool:
		"""
		Check if a value is considered empty using Frappe's built-in utility.

		Args:
			value: Value to check

		Returns:
			True if value is empty
		"""
		# Use Frappe's built-in has_value utility (inverse of is_empty)
		return not frappe.utils.has_value(value)

	def _get_error_message(
		self,
		field_config: Any,
		default_message: str
	) -> str:
		"""
		Get error message for field validation failure.

		Args:
			field_config: Field configuration
			default_message: Default message if no custom message

		Returns:
			Formatted error message
		"""
		# Check for custom error message
		custom_message = getattr(field_config, 'custom_error_message', None)
		if custom_message:
			return custom_message

		# Build default message
		field_label = getattr(field_config, 'field_label', None)
		if not field_label:
			field_name = getattr(field_config, 'field_name', 'Field')
			field_label = field_name.replace('_', ' ').title()

		return f"<strong>{field_label}</strong> {default_message}"

	def validate_multiple_fields(
		self,
		doc: frappe.model.document.Document,
		field_configs: list
	) -> list:
		"""
		Validate multiple fields and return all errors.

		Args:
			doc: Document to validate
			field_configs: List of field configurations

		Returns:
			List of error messages
		"""
		errors = []

		for field_config in field_configs:
			error = self.validate_field(doc, field_config)
			if error:
				errors.append(error)

		return errors


class FormatPatterns:
	"""
	Common format patterns for field validation.
	"""

	# Email pattern
	EMAIL = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

	# Phone patterns
	PHONE_INDIA = r'^[6-9]\d{9}$'
	PHONE_INTERNATIONAL = r'^\+?[1-9]\d{1,14}$'

	# PAN Card (India)
	PAN_CARD = r'^[A-Z]{5}[0-9]{4}[A-Z]$'

	# Aadhaar Card (India)
	AADHAAR = r'^\d{12}$'

	# GST Number (India)
	GST = r'^\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d][Z][A-Z\d]$'

	# URL pattern
	URL = r'^https?://[^\s/$.?#].[^\s]*$'

	# Date patterns
	DATE_YYYY_MM_DD = r'^\d{4}-\d{2}-\d{2}$'
	DATE_DD_MM_YYYY = r'^\d{2}/\d{2}/\d{4}$'

	# Time patterns
	TIME_24H = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
	TIME_12H = r'^(1[0-2]|0?[1-9]):[0-5][0-9] ?([AaPp][Mm])$'

	# Alphanumeric patterns
	ALPHANUMERIC = r'^[a-zA-Z0-9]+$'
	ALPHANUMERIC_WITH_SPACE = r'^[a-zA-Z0-9 ]+$'
	ALPHANUMERIC_WITH_SPECIAL = r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};:\'",.<>/?]+$'

	# Number patterns
	INTEGER = r'^-?\d+$'
	DECIMAL = r'^-?\d+(\.\d+)?$'
	POSITIVE_INTEGER = r'^\d+$'
	POSITIVE_DECIMAL = r'^\d+(\.\d+)?$'

	# Currency patterns
	CURRENCY = r'^\d+(\.\d{1,2})?$'
	CURRENCY_WITH_SYMBOL = r'^[$€£¥₹]\d+(\.\d{1,2})?$'

	# Credit Card patterns
	VISA = r'^4[0-9]{12}(?:[0-9]{3})?$'
	MASTERCARD = r'^5[1-5][0-9]{14}$'
	AMEX = r'^3[47][0-9]{13}$'

	# Postal codes
	PINCODE_INDIA = r'^\d{6}$'
	ZIPCODE_US = r'^\d{5}(-\d{4})?$'
	POSTCODE_UK = r'^[A-Z]{1,2}[0-9]{1,2}[A-Z]?\s?[0-9][A-Z]{2}$'

	@classmethod
	def get_pattern(cls, pattern_name: str) -> Optional[str]:
		"""
		Get a predefined pattern by name.

		Args:
			pattern_name: Name of the pattern

		Returns:
			Pattern string or None if not found
		"""
		return getattr(cls, pattern_name.upper(), None)


class ValidationMessages:
	"""
	Standard validation error messages.
	"""

	REQUIRED = "This field is required"
	INVALID_EMAIL = "Please enter a valid email address"
	INVALID_PHONE = "Please enter a valid phone number"
	INVALID_URL = "Please enter a valid URL"
	INVALID_DATE = "Please enter a valid date"
	INVALID_TIME = "Please enter a valid time"
	TOO_SHORT = "Value is too short"
	TOO_LONG = "Value is too long"
	INVALID_FORMAT = "Value does not match the required format"
	INVALID_NUMBER = "Please enter a valid number"
	OUT_OF_RANGE = "Value is out of the allowed range"

	@classmethod
	def get_message(cls, message_key: str, **kwargs) -> str:
		"""
		Get a formatted validation message.

		Args:
			message_key: Key of the message
			**kwargs: Format parameters

		Returns:
			Formatted message string
		"""
		message = getattr(cls, message_key.upper(), cls.INVALID_FORMAT)
		return message.format(**kwargs) if kwargs else message