"""Standard-library HTTP wrapper around the stateless quote calculation."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path

from .pricing import InvalidQuote, quote

MAX_BODY_BYTES = 16_384
PAGE = Path(__file__).parent / "static" / "index.html"


def reject_non_json_constant(value):
    raise ValueError("Non-JSON numeric constant")


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object key")
        result[key] = value
    return result


class QuoteHandler(BaseHTTPRequestHandler):
    server_version = "WholesaleQuote/1.0"

    def send_payload(self, status, body, content_type="application/json; charset=utf-8"):
        if not isinstance(body, bytes):
            body = json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def error(self, status, code, message):
        self.send_payload(status, {"error": {"code": code, "message": message}})

    def do_GET(self):
        if self.path == "/health":
            self.send_payload(200, {"status": "ok"})
        elif self.path == "/":
            self.send_payload(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/quotes":
            self.method_not_allowed()
        else:
            self.error(404, "not_found", "Route not found.")

    def do_POST(self):
        if self.path != "/quotes":
            if self.path in ("/", "/health"):
                self.method_not_allowed()
            else:
                self.error(404, "not_found", "Route not found.")
            return
        if self.headers.get("Transfer-Encoding") is not None:
            self.error(400, "invalid_body", "Transfer-Encoding is not supported.")
            return
        lengths = self.headers.get_all("Content-Length", [])
        if not lengths:
            self.error(411, "length_required", "Content-Length is required.")
            return
        if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdecimal():
            self.error(400, "invalid_length", "Content-Length must be a nonnegative integer.")
            return
        if len(lengths[0]) > 8 or int(lengths[0]) > MAX_BODY_BYTES:
            self.error(413, "body_too_large", "The request body exceeds 16384 bytes.")
            return
        length = int(lengths[0])
        if self.headers.get_content_type() != "application/json":
            self.error(415, "unsupported_media_type", "Use Content-Type: application/json.")
            return
        self.connection.settimeout(5)
        try:
            body = self.rfile.read(length)
        except TimeoutError:
            self.error(408, "request_timeout", "The request body was not received in time.")
            return
        if len(body) != length:
            self.error(400, "invalid_body", "The request body is incomplete.")
            return
        try:
            payload = json.loads(
                body.decode("utf-8"),
                parse_constant=reject_non_json_constant,
                object_pairs_hook=reject_duplicate_keys,
            )
        except (UnicodeError, ValueError, RecursionError):
            self.error(400, "invalid_json", "The request body must contain valid JSON.")
            return
        try:
            result = quote(payload)
        except InvalidQuote as exc:
            self.error(422, exc.code, exc.message)
            return
        self.send_payload(200, result)

    def method_not_allowed(self):
        self.error(405, "method_not_allowed", "This method is not supported for this route.")

    do_HEAD = method_not_allowed
    do_PUT = method_not_allowed
    do_PATCH = method_not_allowed
    do_DELETE = method_not_allowed
    do_OPTIONS = method_not_allowed


def main():
    parser = argparse.ArgumentParser(description="Run the wholesale quote demo.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), QuoteHandler)
    print(f"Wholesale quote demo listening on {args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
