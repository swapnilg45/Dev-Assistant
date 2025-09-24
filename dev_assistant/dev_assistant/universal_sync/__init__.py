# Copyright (c) 2025, Swapnil and contributors
# Universal Sync System - Simplified Sync Engine

"""
Universal Data Sync System - Simplified

A user-friendly data synchronization system for Frappe/ERPNext that allows
non-technical users to create and manage automated data flows between DocTypes.

Key Features:
- 5-step wizard setup
- Visual workflow builder
- Smart field mapping with auto-suggestions
- Pre-built templates for common processes
- Bi-directional sync engine
- Multi-channel notifications
- User-friendly dashboard

Main Components:
- sync_engine: Core synchronization logic
- field_mapper: Intelligent field mapping system
- sync_templates: Pre-built process templates
- wizard: Setup wizard backend
- notification_system: Multi-channel notifications
"""

# Version information
__version__ = "1.0.0"
__title__ = "Universal Data Sync System - Simplified"
__author__ = "Claude Code Assistant"

# Export main classes for easier imports
from .sync_engine import SimpleSyncEngine
from .field_mapper import SmartFieldMapper
from .notification_system import SyncNotificationSystem

__all__ = [
    'SimpleSyncEngine',
    'SmartFieldMapper',
    'SyncNotificationSystem'
]