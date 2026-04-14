class SystemHealth:
    def __init__(
        self,
        component_id,
        component_name,
        status,
        metric_name,
        metric_value,
        threshold,
        checked_at,
    ):
        self.component_id = component_id
        self.component_name = component_name
        self.status = status
        self.metric_name = metric_name
        self.metric_value = metric_value
        self.threshold = threshold
        self.checked_at = checked_at
