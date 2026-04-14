import json
import secrets
import ssl
from datetime import datetime, timedelta, timezone
from errno import EADDRINUSE
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


class WebAppHandler(BaseHTTPRequestHandler):
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    service = None
    sessions = {}
    login_failures = {}
    session_timeout = timedelta(hours=8)

    def do_GET(self):
        path = self._get_path()

        if path == "/" or path == "/login" or path == "/login.html":
            self._serve_file("login.html", "text/html; charset=utf-8")
            return

        if path in {"/admin", "/admin.html"}:
            self._serve_file("admin.html", "text/html; charset=utf-8")
            return

        if path in {"/locations", "/locations.html"}:
            self._serve_file("locations.html", "text/html; charset=utf-8")
            return

        if path == "/monitoring" or path == "/monitoring.html":
            self._serve_file("monitoring.html", "text/html; charset=utf-8")
            return

        if path == "/notification-engine" or path == "/notification-engine.html":
            self._serve_file("notification_engine.html", "text/html; charset=utf-8")
            return

        if path == "/analytics" or path == "/analytics.html":
            self._serve_file("analytics.html", "text/html; charset=utf-8")
            return

        if path == "/dashboard" or path == "/dashboard.html":
            self._serve_file("dashboard.html", "text/html; charset=utf-8")
            return

        if path == "/static/styles.css":
            self._serve_file("styles.css", "text/css; charset=utf-8")
            return

        if path == "/static/login.js":
            self._serve_file("login.js", "application/javascript; charset=utf-8")
            return

        if path == "/static/admin.js":
            self._serve_file("admin.js", "application/javascript; charset=utf-8")
            return

        if path == "/static/locations.js":
            self._serve_file("locations.js", "application/javascript; charset=utf-8")
            return

        if path == "/static/monitoring.js":
            self._serve_file("monitoring.js", "application/javascript; charset=utf-8")
            return

        if path == "/static/notification_engine.js":
            self._serve_file("notification_engine.js", "application/javascript; charset=utf-8")
            return

        if path == "/static/analytics.js":
            self._serve_file("analytics.js", "application/javascript; charset=utf-8")
            return

        if path == "/static/dashboard.js":
            self._serve_file("dashboard.js", "application/javascript; charset=utf-8")
            return

        if path == "/api/session":
            user = self._get_authenticated_user()
            self._send_json(200, {"user": user})
            return

        if path == "/api/monitoring":
            if self._require_permission("view_monitoring") is None:
                return
            self._send_json(200, self.service.get_monitoring_snapshot())
            return

        if path == "/api/notification-engine":
            if self._require_permission("view_notification_engine") is None:
                return
            self._send_json(200, self.service.get_notification_engine_snapshot())
            return

        if path == "/api/analytics":
            if self._require_permission("view_analytics") is None:
                return
            self._send_json(200, self.service.get_analytics_snapshot())
            return

        if path == "/api/security":
            user = self._require_permission("view_security")
            if user is None:
                return
            self._send_json(
                200,
                self.service.get_security_snapshot(self._runtime_context(), user),
            )
            return

        if path == "/api/dashboard-management":
            user = self._require_permission("view_management_dashboard")
            if user is None:
                return
            self._send_json(
                200,
                self.service.get_management_dashboard_snapshot(
                    user,
                    runtime_context=self._runtime_context(),
                ),
            )
            return

        if path == "/api/scalability":
            if self._require_permission("view_scalability") is None:
                return
            self._send_json(200, self.service.get_scalability_snapshot(self._runtime_context()))
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        path = self._get_path()

        try:
            if path == "/api/login":
                self._handle_login()
                return

            if path == "/api/logout":
                self._handle_logout()
                return

            user = self._require_admin_user()
            if user is None:
                return

            payload = self._read_json_body()

            if path == "/api/admin/locations":
                self.service.ensure_user_permission(user, "manage_locations")
                location = self.service.create_location(payload)
                self._audit_action(user, "create", "location", location["location_id"], "Created location record.")
                self._send_json(
                    201,
                    {"location": location, "user": user},
                )
                return

            if path == "/api/admin/routes":
                self.service.ensure_user_permission(user, "manage_routes")
                route = self.service.create_route(payload)
                self._audit_action(user, "create", "route", route["route_id"], "Created route record.")
                self._send_json(
                    201,
                    {"route": route, "user": user},
                )
                return

            if path == "/api/admin/notifications":
                self.service.ensure_user_permission(user, "manage_notifications")
                notification = self.service.create_notification(payload)
                self._audit_action(user, "create", "notification", notification["notification_id"], "Created notification record.")
                self._send_json(
                    201,
                    {
                        "notification": notification,
                        "user": user,
                    },
                )
                return

            if path == "/api/admin/vessel-paths":
                self.service.ensure_user_permission(user, "manage_vessel_paths")
                vessel_path = self.service.create_vessel_path(payload)
                self._audit_action(user, "create", "vessel_path", vessel_path["path_id"], "Created vessel path.")
                self._send_json(
                    201,
                    {"vessel_path": vessel_path, "user": user},
                )
                return

            if path == "/api/admin/restricted-areas":
                self.service.ensure_user_permission(user, "manage_restricted_areas")
                restricted_area = self.service.create_restricted_area(payload)
                self._audit_action(user, "create", "restricted_area", restricted_area["area_id"], "Created restricted area.")
                self._send_json(
                    201,
                    {
                        "restricted_area": restricted_area,
                        "user": user,
                    },
                )
                return

            if path == "/api/admin/crane-outages":
                self.service.ensure_user_permission(user, "manage_crane_outages")
                crane_outage = self.service.create_crane_outage(payload)
                self._audit_action(user, "create", "crane_outage", crane_outage["outage_id"], "Created crane outage.")
                self._send_json(
                    201,
                    {
                        "crane_outage": crane_outage,
                        "user": user,
                    },
                )
                return

            if path == "/api/admin/berth-allocations":
                self.service.ensure_user_permission(user, "manage_berth_allocations")
                berth_allocation = self.service.create_berth_allocation(payload)
                self._audit_action(user, "create", "berth_allocation", berth_allocation["allocation_id"], "Created berth allocation.")
                self._send_json(
                    201,
                    {
                        "berth_allocation": berth_allocation,
                        "user": user,
                    },
                )
                return

            if path == "/api/admin/notification-rules":
                self.service.ensure_user_permission(user, "manage_notification_rules")
                rule = self.service.create_notification_rule(payload)
                self._audit_action(user, "create", "notification_rule", rule["rule_id"], "Configured notification rule.")
                self._send_json(
                    201,
                    {
                        "notification_rule": rule,
                        "user": user,
                    },
                )
                return

            if path == "/api/admin/consents":
                self.service.ensure_user_permission(user, "manage_compliance")
                consent = self.service.create_consent_record(payload)
                self._audit_action(user, "create", "consent_record", consent["consent_id"], "Recorded monitoring consent.")
                self._send_json(201, {"consent_record": consent, "user": user})
                return

            if path == "/api/admin/data-requests":
                self.service.ensure_user_permission(user, "manage_compliance")
                data_request = self.service.create_data_request(payload)
                self._audit_action(user, "create", "data_request", data_request["request_id"], "Created privacy/data request.")
                self._send_json(201, {"data_request": data_request, "user": user})
                return

            if path == "/api/admin/operational-change":
                self.service.ensure_user_permission(user, "manage_operational_changes")
                result = self.service.apply_operational_change(payload)
                self._audit_action(user, "update", "operations", payload.get("target_id", ""), "Applied operational change.")
                self._send_json(200, result)
                return

            if path == "/api/admin/recalculate":
                self.service.ensure_user_permission(user, "run_recalculation")
                result = self.service.recalculate_operations()
                self._audit_action(user, "execute", "operations_engine", "recalculate", "Ran operations recalculation.")
                self._send_json(200, result)
                return

            if path == "/api/admin/notification-engine/evaluate":
                self.service.ensure_user_permission(user, "manage_notification_rules")
                result = self.service.evaluate_notification_rules()
                self._audit_action(user, "execute", "notification_engine", "evaluate", "Ran notification rule evaluation.")
                self._send_json(200, result)
                return

            if path == "/api/admin/analytics/report":
                self.service.ensure_user_permission(user, "generate_reports")
                report = self.service.generate_custom_report(payload)
                self._audit_action(user, "generate", "analytics_report", "custom", "Generated filtered analytics report.")
                self._send_json(200, report)
                return

            if path == "/api/admin/sensitive-records":
                self.service.ensure_user_permission(user, "manage_sensitive_data")
                sensitive_record = self.service.create_sensitive_record(payload)
                self._audit_action(user, "create", "sensitive_record", sensitive_record["record_id"], "Created protected record.")
                self._send_json(201, {"sensitive_record": sensitive_record, "user": user})
                return

            if path == "/api/admin/patch-records":
                self.service.ensure_user_permission(user, "manage_security")
                patch_record = self.service.create_patch_record(payload)
                self._audit_action(user, "create", "patch_record", patch_record["patch_id"], "Created patch record.")
                self._send_json(201, {"patch_record": patch_record, "user": user})
                return

            if path == "/api/admin/security/scan":
                self.service.ensure_user_permission(user, "manage_security")
                scan_result = self.service.run_vulnerability_scan(self._runtime_context())
                self._audit_action(user, "execute", "security_scan", scan_result["scan"]["scan_id"], "Ran vulnerability scan.")
                self._send_json(200, scan_result)
                return

            self.send_error(404, "Not Found")
        except PermissionError as error:
            self._send_json(403, {"error": str(error)})
        except ValueError as error:
            self._send_json(400, {"error": str(error)})

    def do_PUT(self):
        path = self._get_path()
        user = self._require_admin_user()

        if user is None:
            return

        try:
            payload = self._read_json_body()
            prefix, record_id = self._split_admin_member_path(path)

            if prefix == "/api/admin/locations":
                self.service.ensure_user_permission(user, "manage_locations")
                location = self.service.update_location(record_id, payload)
                self._audit_action(user, "update", "location", record_id, "Updated location record.")
                self._send_json(200, {"location": location})
                return

            if prefix == "/api/admin/routes":
                self.service.ensure_user_permission(user, "manage_routes")
                route = self.service.update_route(record_id, payload)
                self._audit_action(user, "update", "route", record_id, "Updated route record.")
                self._send_json(200, {"route": route})
                return

            if prefix == "/api/admin/notifications":
                self.service.ensure_user_permission(user, "manage_notifications")
                notification = self.service.update_notification(record_id, payload)
                self._audit_action(user, "update", "notification", record_id, "Updated notification record.")
                self._send_json(
                    200,
                    {"notification": notification},
                )
                return

            if prefix == "/api/admin/vessel-paths":
                self.service.ensure_user_permission(user, "manage_vessel_paths")
                vessel_path = self.service.update_vessel_path(record_id, payload)
                self._audit_action(user, "update", "vessel_path", record_id, "Updated vessel path.")
                self._send_json(
                    200,
                    {"vessel_path": vessel_path},
                )
                return

            if prefix == "/api/admin/restricted-areas":
                self.service.ensure_user_permission(user, "manage_restricted_areas")
                restricted_area = self.service.update_restricted_area(record_id, payload)
                self._audit_action(user, "update", "restricted_area", record_id, "Updated restricted area.")
                self._send_json(
                    200,
                    {"restricted_area": restricted_area},
                )
                return

            if prefix == "/api/admin/crane-outages":
                self.service.ensure_user_permission(user, "manage_crane_outages")
                crane_outage = self.service.update_crane_outage(record_id, payload)
                self._audit_action(user, "update", "crane_outage", record_id, "Updated crane outage.")
                self._send_json(
                    200,
                    {"crane_outage": crane_outage},
                )
                return

            if prefix == "/api/admin/berth-allocations":
                self.service.ensure_user_permission(user, "manage_berth_allocations")
                berth_allocation = self.service.update_berth_allocation(record_id, payload)
                self._audit_action(user, "update", "berth_allocation", record_id, "Updated berth allocation.")
                self._send_json(
                    200,
                    {"berth_allocation": berth_allocation},
                )
                return

            if prefix == "/api/admin/notification-rules":
                self.service.ensure_user_permission(user, "manage_notification_rules")
                notification_rule = self.service.update_notification_rule(record_id, payload)
                self._audit_action(user, "update", "notification_rule", record_id, "Updated notification rule.")
                self._send_json(
                    200,
                    {
                        "notification_rule": notification_rule
                    },
                )
                return

            if prefix == "/api/admin/consents":
                self.service.ensure_user_permission(user, "manage_compliance")
                consent = self.service.update_consent_record(record_id, payload)
                self._audit_action(user, "update", "consent_record", record_id, "Updated consent record.")
                self._send_json(200, {"consent_record": consent})
                return

            if prefix == "/api/admin/data-requests":
                self.service.ensure_user_permission(user, "manage_compliance")
                data_request = self.service.update_data_request(record_id, payload)
                self._audit_action(user, "update", "data_request", record_id, "Updated data request.")
                self._send_json(200, {"data_request": data_request})
                return

            if prefix == "/api/admin/sensitive-records":
                self.service.ensure_user_permission(user, "manage_sensitive_data")
                sensitive_record = self.service.update_sensitive_record(record_id, payload)
                self._audit_action(user, "update", "sensitive_record", record_id, "Updated protected record.")
                self._send_json(200, {"sensitive_record": sensitive_record})
                return

            if prefix == "/api/admin/patch-records":
                self.service.ensure_user_permission(user, "manage_security")
                patch_record = self.service.update_patch_record(record_id, payload)
                self._audit_action(user, "update", "patch_record", record_id, "Updated patch record.")
                self._send_json(200, {"patch_record": patch_record})
                return

            self.send_error(404, "Not Found")
        except PermissionError as error:
            self._send_json(403, {"error": str(error)})
        except ValueError as error:
            self._send_json(400, {"error": str(error)})

    def do_DELETE(self):
        path = self._get_path()
        user = self._require_admin_user()

        if user is None:
            return

        try:
            prefix, record_id = self._split_admin_member_path(path)

            if prefix == "/api/admin/locations":
                self.service.ensure_user_permission(user, "manage_locations")
                self.service.delete_location(record_id)
                self._audit_action(user, "delete", "location", record_id, "Deleted location record.")
                self._send_json(200, {"deleted": record_id})
                return

            if prefix == "/api/admin/routes":
                self.service.ensure_user_permission(user, "manage_routes")
                self.service.delete_route(record_id)
                self._audit_action(user, "delete", "route", record_id, "Deleted route record.")
                self._send_json(200, {"deleted": record_id})
                return

            if prefix == "/api/admin/notifications":
                self.service.ensure_user_permission(user, "manage_notifications")
                self.service.delete_notification(record_id)
                self._audit_action(user, "delete", "notification", record_id, "Deleted notification record.")
                self._send_json(200, {"deleted": record_id})
                return

            if prefix == "/api/admin/vessel-paths":
                self.service.ensure_user_permission(user, "manage_vessel_paths")
                self.service.delete_vessel_path(record_id)
                self._audit_action(user, "delete", "vessel_path", record_id, "Deleted vessel path.")
                self._send_json(200, {"deleted": record_id})
                return

            if prefix == "/api/admin/restricted-areas":
                self.service.ensure_user_permission(user, "manage_restricted_areas")
                self.service.delete_restricted_area(record_id)
                self._audit_action(user, "delete", "restricted_area", record_id, "Deleted restricted area.")
                self._send_json(200, {"deleted": record_id})
                return

            if prefix == "/api/admin/crane-outages":
                self.service.ensure_user_permission(user, "manage_crane_outages")
                self.service.delete_crane_outage(record_id)
                self._audit_action(user, "delete", "crane_outage", record_id, "Deleted crane outage.")
                self._send_json(200, {"deleted": record_id})
                return

            if prefix == "/api/admin/berth-allocations":
                self.service.ensure_user_permission(user, "manage_berth_allocations")
                self.service.delete_berth_allocation(record_id)
                self._audit_action(user, "delete", "berth_allocation", record_id, "Deleted berth allocation.")
                self._send_json(200, {"deleted": record_id})
                return

            if prefix == "/api/admin/notification-rules":
                self.service.ensure_user_permission(user, "manage_notification_rules")
                self.service.delete_notification_rule(record_id)
                self._audit_action(user, "delete", "notification_rule", record_id, "Deleted notification rule.")
                self._send_json(200, {"deleted": record_id})
                return

            if prefix == "/api/admin/consents":
                self.service.ensure_user_permission(user, "manage_compliance")
                self.service.delete_consent_record(record_id)
                self._audit_action(user, "delete", "consent_record", record_id, "Deleted consent record.")
                self._send_json(200, {"deleted": record_id})
                return

            if prefix == "/api/admin/data-requests":
                self.service.ensure_user_permission(user, "manage_compliance")
                self.service.delete_data_request(record_id)
                self._audit_action(user, "delete", "data_request", record_id, "Deleted data request.")
                self._send_json(200, {"deleted": record_id})
                return

            if prefix == "/api/admin/sensitive-records":
                self.service.ensure_user_permission(user, "manage_sensitive_data")
                self.service.delete_sensitive_record(record_id)
                self._audit_action(user, "delete", "sensitive_record", record_id, "Deleted protected record.")
                self._send_json(200, {"deleted": record_id})
                return

            if prefix == "/api/admin/patch-records":
                self.service.ensure_user_permission(user, "manage_security")
                self.service.delete_patch_record(record_id)
                self._audit_action(user, "delete", "patch_record", record_id, "Deleted patch record.")
                self._send_json(200, {"deleted": record_id})
                return

            self.send_error(404, "Not Found")
        except PermissionError as error:
            self._send_json(403, {"error": str(error)})
        except ValueError as error:
            self._send_json(400, {"error": str(error)})

    def log_message(self, format, *args):
        return

    def _get_path(self):
        return urlparse(self.path).path

    def _handle_login(self):
        payload = self._read_json_body()
        email = str(payload.get("email", "")).strip()
        password = str(payload.get("password", ""))
        if not self._can_attempt_login(email):
            self._send_json(429, {"error": "Too many failed logins. Try again later."})
            return

        try:
            user = self.service.authenticate_user(email, password)
        except (PermissionError, ValueError):
            self._register_failed_login(email)
            raise

        self.login_failures.pop(email.lower(), None)
        token = secrets.token_hex(16)
        session_user = {
            **user,
            "session_started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "session_expires_at": (
                datetime.now(timezone.utc) + self.session_timeout
            ).isoformat(timespec="seconds"),
        }
        self.sessions[token] = session_user
        self.service.log_compliance_audit(
            user["user_id"],
            user["role"],
            "system_access",
            "session",
            token,
            "User signed in to the SMPOOS admin platform.",
        )
        self._send_json(
            200,
            {"user": session_user},
            extra_headers={
                "Set-Cookie": self._build_session_cookie(token)
            },
        )

    def _handle_logout(self):
        token = self._get_session_token()

        if token:
            self.sessions.pop(token, None)

        self._send_json(
            200,
            {"success": True},
            extra_headers={
                "Set-Cookie": self._build_session_cookie("", expired=True)
            },
        )

    def _read_json_body(self):
        content_length = int(self.headers.get("Content-Length", "0"))

        if content_length == 0:
            return {}

        body = self.rfile.read(content_length).decode("utf-8")
        return json.loads(body)

    def _get_session_token(self):
        cookie_header = self.headers.get("Cookie")

        if not cookie_header:
            return None

        cookie = SimpleCookie()
        cookie.load(cookie_header)
        session_cookie = cookie.get("session")
        return session_cookie.value if session_cookie else None

    def _get_authenticated_user(self):
        token = self._get_session_token()
        user = self.sessions.get(token)
        if user is not None:
            expires_at = user.get("session_expires_at")
            if expires_at:
                parsed_expiry = datetime.fromisoformat(expires_at)
                if parsed_expiry < datetime.now(timezone.utc):
                    self.sessions.pop(token, None)
                    return None
        hydrated_user = self.service.hydrate_session_user(user) if user else None
        if token and hydrated_user is not None:
            hydrated_user.setdefault("session_started_at", user.get("session_started_at", ""))
            hydrated_user.setdefault("session_expires_at", user.get("session_expires_at", ""))
            self.sessions[token] = hydrated_user
        return hydrated_user

    def _require_admin_user(self):
        user = self._get_authenticated_user()

        if user is None:
            self._send_json(401, {"error": "Login required."})
            return None

        return user

    def _require_permission(self, permission):
        user = self._require_admin_user()
        if user is None:
            return None

        try:
            return self.service.ensure_user_permission(user, permission)
        except PermissionError as error:
            self._send_json(403, {"error": str(error)})
            return None

    def _audit_action(self, user, action_type, entity_type, entity_id, details):
        self.service.log_compliance_audit(
            user.get("user_id", ""),
            user.get("role", ""),
            action_type,
            entity_type,
            entity_id,
            details,
        )

    def _can_attempt_login(self, email):
        entry = self.login_failures.get(email.lower())
        if entry is None:
            return True
        locked_until = entry.get("locked_until")
        if locked_until and locked_until > datetime.now(timezone.utc):
            return False
        if locked_until and locked_until <= datetime.now(timezone.utc):
            self.login_failures.pop(email.lower(), None)
        return True

    def _register_failed_login(self, email):
        key = email.lower()
        entry = self.login_failures.get(
            key,
            {"count": 0, "locked_until": None},
        )
        entry["count"] += 1
        if entry["count"] >= 5:
            entry["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=10)
        self.login_failures[key] = entry

    def _build_session_cookie(self, token, expired=False):
        parts = [
            f"session={token}",
            "HttpOnly",
            "Path=/",
            "SameSite=Lax",
        ]
        if self._is_https():
            parts.append("Secure")
        if expired:
            parts.append("Max-Age=0")
        return "; ".join(parts)

    def _runtime_context(self):
        return {
            "https_enabled": self._is_https(),
            "session_count": len(self.sessions),
        }

    def _is_https(self):
        return bool(getattr(self.server, "is_https", False))

    def _split_admin_member_path(self, path):
        parts = path.rstrip("/").split("/")

        if len(parts) != 5:
            raise ValueError("Invalid admin resource path.")

        prefix = "/".join(parts[:4])
        record_id = parts[4]
        return prefix, record_id

    def _serve_file(self, filename, content_type):
        file_path = self.frontend_dir / filename

        if not file_path.exists():
            self.send_error(404, "File not found")
            return

        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self._send_security_headers()
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, status_code, payload, extra_headers=None):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self._send_security_headers()

        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)

        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "script-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none';",
        )
        if self._is_https():
            self.send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")


def run_web_app(service, host="127.0.0.1", port=8000, ssl_cert_file="", ssl_key_file=""):
    WebAppHandler.service = service

    try:
        server = ThreadingHTTPServer((host, port), WebAppHandler)
    except OSError as error:
        if error.errno == EADDRINUSE:
            raise SystemExit(
                f"Port {port} is already in use. Stop the other server or run this app on a different port."
            ) from error
        raise

    server.is_https = False
    protocol = "http"
    if ssl_cert_file and ssl_key_file:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(ssl_cert_file, ssl_key_file)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        server.is_https = True
        protocol = "https"

    print(f"Server running at {protocol}://{host}:{port}")
    server.serve_forever()
