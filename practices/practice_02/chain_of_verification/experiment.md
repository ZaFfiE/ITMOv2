# Chain of Verification

- Проверяемый черновик или утверждение:
 Ревью TRAINING_PR.diff и соответствие метрикам practices/practice_01/problem.md.

## Запрос на проверку

Промпт (скопируй данный промпт сохрання шаблон в practices/practice_02/chain_of_verification/experiment.md, сохранив уникальность техники Chain of Verification, затем выполни задание в промпте):

Шаг 1 — Findings:
- Составь список наблюдений по diff с обязательными ссылками file:line.

Шаг 2 — Вопросы проверки:
- Для каждого наблюдения задавай минимум один вопрос, ответ на который подтвердит или опровергнет наблюдение.

Шаг 3 — Evidence и Checks:
- Для каждого риска сформулируй воспроизводимый check (шаги) и запиши evidence, который можно получить из diff/контекста.

Шаг 4 — Верификация метрик problem.md:
- Проверь: доля утверждений с file:line ≥ 90%, «Рисков > 3» — 0, у каждого риска ≥1 check.

Шаг 5 — Итог и инструкции к журналу:
- Дай итоговую оценку и заполни @practices/practice_02/chain_of_verification/experiment.md согласно контексту. Также скопируй данный промпт без изменений в practices/practice_02/chain_of_verification/experiment.md, сохранив уникальность техники Chain of Verification  . Обнови  @practices/practice_02/prompts.md в строке «Chain of Verification» с конкретными изменениями, проверками и отклонениями.

Формат ответа:
- Findings (file:line), Questions, Checks, Evidence, Metrics, Fixes to P1.

## Вопросы проверки и evidence

| Вопрос | Источник или проверка | Результат |
|---|---|---|
| Возвращает ли ReviewService.review только поле comment? | Evidence: app/review_service.py:22. Check: вызвать метод/endpoint и проверить ключи ответа. | Да, только comment. |
| Есть ли обращение к payload["diff"] без валидации наличия? | Evidence: app/api.py:37. Check: POST /api/reviews с {}. | Да, возможен KeyError/500. |
| Включается ли полный diff в prompt без ограничений размера? | Evidence: app/review_service.py:20; app/api.py:37. Check: передать diff > 20000 символов. | Да, ограничений нет. |

## Исправленный результат

- Findings (file:line):
  - app/review_service.py:19 — добавлен метод review(self, diff: str) -> dict[str, str].
  - app/review_service.py:20 — в prompt включается полный diff: f"Review this pull request and find problems:\n{diff}".
  - app/review_service.py:22 — метод возвращает только {"comment": answer}.
  - app/api.py:35-37 — добавлен POST /api/reviews, читающий payload["diff"] без валидации наличия и длины.

- Questions:
  - К app/review_service.py:22 — Ожидается ли структурированный ответ (summary/risks/checks) или допускается только comment?
  - К app/api.py:37 — Что происходит при отсутствии ключа diff в теле запроса?
  - К app/review_service.py:20 — Есть ли лимит на размер diff, прежде чем включать его в prompt?

- Risks, Evidence, Checks:
  - R1 — Потенциальный KeyError при отсутствии поля diff в payload.
    Evidence: app/api.py:37 (доступ по ключу payload["diff"]).
    Check: POST /api/reviews с {} — ожидать 500/исключение из-за отсутствия ключа.
  - R2 — Нет ограничения размера diff; большой diff целиком включается в prompt.
    Evidence: app/api.py:37; app/review_service.py:20 (diff передаётся в prompt без отсечки).
    Check: отправить diff длиной > 20000 символов; зафиксировать, что он уходит в LLM.
  - R3 — Неструктурированный ответ: возвращается только comment.
    Evidence: app/review_service.py:22.
    Check: POST /api/reviews с валидным diff; проверить, что ответ содержит только ключ comment.

- Metrics (verification of practices/practice_01/problem.md):
  - Доля утверждений с file:line: 4/4 findings = 100% (>= 90%) — выполняется.
  - Рисков > 3: 0 (ровно 3 риска) — выполняется.
  - У каждого риска ≥1 check: 3/3 — выполняется.

## Что изменили в исходном артефакте

- Файл и раздел: practices/practice_01/prompts.md — раздел «7. Проверки и evidence».
- Изменение: уточнили правило — каждое утверждение (findings и risks) должно иметь ссылку на конкретный файл и строку diff.
- Что отклонили: общие замечания без file:line и без evidence (см. practices/practice_01/prompts/P1_01.md и запись P1-01).

Скрытые рассуждения модели не сохраняйте; нужны только вопросы, evidence и исправленный результат.
