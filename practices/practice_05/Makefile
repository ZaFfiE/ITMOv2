PY=python
PORT?=8075

.PHONY: run curl-demo

run:
	$(PY) practices/practice_05/app/service.py --port $(PORT)

curl-demo:
	@curl -sS http://127.0.0.1:$(PORT)/health | jq .
	@curl -sS -X POST http://127.0.0.1:$(PORT)/items \
	  -H 'Content-Type: application/json' \
	  -d '{"title":"Demo","url":"https://example.org","tags":["demo"],"status":"planned"}' | jq .
	@curl -sS http://127.0.0.1:$(PORT)/items | jq .
	@curl -sS -X PATCH http://127.0.0.1:$(PORT)/items/1 \
	  -H 'Content-Type: application/json' \
	  -d '{"status":"done"}' | jq .
	@curl -sS http://127.0.0.1:$(PORT)/items?status=done | jq .
	@curl -sS -X DELETE http://127.0.0.1:$(PORT)/items/1 | jq .
