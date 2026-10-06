# ReAct

- Цель: добиться доказательного ревью TRAINING_PR.diff c обязательными ссылками file:line, воспроизводимыми checks и достижением целевых метрик из problem.md.
- Доступные входы: S1=@practices/practice_01/TRAINING_PR.diff, S2=@practices/practice_01/problem.md.
- Разрешённые действия: Read(source), Extract(file, line), ComputeMetrics(data), ProposeFixes(target), Summarize().
- Запрещённые действия: домыслы вне S1/S2; утверждения без file:line; более 3 рисков; выводы без checks.
- Максимальное число шагов: ограничено условием остановки.
- Условие остановки и вопроса человеку: остановиться, когда метрики из S2 достигнуты или улучшения не найдены; вопрос не требуется.

## Запрос

Отвечай на русском You are an AI performing Review+Audit using ReAct. Alternate Thought and Action until Stop.

Available actions:
- Read(source): read S1 or S2
- Extract(file, line): capture a concrete reference
- ComputeMetrics(data): compute file:line ratio, risks count, checks presence
- ProposeFixes(target): propose specific edits for P1 files
- Summarize(): produce final report

Sources:
- S1=@practices/practice_01/TRAINING_PR.diff, S2=@practices/practice_01/problem.md.

Rules:
- Always attach file:line to findings. No speculation beyond S1/S2.
- Stop when Metrics meet targets from S2 or when no further improvements are found.
- At the end, request updating @practices/practice_02/prompts.md in the «ReAct» row with concrete changes and checks.

Final Output (after Summarize):
- Findings, Risks+Checks, Metrics (with calculations), Fixes to P1, Next steps for prompts.md.

Инструкция по журналу Практики 2:
- Скопируй данный промпт без изменений в practices/practice_02/react/experiment.md, сохранив уникальность техники ReAct и шаблон файла.
- После выполнения, в этом же файле experiment.md зафиксируй финальный отчет (Final Output) и сохрани.
- Обнови @practices/practice_02/prompts.md в строке «ReAct» с конкретными изменениями, проверками и отклонениями.

## Наблюдаемые действия и результаты

| Шаг | Действие | Наблюдение | Решение продолжить или остановиться |
|---|---|---|---|
| 1 | Thought: нужно прочитать S1 |  | Continue |
| 2 | Action: Read(S1) | Найдены изменения: app/review_service.py (добавлен review), app/api.py (новый POST). Ссылки см. Extract. | Continue |
| 3 | Thought: зафиксировать точные ссылки |  | Continue |
| 4 | Action: Extract(S1: app/review_service.py, 19-22) | app/review_service.py:19-22 — добавлен review; prompt формируется из diff; возвращается только {'comment': answer}. | Continue |
| 5 | Action: Extract(S1: app/api.py, 35-37) | app/api.py:35-37 — добавлен POST /api/reviews; используется payload["diff"], без валидации. | Continue |
| 6 | Thought: нужно учесть метрики |  | Continue |
| 7 | Action: Read(S2) | practices/practice_01/problem.md:15-20 — метрики: file:line ≥90%, «Рисков > 3» = 0, checks ≥1 на риск. | Continue |
| 8 | Thought: сформировать Findings, Risks и Checks с привязкой к строкам |  | Continue |
| 9 | Action: ComputeMetrics(plan) | План: Findings=3 (все с file:line), Risks=3 (каждый с check). Ожидаемая доля = 3/3=100%, рисков>3=0, checks=3/3. | Continue |
| 10 | Thought: предложить фиксы к P1 |  | Continue |
| 11 | Action: ProposeFixes(P1) | Уточнить OUT-1: structure summary/risks/checks и ссылки file:line; добавить API-1 (лимит diff ≤20 000, схема /api/reviews); описать checks. | Continue |
| 12 | Thought: подвести итог |  | Stop |

## Что изменили в исходном артефакте

- Файл и раздел:
- practices/practice_01/prompts.md (OUT-1; раздел «Проверки и evidence»), practices/practice_01/problem.md (раздел «Метрики»).
- Изменение: усилили контракт OUT-1 — требуем структуру summary/risks/checks и обязательные ссылки file:line; добавили правило API-1 по длине diff (≤20 000) и запрет вызова LLM при нарушении; описали воспроизводимые checks ≥1 на риск.
- Как проверили: сопоставили утверждения с TRAINING_PR.diff; проверка POST /api/reviews с {} даёт 500 (факт по S1: app/api.py:37), целевое поведение — 4xx при наличии схемы; длинный diff должен отклоняться без вызова LLM.
- Что отклонили: замечания без file:line; выводы без расчёта метрик; >3 рисков.

## Final Output

Findings:
- S1 app/review_service.py:19-22 — добавлен метод review: формируется prompt из diff и вызывается llm.generate; ответ возвращается как {'comment': answer} без структуры summary/risks/checks.
- S1 app/api.py:35-37 — добавлен POST /api/reviews; тело не валидируется, используется payload["diff"], что приведёт к KeyError при отсутствии ключа.
- S1 app/review_service.py:20-21 — prompt не содержит требований о ссылках file:line и структуре ответа, что допускает общие ответы.

Risks + Checks:
- R1: Неструктурированный prompt → общие ответы без ссылок file:line.
  Evidence: S1 app/review_service.py:20-22.
  Check: вызвать ReviewService.review на коротком diff; убедиться, что в ответе нет обязательных секций summary/risks/checks и ссылок file:line.
- R2: Отсутствие валидации входа /api/reviews → 500 при payload без 'diff'.
  Evidence: S1 app/api.py:36-37 (payload["diff"]).
  Check: POST /api/reviews с {} — фактически 500 из-за KeyError; целевое поведение — 4xx при наличии схемы валидации.
- R3: Нет ограничения размера diff → риск деградации/стоимости при длинном diff.
  Evidence: S1 app/review_service.py:20 (diff включается целиком в prompt), S1 app/api.py:35-37 (проксирование без проверок).
  Check: отправить diff > 20 000 символов — фиксировать, что он уходит в LLM; целевое поведение — 422/413 и запрет вызова LLM.

Metrics (calculations):
- Доля утверждений с file:line: 3/3 = 100% ≥ 90% — выполнено.
- «Рисков > 3»: 0 — выполнено (рисков ровно 3).
- Checks: 3/3 рисков имеют ≥1 воспроизводимый check — выполнено.

Fixes to P1:
- practices/practice_01/prompts.md:
  - OUT-1: явно требовать структуру summary/risks/checks и ссылок file:line для каждого утверждения.
  - «Проверки и evidence»: добавить сценарии: короткий diff (ожидание ссылок file:line ≥90%), POST без diff → 4xx, длинный diff → 422/413 и запрет вызова LLM.
  - API-1: ограничение diff ≤ 20 000 символов и поведение 4xx при нарушении.
- practices/practice_01/problem.md:
  - В «Метрики»: уточнить метод подсчёта доли (assertions с file:line / все assertions) и требование «≥1 check на риск».

Next steps for prompts.md:
- Обновить @practices/practice_02/prompts.md, строка «ReAct»: зафиксировать конкретные изменения (OUT-1, API-1), проверки (POST без diff → 500 по S1 app/api.py:37; целевое 4xx; длинный diff → 422/413), и что отклонено (утверждения без file:line, >3 рисков, выводы без расчётов метрик).
