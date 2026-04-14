class NotificationDelivery:
    def __init__(
        self,
        delivery_id,
        notification_id,
        rule_id,
        channel,
        recipient_user_id,
        recipient_role,
        recipient_email,
        delivery_status,
        delivered_at,
    ):
        self.delivery_id = delivery_id
        self.notification_id = notification_id
        self.rule_id = rule_id
        self.channel = channel
        self.recipient_user_id = recipient_user_id
        self.recipient_role = recipient_role
        self.recipient_email = recipient_email
        self.delivery_status = delivery_status
        self.delivered_at = delivered_at
