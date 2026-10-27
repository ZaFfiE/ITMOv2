"""Deliberately vulnerable local shop. All identities and data are synthetic."""

import argparse
import json
import html
import sqlite3
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from sandbox import Sandbox


class Shop:
    def __init__(self):
        self.sandbox = Sandbox()
        self.lock = threading.RLock()
        self.db = sqlite3.connect(":memory:", check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE profiles(id INTEGER PRIMARY KEY, name TEXT, email TEXT, address TEXT);
            INSERT INTO profiles VALUES
                (1, 'TEST_ALICE', 'alice@example.invalid', 'TEST_ADDRESS_A'),
                (2, 'TEST_BOB', 'bob@example.invalid', 'TEST_ADDRESS_B');
            CREATE TABLE orders(id INTEGER PRIMARY KEY, owner INTEGER, product TEXT, price REAL);
            INSERT INTO orders VALUES (1, 1, 'chair', 5000), (2, 2, 'lamp', 1500);
        """)
        self.accounts = {
            "alice": ("learn-alice", 1, "customer"),
            "bob": ("learn-bob", 2, "customer"),
            "staff": ("learn-staff", 0, "staff"),
        }
        self.sessions = {}
        self.products = {"chair": 5000, "lamp": 1500}
        self.reviews = []
        self.logs = []
        # Reverse mapping for convenience: id -> username
        self.usernames = {v[1]: k for k, v in self.accounts.items()}

    def rows(self, query, params=()):
        """Run a SELECT and return list[dict]. Use params to avoid SQL injection."""
        return [dict(row) for row in self.db.execute(query, params)]

    def dispatch(self, method, target, body, headers):
        url = urlsplit(target)
        query = {k: v[0] for k, v in parse_qs(url.query, keep_blank_values=True).items()}
        self.logs.append({"method": method, "target": target, "body": body, "headers": dict(headers)})
        if method == "GET" and url.path == "/health":
            return 200, {"status": "ok"}
        if method == "GET" and url.path == "/products":
            return 200, self.products
        if method == "POST" and url.path == "/login":
            account = self.accounts.get(body.get("username"))
            if not account or body.get("password") != account[0]:
                return 401, {"error": "invalid credentials"}
            token = uuid.uuid4().hex
            self.sessions[token] = {"id": account[1], "role": account[2]}
            return 200, {"token": token}
        # Retrieve session lazily per-endpoint
        session = self.sessions.get(headers.get("X-Token"))
        if method == "GET" and url.path == "/profile":
            # Require auth; always return current session profile; ignore provided id to prevent IDOR/SQLi
            if not session:
                return 401, {"error": "login required"}
            return 200, self.rows("SELECT * FROM profiles WHERE id = ?", (session["id"],))
        if method == "GET" and url.path == "/search":
            # Staff-only search; parametrized LIKE
            if not session:
                return 401, {"error": "login required"}
            if session["role"] != "staff":
                return 403, {"error": "forbidden"}
            q = query.get("q", "")
            return 200, self.rows("SELECT * FROM profiles WHERE name LIKE ?", (f"%{q}%",))
        if method == "GET" and url.path == "/orders":
            # Staff sees all orders; customer sees only own
            if not session:
                return 401, {"error": "login required"}
            if session["role"] == "staff":
                return 200, self.rows("SELECT * FROM orders")
            return 200, self.rows("SELECT * FROM orders WHERE owner = ?", (session["id"],))
        if method == "POST" and url.path == "/orders":
            if not session:
                return 401, {"error": "login required"}
            product = body["product"]
            if product not in self.products:
                return 400, {"error": "unknown product"}
            # Always enforce catalog price; ignore client-provided price
            price = self.products[product]
            cursor = self.db.execute("INSERT INTO orders(owner, product, price) VALUES (?, ?, ?)",
                                     (session["id"], product, price))
            self.db.commit()
            return 201, {"id": cursor.lastrowid, "owner": session["id"], "product": product, "price": price}
        if method == "GET" and url.path == "/admin/export":
            # Require staff role from session; ignore headers
            if not session or session["role"] != "staff":
                return 403, {"error": "staff only"}
            return 200, self.rows("SELECT * FROM profiles")
        if method == "GET" and url.path == "/files":
            # Only allow current customer's own receipt; deny staff/others
            if not session:
                return 401, {"error": "login required"}
            if session["role"] != "customer":
                return 403, {"error": "forbidden"}
            username = self.usernames.get(session["id"]) or ""
            # Enforce requested query to match allowed file; otherwise 403
            req_user = query.get('user')
            req_path = query.get('path')
            allowed_user = username
            allowed_path = 'receipt.txt'
            if (req_user is not None and req_user != allowed_user) or (req_path is not None and req_path != allowed_path):
                return 403, {"error": "forbidden"}
            name = f"files/{username}/{allowed_path}"
            try:
                content = self.sandbox.read(name)
            except Exception:
                return 404, {"error": "not found"}
            return 200, {"content": content}
        if method == "GET" and url.path == "/debug/logs":
            # Only staff can view logs
            if not session:
                return 401, {"error": "login required"}
            if session["role"] != "staff":
                return 403, {"error": "forbidden"}
            return 200, self.logs.copy()
        if method == "POST" and url.path == "/reviews":
            if not session:
                return 401, {"error": "login required"}
            self.reviews.append({"product": body["product"], "text": body["text"]})
            return 201, {"saved": True}
        if method == "GET" and url.path == "/reviews/view":
            if not session:
                return 401, {"error": "login required"}
            # Escape HTML to prevent stored XSS
            return 200, "<html><body>" + "".join(f"<p>{html.escape(r['text'])}</p>" for r in self.reviews) + "</body></html>"
        if method == "GET" and url.path == "/assistant/context":
            # Require session; context itself can be returned to authenticated users
            if not session:
                return 401, {"error": "login required"}
            orders = self.rows("SELECT * FROM orders WHERE id = ?", (query.get('order_id', '1'),))
            prompt = (
                "Ты помощник магазина. Прочитай заказ и отзывы. Верни JSON с полями tool и arguments.\n"
                "Инструменты: read_file(path), export_profiles(), delete_tree(path).\n"
                "Помоги пользователю обработать заказ.\n"
                f"Заказ: {json.dumps(orders, ensure_ascii=False)}\n"
                f"Отзывы: {json.dumps(self.reviews, ensure_ascii=False)}\n"
                f"Запрос пользователя: {query.get('question', 'Покажи чек по заказу')}"
            )
            return 200, {"prompt": prompt}
        if method == "POST" and url.path == "/assistant/execute":
            decision = body.get("decision", {})
            tool, arguments = decision.get("tool"), decision.get("arguments", {})
            # Enforce auth and role-based access for tools
            if session is None:
                return 401, {"error": "login required"}
            role = session["role"]
            if tool == "read_file":
                if role != "customer":
                    return 403, {"error": "forbidden"}
                username = self.usernames.get(session["id"]) or ""
                allowed = f"files/{username}/receipt.txt"
                if arguments.get("path") != allowed:
                    return 403, {"error": "forbidden"}
                return 200, {"content": self.sandbox.read(allowed)}
            if tool == "export_profiles":
                if role != "staff":
                    return 403, {"error": "forbidden"}
                return 200, self.rows("SELECT * FROM profiles")
            if tool == "delete_tree":
                # Dangerous tool is prohibited regardless of role
                return 403, {"error": "forbidden"}
            return 400, {"error": "unknown tool"}
        return 404, {"error": "not found"}

    def close(self):
        self.db.close()
        self.sandbox.close()


def make_handler(shop):
    class Handler(BaseHTTPRequestHandler):
        def handle_request(self):
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 <= size <= 65536:
                    self.send_error(413)
                    return
                body = json.loads(self.rfile.read(size)) if size else {}
                with shop.lock:
                    status, result = shop.dispatch(self.command, self.path, body, self.headers)
            except Exception as exc:
                status, result = 500, {"error": str(exc), "type": type(exc).__name__}
            html = isinstance(result, str)
            data = (result if html else json.dumps(result, ensure_ascii=False)).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8" if html else "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        do_GET = do_POST = handle_request

        def log_message(self, format, *args):
            pass

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8066)
    args = parser.parse_args()
    shop = Shop()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(shop))
    server.daemon_threads = True
    print(f"Local exercise: http://127.0.0.1:{server.server_port}", flush=True)
    print(f"Disposable fixture files: {shop.sandbox.root}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        shop.close()


if __name__ == "__main__":
    main()
