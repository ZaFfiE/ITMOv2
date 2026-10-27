Reading List API (practice_05)

Minimal dependency-free HTTP service using Python stdlib (http.server) with in-memory storage.

Endpoints
- GET /health → {"status":"ok"}
- POST /items → create item. Body: {"title": str, "url": str, "tags": [str]=[], "status": str="planned"}
- GET /items?status=...&tags=tag1,tag2 → list items with optional filters
- GET /items/{id} → get item by id
- PATCH /items/{id} → partial update {"status"?: str, "tags"?: [str]}
- DELETE /items/{id} → delete item

Notes
- Fields: title, url, tags, status, addedAt, readAt; readAt auto-set when status becomes "done".
- Storage is in-memory; data resets on restart.

Run
1. Python 3.11+ recommended.
2. Start service:
   python practices/practice_05/app/service.py --port 8075

Examples (httpie)
Health:
  http :8075/health

Create:
  http POST :8075/items title="Article" url="https://example.com" tags:='["ml","nlp"]'

List (all):
  http :8075/items

List (status filter):
  http :8075/items status==planned

List (tags filter):
  http :8075/items tags==ml,nlp

Get by id:
  http :8075/items/1

Patch (status -> done):
  http PATCH :8075/items/1 status=done

Patch (tags):
  http PATCH :8075/items/1 tags:='["ai"]'

Delete:
  http DELETE :8075/items/1
