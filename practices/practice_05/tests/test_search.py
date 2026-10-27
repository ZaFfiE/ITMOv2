import threading
import time
import unittest
from http.server import ThreadingHTTPServer

import sys
from pathlib import Path


# Ensure `app` package is importable when running tests from repo root
THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import service  # noqa: E402
from tests.test_sorting import http_json  # reuse helper


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


class TitleSearchTests(unittest.TestCase):
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
        from urllib.parse import urlencode

        qs = ("?" + urlencode(query)) if query else ""
        code, obj = http_json("GET", f"{self.base}/items{qs}")
        return code, obj

    def test_case_insensitive_substring_and_trimming(self):
        a = self.create_item("Deep Learning")
        b = self.create_item("Natural Language Processing")
        # lowercase substring
        code, items = self.get_items(q="learn")
        self.assertEqual(code, 200)
        self.assertEqual([it["id"] for it in items], [a["id"]])
        # different casing
        code, items = self.get_items(q="kOTLIN")
        self.assertEqual(code, 200)
        # none should match since no kotlin items yet
        self.assertEqual(items, [])
        # trimming
        code, items = self.get_items(q="   Learning   ")
        self.assertEqual(code, 200)
        self.assertEqual([it["id"] for it in items], [a["id"]])

    def test_no_matches_returns_empty_array(self):
        self.create_item("A")
        code, items = self.get_items(q="zzzz")
        self.assertEqual(code, 200)
        self.assertEqual(items, [])

    def test_combination_with_status_and_tags_and_sort(self):
        dl = self.create_item("Deep Learning", tags=["ml"], status="planned")
        nlp = self.create_item("NLP Fundamentals", tags=["nlp"], status="planned")
        # Mark NLP done
        code, _ = http_json("PATCH", f"{self.base}/items/{nlp['id']}", {"status": "done"})
        self.assertEqual(code, 200)

        # q + status
        code, items = self.get_items(q="nlp", status="done")
        self.assertEqual(code, 200)
        self.assertEqual([it["id"] for it in items], [nlp["id"]])

        # q + tags ANY-of
        code, items = self.get_items(q="learn", tags="ml,nlp")
        self.assertEqual(code, 200)
        self.assertEqual([it["id"] for it in items], [dl["id"]])

        # q + sort
        time.sleep(1)
        late = self.create_item("Learn Rust")
        code, items = self.get_items(q="learn", sort="-addedAt")
        self.assertEqual(code, 200)
        self.assertEqual([it["id"] for it in items], [late["id"], dl["id"]])

    def test_combination_with_status_and_tags_together(self):
        # Create items
        a = self.create_item("Learn NLP", tags=["nlp"], status="done")
        b = self.create_item("Learn ML", tags=["ml"], status="done")
        c = self.create_item("Learning Systems", tags=["systems"], status="planned")
        # q + status + tags (ANY-of): expect only 'Learn NLP' matches 'learn' in title, status=done, tags contains nlp
        code, items = self.get_items(q="learn", status="done", tags="nlp")
        self.assertEqual(code, 200)
        self.assertEqual([it["id"] for it in items], [a["id"]])

    def test_q_missing_or_empty_preserves_behavior_and_invalid_sort(self):
        a = self.create_item("A")
        b = self.create_item("B")
        # Without q
        code, items1 = self.get_items()
        self.assertEqual(code, 200)
        # q empty
        code, items2 = self.get_items(q="")
        self.assertEqual(code, 200)
        self.assertEqual(items2, items1)
        # q spaces
        code, items3 = self.get_items(q="   ")
        self.assertEqual(code, 200)
        self.assertEqual(items3, items1)
        # invalid sort with q
        code, err = self.get_items(q="read", sort="foo")
        self.assertEqual(code, 400)
        self.assertIn("error", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
