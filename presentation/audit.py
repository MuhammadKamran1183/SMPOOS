from business_logic.service import service
from presentation.session import current_user


def audit(action_type, entity_type, entity_id, details, outcome="Success"):
    user = current_user() or {}
    service.log_compliance_audit(
        user.get("user_id", ""),
        user.get("role", user.get("canonical_role", "")),
        action_type,
        entity_type,
        entity_id,
        details,
        outcome=outcome,
    )


def create_record(record_id, create_payload, create_fn, label):
    record_id = (record_id or "").strip()
    create_payload = dict(create_payload)

    if record_id:
        create_payload_key = {
            "Location": "location_id",
            "Route": "route_id",
            "Notification": "notification_id",
            "Vessel path": "path_id",
            "Restricted area": "area_id",
            "Crane outage": "outage_id",
            "Berth allocation": "allocation_id",
        }[label]
        create_payload[create_payload_key] = record_id

    created = create_fn(create_payload)
    return created, "create"

