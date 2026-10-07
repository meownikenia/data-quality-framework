"""Alerting integrations."""

from dq_framework.alerting.slack import SlackAlerter, SlackAlertError

__all__ = ["SlackAlerter", "SlackAlertError"]
