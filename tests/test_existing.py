"""The application's original regression suite."""

import http.client
from http.server import ThreadingHTTPServer
import json
import threading
import unittest

from pricing_service.pricing import InvalidQuote, quote
from pricing_service.server import QuoteHandler


class QuoteTests(unittest.TestCase):
    def test_single_unit(self):
        result = quote({"sku": "WIDGET-100", "quantity": 1})
        self.assertEqual(result, {
            "sku": "WIDGET-100", "quantity": 1, "unit_price_cents": 10000,
            "subtotal_cents": 10000, "discount_cents": 0,
            "total_cents": 10000, "currency": "USD",
        })

    def test_large_order(self):
        result = quote({"sku": "WIDGET-100", "quantity": 20})
        self.assertEqual(result["subtotal_cents"], 200000)
        self.assertEqual(result["discount_cents"], 20000)
        self.assertEqual(result["total_cents"], 180000)
        self.assertTrue(all(type(result[key]) is int for key in result if key.endswith("_cents")))

    def test_invalid_quantities(self):
        for value in (True, False, None, "20", 1.0, -1, 0, 10001, [], {}):
            with self.subTest(value=value), self.assertRaises(InvalidQuote) as context:
                quote({"sku": "WIDGET-100", "quantity": value})
            self.assertEqual(context.exception.code, "invalid_quantity")

    def test_unknown_sku(self):
        for value in ("UNKNOWN", None, [], True):
            with self.subTest(value=value), self.assertRaises(InvalidQuote) as context:
                quote({"sku": value, "quantity": 1})
            self.assertEqual(context.exception.code, "unknown_sku")

    def test_invalid_request_shapes(self):
        for value in (None, [], "hello", 1, {}, {"sku": "WIDGET-100"},
                      {"sku": "WIDGET-100", "quantity": 1, "discount": 99}):
            with self.subTest(value=value), self.assertRaises(InvalidQuote):
                quote(value)


class QuietHandler(QuoteHandler):
    def log_message(self, format, *args):
        pass


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=3)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, response.getheader("Content-Type"), response.read()
        finally:
            connection.close()

    def post(self, body, headers=None):
        return self.request("POST", "/quotes", body, headers or {"Content-Type": "application/json"})

    def test_health(self):
        status, content_type, body = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"status": "ok"})

    def test_homepage(self):
        status, content_type, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn(b"Wholesale quote", body)

    def test_quote_response_is_repeatable(self):
        request = b'{"sku":"WIDGET-100","quantity":20}'
        first = self.post(request)
        self.assertEqual(first[0], 200)
        self.assertEqual(json.loads(first[2])["total_cents"], 180000)
        self.assertEqual(self.post(request), first)

    def test_invalid_quantity_http(self):
        status, _, body = self.post(b'{"sku":"WIDGET-100","quantity":0}')
        self.assertEqual(status, 422)
        self.assertEqual(json.loads(body)["error"]["code"], "invalid_quantity")

    def test_invalid_json(self):
        for body in (b"", b"{", b"\xff", b'{"quantity":NaN}', b'{"quantity":1,"quantity":2}'):
            with self.subTest(body=body):
                status, _, response = self.post(body)
                self.assertEqual(status, 400)
                self.assertEqual(json.loads(response)["error"]["code"], "invalid_json")

    def test_invalid_request_body(self):
        for body in (b"null", b"[]", b"true"):
            with self.subTest(body=body):
                status, _, response = self.post(body)
                self.assertEqual(status, 422)
                self.assertEqual(json.loads(response)["error"]["code"], "invalid_request")

    def test_body_limit(self):
        status, _, body = self.post(b" " * 16385)
        self.assertEqual(status, 413)
        self.assertEqual(json.loads(body)["error"]["code"], "body_too_large")

    def test_content_type(self):
        status, _, body = self.post(b"{}", {"Content-Type": "text/plain"})
        self.assertEqual(status, 415)
        self.assertEqual(json.loads(body)["error"]["code"], "unsupported_media_type")

    def test_invalid_content_length(self):
        status, _, body = self.post(b"", {"Content-Type": "application/json", "Content-Length": "-1"})
        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body)["error"]["code"], "invalid_length")

    def test_routes(self):
        for method, path, expected in (("GET", "/missing", 404), ("GET", "/quotes", 405),
                                       ("POST", "/health", 405), ("POST", "/missing", 404),
                                       ("PUT", "/quotes", 405)):
            with self.subTest(method=method, path=path):
                status, _, body = self.request(method, path)
                self.assertEqual(status, expected)
                self.assertIn("error", json.loads(body))


if __name__ == "__main__":
    unittest.main()
