from model.berth_allocation import BerthAllocation
from model.cargo_activity import CargoActivity
from model.crane_outage import CraneOutage
from model.environmental_update import EnvironmentalUpdate
from model.event_log import EventLog
from model.location import Location
from model.notification import Notification
from model.notification_delivery import NotificationDelivery
from model.notification_rule import NotificationRule
from model.restricted_area import RestrictedArea
from model.route import Route
from model.system_health import SystemHealth
from model.user import User
from model.vessel_path import VesselPath


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
    COMPLIANCE_AUDIT_FILE = "smpoos_compliance_audit.csv"

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

    def __init__(self, database):
        self.database = database

    def _read_entities(self, file_name, model_cls, fields):
        return [
            model_cls(*(row[field] for field in fields))
            for row in self.database.read_rows(file_name)
        ]

    def get_locations(self):
        return self._read_entities(self.LOCATION_FILE, Location, self.LOCATION_FIELDS)

    def get_routes(self):
        return self._read_entities(self.ROUTE_FILE, Route, self.ROUTE_FIELDS)

    def get_notifications(self):
        return self._read_entities(self.NOTIFICATION_FILE, Notification, self.NOTIFICATION_FIELDS)

    def get_users(self):
        return self._read_entities(self.USER_FILE, User, ["user_id", "name", "role", "email", "active"])

    def get_vessel_paths(self):
        return self._read_entities(self.VESSEL_PATH_FILE, VesselPath, self.VESSEL_PATH_FIELDS)

    def get_restricted_areas(self):
        return self._read_entities(self.RESTRICTED_AREA_FILE, RestrictedArea, self.RESTRICTED_AREA_FIELDS)

    def get_crane_outages(self):
        return self._read_entities(self.CRANE_OUTAGE_FILE, CraneOutage, self.CRANE_OUTAGE_FIELDS)

    def get_berth_allocations(self):
        return self._read_entities(self.BERTH_ALLOCATION_FILE, BerthAllocation, self.BERTH_ALLOCATION_FIELDS)

    def get_cargo_activities(self):
        return self._read_entities(self.CARGO_ACTIVITY_FILE, CargoActivity, self.CARGO_ACTIVITY_FIELDS)

    def get_environmental_updates(self):
        return self._read_entities(self.ENVIRONMENTAL_UPDATE_FILE, EnvironmentalUpdate, self.ENVIRONMENTAL_UPDATE_FIELDS)

    def get_system_health(self):
        return self._read_entities(self.SYSTEM_HEALTH_FILE, SystemHealth, self.SYSTEM_HEALTH_FIELDS)

    def get_event_logs(self):
        return self._read_entities(self.EVENT_LOG_FILE, EventLog, self.EVENT_LOG_FIELDS)

    def get_notification_rules(self):
        return self._read_entities(self.NOTIFICATION_RULE_FILE, NotificationRule, self.NOTIFICATION_RULE_FIELDS)

    def get_notification_deliveries(self):
        return self._read_entities(self.NOTIFICATION_DELIVERY_FILE, NotificationDelivery, self.NOTIFICATION_DELIVERY_FIELDS)

    def get_user_by_email(self, email):
        email = email.strip().lower()
        return next(
            (user for user in self.get_users() if user.email.strip().lower() == email),
            None,
        )

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

    def create_compliance_audit(self, payload):
        return self._create_row(
            self.COMPLIANCE_AUDIT_FILE,
            self.COMPLIANCE_AUDIT_FIELDS,
            "audit_id",
            "AU",
            payload,
            "Compliance audit",
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
