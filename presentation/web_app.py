import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class WebAppHandler(BaseHTTPRequestHandler):
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    service = None

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._serve_file("index.html", "text/html; charset=utf-8")
            return

        if self.path == "/static/styles.css":
            self._serve_file("styles.css", "text/css; charset=utf-8")
            return

        if self.path == "/static/app.js":
            self._serve_file("app.js", "application/javascript; charset=utf-8")
            return

        if self.path == "/api/dashboard":
            self._serve_json(self.service.get_port_data())
            return

        self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        return

    def _serve_file(self, filename, content_type):
        file_path = self.frontend_dir / filename

        if not file_path.exists():
            self.send_error(404, "File not found")
            return

        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_json(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_web_app(service, host="127.0.0.1", port=8000):
    WebAppHandler.service = service
    server = ThreadingHTTPServer((host, port), WebAppHandler)
    print(f"Server running at http://{host}:{port}")
    server.serve_forever()
