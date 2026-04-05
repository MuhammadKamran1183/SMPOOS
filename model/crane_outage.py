class CraneOutage:
    def __init__(
        self,
        outage_id,
        crane_id,
        location_id,
        status,
        severity,
        reason,
        start_time,
        end_time,
    ):
        self.outage_id = outage_id
        self.crane_id = crane_id
        self.location_id = location_id
        self.status = status
        self.severity = severity
        self.reason = reason
        self.start_time = start_time
        self.end_time = end_time

    def is_active(self):
        return self.status.lower() in {"active", "out", "unavailable"}
