"""Security expectation tests: describe the intended secure behavior (should fail on vulnerable code)."""

import json
import unittest
from urllib.parse import quote

from service import Shop


class SecurityTest(unittest.TestCase):
    def setUp(self):
        self.shop = Shop()
        self.addCleanup(self.shop.close)

    def request(self, method, path, body=None, headers=None):
        with self.shop.lock:
            return self.shop.dispatch(method, path, body or {}, headers or {})

    def login(self, username="alice", password="learn-alice"):
        status, result = self.request("POST", "/login", {"username": username, "password": password})
        self.assertEqual(status, 200)
        return {"X-Token": result["token"]}

    # /profile: only session owner, ignore query id; no SQLi via string id
    def test_profile_returns_only_session_user(self):
        alice = self.login()
        status, result = self.request("GET", "/profile?id=2", headers=alice)
        self.assertEqual(status, 200)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "TEST_ALICE")

    def test_profile_ignores_injection_and_id(self):
        alice = self.login()
        inj = quote("1 OR 1=1")
        status, result = self.request("GET", f"/profile?id={inj}", headers=alice)
        self.assertEqual(status, 200)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "TEST_ALICE")

    # /search: only for staff; parametrized, no SQLi; customers forbidden
    def test_search_forbidden_for_customer(self):
        alice = self.login()
        status, _ = self.request("GET", "/search?q=ALICE", headers=alice)
        self.assertEqual(status, 403)

    def test_search_allowed_for_staff_only(self):
        staff = self.login("staff", "learn-staff")
        status, result = self.request("GET", "/search?q=TEST_", headers=staff)
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(result), 1)

    # /orders POST: ignore client price, use catalog price
    def test_order_price_from_catalog(self):
        alice = self.login()
        status, order = self.request("POST", "/orders", {"product": "chair", "price": 1}, headers=alice)
        self.assertEqual(status, 201)
        self.assertEqual(order["price"], 5000)

    # /admin/export: require staff session; ignore X-Role header
    def test_admin_export_requires_staff_session(self):
        # Header-only should be forbidden
        status, _ = self.request("GET", "/admin/export", headers={"X-Role": "staff"})
        self.assertEqual(status, 403)
        # Proper staff session should pass without relying on X-Role
        staff = self.login("staff", "learn-staff")
        status, result = self.request("GET", "/admin/export", headers=staff)
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(result), 2)

    # /files: only own receipt; deny traversal/private
    def test_files_cannot_read_others_receipt(self):
        alice = self.login()
        status, _ = self.request("GET", "/files?user=bob&path=receipt.txt", headers=alice)
        self.assertEqual(status, 403)

    def test_files_cannot_access_private_note(self):
        alice = self.login()
        status, _ = self.request("GET", "/files?user=alice&path=" + quote("../../private/operator-note.txt"), headers=alice)
        self.assertEqual(status, 403)

    # /reviews/view: escape HTML (no raw <script>)
    def test_reviews_view_escapes_html(self):
        alice = self.login()
        status, _ = self.request("POST", "/reviews", {"product": "chair", "text": "<script>alert(1)</script>"}, headers=alice)
        self.assertEqual(status, 201)
        status, html = self.request("GET", "/reviews/view", headers=alice)
        self.assertEqual(status, 200)
        self.assertNotIn("<script", html)

    # /assistant/execute: auth required; customers limited tools; staff cannot delete
    def test_assistant_requires_auth(self):
        status, _ = self.request("POST", "/assistant/execute", {"decision": {"tool": "export_profiles"}})
        self.assertEqual(status, 401)

    def test_assistant_customer_only_own_receipt(self):
        alice = self.login()
        # Can read own receipt
        status, res = self.request("POST", "/assistant/execute", {"decision": {"tool": "read_file", "arguments": {"path": "files/alice/receipt.txt"}}}, headers=alice)
        self.assertEqual(status, 200)
        self.assertIn("TEST_ALICE", res.get("content", ""))
        # Cannot read other's receipt
        status, _ = self.request("POST", "/assistant/execute", {"decision": {"tool": "read_file", "arguments": {"path": "files/bob/receipt.txt"}}}, headers=alice)
        self.assertEqual(status, 403)
        # Cannot export profiles
        status, _ = self.request("POST", "/assistant/execute", {"decision": {"tool": "export_profiles"}}, headers=alice)
        self.assertEqual(status, 403)
        # Cannot delete tree
        status, _ = self.request("POST", "/assistant/execute", {"decision": {"tool": "delete_tree", "arguments": {"path": "."}}}, headers=alice)
        self.assertEqual(status, 403)

    def test_assistant_staff_can_export_but_not_delete(self):
        staff = self.login("staff", "learn-staff")
        status, res = self.request("POST", "/assistant/execute", {"decision": {"tool": "export_profiles"}}, headers=staff)
        self.assertEqual(status, 200)
        self.assertIsInstance(res, list)
        # delete_tree still forbidden
        status, _ = self.request("POST", "/assistant/execute", {"decision": {"tool": "delete_tree", "arguments": {"path": "."}}}, headers=staff)
        self.assertEqual(status, 403)

    # /debug/logs: only staff
    def test_debug_logs_only_staff(self):
        # Missing auth
        status, _ = self.request("GET", "/debug/logs")
        self.assertEqual(status, 401)
        # Customer forbidden
        alice = self.login()
        status, _ = self.request("GET", "/debug/logs", headers=alice)
        self.assertEqual(status, 403)
        # Staff allowed
        staff = self.login("staff", "learn-staff")
        status, logs = self.request("GET", "/debug/logs", headers=staff)
        self.assertEqual(status, 200)
        self.assertIsInstance(logs, list)


if __name__ == "__main__":
    unittest.main()
