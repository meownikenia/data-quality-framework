"""Alerting integrations."""

from dq_framework.alerting.slack import SlackAlertError, SlackAlerter

__all__ = ["SlackAlerter", "SlackAlertError"]