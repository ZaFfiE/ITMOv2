import json
import threading
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
from urllib import request


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


class UISearchTests(unittest.TestCase):
    def setUp(self):
        self.httpd, self.thread, self.base = start_server()

    def tearDown(self):
        stop_server(self.httpd, self.thread)

    def post_json(self, url, payload):
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
        with request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def get_text(self, url):
        with request.urlopen(url, timeout=5) as resp:
            return resp.status, resp.read().decode("utf-8")

    def test_index_page_loads(self):
        code, html = self.get_text(f"{self.base}/")
        self.assertEqual(code, 200)
        self.assertIn("Reading List", html)
        self.assertIn("Search by title", html)

    def test_ui_contains_loading_empty_error_elements(self):
        code, html = self.get_text(f"{self.base}/")
        self.assertEqual(code, 200)
        self.assertIn('id="loading"', html)
        self.assertIn('id="empty"', html)
        self.assertIn('id="error"', html)

    def test_ui_script_fetches_real_api(self):
        code, html = self.get_text(f"{self.base}/")
        self.assertEqual(code, 200)
        # Ensure script references the real API endpoint construction
        self.assertIn('const url = "/items"', html)

    def test_ui_script_toggles_states_code_present(self):
        code, html = self.get_text(f"{self.base}/")
        self.assertEqual(code, 200)
        # Verify code manipulates loading, empty, and error displays
        self.assertIn('elLoading.style.display', html)
        self.assertIn('elEmpty.style.display', html)
        self.assertIn('elError.style.display', html)

    def test_api_called_for_results(self):
        # seed
        self.post_json(f"{self.base}/items", {"title": "Deep Learning", "url": "https://example.org"})
        self.post_json(f"{self.base}/items", {"title": "Natural Language Processing", "url": "https://example.org"})
        # verify API response used by UI script: request API directly
        with request.urlopen(f"{self.base}/items?q=learn", timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            items = json.loads(resp.read().decode("utf-8"))
            self.assertIsInstance(items, list)
            self.assertTrue(any("Deep Learning" == it["title"] for it in items))


if __name__ == "__main__":
    unittest.main(verbosity=2)
