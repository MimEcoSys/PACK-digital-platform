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
  see_also: [DP.FM.092, DP.FM.099, DP.FM.703, DP.FM.462, DP.FM.779]
tags: [http, reverse-proxy, timeout, long-running, async, polling, cloudflare, nginx]
source: "session 2026-05-30 WP-201 Ф3.4 mcp_tools (peer-session 30, 02-writer.md)"
schema_version: 1
---

# DP.FM.123 — Reverse proxy режет long-running HTTP-handler — config application-timeout врёт

## Описание

Long-running синхронный HTTP-handler (LLM-orchestration, file-processing, long DB-migration, batch-job) за reverse proxy получает upstream cut-off **раньше** application timeout. `request_timeout_s=180` в коде создаёт ложное ощущение «у нас 180 секунд» — на деле Cloudflare режет на 100s, nginx default — на 60s, у Railway и Vercel свои пределы (в наблюдённом случае 2026-11-09 Railway рвал запрос на 300 с; значения платформ меняются, сверять с их документацией на дату). Клиент получает 504/connection-reset, а backend-handler продолжает работать → orphan rows в state-таблице.

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

**Дополнение (РП-568 Ф12, ночь 08–09.11.2026): платный поставщик модели за посредником.** Хостинг шлюза языковых моделей (Railway) рвал любой запрос на 300 с. Модель у поставщика (OpenRouter) всё равно дописывала длинный ответ, и поставщик брал за него деньги, а программа получала ошибку и через 5 минут повторяла запрос. Каждый повтор тоже оплачен: 55 оборванных ответов, около $30 из $52,6 счёта; лимит ключа $50 кончился раньше срока. Ошибка у клиента ≠ «не потрачено»: обрыв происходит на участке клиент–шлюз, а не у поставщика, и брошенная работа оплачивается так же, как в дополнении про срок жизни задания выше. Отличие от общего случая — прямые деньги за каждую попытку, поэтому обрыв на фиксированной границе времени повторять нельзя: повтор упрётся в ту же границу (классификация повторов — DP.FM.229, «Рецидив 2026-11-09»). Лечение в случае: длинные задания — мимо посредника с жёстким таймаутом (подписка или потоковая передача), внутренняя сеть между шлюзом и прокси моделей, без повтора на обрыв по времени. Недоучёт таких ответов в журнале шлюза — DP.FM.779. Источник: session-transcript 2026-11-09; DS-ai-systems e79b8a4, DS-platform-infra bed7a84; извлечение `DS-my-strategy/inbox/extraction-reports/2026-11-14-inbox-check-3.md`, кандидат 2; решение пилота 17.11.2026.

## Тест применимости

«HTTP-handler работает >30s за reverse proxy?» — да → переписать на 202+polling, не верить config'у с большим timeout.

## Diagnostic

504 при «работа должна была успеть по конфигу» + handler в логах завершился позже клиентского обрыва → red flag.

## Применимо к

LLM-pipelines, file-processing, long DB-migrations, batch-jobs, agent-runner endpoints, любые synchronous HTTP-handlers >30s за proxy/CDN/load-balancer.