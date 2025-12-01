"""
Tests for the WebhookNotifier module.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import json

from shared.circular_exchange.webhook_notifier import (
    WebhookNotifier,
    NotificationConfig,
    NotificationChannel,
    NotificationLevel,
    Notification,
    WEBHOOK_NOTIFIER
)


class TestNotification:
    """Tests for the Notification dataclass."""
    
    def test_notification_creation(self):
        """Test creating a notification."""
        notif = Notification(
            notification_id="test_001",
            level=NotificationLevel.WARNING,
            title="Test Title",
            message="Test message",
            source="test_module",
            data={"key": "value"},
            tags=["test", "demo"]
        )
        
        assert notif.notification_id == "test_001"
        assert notif.level == NotificationLevel.WARNING
        assert notif.title == "Test Title"
        assert notif.message == "Test message"
        assert notif.source == "test_module"
        assert notif.data == {"key": "value"}
        assert notif.tags == ["test", "demo"]
    
    def test_notification_to_dict(self):
        """Test converting notification to dictionary."""
        notif = Notification(
            notification_id="test_001",
            level=NotificationLevel.INFO,
            title="Test",
            message="Test message",
            source="test"
        )
        
        data = notif.to_dict()
        
        assert data["notification_id"] == "test_001"
        assert data["level"] == "info"
        assert data["title"] == "Test"
        assert "timestamp" in data
    
    def test_slack_payload_format(self):
        """Test Slack payload formatting."""
        notif = Notification(
            notification_id="test_001",
            level=NotificationLevel.CRITICAL,
            title="Critical Issue",
            message="Something went wrong",
            source="test"
        )
        
        payload = notif.to_slack_payload()
        
        assert "attachments" in payload
        assert len(payload["attachments"]) == 1
        assert payload["attachments"][0]["color"] == "#dc3545"  # Critical = red
        assert "Critical Issue" in payload["attachments"][0]["title"]
    
    def test_discord_payload_format(self):
        """Test Discord payload formatting."""
        notif = Notification(
            notification_id="test_001",
            level=NotificationLevel.WARNING,
            title="Warning",
            message="Check this out",
            source="test"
        )
        
        payload = notif.to_discord_payload()
        
        assert "embeds" in payload
        assert len(payload["embeds"]) == 1
        assert payload["embeds"][0]["color"] == 0xffc107  # Warning = yellow
    
    def test_teams_payload_format(self):
        """Test Microsoft Teams payload formatting."""
        notif = Notification(
            notification_id="test_001",
            level=NotificationLevel.INFO,
            title="Info",
            message="FYI",
            source="test"
        )
        
        payload = notif.to_teams_payload()
        
        assert payload["@type"] == "MessageCard"
        assert "sections" in payload


class TestNotificationConfig:
    """Tests for NotificationConfig."""
    
    def test_config_creation(self):
        """Test creating a notification config."""
        config = NotificationConfig(
            channel=NotificationChannel.SLACK,
            url="https://hooks.slack.com/test",
            name="my_slack",
            min_level=NotificationLevel.WARNING
        )
        
        assert config.channel == NotificationChannel.SLACK
        assert config.url == "https://hooks.slack.com/test"
        assert config.name == "my_slack"
        assert config.min_level == NotificationLevel.WARNING
        assert config.enabled is True
        assert config.retry_count == 3
    
    def test_auto_generated_name(self):
        """Test auto-generated name from URL."""
        config = NotificationConfig(
            channel=NotificationChannel.WEBHOOK,
            url="https://example.com/webhook"
        )
        
        assert config.name.startswith("webhook_")


class TestWebhookNotifier:
    """Tests for the WebhookNotifier class."""
    
    def test_singleton_pattern(self):
        """Test that WebhookNotifier is a singleton."""
        notifier1 = WebhookNotifier()
        notifier2 = WebhookNotifier()
        
        assert notifier1 is notifier2
    
    def test_add_endpoint(self):
        """Test adding an endpoint."""
        notifier = WebhookNotifier()
        initial_count = len(notifier._endpoints)
        
        config = NotificationConfig(
            channel=NotificationChannel.WEBHOOK,
            url="https://test.example.com/webhook",
            name="test_endpoint_add"
        )
        notifier.add_endpoint(config)
        
        assert "test_endpoint_add" in notifier._endpoints
        
        # Clean up
        notifier.remove_endpoint("test_endpoint_add")
    
    def test_remove_endpoint(self):
        """Test removing an endpoint."""
        notifier = WebhookNotifier()
        
        config = NotificationConfig(
            channel=NotificationChannel.WEBHOOK,
            url="https://test.example.com/webhook",
            name="test_endpoint_remove"
        )
        notifier.add_endpoint(config)
        
        result = notifier.remove_endpoint("test_endpoint_remove")
        assert result is True
        
        result = notifier.remove_endpoint("nonexistent")
        assert result is False
    
    def test_detect_channel(self):
        """Test channel detection from URL."""
        notifier = WebhookNotifier()
        
        assert notifier._detect_channel("https://hooks.slack.com/services/xxx") == NotificationChannel.SLACK
        assert notifier._detect_channel("https://discord.com/api/webhooks/xxx") == NotificationChannel.DISCORD
        assert notifier._detect_channel("https://outlook.office.com/webhook/xxx") == NotificationChannel.TEAMS
        assert notifier._detect_channel("https://example.com/webhook") == NotificationChannel.WEBHOOK
    
    def test_rate_limiting(self):
        """Test rate limiting check."""
        notifier = WebhookNotifier()
        
        # Should not be rate limited initially
        assert notifier._check_rate_limit() is True
    
    def test_notification_history(self):
        """Test notification history storage."""
        notifier = WebhookNotifier()
        
        # Create a notification (even if sending fails)
        notifier.notify(
            title="History Test",
            message="Testing history",
            level=NotificationLevel.INFO,
            source="test"
        )
        
        history = notifier.get_history(limit=10)
        assert len(history) > 0
        
        # Find our notification
        found = any(n.title == "History Test" for n in history)
        assert found
    
    def test_get_stats(self):
        """Test getting notification stats."""
        notifier = WebhookNotifier()
        
        stats = notifier.get_stats()
        
        assert "total_sent" in stats
        assert "total_failed" in stats
        assert "configured_endpoints" in stats
        assert "enabled_endpoints" in stats
        assert "history_size" in stats
    
    def test_get_endpoints(self):
        """Test getting endpoint list."""
        notifier = WebhookNotifier()
        
        endpoints = notifier.get_endpoints()
        
        assert isinstance(endpoints, list)
        for endpoint in endpoints:
            assert "name" in endpoint
            assert "channel" in endpoint
            assert "enabled" in endpoint
    
    def test_notify_critical(self):
        """Test critical notification shortcut."""
        notifier = WebhookNotifier()
        
        result = notifier.notify_critical(
            title="Critical Test",
            message="Critical message",
            source="test"
        )
        
        # Result may be False due to no valid endpoints, but should not raise
        assert isinstance(result, bool)
    
    def test_notify_warning(self):
        """Test warning notification shortcut."""
        notifier = WebhookNotifier()
        
        result = notifier.notify_warning(
            title="Warning Test",
            message="Warning message",
            source="test"
        )
        
        assert isinstance(result, bool)
    
    def test_notify_info(self):
        """Test info notification shortcut."""
        notifier = WebhookNotifier()
        
        result = notifier.notify_info(
            title="Info Test",
            message="Info message",
            source="test"
        )
        
        assert isinstance(result, bool)
    
    def test_format_payload(self):
        """Test payload formatting for different channels."""
        notifier = WebhookNotifier()
        
        notification = Notification(
            notification_id="test_001",
            level=NotificationLevel.WARNING,
            title="Test",
            message="Test message",
            source="test"
        )
        
        # Test each channel format
        slack_payload = notifier._format_payload(notification, NotificationChannel.SLACK)
        assert "attachments" in slack_payload
        
        discord_payload = notifier._format_payload(notification, NotificationChannel.DISCORD)
        assert "embeds" in discord_payload
        
        teams_payload = notifier._format_payload(notification, NotificationChannel.TEAMS)
        assert "@type" in teams_payload
        
        generic_payload = notifier._format_payload(notification, NotificationChannel.WEBHOOK)
        assert "notification_id" in generic_payload


class TestGlobalInstance:
    """Tests for the global WEBHOOK_NOTIFIER instance."""
    
    def test_global_instance_exists(self):
        """Test that the global instance exists."""
        assert WEBHOOK_NOTIFIER is not None
        assert isinstance(WEBHOOK_NOTIFIER, WebhookNotifier)
    
    def test_global_instance_is_singleton(self):
        """Test that global instance is the singleton."""
        assert WEBHOOK_NOTIFIER is WebhookNotifier()
