"""Minimal Reading List API service.

Endpoints:
- GET /health
- POST /items                 -> create item
- GET /items?status=&tags=    -> list items with optional filters
- GET /items/{id}             -> get item by id
- PATCH /items/{id}           -> partial update (status, tags)
- DELETE /items/{id}          -> delete item

Storage: in-memory (process lifetime). Keep it simple and dependency-free.
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from dataclasses import dataclass, asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlsplit


def now_iso() -> str:
    # Use UTC timestamp in ISO-like format without timezone for simplicity
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class Item:
    id: int
    title: str
    url: str
    tags: List[str]
    status: str  # free-form, e.g., "planned" | "reading" | "done"
    addedAt: str
    readAt: Optional[str]


class ReadingList:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._next_id = 1
        self._items: Dict[int, Item] = {}

    # Basic CRUD with minimal validation
    def create(self, payload: dict) -> Tuple[int, dict]:
        title = payload.get("title")
        url = payload.get("url")
        if not isinstance(title, str) or not title.strip():
            return 400, {"error": "title is required"}
        if not isinstance(url, str) or not url.strip():
            return 400, {"error": "url is required"}

        tags = payload.get("tags", [])
        if tags is None:
            tags = []
        elif isinstance(tags, str):
            # Accept single string or comma-separated string; normalize to list
            tags = [t for t in (x.strip() for x in tags.split(",")) if t]
        elif not isinstance(tags, list):
            return 400, {"error": "tags must be an array of strings or a string"}
        if not all(isinstance(t, str) for t in tags):
            return 400, {"error": "tags must be an array of strings"}

        status = payload.get("status", "planned")
        if not isinstance(status, str):
            return 400, {"error": "status must be a string"}

        with self._lock:
            item_id = self._next_id
            self._next_id += 1
            read_at = now_iso() if status == "done" else None
            item = Item(
                id=item_id,
                title=title,
                url=url,
                tags=[t for t in tags],
                status=status,
                addedAt=now_iso(),
                readAt=read_at,
            )
            self._items[item_id] = item
            return 201, asdict(item)

    def get(self, item_id: int) -> Tuple[int, dict]:
        with self._lock:
            item = self._items.get(item_id)
            if not item:
                return 404, {"error": "not found"}
            return 200, asdict(item)

    def list(self, query: dict) -> Tuple[int, List[dict]]:
        # Filters: status=<str>, tags=tag1,tag2, q=<title substring> (case-insensitive)
        # Sorting: sort=addedAt|-addedAt
        status = query.get("status")
        tags_raw = query.get("tags")
        sort = query.get("sort")
        q_raw = query.get("q")
        q: Optional[str] = None
        if q_raw is not None:
            # Trim whitespace; treat empty-after-trim as absent
            t = q_raw.strip()
            if t:
                q = t
        tags_filter: Optional[List[str]] = None
        if tags_raw:
            # Accept comma-separated list
            tags_filter = [t for t in tags_raw.split(",") if t]

        with self._lock:
            items = list(self._items.values())
            if status is not None:
                items = [it for it in items if it.status == status]
            if tags_filter:
                # Match if item contains ANY of requested tags. Keep simple.
                s = set(tags_filter)
                items = [it for it in items if s.intersection(it.tags)]
            if q is not None:
                # Case-insensitive substring match on title
                q_lower = q.lower()
                items = [it for it in items if q_lower in it.title.lower()]

            # Apply optional sorting by addedAt
            if sort is not None:
                if sort == "addedAt":
                    items.sort(key=lambda it: (it.addedAt, it.id))
                elif sort == "-addedAt":
                    # Reverse both primary and tie-breaker
                    items.sort(key=lambda it: (it.addedAt, it.id), reverse=True)
                else:
                    return 400, {"error": "invalid sort"}

            return 200, [asdict(it) for it in items]

    def patch(self, item_id: int, payload: dict) -> Tuple[int, dict]:
        allowed = {"status", "tags"}
        if not isinstance(payload, dict) or not payload:
            return 400, {"error": "empty body"}
        if any(k not in allowed for k in payload):
            return 400, {"error": "only status and tags are updatable"}

        with self._lock:
            item = self._items.get(item_id)
            if not item:
                return 404, {"error": "not found"}
            if "status" in payload:
                status = payload["status"]
                if not isinstance(status, str):
                    return 400, {"error": "status must be a string"}
                item.status = status
                # Auto-set readAt when status becomes done; clear when leaving done.
                if status == "done" and item.readAt is None:
                    item.readAt = now_iso()
                if status != "done" and item.readAt is not None:
                    item.readAt = None
            if "tags" in payload:
                tags = payload["tags"]
                if tags is None:
                    tags = []
                elif isinstance(tags, str):
                    tags = [t for t in (x.strip() for x in tags.split(",")) if t]
                elif not isinstance(tags, list):
                    return 400, {"error": "tags must be an array of strings or a string"}
                if not all(isinstance(t, str) for t in tags):
                    return 400, {"error": "tags must be an array of strings"}
                item.tags = [t for t in tags]
            return 200, asdict(item)

    def delete(self, item_id: int) -> Tuple[int, dict]:
        with self._lock:
            if item_id not in self._items:
                return 404, {"error": "not found"}
            del self._items[item_id]
            # Use JSON response for consistency
            return 200, {"deleted": True}


class Router:
    def __init__(self, store: ReadingList) -> None:
        self.store = store

    def dispatch(self, method: str, target: str, body: dict, headers) -> Tuple[int, object, bool]:
        # Returns (status, payload, is_html)
        url = urlsplit(target)
        query = {k: v[0] for k, v in parse_qs(url.query, keep_blank_values=True).items()}

        # Minimal HTML UI page
        if method == "GET" and url.path in ("/", "/index.html"):
            html = (
                """
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\">
    <title>Reading List</title>
    <style>
      body { font-family: sans-serif; max-width: 800px; margin: 2rem auto; }
      .controls { display: flex; gap: .5rem; flex-wrap: wrap; }
      input { padding: .4rem; }
      button { padding: .4rem .7rem; }
      ul { padding-left: 1.2rem; }
      .tags { color: #555; }
      .error { color: #b00020; }
      .empty { color: #555; }
    </style>
  </head>
  <body>
    <h1>Reading List</h1>
    <div class=\"controls\">
      <label>Search by title <input id=\"q\" placeholder=\"Search...\"></label>
      <label>Status (exact) <input id=\"status\" placeholder=\"planned\"></label>
      <label>Tags (comma-separated) <input id=\"tags\" placeholder=\"ml,nlp\"></label>
      <button id=\"search\">Search</button>
      <button id=\"clear\">Clear</button>
    </div>
    <p id=\"loading\" style=\"display:none\">Loading…</p>
    <p id=\"error\" class=\"error\" style=\"display:none\"></p>
    <p id=\"empty\" class=\"empty\" style=\"display:none\">No items match your search.</p>
    <ul id=\"results\"></ul>
    <script>
    const $ = (id) => document.getElementById(id);
    const inputQ = $("q");
    const inputStatus = $("status");
    const inputTags = $("tags");
    const btnSearch = $("search");
    const btnClear = $("clear");
    const elLoading = $("loading");
    const elError = $("error");
    const elEmpty = $("empty");
    const elResults = $("results");

    function buildQuery() {
      const qs = new URLSearchParams();
      const q = (inputQ.value || "").trim();
      if (q) qs.set("q", q);
      if (inputStatus.value) qs.set("status", inputStatus.value);
      if (inputTags.value) qs.set("tags", inputTags.value);
      return qs.toString();
    }

    async function fetchItems() {
      elLoading.style.display = "";
      elError.style.display = "none";
      elEmpty.style.display = "none";
      elResults.innerHTML = "";
      btnSearch.disabled = true;
      try {
        const qs = buildQuery();
        const url = "/items" + (qs ? ("?" + qs) : "");
        const resp = await fetch(url);
        const text = await resp.text();
        if (!resp.ok) {
          try { const j = JSON.parse(text); elError.textContent = j.error || "Request failed"; }
          catch(_) { elError.textContent = text || "Request failed"; }
          elError.style.display = "";
          return;
        }
        const items = text ? JSON.parse(text) : [];
        if (!Array.isArray(items) || items.length === 0) {
          elEmpty.style.display = "";
          return;
        }
        for (const it of items) {
          const li = document.createElement("li");
          const tags = (it.tags && it.tags.length) ? it.tags.join(", ") : "";
          li.innerHTML = `<strong>${it.title}</strong> — <a href="${it.url}">${it.url}</a> — ${it.status}` + (tags ? ` — <span class="tags">${tags}</span>` : "");
          elResults.appendChild(li);
        }
      } catch (e) {
        elError.textContent = (e && e.message) ? e.message : "Network error";
        elError.style.display = "";
      } finally {
        elLoading.style.display = "none";
        btnSearch.disabled = false;
      }
    }

    btnSearch.addEventListener("click", fetchItems);
    inputQ.addEventListener("keydown", (e) => { if (e.key === "Enter") fetchItems(); });
    btnClear.addEventListener("click", () => { inputQ.value = ""; fetchItems(); });
    // Initial load with no q, status, or tags
    fetchItems();
    </script>
  </body>
 </html>
                """
            )
            return 200, html, True
        if method == "GET" and url.path == "/health":
            return 200, {"status": "ok"}, False

        # /items collection
        if url.path == "/items":
            if method == "POST":
                status, payload = self.store.create(body)
                return status, payload, False
            if method == "GET":
                status, payload = self.store.list(query)
                return status, payload, False

        # /items/{id}
        if url.path.startswith("/items/"):
            try:
                item_id = int(url.path.split("/")[-1])
            except ValueError:
                return 400, {"error": "invalid id"}, False

            if method == "GET":
                status, payload = self.store.get(item_id)
                return status, payload, False
            if method == "PATCH":
                status, payload = self.store.patch(item_id, body)
                return status, payload, False
            if method == "DELETE":
                status, payload = self.store.delete(item_id)
                return status, payload, False

        return 404, {"error": "not found"}, False


def make_handler(router: Router):
    class Handler(BaseHTTPRequestHandler):
        # Keep logs quiet to stdout
        def log_message(self, format, *args):
            pass

        def handle_request(self):
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 <= size <= 1_000_000:
                    self.send_error(413)
                    return
                body = json.loads(self.rfile.read(size)) if size else {}
                status, payload, is_html = router.dispatch(self.command, self.path, body, self.headers)
            except Exception as exc:  # keep service robust in exercises
                status, payload, is_html = 500, {"error": str(exc), "type": type(exc).__name__}, False

            data = (payload if is_html else json.dumps(payload, ensure_ascii=False)).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8" if is_html else "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        do_GET = do_POST = do_PATCH = do_DELETE = handle_request

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Reading List API (in-memory)")
    parser.add_argument("--port", type=int, default=8075)
    args = parser.parse_args()

    store = ReadingList()
    router = Router(store)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(router))
    server.daemon_threads = True
    print(f"Reading List API: http://127.0.0.1:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
