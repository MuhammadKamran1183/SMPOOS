class EventLog:
    def __init__(
        self,
        event_id,
        event_type,
        entity_type,
        entity_id,
        severity,
        message,
        created_at,
    ):
        self.event_id = event_id
        self.event_type = event_type
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.severity = severity
        self.message = message
        self.created_at = created_at
