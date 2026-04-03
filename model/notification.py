class Notification:
    def __init__(self, notification_id, alert_type, location_id, severity, message, timestamp):
        self.notification_id = notification_id
        self.alert_type = alert_type
        self.location_id = location_id
        self.severity = severity
        self.message = message
        self.timestamp = timestamp
        self.is_sent = False

    def mark_sent(self):
        self.is_sent = True

    def is_high_priority(self):
        return self.severity.lower() in ["high", "critical"]

    def __str__(self):
        return f"{self.alert_type} - {self.message}"