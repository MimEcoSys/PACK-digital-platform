---
id: DP.FM.123
name: "Reverse proxy режет long-running HTTP-handler — config application-timeout врёт"
type: failure-mode
domain: digital-platform
pack: PACK-digital-platform
trust: observed
epistemic_stage: formalized
category: networking
severity: major
valid_from: 2026-05-30
related:
  see_also: [DP.FM.092, DP.FM.099]
tags: [http, reverse-proxy, timeout, long-running, async, polling, cloudflare, nginx]
source: "session 2026-05-30 WP-201 Ф3.4 mcp_tools (peer-session 30, 02-writer.md)"
schema_version: 1
---

# DP.FM.123 — Reverse proxy режет long-running HTTP-handler — config application-timeout врёт

## Описание

Long-running синхронный HTTP-handler (LLM-orchestration, file-processing, long DB-migration, batch-job) за reverse proxy получает upstream cut-off **раньше** application timeout. `request_timeout_s=180` в коде создаёт ложное ощущение «у нас 180 секунд» — на деле Cloudflare режет на 100s, nginx default — на 60s, Railway/Vercel ~60s. Клиент получает 504/connection-reset, а backend-handler продолжает работать → orphan rows в state-таблице.

Failure mode **скрытый:** код выглядит корректным, конфиг — большим, smoke-test на localhost проходит. Проявляется только под прод-прокси с теми же или меньшими таймаутами.

## Симптом

- Клиент видит 504 Gateway Timeout / connection reset при работе, которая «должна была успеть» по конфигу.
- В БД остаются orphan rows (state `processing`/`running`) от handler'ов, продолживших работу после cut-off.
- Логи backend: handler завершился успешно через N секунд (N > proxy timeout) — то есть «работа сделана», но клиент об этом не узнал.

## Механизм

1. Architect добавляет конфиг `request_timeout_s=180` на стороне application.
2. Handler опирается на конфиг для time-budgeting (LLM call, DB query).
3. Запрос идёт через reverse proxy (Cloudflare/nginx/Railway/Vercel) с собственным `proxy_read_timeout`.
4. Proxy timeout (например, 100s) < application timeout (180s).
5. Через 100s proxy режет соединение → клиент видит 504.
6. Backend handler ещё работает, доделывает работу, пишет state — клиент уже отключён.
7. Retry клиента → новый run_id → дублирование работы или race на state.

## Canonical fix

POST возвращает **202 Accepted** + `Location: /v1/runs/{run_id}` header + `run_id` в body **немедленно**. Работа стартует через `asyncio.create_task` и tracked в `app.state.background_tasks` (или эквивалент). Клиент poll'ит `GET /v1/runs/{run_id}` с собственным timeout. Дополнительно: внутренний `background_task_timeout_s` (например, 200s) как кэп на task — не для клиента, для cleanup.

**Дополнение (РП-614, служба Image, 2026-10-29): срок жизни задания.** Если задания стоят в очереди с ограниченным пулом (кейс: 3 потока, видео по минутам), задание, простоявшее слишком долго, нужно снимать из очереди до выполнения. Иначе клиент, давно бросивший ожидание по сроку, всё равно «оплачивает» выполнение: в кейсе задание после долгого стояния в очереди было выполнено и кредиты списаны (длительность в записи названа, при записи карточки не проверялась). Связано с DP.FM.703 (возврат квоты при тайм-ауте ожидания). Код службы не проверялся.

## Тест применимости

«HTTP-handler работает >30s за reverse proxy?» — да → переписать на 202+polling, не верить config'у с большим timeout.

## Diagnostic

504 при «работа должна была успеть по конфигу» + handler в логах завершился позже клиентского обрыва → red flag.

## Применимо к

LLM-pipelines, file-processing, long DB-migrations, batch-jobs, agent-runner endpoints, любые synchronous HTTP-handlers >30s за proxy/CDN/load-balancer.