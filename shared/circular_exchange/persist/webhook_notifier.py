"""
=============================================================================
WEBHOOK NOTIFIER - Notifications for Critical Insights and Events
=============================================================================

This module implements webhook-based notifications for the CEF system:
- Critical insight notifications
- Pattern detection alerts
- Test failure alerts
- Model performance degradation alerts

Circular Exchange Framework Integration:
-----------------------------------------
Module ID: shared.circular_exchange.webhook_notifier
Description: Webhook-based notifications for critical events and insights
Dependencies: [shared.circular_exchange.metrics_analyzer, shared.circular_exchange.data_collector]
Exports: [WebhookNotifier, NotificationConfig, NotificationLevel, WEBHOOK_NOTIFIER]

=============================================================================
"""

import logging
import threading
import json
import os
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import hashlib

logger = logging.getLogger(__name__)


class NotificationLevel(Enum):
    """Notification severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class NotificationChannel(Enum):
    """Supported notification channels."""
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    TEAMS = "teams"
    EMAIL = "email"  # Future support


@dataclass
class NotificationConfig:
    """Configuration for a notification endpoint."""
    channel: NotificationChannel
    url: str
    name: str = ""
    enabled: bool = True
    min_level: NotificationLevel = NotificationLevel.WARNING
    secret: Optional[str] = None  # For signature verification
    headers: Dict[str, str] = field(default_factory=dict)
    retry_count: int = 3
    retry_delay_seconds: float = 1.0
    
    def __post_init__(self):
        if not self.name:
            self.name = f"{self.channel.value}_{hash(self.url) % 10000}"


@dataclass
class Notification:
    """Represents a notification to be sent."""
    notification_id: str
    level: NotificationLevel
    title: str
    message: str
    source: str  # Module that generated the notification
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "notification_id": self.notification_id,
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "tags": self.tags
        }
    
    def to_slack_payload(self) -> Dict[str, Any]:
        """Format for Slack webhook."""
        color_map = {
            NotificationLevel.CRITICAL: "#dc3545",
            NotificationLevel.WARNING: "#ffc107",
            NotificationLevel.INFO: "#17a2b8",
            NotificationLevel.DEBUG: "#6c757d"
        }
        
        return {
            "attachments": [{
                "color": color_map.get(self.level, "#6c757d"),
                "title": f"[{self.level.value.upper()}] {self.title}",
                "text": self.message,
                "fields": [
                    {"title": "Source", "value": self.source, "short": True},
                    {"title": "Time", "value": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"), "short": True}
                ],
                "footer": "CEF Notification System",
                "ts": int(self.timestamp.timestamp())
            }]
        }
    
    def to_discord_payload(self) -> Dict[str, Any]:
        """Format for Discord webhook."""
        color_map = {
            NotificationLevel.CRITICAL: 0xdc3545,
            NotificationLevel.WARNING: 0xffc107,
            NotificationLevel.INFO: 0x17a2b8,
            NotificationLevel.DEBUG: 0x6c757d
        }
        
        return {
            "embeds": [{
                "title": f"[{self.level.value.upper()}] {self.title}",
                "description": self.message,
                "color": color_map.get(self.level, 0x6c757d),
                "fields": [
                    {"name": "Source", "value": self.source, "inline": True},
                    {"name": "Tags", "value": ", ".join(self.tags) if self.tags else "None", "inline": True}
                ],
                "timestamp": self.timestamp.isoformat(),
                "footer": {"text": "CEF Notification System"}
            }]
        }
    
    def to_teams_payload(self) -> Dict[str, Any]:
        """Format for Microsoft Teams webhook."""
        color_map = {
            NotificationLevel.CRITICAL: "dc3545",
            NotificationLevel.WARNING: "ffc107",
            NotificationLevel.INFO: "17a2b8",
            NotificationLevel.DEBUG: "6c757d"
        }
        
        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color_map.get(self.level, "6c757d"),
            "summary": self.title,
            "sections": [{
                "activityTitle": f"[{self.level.value.upper()}] {self.title}",
                "facts": [
                    {"name": "Source", "value": self.source},
                    {"name": "Time", "value": self.timestamp.strftime("%Y-%m-%d %H:%M:%S")},
                    {"name": "Message", "value": self.message}
                ],
                "markdown": True
            }]
        }


class WebhookNotifier:
    """
    Centralized webhook notification system for CEF.
    
    Supports multiple notification channels:
    - Generic webhooks
    - Slack
    - Discord
    - Microsoft Teams
    
    Features:
    - Automatic retry on failure
    - Rate limiting
    - Notification history
    - Configurable severity levels
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for global notification system."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the webhook notifier."""
        if self._initialized:
            return
        
        self._lock = threading.RLock()
        
        # Configuration
        self._endpoints: Dict[str, NotificationConfig] = {}
        self._notification_history: List[Notification] = []
        self._max_history = int(os.getenv('WEBHOOK_MAX_HISTORY', 1000))
        
        # Rate limiting
        self._rate_limit_window = 60  # seconds
        self._max_notifications_per_window = int(os.getenv('WEBHOOK_RATE_LIMIT', 100))
        self._notification_timestamps: List[float] = []
        
        # Stats
        self._stats = {
            'total_sent': 0,
            'total_failed': 0,
            'total_rate_limited': 0
        }
        
        # Load endpoints from environment
        self._load_env_endpoints()
        
        self._initialized = True
        logger.info("WebhookNotifier initialized with %d endpoints", len(self._endpoints))
    
    def _load_env_endpoints(self) -> None:
        """Load webhook endpoints from environment variables."""
        # Format: WEBHOOK_ENDPOINT_<NAME>=<URL>
        # Optional: WEBHOOK_<NAME>_LEVEL=<LEVEL>
        
        for key, value in os.environ.items():
            if key.startswith('WEBHOOK_ENDPOINT_'):
                name = key.replace('WEBHOOK_ENDPOINT_', '').lower()
                level_key = f"WEBHOOK_{name.upper()}_LEVEL"
                level_str = os.getenv(level_key, 'WARNING')
                
                try:
                    level = NotificationLevel[level_str.upper()]
                except KeyError:
                    level = NotificationLevel.WARNING
                
                # Detect channel type from URL
                channel = self._detect_channel(value)
                
                self.add_endpoint(NotificationConfig(
                    channel=channel,
                    url=value,
                    name=name,
                    min_level=level
                ))
    
    def _detect_channel(self, url: str) -> NotificationChannel:
        """Detect the notification channel from the URL."""
        if 'slack.com' in url or 'hooks.slack' in url:
            return NotificationChannel.SLACK
        elif 'discord.com' in url or 'discordapp.com' in url:
            return NotificationChannel.DISCORD
        elif 'office.com' in url or 'microsoft.com' in url:
            return NotificationChannel.TEAMS
        else:
            return NotificationChannel.WEBHOOK
    
    def add_endpoint(self, config: NotificationConfig) -> None:
        """Add a notification endpoint."""
        with self._lock:
            self._endpoints[config.name] = config
            logger.info("Added notification endpoint: %s (%s)", config.name, config.channel.value)
    
    def remove_endpoint(self, name: str) -> bool:
        """Remove a notification endpoint."""
        with self._lock:
            if name in self._endpoints:
                del self._endpoints[name]
                logger.info("Removed notification endpoint: %s", name)
                return True
            return False
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = time.time()
        
        # Remove old timestamps
        self._notification_timestamps = [
            ts for ts in self._notification_timestamps
            if now - ts < self._rate_limit_window
        ]
        
        return len(self._notification_timestamps) < self._max_notifications_per_window
    
    def _format_payload(self, notification: Notification, channel: NotificationChannel) -> Dict[str, Any]:
        """Format the notification payload for the target channel."""
        if channel == NotificationChannel.SLACK:
            return notification.to_slack_payload()
        elif channel == NotificationChannel.DISCORD:
            return notification.to_discord_payload()
        elif channel == NotificationChannel.TEAMS:
            return notification.to_teams_payload()
        else:
            return notification.to_dict()
    
    def _sign_payload(self, payload: str, secret: str) -> str:
        """Sign a payload with HMAC-SHA256."""
        import hmac
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _send_webhook(self, config: NotificationConfig, notification: Notification) -> bool:
        """Send a notification to a single endpoint."""
        payload = self._format_payload(notification, config.channel)
        payload_str = json.dumps(payload)
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'CEF-Webhook-Notifier/1.0'
        }
        headers.update(config.headers)
        
        # Add signature if secret is configured
        if config.secret:
            headers['X-Webhook-Signature'] = self._sign_payload(payload_str, config.secret)
        
        for attempt in range(config.retry_count):
            try:
                request = Request(
                    config.url,
                    data=payload_str.encode('utf-8'),
                    headers=headers,
                    method='POST'
                )
                
                with urlopen(request, timeout=10) as response:
                    if response.status in (200, 201, 202, 204):
                        logger.debug("Notification sent to %s", config.name)
                        return True
                    else:
                        logger.warning("Webhook returned status %d", response.status)
                        
            except HTTPError as e:
                logger.warning("HTTP error sending to %s: %s", config.name, e)
            except URLError as e:
                logger.warning("URL error sending to %s: %s", config.name, e)
            except Exception as e:
                logger.error("Error sending to %s: %s", config.name, e)
            
            if attempt < config.retry_count - 1:
                time.sleep(config.retry_delay_seconds * (attempt + 1))
        
        return False
    
    def notify(
        self,
        title: str,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        source: str = "CEF",
        data: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        endpoint_filter: Optional[List[str]] = None
    ) -> bool:
        """
        Send a notification to all configured endpoints.
        
        Args:
            title: Notification title
            message: Notification message
            level: Severity level
            source: Module generating the notification
            data: Additional structured data
            tags: Tags for filtering/categorization
            endpoint_filter: Only send to these endpoints (by name)
            
        Returns:
            True if at least one notification was sent successfully
        """
        # Check rate limit
        if not self._check_rate_limit():
            self._stats['total_rate_limited'] += 1
            logger.warning("Rate limit exceeded, notification dropped")
            return False
        
        # Create notification
        notification = Notification(
            notification_id=f"notif_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            level=level,
            title=title,
            message=message,
            source=source,
            data=data or {},
            tags=tags or []
        )
        
        # Store in history
        with self._lock:
            self._notification_history.append(notification)
            if len(self._notification_history) > self._max_history:
                self._notification_history = self._notification_history[-self._max_history:]
            self._notification_timestamps.append(time.time())
        
        # Send to endpoints
        success_count = 0
        for name, config in self._endpoints.items():
            # Skip if endpoint is disabled
            if not config.enabled:
                continue
            
            # Apply endpoint filter
            if endpoint_filter and name not in endpoint_filter:
                continue
            
            # Check level threshold
            if level.value > config.min_level.value:
                continue
            
            if self._send_webhook(config, notification):
                success_count += 1
                self._stats['total_sent'] += 1
            else:
                self._stats['total_failed'] += 1
        
        return success_count > 0
    
    def notify_critical(self, title: str, message: str, source: str = "CEF", **kwargs) -> bool:
        """Send a critical notification."""
        return self.notify(title, message, NotificationLevel.CRITICAL, source, **kwargs)
    
    def notify_warning(self, title: str, message: str, source: str = "CEF", **kwargs) -> bool:
        """Send a warning notification."""
        return self.notify(title, message, NotificationLevel.WARNING, source, **kwargs)
    
    def notify_info(self, title: str, message: str, source: str = "CEF", **kwargs) -> bool:
        """Send an info notification."""
        return self.notify(title, message, NotificationLevel.INFO, source, **kwargs)
    
    # =========================================================================
    # CEF INTEGRATION - Auto-notify on patterns and insights
    # =========================================================================
    
    def setup_cef_subscriptions(self) -> None:
        """Set up automatic notifications for CEF events."""
        try:
            from shared.circular_exchange.analysis.metrics_analyzer import METRICS_ANALYZER
            from shared.circular_exchange.analysis.data_collector import DATA_COLLECTOR, DataCategory
            
            # Subscribe to patterns
            METRICS_ANALYZER.subscribe_to_patterns(self._on_pattern_detected)
            
            # Subscribe to insights
            METRICS_ANALYZER.subscribe_to_insights(self._on_insight_generated)
            
            # Subscribe to critical test failures
            DATA_COLLECTOR.subscribe(DataCategory.TEST_RESULT, self._on_test_result)
            
            logger.info("CEF subscriptions set up successfully")
            
        except ImportError as e:
            logger.warning("Could not set up CEF subscriptions: %s", e)
    
    def _on_pattern_detected(self, pattern) -> None:
        """Handle pattern detection."""
        from shared.circular_exchange.analysis.metrics_analyzer import PatternType
        
        if pattern.occurrences >= 10 or pattern.pattern_type == PatternType.ERROR_RECURRING:
            self.notify_warning(
                title=f"Pattern Detected: {pattern.pattern_type.value}",
                message=pattern.description,
                source="MetricsAnalyzer",
                data={"pattern_id": pattern.pattern_id, "occurrences": pattern.occurrences},
                tags=["pattern", pattern.pattern_type.value]
            )
    
    def _on_insight_generated(self, insight) -> None:
        """Handle insight generation."""
        from shared.circular_exchange.analysis.metrics_analyzer import InsightPriority
        
        if insight.priority in (InsightPriority.CRITICAL, InsightPriority.HIGH):
            level = NotificationLevel.CRITICAL if insight.priority == InsightPriority.CRITICAL else NotificationLevel.WARNING
            
            self.notify(
                title=insight.title,
                message=insight.description,
                level=level,
                source="MetricsAnalyzer",
                data={"insight_id": insight.insight_id, "category": insight.category.value},
                tags=["insight", insight.category.value]
            )
    
    def _on_test_result(self, result) -> None:
        """Handle test result - notify on failures."""
        from shared.circular_exchange.analysis.data_collector import TestStatus
        
        if result.status == TestStatus.FAILED and result.error_message:
            # Only notify on first failure (avoid spam)
            self.notify_warning(
                title=f"Test Failed: {result.test_name}",
                message=result.error_message[:500],
                source="DataCollector",
                data={"test_id": result.test_id, "module": result.module_path},
                tags=["test", "failure"]
            )
    
    # =========================================================================
    # QUERY METHODS
    # =========================================================================
    
    def get_history(self, limit: int = 100, level: Optional[NotificationLevel] = None) -> List[Notification]:
        """Get notification history."""
        with self._lock:
            history = self._notification_history.copy()
        
        if level:
            history = [n for n in history if n.level == level]
        
        return history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics."""
        with self._lock:
            stats = self._stats.copy()
            stats['configured_endpoints'] = len(self._endpoints)
            stats['enabled_endpoints'] = sum(1 for e in self._endpoints.values() if e.enabled)
            stats['history_size'] = len(self._notification_history)
            return stats
    
    def get_endpoints(self) -> List[Dict[str, Any]]:
        """Get list of configured endpoints (without secrets)."""
        with self._lock:
            return [
                {
                    'name': config.name,
                    'channel': config.channel.value,
                    'enabled': config.enabled,
                    'min_level': config.min_level.value,
                    'url': config.url[:50] + '...' if len(config.url) > 50 else config.url
                }
                for config in self._endpoints.values()
            ]


# Global singleton instance
WEBHOOK_NOTIFIER = WebhookNotifier()


# Circular Exchange Framework Integration
try:
    from shared.circular_exchange import PROJECT_CONFIG, ModuleRegistration
    CIRCULAR_EXCHANGE_AVAILABLE = True
except ImportError:
    CIRCULAR_EXCHANGE_AVAILABLE = False

if CIRCULAR_EXCHANGE_AVAILABLE:
    try:
        PROJECT_CONFIG.register_module(ModuleRegistration(
            module_id="shared.circular_exchange.webhook_notifier",
            file_path=__file__,
            description="Webhook-based notifications for critical events and insights",
            dependencies=["shared.circular_exchange.metrics_analyzer", "shared.circular_exchange.data_collector"],
            exports=["WebhookNotifier", "NotificationConfig", "NotificationLevel", 
                    "NotificationChannel", "Notification", "WEBHOOK_NOTIFIER"]
        ))
    except Exception:
        pass  # Ignore registration errors during import
