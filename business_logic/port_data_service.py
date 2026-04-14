import json
from collections import Counter, defaultdict
import hmac
import hashlib
import os
from datetime import datetime, timedelta, timezone


class PortDataService:
    PASSWORD_HASH_SCHEME = "pbkdf2_sha256"
    PASSWORD_HASH_ITERATIONS = 390000
    ROLE_ALIASES = {
        "administrator": "administrator",
        "harbourmaster": "harbourmaster",
        "crane supervisor": "operations supervisor",
        "operations supervisor": "operations supervisor",
        "safety officer": "safety officer",
        "security officer": "safety officer",
    }
    ROLE_PERMISSIONS = {
        "administrator": {
            "view_admin_portal",
            "view_monitoring",
            "view_notification_engine",
            "view_security",
            "manage_security",
            "view_sensitive_data",
            "manage_sensitive_data",
            "manage_compliance",
            "view_analytics",
            "view_management_dashboard",
            "view_scalability",
            "generate_reports",
            "manage_locations",
            "manage_routes",
            "manage_notifications",
            "manage_vessel_paths",
            "manage_restricted_areas",
            "manage_crane_outages",
            "manage_berth_allocations",
            "manage_operational_changes",
            "run_recalculation",
            "manage_notification_rules",
        },
        "harbourmaster": {
            "view_admin_portal",
            "view_monitoring",
            "view_management_dashboard",
            "view_security",
            "view_sensitive_data",
            "view_analytics",
            "view_scalability",
            "generate_reports",
            "manage_locations",
            "manage_routes",
            "manage_notifications",
            "manage_vessel_paths",
            "manage_berth_allocations",
            "manage_operational_changes",
            "run_recalculation",
        },
        "operations supervisor": {
            "view_admin_portal",
            "view_monitoring",
            "view_management_dashboard",
            "view_analytics",
            "view_scalability",
            "generate_reports",
            "manage_routes",
            "manage_notifications",
            "manage_vessel_paths",
            "manage_berth_allocations",
            "manage_operational_changes",
            "run_recalculation",
        },
        "safety officer": {
            "view_admin_portal",
            "view_monitoring",
            "view_management_dashboard",
            "view_analytics",
            "manage_notifications",
            "manage_restricted_areas",
            "manage_crane_outages",
            "manage_operational_changes",
        },
    }
    PERMISSION_LABELS = {
        "view_admin_portal": "open the admin portal",
        "view_monitoring": "view monitoring data",
        "view_notification_engine": "view the notification engine",
        "view_security": "view the security centre",
        "manage_security": "manage security controls, scans, and patch records",
        "view_sensitive_data": "view protected manifests and schedules",
        "manage_sensitive_data": "manage protected manifests and schedules",
        "manage_compliance": "manage compliance records and data requests",
        "view_analytics": "view analytics dashboards",
        "view_management_dashboard": "view the management dashboard",
        "view_scalability": "view scalability planning and performance metrics",
        "generate_reports": "generate custom reports",
        "manage_locations": "manage port zones and berths",
        "manage_routes": "manage internal transport routes",
        "manage_notifications": "manage operational notifications",
        "manage_vessel_paths": "manage vessel paths",
        "manage_restricted_areas": "manage restricted areas",
        "manage_crane_outages": "manage crane outages",
        "manage_berth_allocations": "manage berth allocations",
        "manage_operational_changes": "apply operational changes",
        "run_recalculation": "run berth and route recalculation",
        "manage_notification_rules": "configure notification rules",
    }
    DISRUPTED_LOCATION_STATUSES = {"Closed", "Inactive", "Under Maintenance", "Hazardous"}
    ACTIVE_OUTAGE_STATUSES = {"Active", "Out", "Unavailable"}
    ACTIVE_RESTRICTION_STATUSES = {"Active", "Restricted", "Closed"}

    def __init__(self, repository, secure_storage=None):
        self.repository = repository
        self.secure_storage = secure_storage
        self.cache_store = {}
        self.cache_stats = {"hits": 0, "misses": 0}

    def _serialize_records(self, records):
        return [vars(record) for record in records]

    def _serialise_user(self, user):
        canonical_role = self._canonical_role(user.role)
        return {
            "user_id": user.user_id,
            "name": user.name,
            "role": user.role,
            "canonical_role": canonical_role,
            "email": user.email,
            "active": user.is_active(),
            "permissions": sorted(self._permissions_for_role(canonical_role)),
        }

    def _canonical_role(self, role):
        role_name = str(role).strip().lower()
        return self.ROLE_ALIASES.get(role_name, role_name)

    def _permissions_for_role(self, role):
        return self.ROLE_PERMISSIONS.get(self._canonical_role(role), set())

    def hydrate_session_user(self, session_user):
        if session_user is None:
            return None

        if session_user.get("permissions") and session_user.get("canonical_role"):
            return session_user

        user_id = session_user.get("user_id")
        if not user_id:
            return session_user

        matched_user = next(
            (user for user in self.repository.get_users() if user.user_id == user_id),
            None,
        )
        if matched_user is None:
            return session_user

        return self._serialise_user(matched_user)

    def ensure_user_permission(self, user, permission):
        permissions = self._permissions_for_role(
            user.get("canonical_role", user.get("role", ""))
        )
        if permission not in permissions:
            action = self.PERMISSION_LABELS.get(permission, permission.replace("_", " "))
            raise PermissionError(f"{user.get('role', 'This role')} is not authorised to {action}.")
        return user

    def _ensure_required(self, payload, required_fields):
        missing_fields = [
            field for field in required_fields if not str(payload.get(field, "")).strip()
        ]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}.")

    def _normalise_status(self, status):
        return str(status).strip().title()

    def _safe_float(self, value):
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    def _cache_key(self, prefix, payload=None):
        if payload is None:
            return prefix
        raw_payload = json.dumps(payload, sort_keys=True, default=str)
        return f"{prefix}:{hashlib.sha1(raw_payload.encode('utf-8')).hexdigest()}"

    def _get_cached_result(self, key, builder, ttl_seconds=5):
        now = datetime.now(timezone.utc).timestamp()
        cached = self.cache_store.get(key)
        if cached and cached["expires_at"] > now:
            self.cache_stats["hits"] += 1
            return cached["value"]

        self.cache_stats["misses"] += 1
        value = builder()
        self.cache_store[key] = {
            "value": value,
            "expires_at": now + ttl_seconds,
        }
        return value

    def _hash_password(self, password, salt_hex=None):
        salt = bytes.fromhex(salt_hex) if salt_hex else os.urandom(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            self.PASSWORD_HASH_ITERATIONS,
        )
        return (
            f"{self.PASSWORD_HASH_SCHEME}$"
            f"{self.PASSWORD_HASH_ITERATIONS}$"
            f"{salt.hex()}$"
            f"{digest.hex()}"
        )

    def _verify_password_hash(self, password, stored_hash):
        if not stored_hash:
            return {"matched": False, "upgrade_hash": None, "scheme": "missing"}

        if stored_hash.startswith(f"{self.PASSWORD_HASH_SCHEME}$"):
            _, iteration_text, salt_hex, digest_hex = stored_hash.split("$", 3)
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                bytes.fromhex(salt_hex),
                int(iteration_text),
            )
            return {
                "matched": hmac.compare_digest(digest.hex(), digest_hex),
                "upgrade_hash": None,
                "scheme": self.PASSWORD_HASH_SCHEME,
            }

        legacy_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        matched = hmac.compare_digest(legacy_hash, stored_hash)
        return {
            "matched": matched,
            "upgrade_hash": self._hash_password(password) if matched else None,
            "scheme": "legacy_sha256",
        }

    def _parse_iso_datetime(self, value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None

    def _now_iso(self):
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _is_disrupted_location_status(self, status):
        return self._normalise_status(status) in self.DISRUPTED_LOCATION_STATUSES

    def authenticate_user(self, email, password):
        user = self.repository.get_user_by_email(email)
        if user is None:
            raise ValueError("Invalid email or password.")
        if not user.is_active():
            raise PermissionError("Only active users can access the admin interface.")
        if self._canonical_role(user.role) not in self.ROLE_PERMISSIONS:
            raise PermissionError("This user is not authorised for admin changes.")

        verification = self._verify_password_hash(
            password,
            self.repository.get_password_hash(user.user_id),
        )
        if not verification["matched"]:
            raise ValueError("Invalid email or password.")

        if verification["upgrade_hash"]:
            self.repository.update_password_hash(user.user_id, verification["upgrade_hash"])

        return self._serialise_user(user)

    def create_location(self, payload):
        self._ensure_required(payload, ["name", "type", "status", "capacity_tonnes"])
        payload["status"] = self._normalise_status(payload["status"])
        return self.repository.create_location(payload)

    def update_location(self, location_id, payload):
        if "status" in payload:
            payload["status"] = self._normalise_status(payload["status"])
        return self.repository.update_location(location_id, payload)

    def delete_location(self, location_id):
        self.repository.delete_location(location_id)

    def create_route(self, payload):
        self._ensure_required(
            payload,
            ["start_location", "end_location", "route_type", "distance_km", "status"],
        )
        payload["status"] = self._normalise_status(payload["status"])
        return self.repository.create_route(payload)

    def update_route(self, route_id, payload):
        if "status" in payload:
            payload["status"] = self._normalise_status(payload["status"])
        return self.repository.update_route(route_id, payload)

    def delete_route(self, route_id):
        self.repository.delete_route(route_id)

    def create_notification(self, payload):
        self._ensure_required(payload, ["alert_type", "location_id", "severity", "message"])
        payload.setdefault("timestamp", self._now_iso())
        return self.repository.create_notification(payload)

    def update_notification(self, notification_id, payload):
        return self.repository.update_notification(notification_id, payload)

    def delete_notification(self, notification_id):
        self.repository.delete_notification(notification_id)

    def get_notification_engine_snapshot(self):
        return {
            "rules": self._serialize_records(self.repository.get_notification_rules()),
            "deliveries": self._serialize_records(self.repository.get_notification_deliveries())[-50:],
            "notifications": self._serialize_records(self.repository.get_notifications())[-30:],
            "event_logs": self._serialize_records(self.repository.get_event_logs())[-30:],
        }

    def create_consent_record(self, payload):
        self._ensure_required(
            payload,
            [
                "user_id",
                "consent_type",
                "purpose",
                "lawful_basis",
                "status",
            ],
        )
        if not payload.get("granted_at") and str(payload.get("status", "")).strip().lower() in {
            "granted",
            "active",
            "yes",
        }:
            payload["granted_at"] = self._now_iso()
        return self.repository.create_consent_record(payload)

    def update_consent_record(self, consent_id, payload):
        status = str(payload.get("status", "")).strip().lower()
        if status in {"withdrawn", "revoked", "no"} and not payload.get("withdrawn_at"):
            payload["withdrawn_at"] = self._now_iso()
        return self.repository.update_consent_record(consent_id, payload)

    def delete_consent_record(self, consent_id):
        self.repository.delete_consent_record(consent_id)

    def create_data_request(self, payload):
        self._ensure_required(payload, ["user_id", "request_type", "requester_email"])
        payload.setdefault("status", "Open")
        payload.setdefault("requested_at", self._now_iso())
        if payload["status"].strip().lower() == "completed":
            payload.setdefault("resolved_at", self._now_iso())
            payload.setdefault(
                "export_payload",
                self._encrypt_sensitive_text(
                    self._build_user_data_export(payload["user_id"], payload["request_type"])
                ),
            )
        return self.repository.create_data_request(payload)

    def update_data_request(self, request_id, payload):
        request = next(
            (request for request in self.repository.get_data_requests() if request.request_id == request_id),
            None,
        )
        if request is None:
            raise ValueError(f"Data request {request_id} was not found.")

        next_status = str(payload.get("status", request.status)).strip().lower()
        request_type = str(payload.get("request_type", request.request_type)).strip().lower()
        if next_status == "completed":
            payload.setdefault("resolved_at", self._now_iso())
            if request_type in {"access", "portability"} and not payload.get("export_payload"):
                payload["export_payload"] = self._encrypt_sensitive_text(
                    self._build_user_data_export(
                        payload.get("user_id", request.user_id),
                        request_type,
                    )
                )
        return self.repository.update_data_request(request_id, payload)

    def delete_data_request(self, request_id):
        self.repository.delete_data_request(request_id)

    def get_security_snapshot(self, runtime_context=None, user=None):
        runtime_context = runtime_context or {}
        cache_key = self._cache_key(
            "security_snapshot",
            {
                "role": (user or {}).get("canonical_role", (user or {}).get("role", "")),
                "https_enabled": runtime_context.get("https_enabled", False),
                "session_count": runtime_context.get("session_count", 0),
            },
        )
        return self._get_cached_result(
            cache_key,
            lambda: self._build_security_snapshot(runtime_context, user or {}),
            ttl_seconds=5,
        )

    def create_sensitive_record(self, payload):
        self._ensure_required(
            payload,
            ["record_type", "reference_id", "classification", "allowed_role", "plaintext_payload"],
        )
        return self.repository.create_sensitive_record(
            {
                "record_id": payload.get("record_id", ""),
                "record_type": payload["record_type"],
                "reference_id": payload["reference_id"],
                "classification": payload["classification"],
                "allowed_role": payload["allowed_role"],
                "encryption_status": "Encrypted",
                "encrypted_payload": self._encrypt_sensitive_text(payload["plaintext_payload"]),
                "updated_at": self._now_iso(),
            }
        )

    def update_sensitive_record(self, record_id, payload):
        repository_payload = {
            key: value
            for key, value in payload.items()
            if key in {"record_type", "reference_id", "classification", "allowed_role"}
        }
        if "plaintext_payload" in payload:
            repository_payload["encrypted_payload"] = self._encrypt_sensitive_text(
                payload["plaintext_payload"]
            )
            repository_payload["encryption_status"] = "Encrypted"
        repository_payload["updated_at"] = self._now_iso()
        return self.repository.update_sensitive_record(record_id, repository_payload)

    def delete_sensitive_record(self, record_id):
        self.repository.delete_sensitive_record(record_id)

    def run_vulnerability_scan(self, runtime_context=None):
        runtime_context = runtime_context or {}
        findings = []
        if not runtime_context.get("https_enabled"):
            findings.append(
                {
                    "severity": "High",
                    "finding": "HTTPS/TLS is not enabled for the web server.",
                }
            )
        if self.secure_storage is None or self.secure_storage.is_default_secret():
            findings.append(
                {
                    "severity": "High",
                    "finding": "The default encryption secret is still in use for protected data.",
                }
            )

        legacy_hash_count = sum(
            1
            for credential in self.repository.get_credentials()
            if not credential["password_hash"].startswith(f"{self.PASSWORD_HASH_SCHEME}$")
        )
        if legacy_hash_count:
            findings.append(
                {
                    "severity": "Medium",
                    "finding": f"{legacy_hash_count} account(s) still use a legacy password hash and should be upgraded by login.",
                }
            )

        patch_records = self.repository.get_patch_records()
        latest_patch_time = max(
            (
                self._parse_iso_datetime(record.applied_at or record.patch_window)
                for record in patch_records
                if record.applied_at or record.patch_window
            ),
            default=None,
        )
        if latest_patch_time is None or latest_patch_time < datetime.now(timezone.utc) - timedelta(days=30):
            findings.append(
                {
                    "severity": "Medium",
                    "finding": "No recent applied patch window is recorded in the last 30 days.",
                }
            )

        if runtime_context.get("session_count", 0) > 100:
            findings.append(
                {
                    "severity": "Low",
                    "finding": "High concurrent session count detected. Review session scaling and expiry settings.",
                }
            )

        if findings:
            status = "Critical" if any(finding["severity"] == "High" for finding in findings) else "Warning"
        else:
            status = "Healthy"
            findings.append({"severity": "Info", "finding": "No immediate security findings were detected."})

        scan = self.repository.create_vulnerability_scan(
            {
                "scan_type": "Application Security Review",
                "status": status,
                "findings_count": len(findings),
                "findings_summary": json.dumps(findings, separators=(",", ":")),
                "scanned_at": self._now_iso(),
            }
        )
        return {"scan": scan, "findings": findings}

    def create_patch_record(self, payload):
        self._ensure_required(payload, ["component_name", "patch_version", "patch_status"])
        payload.setdefault("applied_at", self._now_iso() if payload["patch_status"].strip().lower() == "applied" else "")
        return self.repository.create_patch_record(payload)

    def update_patch_record(self, patch_id, payload):
        if payload.get("patch_status", "").strip().lower() == "applied" and not payload.get("applied_at"):
            payload["applied_at"] = self._now_iso()
        return self.repository.update_patch_record(patch_id, payload)

    def delete_patch_record(self, patch_id):
        self.repository.delete_patch_record(patch_id)

    def get_management_dashboard_snapshot(self, user, filters=None, runtime_context=None):
        filters = filters or {}
        runtime_context = runtime_context or {}
        cache_key = self._cache_key(
            "management_dashboard",
            {
                "role": user.get("canonical_role", user.get("role", "")),
                "filters": filters,
            },
        )
        return self._get_cached_result(
            cache_key,
            lambda: self._build_management_dashboard_snapshot(user, filters, runtime_context),
            ttl_seconds=5,
        )

    def get_scalability_snapshot(self, runtime_context=None):
        runtime_context = runtime_context or {}
        cache_key = self._cache_key("scalability_snapshot", runtime_context)
        return self._get_cached_result(
            cache_key,
            lambda: self._build_scalability_snapshot(runtime_context),
            ttl_seconds=5,
        )

    def get_analytics_snapshot(self):
        return self._get_cached_result(
            "analytics_snapshot",
            self._build_analytics_snapshot,
            ttl_seconds=5,
        )

    def _build_analytics_snapshot(self):
        berth_usage = self._build_berth_usage_rows()
        route_usage = self._build_route_usage_rows()
        congestion = self._build_peak_congestion_rows()
        equipment = self._build_equipment_utilisation_rows()
        environmental = self._build_environmental_trend_rows()

        return {
            "summary": {
                "most_used_berth": berth_usage[0]["berth_name"] if berth_usage else "No data",
                "busiest_route": route_usage[0]["route_id"] if route_usage else "No data",
                "peak_congestion_hour": congestion[0]["hour_window"] if congestion else "No data",
                "highest_wind_zone": environmental[0]["zone_name"] if environmental else "No data",
            },
            "most_used_berths": berth_usage,
            "common_routes": route_usage,
            "peak_congestion_times": congestion,
            "equipment_utilisation": equipment,
            "environmental_trends": environmental,
            "recommendations": self._build_analytics_recommendations(
                berth_usage,
                congestion,
                equipment,
                environmental,
            ),
        }

    def generate_custom_report(self, filters):
        report_rows = []
        start_dt = self._parse_iso_datetime(filters.get("start_date"))
        end_dt = self._parse_iso_datetime(filters.get("end_date"))
        vessel_type_filter = str(filters.get("vessel_type", "")).strip().lower()
        cargo_type_filter = str(filters.get("cargo_type", "")).strip().lower()
        port_area_filter = str(filters.get("port_area", "")).strip().lower()

        cargo_by_vessel = defaultdict(list)
        for activity in self.repository.get_cargo_activities():
            cargo_by_vessel[activity.vessel_name].append(activity)

        locations = {location.location_id: location for location in self.repository.get_locations()}
        allocations = {
            allocation.vessel_name: allocation for allocation in self.repository.get_berth_allocations()
        }

        for path in self.repository.get_vessel_paths():
            if vessel_type_filter and path.vessel_type.strip().lower() != vessel_type_filter:
                continue

            related_activities = cargo_by_vessel.get(path.vessel_name, [])
            if cargo_type_filter and not any(
                activity.cargo_type.strip().lower() == cargo_type_filter
                for activity in related_activities
            ):
                continue

            destination = locations.get(path.destination_location_id)
            destination_name = destination.name if destination else path.destination_location_id
            if port_area_filter and port_area_filter not in destination_name.lower():
                continue

            allocation = allocations.get(path.vessel_name)
            eta_dt = self._parse_iso_datetime(allocation.eta if allocation else "")
            if start_dt and eta_dt and eta_dt < start_dt:
                continue
            if end_dt and eta_dt and eta_dt > end_dt:
                continue

            report_rows.append(
                {
                    "vessel_name": path.vessel_name,
                    "vessel_type": path.vessel_type,
                    "cargo_type": related_activities[0].cargo_type if related_activities else "",
                    "current_location_id": path.current_location_id,
                    "destination": destination_name,
                    "assigned_route_id": path.assigned_route_id,
                    "assigned_berth_id": path.assigned_berth_id or (allocation.berth_id if allocation else ""),
                    "eta": allocation.eta if allocation else "",
                    "status": path.status,
                }
            )

        return {
            "generated_at": self._now_iso(),
            "filters": filters,
            "rows": report_rows[:100],
            "summary": {
                "matched_records": len(report_rows),
                "vessel_types": sorted({row["vessel_type"] for row in report_rows if row["vessel_type"]}),
                "cargo_types": sorted({row["cargo_type"] for row in report_rows if row["cargo_type"]}),
            },
            "recommendations": self._build_report_recommendations(report_rows),
        }

    def create_notification_rule(self, payload):
        self._ensure_required(
            payload,
            [
                "name",
                "target_role",
                "context_type",
                "metric_name",
                "operator",
                "threshold_value",
                "severity",
                "channels",
                "message_template",
                "active",
            ],
        )
        return self.repository.create_notification_rule(payload)

    def update_notification_rule(self, rule_id, payload):
        return self.repository.update_notification_rule(rule_id, payload)

    def delete_notification_rule(self, rule_id):
        self.repository.delete_notification_rule(rule_id)

    def evaluate_notification_rules(self):
        rules = [rule for rule in self.repository.get_notification_rules() if rule.is_active()]
        triggered = []
        for rule in rules:
            match = self._evaluate_notification_rule(rule)
            if not match["matched"]:
                continue

            location_id = match.get("location_id") or rule.location_id or "SYSTEM"
            notification = self.create_notification(
                {
                    "alert_type": rule.context_type.replace("_", " ").title(),
                    "location_id": location_id,
                    "severity": rule.severity,
                    "message": match["message"],
                    "timestamp": self._now_iso(),
                }
            )
            deliveries = self._deliver_notification(rule, notification)
            self._log_event(
                "Notification Triggered",
                "notification_rule",
                rule.rule_id,
                rule.severity,
                match["message"],
            )
            triggered.append(
                {
                    "rule": vars(rule),
                    "notification": notification,
                    "deliveries": deliveries,
                }
            )
        return {"triggered_rules": triggered}

    def create_vessel_path(self, payload):
        self._ensure_required(
            payload,
            [
                "vessel_name",
                "vessel_type",
                "cargo_tonnes",
                "current_location_id",
                "destination_location_id",
                "status",
            ],
        )
        payload.setdefault("last_updated", self._now_iso())
        return self.repository.create_vessel_path(payload)

    def update_vessel_path(self, path_id, payload):
        payload["last_updated"] = self._now_iso()
        return self.repository.update_vessel_path(path_id, payload)

    def delete_vessel_path(self, path_id):
        self.repository.delete_vessel_path(path_id)

    def create_restricted_area(self, payload):
        self._ensure_required(
            payload,
            ["name", "location_id", "area_type", "status", "severity", "reason"],
        )
        payload["status"] = self._normalise_status(payload["status"])
        return self.repository.create_restricted_area(payload)

    def update_restricted_area(self, area_id, payload):
        if "status" in payload:
            payload["status"] = self._normalise_status(payload["status"])
        return self.repository.update_restricted_area(area_id, payload)

    def delete_restricted_area(self, area_id):
        self.repository.delete_restricted_area(area_id)

    def create_crane_outage(self, payload):
        self._ensure_required(
            payload,
            ["crane_id", "location_id", "status", "severity", "reason"],
        )
        payload["status"] = self._normalise_status(payload["status"])
        return self.repository.create_crane_outage(payload)

    def update_crane_outage(self, outage_id, payload):
        if "status" in payload:
            payload["status"] = self._normalise_status(payload["status"])
        return self.repository.update_crane_outage(outage_id, payload)

    def delete_crane_outage(self, outage_id):
        self.repository.delete_crane_outage(outage_id)

    def create_berth_allocation(self, payload):
        self._ensure_required(
            payload,
            ["vessel_name", "cargo_tonnes", "eta", "status", "priority"],
        )
        payload["status"] = self._normalise_status(payload["status"])
        return self.repository.create_berth_allocation(payload)

    def update_berth_allocation(self, allocation_id, payload):
        if "status" in payload:
            payload["status"] = self._normalise_status(payload["status"])
        return self.repository.update_berth_allocation(allocation_id, payload)

    def delete_berth_allocation(self, allocation_id):
        self.repository.delete_berth_allocation(allocation_id)

    def get_monitoring_snapshot(self):
        return self._get_cached_result(
            "monitoring_snapshot",
            self._build_monitoring_snapshot,
            ttl_seconds=5,
        )

    def _build_monitoring_snapshot(self):
        return {
            "vessel_movements": self._build_vessel_movements(),
            "berth_occupancy": self._build_berth_occupancy(),
            "cargo_activity": self._serialize_records(self.repository.get_cargo_activities()),
            "environmental_updates": self._serialize_records(
                self.repository.get_environmental_updates()
            ),
            "system_health": self._serialize_records(self.repository.get_system_health()),
            "event_logs": self._serialize_records(self.repository.get_event_logs())[-20:],
            "alerts": self._serialize_records(self.repository.get_notifications())[-10:],
        }

    def recalculate_operations(self):
        impacted_routes = self._recalculate_route_statuses()
        berth_allocations = self._recalculate_berth_allocations()
        vessel_paths = self._recalculate_vessel_paths()
        result = {
            "impacted_routes": impacted_routes,
            "berth_allocations": berth_allocations,
            "vessel_paths": vessel_paths,
            "blocked_locations": sorted(self._get_blocked_location_ids()),
        }
        self._log_event(
            "Recalculation",
            "operations",
            "engine",
            "Medium",
            "Operations engine recalculated routes, berth allocations, and vessel paths.",
        )
        self.evaluate_notification_rules()
        return result

    def apply_operational_change(self, payload):
        self._ensure_required(payload, ["target_type", "target_id", "new_status", "message"])
        target_type = payload["target_type"].strip().lower()
        target_id = payload["target_id"].strip()
        new_status = self._normalise_status(payload["new_status"])
        message = payload["message"].strip()

        handlers = {
            "location": self.update_location,
            "route": self.update_route,
            "restricted_area": self.update_restricted_area,
            "crane_outage": self.update_crane_outage,
            "vessel_path": self.update_vessel_path,
            "berth_allocation": self.update_berth_allocation,
        }
        if target_type not in handlers:
            raise ValueError(
                "target_type must be one of: location, route, restricted_area, crane_outage, vessel_path, berth_allocation."
            )

        updated_target = handlers[target_type](target_id, {"status": new_status})
        recalculation = self.recalculate_operations()
        notification = self.create_notification(
            {
                "alert_type": payload.get("alert_type", "Operational Change"),
                "location_id": payload.get("location_id", payload.get("target_id", "")),
                "severity": payload.get("severity", "High"),
                "message": message,
                "timestamp": self._now_iso(),
            }
        )
        self._log_event(
            "Operational Change",
            target_type,
            target_id,
            payload.get("severity", "High"),
            message,
        )
        self.evaluate_notification_rules()

        return {
            "updated_target": updated_target,
            "recalculation": recalculation,
            "notification": notification,
        }

    def _get_blocked_location_ids(self):
        blocked_locations = {
            location.location_id
            for location in self.repository.get_locations()
            if self._is_disrupted_location_status(location.status)
        }
        blocked_locations.update(
            area.location_id
            for area in self.repository.get_restricted_areas()
            if area.status.strip().title() in self.ACTIVE_RESTRICTION_STATUSES
        )
        blocked_locations.update(
            outage.location_id
            for outage in self.repository.get_crane_outages()
            if outage.status.strip().title() in self.ACTIVE_OUTAGE_STATUSES
        )
        return blocked_locations

    def _recalculate_route_statuses(self):
        blocked_locations = self._get_blocked_location_ids()
        impacted_routes = []
        for route in self.repository.get_routes():
            should_restrict = route.start_location in blocked_locations or route.end_location in blocked_locations
            next_status = "Restricted" if should_restrict else "Open"
            if route.status != next_status:
                impacted_routes.append(
                    self.repository.update_route(route.route_id, {"status": next_status})
                )
        return impacted_routes

    def _get_available_berths(self, exclude_location_id=None):
        blocked_locations = self._get_blocked_location_ids()
        available_berths = []
        for location in self.repository.get_locations():
            location_type = location.type.strip().lower()
            if "berth" not in location_type and "dock" not in location_type:
                continue
            if not location.is_active():
                continue
            if location.location_id == exclude_location_id:
                continue
            if location.location_id in blocked_locations:
                continue
            available_berths.append(vars(location))

        available_berths.sort(key=lambda berth: int(berth["capacity_tonnes"]), reverse=True)
        return available_berths

    def _recalculate_berth_allocations(self):
        available_berths = self._get_available_berths()
        allocations = []
        for allocation in self.repository.get_berth_allocations():
            if not allocation.is_open_for_recalculation():
                continue

            preferred_berth = allocation.berth_id
            available_berth_ids = {berth["location_id"] for berth in available_berths}
            target_berth = preferred_berth if preferred_berth in available_berth_ids else ""

            if not target_berth:
                cargo_tonnes = int(float(allocation.cargo_tonnes or 0))
                target_berth = self._find_best_berth_for_cargo(available_berths, cargo_tonnes)

            if target_berth:
                updated = self.repository.update_berth_allocation(
                    allocation.allocation_id,
                    {"berth_id": target_berth, "status": "Scheduled"},
                )
            else:
                updated = self.repository.update_berth_allocation(
                    allocation.allocation_id,
                    {"status": "Waiting"},
                )
            allocations.append(updated)
        return allocations

    def _find_best_berth_for_cargo(self, available_berths, cargo_tonnes):
        suitable_berths = [
            berth
            for berth in available_berths
            if int(berth["capacity_tonnes"]) >= cargo_tonnes
        ]
        if suitable_berths:
            suitable_berths.sort(key=lambda berth: int(berth["capacity_tonnes"]))
            return suitable_berths[0]["location_id"]
        return available_berths[0]["location_id"] if available_berths else ""

    def _recalculate_vessel_paths(self):
        blocked_locations = self._get_blocked_location_ids()
        open_routes = [route for route in self.repository.get_routes() if route.is_open()]
        berth_allocations = {
            allocation.vessel_name: allocation
            for allocation in self.repository.get_berth_allocations()
        }
        updated_paths = []

        for path in self.repository.get_vessel_paths():
            payload = {"last_updated": self._now_iso()}
            destination_blocked = path.destination_location_id in blocked_locations

            if path.current_location_id in blocked_locations or destination_blocked:
                payload["status"] = "Holding"

            matching_route = next(
                (
                    route
                    for route in open_routes
                    if route.end_location == path.destination_location_id
                ),
                open_routes[0] if open_routes else None,
            )
            if matching_route is not None:
                payload["assigned_route_id"] = matching_route.route_id
                if payload.get("status") != "Holding":
                    payload["status"] = "Rerouted"

            allocation = berth_allocations.get(path.vessel_name)
            if allocation and allocation.berth_id:
                payload["assigned_berth_id"] = allocation.berth_id

            updated_paths.append(self.repository.update_vessel_path(path.path_id, payload))
        return updated_paths

    def _build_vessel_movements(self):
        allocations = {
            allocation.vessel_name: allocation
            for allocation in self.repository.get_berth_allocations()
        }
        vessel_movements = []
        for path in self.repository.get_vessel_paths():
            allocation = allocations.get(path.vessel_name)
            eta = allocation.eta if allocation else ""
            etd = self._estimate_departure(eta, path.cargo_tonnes)
            vessel_movements.append(
                {
                    "path_id": path.path_id,
                    "vessel_name": path.vessel_name,
                    "vessel_type": path.vessel_type,
                    "current_location_id": path.current_location_id,
                    "destination_location_id": path.destination_location_id,
                    "assigned_route_id": path.assigned_route_id,
                    "assigned_berth_id": path.assigned_berth_id,
                    "status": path.status,
                    "estimated_arrival": eta,
                    "estimated_departure": etd,
                    "last_updated": path.last_updated,
                }
            )
        return vessel_movements

    def _build_berth_occupancy(self):
        berth_lookup = {
            location.location_id: location
            for location in self.repository.get_locations()
        }
        occupancy_rows = []
        for allocation in self.repository.get_berth_allocations():
            berth = berth_lookup.get(allocation.berth_id)
            if berth is None:
                continue
            occupied_tonnes = int(float(allocation.cargo_tonnes or 0))
            capacity_tonnes = int(float(berth.capacity_tonnes or 0))
            occupancy_percent = (
                round((occupied_tonnes / capacity_tonnes) * 100, 1)
                if capacity_tonnes
                else 0
            )
            occupancy_rows.append(
                {
                    "berth_id": berth.location_id,
                    "berth_name": berth.name,
                    "vessel_name": allocation.vessel_name,
                    "occupancy_status": allocation.status,
                    "occupied_tonnes": occupied_tonnes,
                    "capacity_tonnes": capacity_tonnes,
                    "occupancy_percent": occupancy_percent,
                    "eta": allocation.eta,
                }
            )
        return occupancy_rows

    def _estimate_departure(self, eta, cargo_tonnes):
        if not eta:
            return ""
        try:
            eta_dt = datetime.fromisoformat(eta)
            handling_hours = max(2, int(float(cargo_tonnes or 0) / 4000))
            return (eta_dt + timedelta(hours=handling_hours)).isoformat()
        except ValueError:
            return ""

    def _log_event(self, event_type, entity_type, entity_id, severity, message):
        self.repository.create_event_log(
            {
                "event_type": event_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "severity": severity,
                "message": message,
                "created_at": self._now_iso(),
            }
        )

    def log_compliance_audit(
        self,
        actor_user_id,
        actor_role,
        action_type,
        entity_type,
        entity_id,
        details,
        outcome="Success",
    ):
        self.repository.create_compliance_audit(
            {
                "actor_user_id": actor_user_id,
                "actor_role": actor_role,
                "action_type": action_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "outcome": outcome,
                "framework_tags": "GDPR|IMO|Port Governance",
                "details": details,
                "created_at": self._now_iso(),
            }
        )

    def _build_user_data_export(self, user_id, request_type):
        user = self.repository.get_user_by_id(user_id)
        consent_records = [
            vars(record)
            for record in self.repository.get_consent_records()
            if record.user_id == user_id
        ]
        deliveries = [
            vars(delivery)
            for delivery in self.repository.get_notification_deliveries()
            if delivery.recipient_user_id == user_id
        ]
        payload = {
            "request_type": request_type,
            "user_profile": vars(user) if user else {"user_id": user_id},
            "consent_records": consent_records,
            "notification_deliveries": deliveries[-50:],
            "exported_at": self._now_iso(),
        }
        return json.dumps(payload, separators=(",", ":"))

    def _build_berth_usage_rows(self):
        berth_lookup = {
            location.location_id: location.name for location in self.repository.get_locations()
        }
        usage = defaultdict(lambda: {"allocation_count": 0, "cargo_tonnes": 0.0})

        for allocation in self.repository.get_berth_allocations():
            berth_id = allocation.berth_id or "UNASSIGNED"
            usage[berth_id]["allocation_count"] += 1
            usage[berth_id]["cargo_tonnes"] += self._safe_float(allocation.cargo_tonnes)

        rows = [
            {
                "berth_id": berth_id,
                "berth_name": berth_lookup.get(berth_id, berth_id),
                "allocation_count": values["allocation_count"],
                "cargo_tonnes": round(values["cargo_tonnes"], 1),
            }
            for berth_id, values in usage.items()
        ]
        rows.sort(key=lambda row: (-row["allocation_count"], -row["cargo_tonnes"]))
        return rows[:10]

    def _build_route_usage_rows(self):
        route_counts = Counter(
            path.assigned_route_id for path in self.repository.get_vessel_paths() if path.assigned_route_id
        )
        route_lookup = {route.route_id: route for route in self.repository.get_routes()}
        rows = []
        for route_id, usage_count in route_counts.most_common(10):
            route = route_lookup.get(route_id)
            rows.append(
                {
                    "route_id": route_id,
                    "route_type": route.route_type if route else "",
                    "start_location": route.start_location if route else "",
                    "end_location": route.end_location if route else "",
                    "usage_count": usage_count,
                    "status": route.status if route else "",
                }
            )
        return rows

    def _build_peak_congestion_rows(self):
        congestion_counter = Counter()
        for record in [*self.repository.get_notifications(), *self.repository.get_event_logs()]:
            text = " ".join(
                [
                    str(getattr(record, "alert_type", "")),
                    str(getattr(record, "event_type", "")),
                    str(getattr(record, "message", "")),
                ]
            ).lower()
            if not any(keyword in text for keyword in {"congestion", "delay", "holding", "restricted"}):
                continue
            timestamp = self._parse_iso_datetime(
                getattr(record, "timestamp", "") or getattr(record, "created_at", "")
            )
            if timestamp is None:
                continue
            congestion_counter[f"{timestamp.hour:02d}:00-{timestamp.hour:02d}:59"] += 1

        return [
            {"hour_window": hour_window, "incident_count": count}
            for hour_window, count in congestion_counter.most_common(10)
        ]

    def _build_equipment_utilisation_rows(self):
        activities_by_berth = Counter(activity.berth_id for activity in self.repository.get_cargo_activities())
        outages_by_location = Counter(
            outage.location_id
            for outage in self.repository.get_crane_outages()
            if outage.status.strip().title() in self.ACTIVE_OUTAGE_STATUSES
        )
        berth_lookup = {location.location_id: location.name for location in self.repository.get_locations()}
        rows = []
        for berth_id, activity_count in activities_by_berth.items():
            outage_count = outages_by_location.get(berth_id, 0)
            utilisation_rate = round((activity_count / max(activity_count + outage_count, 1)) * 100, 1)
            rows.append(
                {
                    "location_id": berth_id,
                    "location_name": berth_lookup.get(berth_id, berth_id),
                    "activity_count": activity_count,
                    "active_outages": outage_count,
                    "utilisation_rate_percent": utilisation_rate,
                }
            )
        rows.sort(key=lambda row: (-row["utilisation_rate_percent"], -row["activity_count"]))
        return rows[:10]

    def _build_environmental_trend_rows(self):
        zone_stats = defaultdict(
            lambda: {
                "wind_total": 0.0,
                "tide_total": 0.0,
                "visibility_total": 0.0,
                "samples": 0,
                "wind_alerts": 0,
            }
        )
        for update in self.repository.get_environmental_updates():
            stats = zone_stats[update.zone_name]
            stats["wind_total"] += self._safe_float(update.wind_speed_knots)
            stats["tide_total"] += self._safe_float(update.tide_level_m)
            stats["visibility_total"] += self._safe_float(update.visibility_km)
            stats["samples"] += 1
            if self._safe_float(update.wind_speed_knots) >= 20 or self._safe_float(update.visibility_km) <= 5:
                stats["wind_alerts"] += 1

        rows = []
        for zone_name, stats in zone_stats.items():
            samples = max(stats["samples"], 1)
            rows.append(
                {
                    "zone_name": zone_name,
                    "average_wind_knots": round(stats["wind_total"] / samples, 1),
                    "average_tide_m": round(stats["tide_total"] / samples, 2),
                    "average_visibility_km": round(stats["visibility_total"] / samples, 1),
                    "hazard_samples": stats["wind_alerts"],
                }
            )
        rows.sort(key=lambda row: (-row["average_wind_knots"], row["average_visibility_km"]))
        return rows[:10]

    def _build_analytics_recommendations(
        self,
        berth_usage,
        congestion_rows,
        equipment_rows,
        environmental_rows,
    ):
        recommendations = []
        if berth_usage and berth_usage[0]["allocation_count"] >= 1:
            recommendations.append(
                {
                    "category": "Berth optimisation",
                    "insight": (
                        f"Review berth allocation pressure at {berth_usage[0]['berth_name']} "
                        "and pre-stage overflow capacity at lower-use berths."
                    ),
                }
            )
        if congestion_rows:
            recommendations.append(
                {
                    "category": "Operational bottleneck",
                    "insight": (
                        f"Peak congestion currently clusters around {congestion_rows[0]['hour_window']}; "
                        "stagger arrivals and tug dispatches during this period."
                    ),
                }
            )
        if equipment_rows and equipment_rows[0]["active_outages"] > 0:
            recommendations.append(
                {
                    "category": "Equipment utilisation",
                    "insight": (
                        f"{equipment_rows[0]['location_name']} is affected by crane outages; "
                        "reroute work packages before utilisation degrades further."
                    ),
                }
            )
        if environmental_rows and environmental_rows[0]["hazard_samples"] > 0:
            recommendations.append(
                {
                    "category": "Safety / accessibility",
                    "insight": (
                        f"{environmental_rows[0]['zone_name']} shows the strongest environmental risk trend; "
                        "tighten berth access and crane-operating thresholds there."
                    ),
                }
            )
        return recommendations

    def _build_report_recommendations(self, report_rows):
        if not report_rows:
            return [
                {
                    "category": "Reporting",
                    "insight": "No records match the selected filters. Broaden the date, vessel, cargo, or port-area filters.",
                }
            ]
        destination_counts = Counter(row["destination"] for row in report_rows if row["destination"])
        busiest_destination = destination_counts.most_common(1)[0][0] if destination_counts else "the selected area"
        return [
            {
                "category": "Planning",
                "insight": f"Use {busiest_destination} as the primary focus for berth and route optimisation planning.",
            }
        ]

    def _encrypt_sensitive_text(self, plaintext):
        if not plaintext:
            return ""
        if self.secure_storage is None:
            return plaintext
        return self.secure_storage.encrypt_text(plaintext)

    def _decrypt_sensitive_text(self, ciphertext):
        if not ciphertext:
            return ""
        if self.secure_storage is None:
            return ciphertext
        try:
            return self.secure_storage.decrypt_text(ciphertext)
        except Exception:
            return "[unable to decrypt payload]"

    def _can_view_sensitive_record(self, user, record):
        role = self._canonical_role(user.get("canonical_role", user.get("role", "")))
        if role == "administrator":
            return True
        return role == self._canonical_role(record.allowed_role)

    def _serialise_sensitive_record(self, record, user):
        preview = "[protected]"
        if self._can_view_sensitive_record(user, record):
            preview = self._decrypt_sensitive_text(record.encrypted_payload)[:240]
        return {
            "record_id": record.record_id,
            "record_type": record.record_type,
            "reference_id": record.reference_id,
            "classification": record.classification,
            "allowed_role": record.allowed_role,
            "encryption_status": record.encryption_status,
            "payload_preview": preview,
            "updated_at": record.updated_at,
        }

    def _build_security_snapshot(self, runtime_context, user):
        scans = self.repository.get_vulnerability_scans()
        sensitive_records = self.repository.get_sensitive_records()
        patch_records = self.repository.get_patch_records()
        latest_scan = scans[-1] if scans else None
        return {
            "summary": {
                "secure_authentication": "PBKDF2 session authentication with timeout and lockout protection",
                "tls_in_transit": "Enabled" if runtime_context.get("https_enabled") else "HTTP only - enable certs",
                "encrypted_records": len(sensitive_records),
                "active_sessions": runtime_context.get("session_count", 0),
                "latest_scan_status": latest_scan.status if latest_scan else "Not Run",
                "default_secret_in_use": self.secure_storage.is_default_secret() if self.secure_storage else True,
            },
            "access_control_policies": [
                {
                    "asset": "Vessel manifests",
                    "policy": "Only administrator and harbourmaster roles can view protected payloads.",
                },
                {
                    "asset": "Logistical schedules",
                    "policy": "Role-based access is enforced through protected record permissions and API checks.",
                },
                {
                    "asset": "AIS / movement payloads",
                    "policy": "Sensitive streams are stored encrypted at rest and flagged if TLS is disabled in transit.",
                },
            ],
            "sensitive_records": [
                self._serialise_sensitive_record(record, user)
                for record in sensitive_records[-50:]
            ],
            "vulnerability_scans": self._serialize_records(scans)[-20:],
            "patch_records": self._serialize_records(patch_records)[-20:],
            "security_audits": self._serialize_records(self.repository.get_event_logs())[-30:],
        }

    def _build_management_dashboard_snapshot(self, user, filters, runtime_context):
        canonical_role = self._canonical_role(user.get("canonical_role", user.get("role", "")))
        return {
            "role_layout": self._build_role_dashboard_layout(canonical_role),
            "port_status_overview": self._build_port_status_overview(),
            "vessel_vehicle_activity": self._build_vessel_vehicle_activity(filters),
            "alerts_panel": self._serialize_records(self.repository.get_notifications())[-12:],
            "analytics_summary": self._build_analytics_snapshot()["summary"],
            "congestion_heatmap": self._build_congestion_heatmap(),
            "map_overlays": self._build_map_overlays(),
            "playback_frames": self._build_playback_frames(filters),
            "runtime_context": {
                "https_enabled": runtime_context.get("https_enabled", False),
                "active_sessions": runtime_context.get("session_count", 0),
            },
        }

    def _build_port_status_overview(self):
        berth_occupancy = self._build_berth_occupancy()
        vessel_queue = [
            path for path in self.repository.get_vessel_paths() if path.status.strip().lower() in {"holding", "waiting"}
        ]
        environmental = self.repository.get_environmental_updates()
        average_wind = round(
            sum(self._safe_float(update.wind_speed_knots) for update in environmental) / max(len(environmental), 1),
            1,
        )
        return {
            "occupied_berths": len([row for row in berth_occupancy if row["occupancy_percent"] > 0]),
            "vessel_queue": len(vessel_queue),
            "average_wind_knots": average_wind,
            "environmental_alert_zones": len(
                [
                    update
                    for update in environmental
                    if self._safe_float(update.wind_speed_knots) >= 20 or self._safe_float(update.visibility_km) <= 5
                ]
            ),
        }

    def _build_vessel_vehicle_activity(self, filters):
        zone_filter = str(filters.get("zone", "")).strip().lower()
        status_filter = str(filters.get("status", "")).strip().lower()
        locations = {location.location_id: location.name for location in self.repository.get_locations()}
        rows = []
        for path in self.repository.get_vessel_paths():
            destination_name = locations.get(path.destination_location_id, path.destination_location_id)
            if zone_filter and zone_filter not in destination_name.lower():
                continue
            if status_filter and status_filter != path.status.strip().lower():
                continue
            rows.append(
                {
                    "activity_type": "Vessel",
                    "asset_name": path.vessel_name,
                    "status": path.status,
                    "current_location": locations.get(path.current_location_id, path.current_location_id),
                    "target_location": destination_name,
                    "assigned_route": path.assigned_route_id,
                    "last_updated": path.last_updated,
                }
            )
        for activity in self.repository.get_cargo_activities():
            location_name = locations.get(activity.berth_id, activity.berth_id)
            if zone_filter and zone_filter not in location_name.lower():
                continue
            if status_filter and status_filter != activity.status.strip().lower():
                continue
            rows.append(
                {
                    "activity_type": "Vehicle / Cargo",
                    "asset_name": activity.vessel_name,
                    "status": activity.status,
                    "current_location": location_name,
                    "target_location": activity.operation_type,
                    "assigned_route": self._build_cargo_route_placeholder(activity.status, activity.operation_type),
                    "last_updated": activity.last_updated,
                }
            )
        rows.sort(key=lambda row: row["last_updated"], reverse=True)
        return rows[:25]

    def _build_cargo_route_placeholder(self, status, operation_type):
        status_text = str(status).strip().lower()
        operation_text = str(operation_type).strip().lower()
        if status_text == "active" and operation_text == "loading":
            return "Assigning"
        if status_text == "active" and operation_text == "unloading":
            return "Coming"
        if status_text == "paused":
            return "Waiting"
        return "Pending"

    def _build_congestion_heatmap(self):
        heatmap = []
        for row in self._build_peak_congestion_rows():
            heatmap.append(
                {
                    "time_window": row["hour_window"],
                    "incident_count": row["incident_count"],
                    "severity_band": (
                        "High"
                        if row["incident_count"] >= 10
                        else "Medium" if row["incident_count"] >= 5 else "Low"
                    ),
                }
            )
        return heatmap

    def _build_map_overlays(self):
        locations = self.repository.get_locations()
        routes = self.repository.get_routes()
        restricted_areas = self.repository.get_restricted_areas()
        return {
            "berth_layout": [
                {
                    "id": location.location_id,
                    "label": location.name,
                    "status": location.status,
                    "x": index % 6,
                    "y": index // 6,
                }
                for index, location in enumerate(locations[:24])
                if "berth" in location.type.strip().lower() or "dock" in location.type.strip().lower()
            ],
            "shipping_lanes": [
                {
                    "id": route.route_id,
                    "label": f"{route.start_location} -> {route.end_location}",
                    "status": route.status,
                }
                for route in routes[:20]
            ],
            "restricted_zones": [
                {
                    "id": area.area_id,
                    "label": area.name,
                    "location_id": area.location_id,
                    "status": area.status,
                    "severity": area.severity,
                }
                for area in restricted_areas[:20]
            ],
        }

    def _build_playback_frames(self, filters):
        time_window_filter = str(filters.get("time_window", "")).strip().lower()
        frames = []
        for path in self.repository.get_vessel_paths():
            frame_time = path.last_updated or self._now_iso()
            hour_window = ""
            parsed_frame = self._parse_iso_datetime(frame_time)
            if parsed_frame is not None:
                hour_window = f"{parsed_frame.hour:02d}:00-{parsed_frame.hour:02d}:59"
            if time_window_filter and hour_window.lower() != time_window_filter:
                continue
            frames.append(
                {
                    "frame_time": frame_time,
                    "asset_name": path.vessel_name,
                    "status": path.status,
                    "current_location_id": path.current_location_id,
                    "destination_location_id": path.destination_location_id,
                    "assigned_route_id": path.assigned_route_id,
                }
            )
        frames.sort(key=lambda frame: frame["frame_time"])
        return frames[-40:]

    def _build_role_dashboard_layout(self, canonical_role):
        layouts = {
            "administrator": [
                "port_status_overview",
                "alerts_panel",
                "analytics_summary",
                "congestion_heatmap",
                "map_overlays",
                "playback_frames",
            ],
            "harbourmaster": [
                "port_status_overview",
                "vessel_vehicle_activity",
                "alerts_panel",
                "map_overlays",
                "playback_frames",
            ],
            "operations supervisor": [
                "vessel_vehicle_activity",
                "port_status_overview",
                "analytics_summary",
                "congestion_heatmap",
                "playback_frames",
            ],
            "safety officer": [
                "port_status_overview",
                "alerts_panel",
                "map_overlays",
                "congestion_heatmap",
                "playback_frames",
            ],
        }
        return layouts.get(canonical_role, layouts["administrator"])

    def _build_scalability_snapshot(self, runtime_context):
        vessel_paths = self.repository.get_vessel_paths()
        sensor_updates = self.repository.get_environmental_updates()
        analytics_inputs = [*self.repository.get_notifications(), *self.repository.get_event_logs()]
        return {
            "summary": {
                "layered_architecture": "presentation -> business_logic -> data_access -> database",
                "active_sessions": runtime_context.get("session_count", 0),
                "cache_hits": self.cache_stats["hits"],
                "cache_misses": self.cache_stats["misses"],
            },
            "data_volume": {
                "vessel_paths": len(vessel_paths),
                "sensor_updates": len(sensor_updates),
                "notifications": len(self.repository.get_notifications()),
                "event_logs": len(self.repository.get_event_logs()),
            },
            "cache_status": [
                {
                    "cache_entries": len(self.cache_store),
                    "hits": self.cache_stats["hits"],
                    "misses": self.cache_stats["misses"],
                    "strategy": "Short-lived in-memory snapshot caching for monitoring, analytics, dashboard, and scalability views.",
                }
            ],
            "load_balancing": {
                "ais_workers": self._assign_to_workers(
                    [path.path_id for path in vessel_paths],
                    "AIS-Worker",
                    3,
                ),
                "analytics_workers": self._assign_to_workers(
                    [
                        getattr(item, "notification_id", getattr(item, "event_id", ""))
                        for item in analytics_inputs
                    ],
                    "Analytics-Worker",
                    2,
                ),
            },
            "stream_processing": [
                {
                    "pipeline": "AIS ingestion",
                    "batch_size": 25,
                    "window_seconds": 5,
                    "optimisation": "Shard vessel paths across worker buckets before analytics aggregation.",
                },
                {
                    "pipeline": "Environmental sensors",
                    "batch_size": 20,
                    "window_seconds": 10,
                    "optimisation": "Aggregate zone metrics before dashboard rendering and alert evaluation.",
                },
            ],
            "recommendations": [
                {
                    "category": "Caching",
                    "insight": "Keep snapshot cache TTL short to reduce stale operational views while still lowering repeated computation.",
                },
                {
                    "category": "Concurrency",
                    "insight": "Scale AIS and analytics workers independently as vessel traffic and sensor volume increase.",
                },
                {
                    "category": "Modularity",
                    "insight": "Preserve the layered repository/service/web separation so additional data pipelines can be added without rewriting the UI.",
                },
            ],
        }

    def _assign_to_workers(self, items, prefix, worker_count):
        assignments = {f"{prefix}-{index + 1}": [] for index in range(worker_count)}
        for item in items:
            worker_index = sum(ord(char) for char in str(item)) % worker_count
            assignments[f"{prefix}-{worker_index + 1}"].append(item)
        return [
            {"worker": worker, "items": assigned_items, "item_count": len(assigned_items)}
            for worker, assigned_items in assignments.items()
        ]

    def _evaluate_notification_rule(self, rule):
        context = rule.context_type.strip().lower()
        metric_name = rule.metric_name.strip().lower()
        threshold_value = float(rule.threshold_value or 0)

        if context == "hazard":
            matching_areas = [
                area
                for area in self.repository.get_restricted_areas()
                if area.is_active()
                and ("hazard" in area.area_type.lower() or area.location_id == rule.location_id)
            ]
            metric_value = len(
                [
                    area
                    for area in matching_areas
                    if not rule.location_id or area.location_id == rule.location_id
                ]
            )
            matched = self._compare_metric(metric_value, rule.operator, threshold_value)
            first_area = matching_areas[0] if matching_areas else None
            message = self._render_rule_message(
                rule,
                {
                    "location_id": first_area.location_id if first_area else rule.location_id or "Unknown",
                    "metric_value": metric_value,
                },
            )
            return {"matched": matched, "metric_value": metric_value, "message": message, "location_id": first_area.location_id if first_area else rule.location_id}

        if context == "delay":
            blocked_count = len(self._get_blocked_location_ids())
            matched = self._compare_metric(blocked_count, rule.operator, threshold_value)
            message = self._render_rule_message(
                rule,
                {"metric_value": blocked_count, "location_id": rule.location_id or "SYSTEM"},
            )
            return {"matched": matched, "metric_value": blocked_count, "message": message, "location_id": rule.location_id}

        if context == "equipment_faults":
            active_outages = [
                outage
                for outage in self.repository.get_crane_outages()
                if outage.status.strip().title() in self.ACTIVE_OUTAGE_STATUSES
            ]
            metric_value = len(active_outages)
            matched = self._compare_metric(metric_value, rule.operator, threshold_value)
            outage = active_outages[0] if active_outages else None
            message = self._render_rule_message(
                rule,
                {
                    "metric_value": metric_value,
                    "location_id": outage.location_id if outage else rule.location_id or "SYSTEM",
                },
            )
            return {"matched": matched, "metric_value": metric_value, "message": message, "location_id": outage.location_id if outage else rule.location_id}

        if context == "weather":
            updates = self.repository.get_environmental_updates()
            best_match = None
            metric_value = 0.0
            for update in updates:
                value = float(getattr(update, metric_name, 0) or 0)
                if self._compare_metric(value, rule.operator, threshold_value):
                    best_match = update
                    metric_value = value
                    break
            message = self._render_rule_message(
                rule,
                {
                    "metric_value": metric_value,
                    "zone_name": best_match.zone_name if best_match else "Unknown zone",
                    "location_id": rule.location_id or "SYSTEM",
                },
            )
            return {"matched": best_match is not None, "metric_value": metric_value, "message": message, "location_id": rule.location_id}

        if context == "workflow_changes":
            rerouted_count = len(
                [
                    path
                    for path in self.repository.get_vessel_paths()
                    if path.status.strip().lower() in {"rerouted", "holding"}
                ]
            )
            matched = self._compare_metric(rerouted_count, rule.operator, threshold_value)
            message = self._render_rule_message(
                rule,
                {"metric_value": rerouted_count, "location_id": rule.location_id or "SYSTEM"},
            )
            return {"matched": matched, "metric_value": rerouted_count, "message": message, "location_id": rule.location_id}

        return {"matched": False, "metric_value": 0, "message": rule.message_template, "location_id": rule.location_id}

    def _compare_metric(self, metric_value, operator, threshold_value):
        operator = operator.strip()
        if operator == ">=":
            return metric_value >= threshold_value
        if operator == "<=":
            return metric_value <= threshold_value
        if operator == ">":
            return metric_value > threshold_value
        if operator == "<":
            return metric_value < threshold_value
        if operator == "==":
            return metric_value == threshold_value
        return False

    def _render_rule_message(self, rule, values):
        message = rule.message_template
        for key, value in values.items():
            message = message.replace(f"{{{key}}}", str(value))
        return message

    def _deliver_notification(self, rule, notification):
        recipients = self._get_rule_recipients(rule.target_role)
        channels = [channel.strip() for channel in rule.channels.split(",") if channel.strip()]
        deliveries = []

        for recipient in recipients:
            for channel in channels:
                status = "Sent" if channel == "email" else "Delivered"
                deliveries.append(
                    self.repository.create_notification_delivery(
                        {
                            "notification_id": notification["notification_id"],
                            "rule_id": rule.rule_id,
                            "channel": channel,
                            "recipient_user_id": recipient.user_id,
                            "recipient_role": recipient.role,
                            "recipient_email": recipient.email,
                            "delivery_status": status,
                            "delivered_at": self._now_iso(),
                        }
                    )
                )
        return deliveries

    def _get_rule_recipients(self, target_role):
        role_lower = self._canonical_role(target_role)
        recipients = [
            user
            for user in self.repository.get_users()
            if user.is_active() and self._canonical_role(user.role) == role_lower
        ]
        return recipients
