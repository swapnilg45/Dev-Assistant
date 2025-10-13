# Copyright (c) 2025, Hybrowlabs and contributors
# For license information, please see license.txt

"""
Access Control Module

Provides field-level access control functionality for Frappe/ERPNext.
Includes permission calculation, monkey patching, and cache management.

Main Components:
    - permission_manager: Core permission calculation logic
    - monkey_patches: Frappe core function patching
    - utils: Cache management and helper functions

Usage:
    from dev_assistant.access_control.monkey_patches import apply_patches
    apply_patches()
"""

# Import main functions for easy access
from dev_assistant.access_control.monkey_patches import (
    apply_patches,
    remove_patches,
    is_patched
)

from dev_assistant.access_control.permission_manager import (
    calculate_field_permissions,
    get_field_access_configurations,
    PERMLEVEL_HIDDEN,
    PERMLEVEL_READ_ONLY
)

from dev_assistant.access_control.utils import (
    clear_all_cache,
    clear_configuration_cache,
    clear_user_cache,
    get_cache_stats,
    check_patch_status
)

# Module metadata
__version__ = '1.0.0'
__author__ = 'Hybrowlabs'

# Public API
__all__ = [
    # Monkey patches
    'apply_patches',
    'remove_patches',
    'is_patched',
    # Permission calculation
    'calculate_field_permissions',
    'get_field_access_configurations',
    # Constants
    'PERMLEVEL_HIDDEN',
    'PERMLEVEL_READ_ONLY',
    # Cache management
    'clear_all_cache',
    'clear_configuration_cache',
    'clear_user_cache',
    'get_cache_stats',
    'check_patch_status'
]
