import json
import secrets
from errno import EADDRINUSE
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


class WebAppHandler(BaseHTTPRequestHandler):
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    service = None
    sessions = {}

    def do_GET(self):
        path = self._get_path()

        if path == "/" or path == "/login" or path == "/login.html":
            self._serve_file("login.html", "text/html; charset=utf-8")
            return

        if path == "/admin" or path == "/admin.html":
            self._serve_file("admin.html", "text/html; charset=utf-8")
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

        if path == "/api/session":
            user = self._get_authenticated_user()
            self._send_json(200, {"user": user})
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
                self._send_json(
                    201,
                    {"location": self.service.create_location(payload), "user": user},
                )
                return

            if path == "/api/admin/routes":
                self._send_json(
                    201,
                    {"route": self.service.create_route(payload), "user": user},
                )
                return

            if path == "/api/admin/notifications":
                self._send_json(
                    201,
                    {
                        "notification": self.service.create_notification(payload),
                        "user": user,
                    },
                )
                return

            if path == "/api/admin/operational-change":
                result = self.service.apply_operational_change(payload)
                self._send_json(200, result)
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
                self._send_json(200, {"location": self.service.update_location(record_id, payload)})
                return

            if prefix == "/api/admin/routes":
                self._send_json(200, {"route": self.service.update_route(record_id, payload)})
                return

            if prefix == "/api/admin/notifications":
                self._send_json(
                    200,
                    {"notification": self.service.update_notification(record_id, payload)},
                )
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
                self.service.delete_location(record_id)
                self._send_json(200, {"deleted": record_id})
                return

            if prefix == "/api/admin/routes":
                self.service.delete_route(record_id)
                self._send_json(200, {"deleted": record_id})
                return

            if prefix == "/api/admin/notifications":
                self.service.delete_notification(record_id)
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
        user = self.service.authenticate_user(email, password)
        token = secrets.token_hex(16)
        self.sessions[token] = user
        self._send_json(
            200,
            {"user": user},
            extra_headers={
                "Set-Cookie": f"session={token}; HttpOnly; Path=/; SameSite=Lax"
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
                "Set-Cookie": (
                    "session=; HttpOnly; Path=/; SameSite=Lax; Max-Age=0"
                )
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
        return self.sessions.get(token)

    def _require_admin_user(self):
        user = self._get_authenticated_user()

        if user is None:
            self._send_json(401, {"error": "Login required."})
            return None

        return user

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
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, status_code, payload, extra_headers=None):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")

        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)

        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_web_app(service, host="127.0.0.1", port=8000):
    WebAppHandler.service = service

    try:
        server = ThreadingHTTPServer((host, port), WebAppHandler)
    except OSError as error:
        if error.errno == EADDRINUSE:
            raise SystemExit(
                f"Port {port} is already in use. Stop the other server or run this app on a different port."
            ) from error
        raise

    print(f"Server running at http://{host}:{port}")
    server.serve_forever()
