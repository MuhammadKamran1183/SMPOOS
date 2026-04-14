class DataRequest:
    def __init__(
        self,
        request_id,
        user_id,
        request_type,
        requester_email,
        status,
        requested_at,
        resolved_at,
        export_payload,
        notes,
    ):
        self.request_id = request_id
        self.user_id = user_id
        self.request_type = request_type
        self.requester_email = requester_email
        self.status = status
        self.requested_at = requested_at
        self.resolved_at = resolved_at
        self.export_payload = export_payload
        self.notes = notes
