"""
Tests for Alerts Module
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from ..alerts.rules import (
    AlertRule, AlertCondition, AlertSeverity, AlertState,
    ConditionOperator
)
from ..alerts.engine import AlertEngine, AlertEvent
from ..alerts.channels import (
    NotificationChannel, ChannelType, ChannelManager,
    SlackConfig, EmailConfig
)
from ..alerts.incidents import Incident, IncidentManager, IncidentStatus


class TestAlertRule:
    """Tests for AlertRule."""
    
    def test_create_rule(self):
        """Test creating alert rule."""
        rule = AlertRule(
            id="test_rule",
            name="High Error Rate",
            description="Alert when error rate exceeds 5%",
            severity=AlertSeverity.WARNING,
            conditions=[
                AlertCondition(
                    metric="error_rate",
                    operator=ConditionOperator.GREATER_THAN,
                    threshold=0.05
                )
            ]
        )
        
        assert rule.id == "test_rule"
        assert rule.severity == AlertSeverity.WARNING
        assert len(rule.conditions) == 1
    
    def test_evaluate_condition_gt(self):
        """Test evaluating greater than condition."""
        condition = AlertCondition(
            metric="error_rate",
            operator=ConditionOperator.GREATER_THAN,
            threshold=0.05
        )
        
        assert condition.evaluate(0.10) is True
        assert condition.evaluate(0.03) is False
        assert condition.evaluate(0.05) is False
    
    def test_evaluate_condition_lt(self):
        """Test evaluating less than condition."""
        condition = AlertCondition(
            metric="success_rate",
            operator=ConditionOperator.LESS_THAN,
            threshold=0.95
        )
        
        assert condition.evaluate(0.90) is True
        assert condition.evaluate(0.98) is False
    
    def test_evaluate_condition_eq(self):
        """Test evaluating equal condition."""
        condition = AlertCondition(
            metric="status_code",
            operator=ConditionOperator.EQUAL,
            threshold=500
        )
        
        assert condition.evaluate(500) is True
        assert condition.evaluate(200) is False
    
    def test_rule_state_transitions(self):
        """Test rule state transitions."""
        rule = AlertRule(
            id="test",
            name="Test",
            conditions=[
                AlertCondition(
                    metric="value",
                    operator=ConditionOperator.GREATER_THAN,
                    threshold=100
                )
            ]
        )
        
        assert rule.state == AlertState.OK
        
        # Trigger pending
        rule.update_state(True)
        assert rule.state == AlertState.PENDING
        
        # Trigger firing after duration
        rule.pending_since = datetime.now() - timedelta(minutes=10)
        rule.update_state(True)
        assert rule.state == AlertState.FIRING
        
        # Resolve
        rule.update_state(False)
        assert rule.state == AlertState.OK
    
    def test_factory_high_error_rate(self):
        """Test high error rate factory."""
        rule = AlertRule.high_error_rate(
            threshold=0.05,
            duration_minutes=5
        )
        
        assert "error" in rule.name.lower()
        assert rule.severity == AlertSeverity.CRITICAL


class TestAlertEngine:
    """Tests for AlertEngine."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.engine = AlertEngine()
    
    def test_add_rule(self):
        """Test adding rule to engine."""
        rule = AlertRule(
            id="test_rule",
            name="Test",
            conditions=[]
        )
        
        self.engine.add_rule(rule)
        
        assert self.engine.get_rule("test_rule") is not None
    
    def test_remove_rule(self):
        """Test removing rule from engine."""
        rule = AlertRule(id="test", name="Test", conditions=[])
        self.engine.add_rule(rule)
        
        result = self.engine.remove_rule("test")
        
        assert result is True
        assert self.engine.get_rule("test") is None
    
    def test_get_firing_alerts(self):
        """Test getting firing alerts."""
        rule = AlertRule(
            id="firing_rule",
            name="Firing",
            conditions=[],
            state=AlertState.FIRING
        )
        self.engine.add_rule(rule)
        
        firing = self.engine.get_firing_alerts()
        
        assert len(firing) == 1
        assert firing[0].id == "firing_rule"
    
    @pytest.mark.asyncio
    async def test_register_handler(self):
        """Test registering alert handler."""
        events = []
        
        async def handler(event: AlertEvent):
            events.append(event)
        
        self.engine.register_handler(handler)
        
        # Trigger an event
        event = AlertEvent(
            rule_id="test",
            rule_name="Test",
            state=AlertState.FIRING,
            severity=AlertSeverity.WARNING
        )
        
        await self.engine._dispatch_event(event)
        
        assert len(events) == 1


class TestNotificationChannel:
    """Tests for NotificationChannel."""
    
    def test_create_slack_channel(self):
        """Test creating Slack channel."""
        channel = NotificationChannel(
            id="slack_main",
            name="Main Slack",
            type=ChannelType.SLACK,
            config=SlackConfig(
                webhook_url="https://hooks.slack.com/...",
                channel="#alerts"
            )
        )
        
        assert channel.type == ChannelType.SLACK
        assert channel.config.channel == "#alerts"
    
    def test_create_email_channel(self):
        """Test creating Email channel."""
        channel = NotificationChannel(
            id="email_ops",
            name="Ops Email",
            type=ChannelType.EMAIL,
            config=EmailConfig(
                recipients=["ops@example.com"],
                smtp_host="smtp.example.com"
            )
        )
        
        assert channel.type == ChannelType.EMAIL
        assert "ops@example.com" in channel.config.recipients


class TestChannelManager:
    """Tests for ChannelManager."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.manager = ChannelManager()
    
    def test_register_channel(self):
        """Test registering channel."""
        channel = NotificationChannel(
            id="test_channel",
            name="Test",
            type=ChannelType.WEBHOOK,
            config={}
        )
        
        self.manager.register(channel)
        
        assert self.manager.get("test_channel") is not None
    
    def test_list_by_type(self):
        """Test listing channels by type."""
        self.manager.register(NotificationChannel(
            id="slack1", name="Slack 1", type=ChannelType.SLACK, config={}
        ))
        self.manager.register(NotificationChannel(
            id="email1", name="Email 1", type=ChannelType.EMAIL, config={}
        ))
        self.manager.register(NotificationChannel(
            id="slack2", name="Slack 2", type=ChannelType.SLACK, config={}
        ))
        
        slack_channels = self.manager.list_by_type(ChannelType.SLACK)
        
        assert len(slack_channels) == 2


class TestIncident:
    """Tests for Incident."""
    
    def test_create_incident(self):
        """Test creating incident."""
        incident = Incident(
            id="inc_001",
            title="High Error Rate",
            description="Error rate exceeded 10%",
            severity="sev2"
        )
        
        assert incident.status == IncidentStatus.OPEN
        assert incident.severity == "sev2"
    
    def test_add_update(self):
        """Test adding update to incident."""
        incident = Incident(id="inc_001", title="Test")
        
        incident.add_update(
            author="user1",
            message="Investigating the issue"
        )
        
        assert len(incident.updates) == 1
        assert incident.updates[0].author == "user1"
    
    def test_acknowledge(self):
        """Test acknowledging incident."""
        incident = Incident(id="inc_001", title="Test")
        
        incident.acknowledge("user1")
        
        assert incident.status == IncidentStatus.ACKNOWLEDGED
        assert incident.acknowledged_at is not None
    
    def test_resolve(self):
        """Test resolving incident."""
        incident = Incident(id="inc_001", title="Test")
        
        incident.resolve(
            root_cause="Database connection pool exhausted",
            resolution="Increased pool size"
        )
        
        assert incident.status == IncidentStatus.RESOLVED
        assert incident.resolved_at is not None
        assert incident.root_cause is not None


class TestIncidentManager:
    """Tests for IncidentManager."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.manager = IncidentManager()
    
    def test_create_incident(self):
        """Test creating incident through manager."""
        incident = self.manager.create(
            title="Service Down",
            description="API not responding",
            severity="sev1",
            alert_rule_ids=["rule_1"]
        )
        
        assert incident.id is not None
        assert self.manager.get(incident.id) is not None
    
    def test_list_open_incidents(self):
        """Test listing open incidents."""
        self.manager.create(title="Incident 1", severity="sev2")
        inc2 = self.manager.create(title="Incident 2", severity="sev3")
        inc2.resolve("Fixed", "Restarted service")
        
        open_incidents = self.manager.list_open()
        
        assert len(open_incidents) == 1
    
    def test_get_stats(self):
        """Test getting incident stats."""
        self.manager.create(title="Inc 1", severity="sev1")
        self.manager.create(title="Inc 2", severity="sev2")
        inc3 = self.manager.create(title="Inc 3", severity="sev2")
        inc3.resolve("Fixed", "Fixed")
        
        stats = self.manager.get_stats()
        
        assert stats["total"] == 3
        assert stats["open"] == 2
        assert stats["resolved"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
