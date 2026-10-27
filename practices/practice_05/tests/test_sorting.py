import json
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from urllib.parse import urlencode
from urllib import request, error

import sys
from pathlib import Path


# Ensure `app` package is importable when running tests from repo root
THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import service  # noqa: E402


def start_server():
    store = service.ReadingList()
    router = service.Router(store)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), service.make_handler(router))
    httpd.daemon_threads = True
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()
    base_url = f"http://127.0.0.1:{httpd.server_port}"
    return httpd, th, base_url


def stop_server(httpd, th):
    httpd.shutdown()
    httpd.server_close()
    th.join(timeout=2)


def http_json(method, url, body=None):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=data, method=method, headers=headers)
    try:
        with request.urlopen(req, timeout=5) as resp:
            payload = resp.read().decode("utf-8")
            return resp.status, json.loads(payload) if payload else None
    except error.HTTPError as e:
        payload = e.read().decode("utf-8")
        return e.code, (json.loads(payload) if payload else None)


class SortingTests(unittest.TestCase):
    def setUp(self):
        self.httpd, self.thread, self.base = start_server()

    def tearDown(self):
        stop_server(self.httpd, self.thread)

    def create_item(self, title, tags=None, status="planned"):
        payload = {"title": title, "url": "https://example.org", "status": status}
        if tags is not None:
            payload["tags"] = tags
        code, obj = http_json("POST", f"{self.base}/items", payload)
        self.assertEqual(code, 201)
        return obj

    def get_items(self, **query):
        qs = ("?" + urlencode(query)) if query else ""
        code, obj = http_json("GET", f"{self.base}/items{qs}")
        return code, obj

    def test_default_order_matches_insertion(self):
        a = self.create_item("A")
        time.sleep(1)
        b = self.create_item("B")
        code, items = self.get_items()
        self.assertEqual(code, 200)
        self.assertEqual([it["id"] for it in items], [a["id"], b["id"]])

    def test_sort_ascending_and_descending(self):
        a = self.create_item("A")
        time.sleep(1)
        b = self.create_item("B")
        code, asc = self.get_items(sort="addedAt")
        self.assertEqual(code, 200)
        self.assertEqual([it["id"] for it in asc], [a["id"], b["id"]])
        code, desc = self.get_items(sort="-addedAt")
        self.assertEqual(code, 200)
        self.assertEqual([it["id"] for it in desc], [b["id"], a["id"]])

    def test_sort_with_status_and_tags_filters(self):
        a = self.create_item("A", tags=["ml"])  # planned
        b = self.create_item("B", tags=["nlp"])  # planned
        # Mark B as done to test status filter
        code, obj = http_json("PATCH", f"{self.base}/items/{b['id']}", {"status": "done"})
        self.assertEqual(code, 200)

        # status filter + sort desc: only planned (A)
        code, items = self.get_items(status="planned", sort="-addedAt")
        self.assertEqual(code, 200)
        self.assertEqual([it["id"] for it in items], [a["id"]])

        # tags ANY-of + sort asc: only nlp (B)
        code, items = self.get_items(tags="nlp", sort="addedAt")
        self.assertEqual(code, 200)
        self.assertEqual([it["id"] for it in items], [b["id"]])

    def test_invalid_sort_value_returns_400_and_does_not_mutate_state(self):
        a = self.create_item("A")
        b = self.create_item("B")
        # Snapshot before
        code, before = self.get_items()
        self.assertEqual(code, 200)
        # Invalid sort
        code, err = self.get_items(sort="foo")
        self.assertEqual(code, 400)
        self.assertIsInstance(err, dict)
        self.assertIn("error", err)
        # Ensure state unchanged
        code, after = self.get_items()
        self.assertEqual([it["id"] for it in after], [it["id"] for it in before])

    def test_empty_sort_value_is_400(self):
        self.create_item("A")
        code, err = self.get_items(sort="")
        self.assertEqual(code, 400)
        self.assertIn("error", err)

    def test_tie_breaker_when_addedAt_equal(self):
        # Create quickly to share the same second in now_iso
        a = self.create_item("A")
        b = self.create_item("B")
        # Ascending: lower id first when timestamps equal
        code, asc = self.get_items(sort="addedAt")
        self.assertEqual(code, 200)
        self.assertEqual([it["id"] for it in asc], sorted([a["id"], b["id"]]))
        # Descending: higher id first when timestamps equal
        code, desc = self.get_items(sort="-addedAt")
        self.assertEqual(code, 200)
        self.assertEqual([it["id"] for it in desc], sorted([a["id"], b["id"]], reverse=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
