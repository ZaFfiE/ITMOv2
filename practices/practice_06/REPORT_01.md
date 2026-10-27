# Отчёт 1. Атаки на исходный сервис

## Бейзлайн

- Python: 3.12.3; pip: 24.0
- Команда `make install` (lab): OK — "Standard library only: ready"
- Команда `make test` (lab): OK — 16 тестов, все зелёные

Логи и окружение (до изменений):

- evidence/before/make_install.log — вывод `make install`
- evidence/before/make_test.log — вывод `make test`
- evidence/before/server_start.log — первые строки запуска сервера и каталог песочницы
- Сервер запущен локально: http://127.0.0.1:8066

Примечание: порт 8066 свободен и использован для локального прогона.

## Локальный запуск и проверка /health

- Адрес сервера: http://127.0.0.1:8066
- Проверка `GET /health`: 200, тело {"status": "ok"}
- Заголовки ответа включают `Content-Type: application/json; charset=utf-8`

## PoC «до исправлений» (ручные проверки)

Ниже — выдержки ключевых запросов/результатов. Полные ответы сохранены в evidence/before/.

1) Эскалация роли заголовком
- Запрос: `GET /admin/export` c заголовком `X-Role: staff`, без сессии staff
- Результат: 200, тела с профилями — admin_export_header_only.json

Пример HTTP (сжатый):
```
GET /admin/export HTTP/1.1
Host: 127.0.0.1:8066
Content-Type: application/json
X-Role: staff

HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
[
  {"id":1,"name":"TEST_ALICE",...},
  {"id":2,"name":"TEST_BOB",...}
]
```

2) Небезопасный /assistant/execute (без авторизации)
- `POST /assistant/execute` с `{tool: export_profiles}` → 200, содержимое профилей — assistant_export_profiles_noauth.json
- `POST /assistant/execute` с `{tool: delete_tree, arguments: {path: "."}}` → 200, `{deleted: "."}` — assistant_delete_tree_noauth.json

3) Утечки через /debug/logs
- `GET /debug/logs` → 200, в журнале отражаются заголовки и тела запросов, включая токены — debug_logs.json

4) IDOR и SQLi
- `POST /login` (alice) → 200, получен токен — login_alice.json
- `GET /profile?id=2` с токеном alice → 200, профиль Bob — idor_profile_bob.json
- `GET /profile?id=1 OR 1=1` → 200, все профили — sqli_profile_or_1_1.json
- `GET /search?q=%' OR 1=1 -- ` → 200, все профили — sqli_search_or_1_1.json

5) Подмена цены
- `POST /orders` с `{product: "chair", price: 1}` → 201, создан заказ с ценой 1 — order_price_tamper.json

6) Доступ к чужим/закрытым файлам
- `GET /files?user=bob&path=receipt.txt` → 200, чек Bob — files_bob_receipt.json
- `GET /files?user=alice&path=../../private/operator-note.txt` → 200, секрет — files_private_note.json

7) Stored XSS
- `POST /reviews` с `text="<script>alert(1)</script>"` → 201 — review_xss_post.json
- `GET /reviews/view` → 200, HTML содержит скрипт — reviews_view.html.json

Вывод: на исходном сервисе воспроизводятся критические уязвимости: авторизация по заголовку, отсутствие проверок в /assistant/execute, SQLi, IDOR, Path Traversal в пределах песочницы, подмена цены, XSS и утечки логов. Эти PoC будут покрыты тестами и устранены в следующих шагах.

### Prompt Injection (до фиксов)

- Сохранён исходный контекст ассистента: `evidence/before/assistant_context_before.json` и после добавления вредоносного отзыва: `evidence/before/assistant_context_after_injection.json`.
- Прямой вызов опасных решений в `/assistant/execute` до фиксов демонстрировал их выполнение (см. раздел PoC выше). Эти артефакты сохранены в evidence/before/.

## Security-тесты (ожидаемое защищённое поведение)

Добавлены негативные тесты в `lab/test_security.py`. На исходном уязвимом сервисе они предсказуемо падают (12 из 12 новых кейсов), фиксируя следующие проблемы:

- /profile: доступ к чужим данным и SQLi через `id`
- /search: доступен клиентам, SQL без параметров
- /orders: доверие к переданному `price`
- /admin/export: авторизация по заголовку `X-Role`
- /files: чтение чужих чеков и приватной заметки (traversal внутри песочницы)
- /reviews/view: неэкранированный HTML (stored XSS)
- /assistant/execute: нет аутентификации и ограничения инструментов
- /debug/logs: открыт всем

Следующий шаг — внедрение фиксов и доведение тестов до зелёного состояния.
