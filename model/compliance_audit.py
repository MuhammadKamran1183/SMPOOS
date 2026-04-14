class ComplianceAudit:
    def __init__(
        self,
        audit_id,
        actor_user_id,
        actor_role,
        action_type,
        entity_type,
        entity_id,
        outcome,
        framework_tags,
        details,
        created_at,
    ):
        self.audit_id = audit_id
        self.actor_user_id = actor_user_id
        self.actor_role = actor_role
        self.action_type = action_type
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.outcome = outcome
        self.framework_tags = framework_tags
        self.details = details
        self.created_at = created_at
