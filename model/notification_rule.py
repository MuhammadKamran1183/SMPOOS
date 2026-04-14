class NotificationRule:
    def __init__(
        self,
        rule_id,
        name,
        location_id,
        target_role,
        context_type,
        metric_name,
        operator,
        threshold_value,
        severity,
        channels,
        message_template,
        active,
    ):
        self.rule_id = rule_id
        self.name = name
        self.location_id = location_id
        self.target_role = target_role
        self.context_type = context_type
        self.metric_name = metric_name
        self.operator = operator
        self.threshold_value = threshold_value
        self.severity = severity
        self.channels = channels
        self.message_template = message_template
        self.active = active

    def is_active(self):
        return self.active.strip().lower() == "yes"
