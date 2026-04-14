class SensitiveRecord:
    def __init__(
        self,
        record_id,
        record_type,
        reference_id,
        classification,
        allowed_role,
        encryption_status,
        encrypted_payload,
        updated_at,
    ):
        self.record_id = record_id
        self.record_type = record_type
        self.reference_id = reference_id
        self.classification = classification
        self.allowed_role = allowed_role
        self.encryption_status = encryption_status
        self.encrypted_payload = encrypted_payload
        self.updated_at = updated_at
