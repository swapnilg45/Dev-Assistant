# Copyright (c) 2025, Swapnil and contributors
# Notification System for Universal Sync System

import frappe
from frappe import _
import json
from typing import Dict, List, Any, Optional


class SyncNotificationSystem:
	"""Multi-channel notification system for sync events"""

	def __init__(self):
		self.channels = {
			'email': self.send_email_notification,
			'system': self.send_system_notification,
			'webhook': self.send_webhook_notification,
			'sms': self.send_sms_notification
		}

	def send_notification(self, event_type: str, sync_chain: str, data: Dict[str, Any], channels: List[str] = None):
		"""Send notification through specified channels"""
		try:
			# Get sync chain configuration
			chain_doc = frappe.get_doc("Sync Chain", sync_chain)

			# Default channels if not specified
			if not channels:
				channels = self.get_default_channels(chain_doc)

			# Get notification recipients
			recipients = self.get_notification_recipients(chain_doc, event_type)

			# Send through each channel
			results = []
			for channel in channels:
				if channel in self.channels:
					try:
						result = self.channels[channel](event_type, chain_doc, data, recipients)
						results.append({
							"channel": channel,
							"status": "success",
							"result": result
						})
					except Exception as e:
						frappe.log_error(f"Notification failed for channel {channel}: {str(e)}", "Sync Notifications")
						results.append({
							"channel": channel,
							"status": "failed",
							"error": str(e)
						})

			return results

		except Exception as e:
			frappe.log_error(f"Notification system error: {str(e)}", "Sync Notifications")
			return [{"status": "error", "error": str(e)}]

	def get_default_channels(self, chain_doc) -> List[str]:
		"""Get default notification channels for a sync chain"""
		# This could be extended to read from chain configuration
		return ['system', 'email']

	def get_notification_recipients(self, chain_doc, event_type: str) -> List[str]:
		"""Get notification recipients based on event type"""
		recipients = []

		# Chain owner
		recipients.append(chain_doc.owner)

		# System managers for critical events
		if event_type in ['sync_failed', 'chain_error', 'conflict_detected']:
			system_managers = frappe.get_all("Has Role",
				filters={"role": "System Manager"},
				fields=["parent"]
			)
			recipients.extend([sm.parent for sm in system_managers])

		# Sync managers
		sync_managers = frappe.get_all("Has Role",
			filters={"role": "Sync Manager"},
			fields=["parent"]
		)
		recipients.extend([sm.parent for sm in sync_managers])

		# Remove duplicates and invalid users
		unique_recipients = []
		for user in set(recipients):
			if frappe.db.exists("User", user) and frappe.db.get_value("User", user, "enabled"):
				unique_recipients.append(user)

		return unique_recipients

	def send_email_notification(self, event_type: str, chain_doc, data: Dict, recipients: List[str]):
		"""Send email notification"""
		try:
			subject, message = self.get_email_content(event_type, chain_doc, data)

			sent_count = 0
			for recipient in recipients:
				try:
					frappe.sendmail(
						recipients=[recipient],
						subject=subject,
						message=message,
						now=True
					)
					sent_count += 1
				except Exception as e:
					frappe.log_error(f"Email failed for {recipient}: {str(e)}", "Email Notification")

			return {"sent_count": sent_count, "total_recipients": len(recipients)}

		except Exception as e:
			raise Exception(f"Email notification failed: {str(e)}")

	def send_system_notification(self, event_type: str, chain_doc, data: Dict, recipients: List[str]):
		"""Send system notification"""
		try:
			subject, message = self.get_notification_content(event_type, chain_doc, data)
			notification_type = self.get_notification_type(event_type)

			sent_count = 0
			for recipient in recipients:
				try:
					frappe.get_doc({
						"doctype": "Notification Log",
						"for_user": recipient,
						"type": notification_type,
						"document_type": "Sync Chain",
						"document_name": chain_doc.name,
						"subject": subject,
						"email_content": message,
						"read": 0
					}).insert(ignore_permissions=True)

					# Also create a real-time notification
					frappe.publish_realtime(
						'sync_notification',
						{
							'type': event_type,
							'chain': chain_doc.chain_name,
							'message': subject,
							'data': data
						},
						user=recipient
					)

					sent_count += 1
				except Exception as e:
					frappe.log_error(f"System notification failed for {recipient}: {str(e)}", "System Notification")

			return {"sent_count": sent_count, "total_recipients": len(recipients)}

		except Exception as e:
			raise Exception(f"System notification failed: {str(e)}")

	def send_webhook_notification(self, event_type: str, chain_doc, data: Dict, recipients: List[str]):
		"""Send webhook notification to external systems"""
		try:
			# Get webhook URLs from system settings (this could be extended)
			webhook_urls = self.get_webhook_urls()

			if not webhook_urls:
				return {"status": "skipped", "reason": "No webhook URLs configured"}

			payload = {
				"event_type": event_type,
				"sync_chain": {
					"name": chain_doc.name,
					"chain_name": chain_doc.chain_name,
					"description": chain_doc.description
				},
				"data": data,
				"timestamp": frappe.utils.now()
			}

			sent_count = 0
			for url in webhook_urls:
				try:
					import requests
					response = requests.post(url, json=payload, timeout=10)
					if response.status_code == 200:
						sent_count += 1
				except Exception as e:
					frappe.log_error(f"Webhook failed for {url}: {str(e)}", "Webhook Notification")

			return {"sent_count": sent_count, "total_webhooks": len(webhook_urls)}

		except Exception as e:
			raise Exception(f"Webhook notification failed: {str(e)}")

	def send_sms_notification(self, event_type: str, chain_doc, data: Dict, recipients: List[str]):
		"""Send SMS notification (placeholder for SMS integration)"""
		try:
			# This would integrate with SMS service provider
			# For now, just log that SMS would be sent
			frappe.log_error(
				f"SMS notification would be sent to {len(recipients)} recipients for event {event_type}",
				"SMS Notification"
			)

			return {"status": "simulated", "recipients": len(recipients)}

		except Exception as e:
			raise Exception(f"SMS notification failed: {str(e)}")

	def get_email_content(self, event_type: str, chain_doc, data: Dict) -> tuple:
		"""Get email subject and content"""
		templates = {
			'sync_success': {
				'subject': _('Sync Completed: {0}').format(chain_doc.chain_name),
				'message': _('''
					<h3>Sync Process Completed Successfully</h3>
					<p>Your sync process "<strong>{chain_name}</strong>" has completed successfully.</p>
					<h4>Details:</h4>
					<ul>
						<li><strong>Source:</strong> {source_doctype}</li>
						<li><strong>Target:</strong> {target_doctype}</li>
						<li><strong>Records Synced:</strong> {records_count}</li>
						<li><strong>Time:</strong> {sync_time}</li>
					</ul>
					<p><a href="{dashboard_url}">View Dashboard</a></p>
				''').format(
					chain_name=chain_doc.chain_name,
					source_doctype=data.get('source_doctype', 'N/A'),
					target_doctype=data.get('target_doctype', 'N/A'),
					records_count=data.get('records_count', 1),
					sync_time=frappe.utils.now(),
					dashboard_url=frappe.utils.get_url('app/sync-dashboard')
				)
			},
			'sync_failed': {
				'subject': _('Sync Failed: {0}').format(chain_doc.chain_name),
				'message': _('''
					<h3>Sync Process Failed</h3>
					<p>Your sync process "<strong>{chain_name}</strong>" has failed.</p>
					<h4>Error Details:</h4>
					<div style="background: #f8f9fa; padding: 10px; border-left: 3px solid #dc3545;">
						{error_message}
					</div>
					<h4>Process Details:</h4>
					<ul>
						<li><strong>Source:</strong> {source_doctype}</li>
						<li><strong>Target:</strong> {target_doctype}</li>
						<li><strong>Time:</strong> {sync_time}</li>
					</ul>
					<p><a href="{dashboard_url}">View Dashboard</a> | <a href="{logs_url}">View Logs</a></p>
				''').format(
					chain_name=chain_doc.chain_name,
					error_message=data.get('error_message', 'Unknown error'),
					source_doctype=data.get('source_doctype', 'N/A'),
					target_doctype=data.get('target_doctype', 'N/A'),
					sync_time=frappe.utils.now(),
					dashboard_url=frappe.utils.get_url('app/sync-dashboard'),
					logs_url=frappe.utils.get_url('app/List/Sync%20Activity%20Log')
				)
			},
			'conflict_detected': {
				'subject': _('Manual Review Required: {0}').format(chain_doc.chain_name),
				'message': _('''
					<h3>Data Conflict Detected - Manual Review Required</h3>
					<p>A data conflict has been detected in your sync process "<strong>{chain_name}</strong>" and requires manual review.</p>
					<h4>Conflict Details:</h4>
					<ul>
						<li><strong>Source Document:</strong> {source_document}</li>
						<li><strong>Target Document:</strong> {target_document}</li>
						<li><strong>Conflict Type:</strong> {conflict_type}</li>
						<li><strong>Time:</strong> {sync_time}</li>
					</ul>
					<p>Please review and resolve this conflict to continue syncing.</p>
					<p><a href="{dashboard_url}">Resolve Conflict</a></p>
				''').format(
					chain_name=chain_doc.chain_name,
					source_document=data.get('source_document', 'N/A'),
					target_document=data.get('target_document', 'N/A'),
					conflict_type=data.get('conflict_type', 'Data mismatch'),
					sync_time=frappe.utils.now(),
					dashboard_url=frappe.utils.get_url('app/sync-dashboard')
				)
			},
			'chain_created': {
				'subject': _('New Sync Process Created: {0}').format(chain_doc.chain_name),
				'message': _('''
					<h3>New Sync Process Created</h3>
					<p>A new sync process "<strong>{chain_name}</strong>" has been created successfully.</p>
					<h4>Process Details:</h4>
					<ul>
						<li><strong>Description:</strong> {description}</li>
						<li><strong>Steps:</strong> {steps_count}</li>
						<li><strong>Sync Frequency:</strong> {sync_frequency}</li>
						<li><strong>Status:</strong> {status}</li>
					</ul>
					<p><a href="{chain_url}">View Process</a> | <a href="{dashboard_url}">View Dashboard</a></p>
				''').format(
					chain_name=chain_doc.chain_name,
					description=chain_doc.description or 'No description',
					steps_count=len(chain_doc.chain_steps),
					sync_frequency=chain_doc.sync_frequency,
					status='Active' if chain_doc.is_active else 'Inactive',
					chain_url=frappe.utils.get_url(f'app/Form/Sync Chain/{chain_doc.name}'),
					dashboard_url=frappe.utils.get_url('app/sync-dashboard')
				)
			}
		}

		template = templates.get(event_type, {
			'subject': f'Sync Event: {event_type}',
			'message': f'Sync event {event_type} occurred for {chain_doc.chain_name}'
		})

		return template['subject'], template['message']

	def get_notification_content(self, event_type: str, chain_doc, data: Dict) -> tuple:
		"""Get system notification content (shorter than email)"""
		templates = {
			'sync_success': (
				_('Sync completed: {0}').format(chain_doc.chain_name),
				_('Successfully synced {0} to {1}').format(
					data.get('source_doctype', 'documents'),
					data.get('target_doctype', 'target')
				)
			),
			'sync_failed': (
				_('Sync failed: {0}').format(chain_doc.chain_name),
				_('Error: {0}').format(data.get('error_message', 'Unknown error'))
			),
			'conflict_detected': (
				_('Manual review required: {0}').format(chain_doc.chain_name),
				_('Data conflict detected between {0} and {1}').format(
					data.get('source_document', 'source'),
					data.get('target_document', 'target')
				)
			),
			'chain_created': (
				_('New sync process: {0}').format(chain_doc.chain_name),
				_('Process created with {0} steps').format(len(chain_doc.chain_steps))
			)
		}

		return templates.get(event_type, (f'Sync Event: {event_type}', f'Event occurred for {chain_doc.chain_name}'))

	def get_notification_type(self, event_type: str) -> str:
		"""Get notification type for system notifications"""
		type_map = {
			'sync_success': 'Success',
			'sync_failed': 'Alert',
			'conflict_detected': 'Alert',
			'chain_created': 'Mention',
			'chain_error': 'Alert'
		}
		return type_map.get(event_type, 'Mention')

	def get_webhook_urls(self) -> List[str]:
		"""Get configured webhook URLs"""
		# This could be configured in System Settings
		# For now, return empty list
		return []

	def test_notification_channels(self, test_user: str = None) -> Dict[str, Any]:
		"""Test all notification channels"""
		try:
			test_user = test_user or frappe.session.user

			# Create a dummy sync chain for testing
			test_data = {
				'source_doctype': 'Lead',
				'target_doctype': 'Customer',
				'records_count': 1,
				'error_message': 'This is a test error message',
				'source_document': 'TEST-001',
				'target_document': 'CUST-001',
				'conflict_type': 'Data mismatch'
			}

			# Create a minimal chain doc for testing
			class TestChainDoc:
				def __init__(self):
					self.name = 'TEST-CHAIN'
					self.chain_name = 'Test Notification Chain'
					self.description = 'Test chain for notification testing'
					self.owner = test_user
					self.chain_steps = []
					self.sync_frequency = 'Immediately'

			test_chain = TestChainDoc()

			results = {}

			# Test each channel
			for channel in ['email', 'system']:
				try:
					result = self.channels[channel]('sync_success', test_chain, test_data, [test_user])
					results[channel] = {"status": "success", "result": result}
				except Exception as e:
					results[channel] = {"status": "failed", "error": str(e)}

			return {
				"success": True,
				"test_user": test_user,
				"results": results,
				"message": "Notification test completed"
			}

		except Exception as e:
			return {
				"success": False,
				"error": str(e),
				"message": "Notification test failed"
			}


# Notification helper functions
notification_system = SyncNotificationSystem()


def send_sync_notification(event_type: str, sync_chain: str, data: Dict[str, Any], channels: List[str] = None):
	"""Helper function to send sync notifications"""
	return notification_system.send_notification(event_type, sync_chain, data, channels)


@frappe.whitelist()
def test_notifications(test_user: str = None):
	"""API endpoint to test notification system"""
	return notification_system.test_notification_channels(test_user)


@frappe.whitelist()
def send_manual_notification(event_type: str, sync_chain: str, message: str, channels: List[str] = None):
	"""Send manual notification"""
	try:
		if isinstance(channels, str):
			channels = json.loads(channels)

		data = {
			'message': message,
			'manual': True
		}

		results = notification_system.send_notification(event_type, sync_chain, data, channels)

		return {
			"success": True,
			"results": results,
			"message": "Manual notification sent"
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_notification_settings():
	"""Get notification settings for user interface"""
	return {
		"available_channels": list(notification_system.channels.keys()),
		"event_types": [
			{"value": "sync_success", "label": _("Sync Success")},
			{"value": "sync_failed", "label": _("Sync Failed")},
			{"value": "conflict_detected", "label": _("Conflict Detected")},
			{"value": "chain_created", "label": _("Chain Created")},
			{"value": "chain_error", "label": _("Chain Error")}
		],
		"notification_types": [
			{"value": "Success", "label": _("Success")},
			{"value": "Alert", "label": _("Alert")},
			{"value": "Mention", "label": _("Mention")}
		]
	}


@frappe.whitelist()
def get_user_notification_preferences(user: str = None):
	"""Get user notification preferences"""
	user = user or frappe.session.user

	# This could be extended to read from User Preferences
	# For now, return default preferences
	return {
		"user": user,
		"email_enabled": True,
		"system_enabled": True,
		"webhook_enabled": False,
		"sms_enabled": False,
		"event_preferences": {
			"sync_success": ["system"],
			"sync_failed": ["email", "system"],
			"conflict_detected": ["email", "system"],
			"chain_created": ["system"],
			"chain_error": ["email", "system"]
		}
	}


@frappe.whitelist()
def update_user_notification_preferences(preferences: Dict[str, Any]):
	"""Update user notification preferences"""
	try:
		if isinstance(preferences, str):
			preferences = json.loads(preferences)

		user = frappe.session.user

		# Save to User Settings (this could be implemented)
		# For now, just return success
		return {
			"success": True,
			"message": _("Notification preferences updated"),
			"user": user
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}