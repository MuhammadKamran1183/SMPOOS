from model.berth_allocation import BerthAllocation
from model.cargo_activity import CargoActivity
from model.crane_outage import CraneOutage
from model.data_request import DataRequest
from model.environmental_update import EnvironmentalUpdate
from model.event_log import EventLog
from model.location import Location
from model.notification import Notification
from model.notification_delivery import NotificationDelivery
from model.notification_rule import NotificationRule
from model.compliance_audit import ComplianceAudit
from model.consent_record import ConsentRecord
from model.sensitive_record import SensitiveRecord
from model.restricted_area import RestrictedArea
from model.route import Route
from model.system_health import SystemHealth
from model.user import User
from model.vessel_path import VesselPath
from model.vulnerability_scan import VulnerabilityScan


class CSVRepository:
    LOCATION_FILE = "smpoos_locations.csv"
    ROUTE_FILE = "smpoos_routes.csv"
    NOTIFICATION_FILE = "smpoos_notifications.csv"
    USER_FILE = "smpoos_users.csv"
    CREDENTIAL_FILE = "smpoos_credentials.csv"
    VESSEL_PATH_FILE = "smpoos_vessel_paths.csv"
    RESTRICTED_AREA_FILE = "smpoos_restricted_areas.csv"
    CRANE_OUTAGE_FILE = "smpoos_crane_outages.csv"
    BERTH_ALLOCATION_FILE = "smpoos_berth_allocations.csv"
    CARGO_ACTIVITY_FILE = "smpoos_cargo_activities.csv"
    ENVIRONMENTAL_UPDATE_FILE = "smpoos_environmental_updates.csv"
    SYSTEM_HEALTH_FILE = "smpoos_system_health.csv"
    EVENT_LOG_FILE = "smpoos_event_logs.csv"
    NOTIFICATION_RULE_FILE = "smpoos_notification_rules.csv"
    NOTIFICATION_DELIVERY_FILE = "smpoos_notification_deliveries.csv"
    CONSENT_RECORD_FILE = "smpoos_consent_records.csv"
    DATA_REQUEST_FILE = "smpoos_data_requests.csv"
    COMPLIANCE_AUDIT_FILE = "smpoos_compliance_audit.csv"
    SENSITIVE_RECORD_FILE = "smpoos_sensitive_records.csv"
    VULNERABILITY_SCAN_FILE = "smpoos_vulnerability_scans.csv"
    PATCH_RECORD_FILE = "smpoos_patch_records.csv"

    LOCATION_FIELDS = ["location_id", "name", "type", "status", "capacity_tonnes"]
    ROUTE_FIELDS = [
        "route_id",
        "start_location",
        "end_location",
        "route_type",
        "distance_km",
        "status",
    ]
    NOTIFICATION_FIELDS = [
        "notification_id",
        "alert_type",
        "location_id",
        "severity",
        "message",
        "timestamp",
    ]
    CREDENTIAL_FIELDS = ["user_id", "password_hash"]
    VESSEL_PATH_FIELDS = [
        "path_id",
        "vessel_name",
        "vessel_type",
        "cargo_tonnes",
        "current_location_id",
        "destination_location_id",
        "assigned_route_id",
        "assigned_berth_id",
        "status",
        "last_updated",
    ]
    RESTRICTED_AREA_FIELDS = [
        "area_id",
        "name",
        "location_id",
        "area_type",
        "status",
        "severity",
        "reason",
        "start_time",
        "end_time",
    ]
    CRANE_OUTAGE_FIELDS = [
        "outage_id",
        "crane_id",
        "location_id",
        "status",
        "severity",
        "reason",
        "start_time",
        "end_time",
    ]
    BERTH_ALLOCATION_FIELDS = [
        "allocation_id",
        "vessel_name",
        "cargo_tonnes",
        "berth_id",
        "eta",
        "status",
        "priority",
        "notes",
    ]
    CARGO_ACTIVITY_FIELDS = [
        "activity_id",
        "vessel_name",
        "berth_id",
        "cargo_type",
        "operation_type",
        "tonnes_processed",
        "status",
        "last_updated",
    ]
    ENVIRONMENTAL_UPDATE_FIELDS = [
        "update_id",
        "zone_name",
        "wind_speed_knots",
        "tide_level_m",
        "visibility_km",
        "condition_status",
        "recorded_at",
    ]
    SYSTEM_HEALTH_FIELDS = [
        "component_id",
        "component_name",
        "status",
        "metric_name",
        "metric_value",
        "threshold",
        "checked_at",
    ]
    EVENT_LOG_FIELDS = [
        "event_id",
        "event_type",
        "entity_type",
        "entity_id",
        "severity",
        "message",
        "created_at",
    ]
    NOTIFICATION_RULE_FIELDS = [
        "rule_id",
        "name",
        "location_id",
        "target_role",
        "context_type",
        "metric_name",
        "operator",
        "threshold_value",
        "severity",
        "channels",
        "message_template",
        "active",
    ]
    NOTIFICATION_DELIVERY_FIELDS = [
        "delivery_id",
        "notification_id",
        "rule_id",
        "channel",
        "recipient_user_id",
        "recipient_role",
        "recipient_email",
        "delivery_status",
        "delivered_at",
    ]
    CONSENT_RECORD_FIELDS = [
        "consent_id",
        "user_id",
        "consent_type",
        "purpose",
        "lawful_basis",
        "status",
        "granted_at",
        "withdrawn_at",
        "retention_period_days",
        "notes",
    ]
    DATA_REQUEST_FIELDS = [
        "request_id",
        "user_id",
        "request_type",
        "requester_email",
        "status",
        "requested_at",
        "resolved_at",
        "export_payload",
        "notes",
    ]
    COMPLIANCE_AUDIT_FIELDS = [
        "audit_id",
        "actor_user_id",
        "actor_role",
        "action_type",
        "entity_type",
        "entity_id",
        "outcome",
        "framework_tags",
        "details",
        "created_at",
    ]
    SENSITIVE_RECORD_FIELDS = [
        "record_id",
        "record_type",
        "reference_id",
        "classification",
        "allowed_role",
        "encryption_status",
        "encrypted_payload",
        "updated_at",
    ]
    VULNERABILITY_SCAN_FIELDS = [
        "scan_id",
        "scan_type",
        "status",
        "findings_count",
        "findings_summary",
        "scanned_at",
    ]
    PATCH_RECORD_FIELDS = [
        "patch_id",
        "component_name",
        "patch_version",
        "patch_status",
        "patch_window",
        "applied_at",
        "notes",
    ]

    def __init__(self, database):
        self.database = database

    def get_locations(self):
        return [
            Location(
                row["location_id"],
                row["name"],
                row["type"],
                row["status"],
                row["capacity_tonnes"],
            )
            for row in self.database.read_rows(self.LOCATION_FILE)
        ]

    def get_routes(self):
        return [
            Route(
                row["route_id"],
                row["start_location"],
                row["end_location"],
                row["route_type"],
                row["distance_km"],
                row["status"],
            )
            for row in self.database.read_rows(self.ROUTE_FILE)
        ]

    def get_notifications(self):
        return [
            Notification(
                row["notification_id"],
                row["alert_type"],
                row["location_id"],
                row["severity"],
                row["message"],
                row["timestamp"],
            )
            for row in self.database.read_rows(self.NOTIFICATION_FILE)
        ]

    def get_users(self):
        return [
            User(
                row["user_id"],
                row["name"],
                row["role"],
                row["email"],
                row["active"],
            )
            for row in self.database.read_rows(self.USER_FILE)
        ]

    def get_vessel_paths(self):
        return [
            VesselPath(
                row["path_id"],
                row["vessel_name"],
                row["vessel_type"],
                row["cargo_tonnes"],
                row["current_location_id"],
                row["destination_location_id"],
                row["assigned_route_id"],
                row["assigned_berth_id"],
                row["status"],
                row["last_updated"],
            )
            for row in self.database.read_rows(self.VESSEL_PATH_FILE)
        ]

    def get_restricted_areas(self):
        return [
            RestrictedArea(
                row["area_id"],
                row["name"],
                row["location_id"],
                row["area_type"],
                row["status"],
                row["severity"],
                row["reason"],
                row["start_time"],
                row["end_time"],
            )
            for row in self.database.read_rows(self.RESTRICTED_AREA_FILE)
        ]

    def get_crane_outages(self):
        return [
            CraneOutage(
                row["outage_id"],
                row["crane_id"],
                row["location_id"],
                row["status"],
                row["severity"],
                row["reason"],
                row["start_time"],
                row["end_time"],
            )
            for row in self.database.read_rows(self.CRANE_OUTAGE_FILE)
        ]

    def get_berth_allocations(self):
        return [
            BerthAllocation(
                row["allocation_id"],
                row["vessel_name"],
                row["cargo_tonnes"],
                row["berth_id"],
                row["eta"],
                row["status"],
                row["priority"],
                row["notes"],
            )
            for row in self.database.read_rows(self.BERTH_ALLOCATION_FILE)
        ]

    def get_cargo_activities(self):
        return [
            CargoActivity(
                row["activity_id"],
                row["vessel_name"],
                row["berth_id"],
                row["cargo_type"],
                row["operation_type"],
                row["tonnes_processed"],
                row["status"],
                row["last_updated"],
            )
            for row in self.database.read_rows(self.CARGO_ACTIVITY_FILE)
        ]

    def get_environmental_updates(self):
        return [
            EnvironmentalUpdate(
                row["update_id"],
                row["zone_name"],
                row["wind_speed_knots"],
                row["tide_level_m"],
                row["visibility_km"],
                row["condition_status"],
                row["recorded_at"],
            )
            for row in self.database.read_rows(self.ENVIRONMENTAL_UPDATE_FILE)
        ]

    def get_system_health(self):
        return [
            SystemHealth(
                row["component_id"],
                row["component_name"],
                row["status"],
                row["metric_name"],
                row["metric_value"],
                row["threshold"],
                row["checked_at"],
            )
            for row in self.database.read_rows(self.SYSTEM_HEALTH_FILE)
        ]

    def get_event_logs(self):
        return [
            EventLog(
                row["event_id"],
                row["event_type"],
                row["entity_type"],
                row["entity_id"],
                row["severity"],
                row["message"],
                row["created_at"],
            )
            for row in self.database.read_rows(self.EVENT_LOG_FILE)
        ]

    def get_notification_rules(self):
        return [
            NotificationRule(
                row["rule_id"],
                row["name"],
                row["location_id"],
                row["target_role"],
                row["context_type"],
                row["metric_name"],
                row["operator"],
                row["threshold_value"],
                row["severity"],
                row["channels"],
                row["message_template"],
                row["active"],
            )
            for row in self.database.read_rows(self.NOTIFICATION_RULE_FILE)
        ]

    def get_notification_deliveries(self):
        return [
            NotificationDelivery(
                row["delivery_id"],
                row["notification_id"],
                row["rule_id"],
                row["channel"],
                row["recipient_user_id"],
                row["recipient_role"],
                row["recipient_email"],
                row["delivery_status"],
                row["delivered_at"],
            )
            for row in self.database.read_rows(self.NOTIFICATION_DELIVERY_FILE)
        ]

    def get_consent_records(self):
        return [
            ConsentRecord(
                row["consent_id"],
                row["user_id"],
                row["consent_type"],
                row["purpose"],
                row["lawful_basis"],
                row["status"],
                row["granted_at"],
                row["withdrawn_at"],
                row["retention_period_days"],
                row["notes"],
            )
            for row in self.database.read_rows(self.CONSENT_RECORD_FILE)
        ]

    def get_data_requests(self):
        return [
            DataRequest(
                row["request_id"],
                row["user_id"],
                row["request_type"],
                row["requester_email"],
                row["status"],
                row["requested_at"],
                row["resolved_at"],
                row["export_payload"],
                row["notes"],
            )
            for row in self.database.read_rows(self.DATA_REQUEST_FILE)
        ]

    def get_compliance_audit_entries(self):
        return [
            ComplianceAudit(
                row["audit_id"],
                row["actor_user_id"],
                row["actor_role"],
                row["action_type"],
                row["entity_type"],
                row["entity_id"],
                row["outcome"],
                row["framework_tags"],
                row["details"],
                row["created_at"],
            )
            for row in self.database.read_rows(self.COMPLIANCE_AUDIT_FILE)
        ]

    def get_sensitive_records(self):
        return [
            SensitiveRecord(
                row["record_id"],
                row["record_type"],
                row["reference_id"],
                row["classification"],
                row["allowed_role"],
                row["encryption_status"],
                row["encrypted_payload"],
                row["updated_at"],
            )
            for row in self.database.read_rows(self.SENSITIVE_RECORD_FILE)
        ]

    def get_vulnerability_scans(self):
        return [
            VulnerabilityScan(
                row["scan_id"],
                row["scan_type"],
                row["status"],
                row["findings_count"],
                row["findings_summary"],
                row["scanned_at"],
            )
            for row in self.database.read_rows(self.VULNERABILITY_SCAN_FILE)
        ]

    def get_patch_records(self):
        return [
            PatchRecord(
                row["patch_id"],
                row["component_name"],
                row["patch_version"],
                row["patch_status"],
                row["patch_window"],
                row["applied_at"],
                row["notes"],
            )
            for row in self.database.read_rows(self.PATCH_RECORD_FILE)
        ]

    def get_user_by_email(self, email):
        email = email.strip().lower()
        return next(
            (user for user in self.get_users() if user.email.strip().lower() == email),
            None,
        )

    def get_user_by_id(self, user_id):
        return next((user for user in self.get_users() if user.user_id == user_id), None)

    def get_credentials(self):
        return self.database.read_rows(self.CREDENTIAL_FILE)

    def get_password_hash(self, user_id):
        credential = self._find_row(self.get_credentials(), "user_id", user_id)
        return credential["password_hash"] if credential else None

    def update_password_hash(self, user_id, password_hash):
        credentials = self.get_credentials()
        credential = self._find_row(credentials, "user_id", user_id)
        if credential is None:
            raise ValueError(f"Credential for {user_id} was not found.")
        credential["password_hash"] = password_hash
        self.database.write_rows(self.CREDENTIAL_FILE, self.CREDENTIAL_FIELDS, credentials)
        return credential

    def create_location(self, payload):
        return self._create_row(
            self.LOCATION_FILE,
            self.LOCATION_FIELDS,
            "location_id",
            "L",
            payload,
            "Location",
        )

    def update_location(self, location_id, payload):
        return self._update_row(
            self.LOCATION_FILE,
            self.LOCATION_FIELDS,
            "location_id",
            location_id,
            payload,
            "Location",
        )

    def delete_location(self, location_id):
        self._delete_row(
            self.LOCATION_FILE,
            self.LOCATION_FIELDS,
            "location_id",
            location_id,
            "Location",
        )

    def create_route(self, payload):
        return self._create_row(
            self.ROUTE_FILE,
            self.ROUTE_FIELDS,
            "route_id",
            "R",
            payload,
            "Route",
        )

    def update_route(self, route_id, payload):
        return self._update_row(
            self.ROUTE_FILE,
            self.ROUTE_FIELDS,
            "route_id",
            route_id,
            payload,
            "Route",
        )

    def delete_route(self, route_id):
        self._delete_row(self.ROUTE_FILE, self.ROUTE_FIELDS, "route_id", route_id, "Route")

    def create_notification(self, payload):
        return self._create_row(
            self.NOTIFICATION_FILE,
            self.NOTIFICATION_FIELDS,
            "notification_id",
            "N",
            payload,
            "Notification",
        )

    def update_notification(self, notification_id, payload):
        return self._update_row(
            self.NOTIFICATION_FILE,
            self.NOTIFICATION_FIELDS,
            "notification_id",
            notification_id,
            payload,
            "Notification",
        )

    def delete_notification(self, notification_id):
        self._delete_row(
            self.NOTIFICATION_FILE,
            self.NOTIFICATION_FIELDS,
            "notification_id",
            notification_id,
            "Notification",
        )

    def create_vessel_path(self, payload):
        return self._create_row(
            self.VESSEL_PATH_FILE,
            self.VESSEL_PATH_FIELDS,
            "path_id",
            "VP",
            payload,
            "Vessel path",
        )

    def update_vessel_path(self, path_id, payload):
        return self._update_row(
            self.VESSEL_PATH_FILE,
            self.VESSEL_PATH_FIELDS,
            "path_id",
            path_id,
            payload,
            "Vessel path",
        )

    def delete_vessel_path(self, path_id):
        self._delete_row(
            self.VESSEL_PATH_FILE,
            self.VESSEL_PATH_FIELDS,
            "path_id",
            path_id,
            "Vessel path",
        )

    def create_restricted_area(self, payload):
        return self._create_row(
            self.RESTRICTED_AREA_FILE,
            self.RESTRICTED_AREA_FIELDS,
            "area_id",
            "RA",
            payload,
            "Restricted area",
        )

    def update_restricted_area(self, area_id, payload):
        return self._update_row(
            self.RESTRICTED_AREA_FILE,
            self.RESTRICTED_AREA_FIELDS,
            "area_id",
            area_id,
            payload,
            "Restricted area",
        )

    def delete_restricted_area(self, area_id):
        self._delete_row(
            self.RESTRICTED_AREA_FILE,
            self.RESTRICTED_AREA_FIELDS,
            "area_id",
            area_id,
            "Restricted area",
        )

    def create_crane_outage(self, payload):
        return self._create_row(
            self.CRANE_OUTAGE_FILE,
            self.CRANE_OUTAGE_FIELDS,
            "outage_id",
            "CO",
            payload,
            "Crane outage",
        )

    def update_crane_outage(self, outage_id, payload):
        return self._update_row(
            self.CRANE_OUTAGE_FILE,
            self.CRANE_OUTAGE_FIELDS,
            "outage_id",
            outage_id,
            payload,
            "Crane outage",
        )

    def delete_crane_outage(self, outage_id):
        self._delete_row(
            self.CRANE_OUTAGE_FILE,
            self.CRANE_OUTAGE_FIELDS,
            "outage_id",
            outage_id,
            "Crane outage",
        )

    def create_berth_allocation(self, payload):
        return self._create_row(
            self.BERTH_ALLOCATION_FILE,
            self.BERTH_ALLOCATION_FIELDS,
            "allocation_id",
            "BA",
            payload,
            "Berth allocation",
        )

    def update_berth_allocation(self, allocation_id, payload):
        return self._update_row(
            self.BERTH_ALLOCATION_FILE,
            self.BERTH_ALLOCATION_FIELDS,
            "allocation_id",
            allocation_id,
            payload,
            "Berth allocation",
        )

    def delete_berth_allocation(self, allocation_id):
        self._delete_row(
            self.BERTH_ALLOCATION_FILE,
            self.BERTH_ALLOCATION_FIELDS,
            "allocation_id",
            allocation_id,
            "Berth allocation",
        )

    def create_event_log(self, payload):
        return self._create_row(
            self.EVENT_LOG_FILE,
            self.EVENT_LOG_FIELDS,
            "event_id",
            "EV",
            payload,
            "Event log",
        )

    def create_notification_rule(self, payload):
        return self._create_row(
            self.NOTIFICATION_RULE_FILE,
            self.NOTIFICATION_RULE_FIELDS,
            "rule_id",
            "NR",
            payload,
            "Notification rule",
        )

    def update_notification_rule(self, rule_id, payload):
        return self._update_row(
            self.NOTIFICATION_RULE_FILE,
            self.NOTIFICATION_RULE_FIELDS,
            "rule_id",
            rule_id,
            payload,
            "Notification rule",
        )

    def delete_notification_rule(self, rule_id):
        self._delete_row(
            self.NOTIFICATION_RULE_FILE,
            self.NOTIFICATION_RULE_FIELDS,
            "rule_id",
            rule_id,
            "Notification rule",
        )

    def create_notification_delivery(self, payload):
        return self._create_row(
            self.NOTIFICATION_DELIVERY_FILE,
            self.NOTIFICATION_DELIVERY_FIELDS,
            "delivery_id",
            "ND",
            payload,
            "Notification delivery",
        )

    def create_consent_record(self, payload):
        return self._create_row(
            self.CONSENT_RECORD_FILE,
            self.CONSENT_RECORD_FIELDS,
            "consent_id",
            "CR",
            payload,
            "Consent record",
        )

    def update_consent_record(self, consent_id, payload):
        return self._update_row(
            self.CONSENT_RECORD_FILE,
            self.CONSENT_RECORD_FIELDS,
            "consent_id",
            consent_id,
            payload,
            "Consent record",
        )

    def delete_consent_record(self, consent_id):
        self._delete_row(
            self.CONSENT_RECORD_FILE,
            self.CONSENT_RECORD_FIELDS,
            "consent_id",
            consent_id,
            "Consent record",
        )

    def create_data_request(self, payload):
        return self._create_row(
            self.DATA_REQUEST_FILE,
            self.DATA_REQUEST_FIELDS,
            "request_id",
            "DR",
            payload,
            "Data request",
        )

    def update_data_request(self, request_id, payload):
        return self._update_row(
            self.DATA_REQUEST_FILE,
            self.DATA_REQUEST_FIELDS,
            "request_id",
            request_id,
            payload,
            "Data request",
        )

    def delete_data_request(self, request_id):
        self._delete_row(
            self.DATA_REQUEST_FILE,
            self.DATA_REQUEST_FIELDS,
            "request_id",
            request_id,
            "Data request",
        )

    def create_compliance_audit(self, payload):
        return self._create_row(
            self.COMPLIANCE_AUDIT_FILE,
            self.COMPLIANCE_AUDIT_FIELDS,
            "audit_id",
            "AU",
            payload,
            "Compliance audit",
        )

    def create_sensitive_record(self, payload):
        return self._create_row(
            self.SENSITIVE_RECORD_FILE,
            self.SENSITIVE_RECORD_FIELDS,
            "record_id",
            "SR",
            payload,
            "Sensitive record",
        )

    def update_sensitive_record(self, record_id, payload):
        return self._update_row(
            self.SENSITIVE_RECORD_FILE,
            self.SENSITIVE_RECORD_FIELDS,
            "record_id",
            record_id,
            payload,
            "Sensitive record",
        )

    def delete_sensitive_record(self, record_id):
        self._delete_row(
            self.SENSITIVE_RECORD_FILE,
            self.SENSITIVE_RECORD_FIELDS,
            "record_id",
            record_id,
            "Sensitive record",
        )

    def create_vulnerability_scan(self, payload):
        return self._create_row(
            self.VULNERABILITY_SCAN_FILE,
            self.VULNERABILITY_SCAN_FIELDS,
            "scan_id",
            "VS",
            payload,
            "Vulnerability scan",
        )

    def create_patch_record(self, payload):
        return self._create_row(
            self.PATCH_RECORD_FILE,
            self.PATCH_RECORD_FIELDS,
            "patch_id",
            "PR",
            payload,
            "Patch record",
        )

    def update_patch_record(self, patch_id, payload):
        return self._update_row(
            self.PATCH_RECORD_FILE,
            self.PATCH_RECORD_FIELDS,
            "patch_id",
            patch_id,
            payload,
            "Patch record",
        )

    def delete_patch_record(self, patch_id):
        self._delete_row(
            self.PATCH_RECORD_FILE,
            self.PATCH_RECORD_FIELDS,
            "patch_id",
            patch_id,
            "Patch record",
        )

    def _create_row(self, filename, fieldnames, id_key, prefix, payload, label):
        rows = self.database.read_rows(filename)
        record_id = payload.get(id_key) or self._next_id(rows, id_key, prefix)

        if self._find_row(rows, id_key, record_id):
            raise ValueError(f"{label} {record_id} already exists.")

        row = self._normalise_row(fieldnames, {**payload, id_key: record_id})
        rows.append(row)
        self.database.write_rows(filename, fieldnames, rows)
        return row

    def _update_row(self, filename, fieldnames, id_key, record_id, payload, label):
        rows = self.database.read_rows(filename)
        row = self._find_row(rows, id_key, record_id)

        if row is None:
            raise ValueError(f"{label} {record_id} was not found.")

        row.update(self._normalise_partial(payload))
        self.database.write_rows(filename, fieldnames, rows)
        return row

    def _delete_row(self, filename, fieldnames, id_key, record_id, label):
        rows = self.database.read_rows(filename)
        filtered_rows = [row for row in rows if row[id_key] != record_id]

        if len(filtered_rows) == len(rows):
            raise ValueError(f"{label} {record_id} was not found.")

        self.database.write_rows(filename, fieldnames, filtered_rows)

    def _find_row(self, rows, key, value):
        return next((row for row in rows if row.get(key) == value), None)

    def _next_id(self, rows, key, prefix):
        max_value = 0
        for row in rows:
            raw_value = row.get(key, "")
            if raw_value.startswith(prefix):
                suffix = raw_value[len(prefix) :]
                if suffix.isdigit():
                    max_value = max(max_value, int(suffix))
        return f"{prefix}{max_value + 1:04d}"

    def _normalise_row(self, fieldnames, payload):
        return {field: str(payload.get(field, "")).strip() for field in fieldnames}

    def _normalise_partial(self, payload):
        return {
            key: str(value).strip()
            for key, value in payload.items()
            if value is not None
        }
