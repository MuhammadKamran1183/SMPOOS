class RestrictedArea:
    def __init__(
        self,
        area_id,
        name,
        location_id,
        area_type,
        status,
        severity,
        reason,
        start_time,
        end_time,
    ):
        self.area_id = area_id
        self.name = name
        self.location_id = location_id
        self.area_type = area_type
        self.status = status
        self.severity = severity
        self.reason = reason
        self.start_time = start_time
        self.end_time = end_time

    def is_active(self):
        return self.status.lower() in {"active", "restricted", "closed"}
