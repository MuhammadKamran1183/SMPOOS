class ConsentRecord:
    def __init__(
        self,
        consent_id,
        user_id,
        consent_type,
        purpose,
        lawful_basis,
        status,
        granted_at,
        withdrawn_at,
        retention_period_days,
        notes,
    ):
        self.consent_id = consent_id
        self.user_id = user_id
        self.consent_type = consent_type
        self.purpose = purpose
        self.lawful_basis = lawful_basis
        self.status = status
        self.granted_at = granted_at
        self.withdrawn_at = withdrawn_at
        self.retention_period_days = retention_period_days
        self.notes = notes

    def is_active(self):
        return str(self.status).strip().lower() in {"active", "granted", "yes"}
