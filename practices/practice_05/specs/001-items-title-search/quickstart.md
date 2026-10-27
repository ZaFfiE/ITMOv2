# Quickstart Validation: Items Title Search

Prerequisites
- Python 3.x

Start the server

1. Run: `python3 app/service.py --port 8075`
2. Observe: "Reading List API: http://127.0.0.1:8075"

Seed data (example via curl)

```sh
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"title":"Deep Learning","url":"https://example.org","tags":["ml"],"status":"planned"}' \
  http://127.0.0.1:8075/items

curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"title":"Natural Language Processing","url":"https://example.org","tags":["nlp"],"status":"done"}' \
  http://127.0.0.1:8075/items
```

Validate API search

- `GET /items?q=learn` → returns only titles containing "learn".
- `GET /items?q=kotlin` (if seeded) → matches titles case-insensitively.
- `GET /items?q=  learn  &status=done` → trims q and filters by status.
- `GET /items?q=learn&tags=ml,nlp` → title match AND ANY-of tags.
- `GET /items?q=zzz` → 200 []
- `GET /items?q=read&sort=` → 400 {"error":"invalid sort"}

Validate UI behavior

- Load `/` in a browser (after UI addition). Enter a query and click Search. Observe matching items list or empty message. Click Clear to remove the search while preserving any status or tags filters.
