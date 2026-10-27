# Отчёт 2. Повторные атаки после исправлений

## Результаты тестов «после»

- Команда: `make test`
- Все тесты (исходные + добавленные security-тесты) прошли успешно: 29 тестов, OK
- Лог прогона: см. `evidence/after/make_test.log`

Кратко, чего добились фиксы:
- /profile: только профиль текущей сессии, параметризованный запрос
- /search: только staff, параметризованный LIKE
- /orders GET: клиент видит только свои, staff — все
- /orders POST: цена строго из каталога
- /admin/export: только staff из сессии, заголовок роли игнорируется
- /files: клиенту доступен только собственный чек, traversal/чужие файлы запрещены
- /reviews/view: HTML экранируется
- /assistant/execute: требует сессию; клиент — только свой чек; export_profiles — только staff; delete_tree запрещён
- /debug/logs: доступ только для staff

Дальше: повторим PoC из отчёта 1 и убедимся, что эксплуатация не проходит (будет приложено в этом же отчёте после прогонов ассистента и ручных проверок «после»).

## Prompt Injection (после фиксов)

- Контексты ассистента после добавления вредоносного отзыва сохранены: `evidence/after/assistant_context_after_injection.json`.
- Принудительная передача опасных решений:
  - `export_profiles` как клиент → 403, `evidence/after/assistant_execute_export_after.json`.
  - `delete_tree` как клиент → 403, `evidence/after/assistant_execute_delete_after.json`.
  - Разрешённое действие: `read_file` на собственный чек клиента → 200, `evidence/after/assistant_execute_read_own_after.json`.
- Вывод: независимо от posлушания модели, сервер применяет авторизацию и не допускает опасные действия.

## Ссылки на тесты и покрытие кейсов

- Набор security-тестов: `lab/test_security.py`
- Ключевые проверки:
  - Профили и SQLi: `test_profile_returns_only_session_user`, `test_profile_ignores_injection_and_id`
  - Поиск: `test_search_forbidden_for_customer`, `test_search_allowed_for_staff_only`
  - Админ-экспорт: `test_admin_export_requires_staff_session`
  - Цена заказа: `test_order_price_from_catalog`
  - Файлы: `test_files_cannot_read_others_receipt`, `test_files_cannot_access_private_note`
  - XSS: `test_reviews_view_escapes_html`
  - Ассистент: `test_assistant_requires_auth`, `test_assistant_customer_only_own_receipt`, `test_assistant_staff_can_export_but_not_delete`
  - Логи: `test_debug_logs_only_staff`

## Краткие выводы

- Функциональность сохранена: легальные кейсы пользователя и staff проходят (см. исходные тесты).
- Эксплуатация уязвимостей из отчёта 1 больше не воспроизводится; серверная логика удерживает границы стенда и ролей.
