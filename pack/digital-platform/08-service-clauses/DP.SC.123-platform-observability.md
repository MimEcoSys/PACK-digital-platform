---
id: DP.SC.123
name: Platform Observability (internal — наблюдаемость инфраструктуры для команды)
type: sc
status: draft
layer: L2-Platform
summary: "Минимально достаточный набор сигналов о здоровье 12 БД и ~10 сервисов для команды: реактивные ответы, проактивные алерты, retro-queries. SaaS-first (Better Stack owner external observability) + узкая projection в Neon для JOIN с business-данными."
consumer: Платформенная команда (R2 Архитектор, R5 CRM+оплата), AIST-бот (TG-алерты), WP-253 Ф9.6 reliability gate verifier
created: 2026-04-25
updated: 2026-11-14
related:
  realizes: [WP-244]
  uses: [DP.ARCH.004, DP.SC.020, DP.SC.122]
  realized_by_user_facing: [DP.SC.144]  # Public status page для пользователей — отдельное обещание
  complementary: [WP-217]  # AI-observability (поведение агента) — другой слой
  source: "WP-244 Ф0 IntegrationGate (drift-ревизия 25 апр 2026 после DP.ARCH.004 v2.3) + ArchGate (вариант β: Better Stack owner external + узкая internal_metrics в Neon)"
---

# DP.SC.123 — Platform Observability

## Обещание

> **Изменение 25 апр (после ArchGate):** scope этого SC сужен до **internal observability** (для команды). Public status page для пользователей вынесен в **[DP.SC.144 User-Facing Platform Health](DP.SC.144-user-facing-platform-health.md)**. ArchGate выбрал вариант β: SaaS-first (Better Stack owner external), узкая `health.internal_metrics` в Neon только для projection lag и custom business metrics, JOIN которых с business-таблицами невозможен в Better Stack.

**Кому:** платформенной команде (R2 Архитектор, R5 CRM+оплата), AIST-боту (как потребителю TG-алертов команде), WP-253 Ф9.6 reliability gate verifier (читает projection lag/custom metrics из `health.internal_metrics`).

**Зачем:** до этого аптайм наших сервисов измерялся ad-hoc (`wrangler tail` руками, grep по логам). Инциденты ловились по жалобам пользователей (WP-187 Ф-J: 401 Евгения 17 апр узнали через 6 часов; WP-183: GHA cron упал на 4.5 часа без алерта). Reliability gate WP-253 Ф9.6 («zero data loss + 0 ложных reject + p95 стабилен 48-72h») не верифицируем без структурированных метрик. Нет данных для SLA, нет корреляции с Anthropic деградацией.

**Что получит потребитель:**
- **Реактивный ответ** на запрос «жив ли сервис X?», «сколько 401 на tool Y за неделю?», «когда последний инцидент Z?», «какой p95 W?» — за **≤30s** через SQL-запрос к схеме `health` ИЛИ Grafana dashboard.
- **Проактивный алерт** в TG (через AIST Bot DM) при `>3 fail подряд` или `p95 > baseline × 2` — за **≤5 min** от события.
- **Retro-query за окно ≥7 дней:** структурированные логи в `health.mcp_request_logs`/`uptime_checks` хранятся минимум 30 дней — корневая причина инцидента находится без `wrangler tail`.

## Критерий приёмки

1. **Coverage:** все сервисы из DP.ARCH.004 §4.2 со статусом ✅ имеют запись в `health.service_registry` и пингуются с интервалом ≤5 мин.
2. **Latency reactive query:** `SELECT … FROM health.uptime_checks WHERE service=$1 AND checked_at > NOW() - INTERVAL '24h'` отрабатывает ≤30s на dataset 1 год × 10 сервисов × 5-min интервал (~10M строк).
3. **Alert latency:** от события `is_up=false × 3` до TG-сообщения ≤5 min (включая cron-период коллектора).
4. **Retro-query availability:** для любого MCP-tool вызова за последние 7 дней доступен `tool_name + status_code + error_code + user_id (ory_sub) + latency_ms` в `health.mcp_request_logs`.
5. **Reliability gate WP-253 Ф9.6:** запрос «projection lag p99 за 72h» возвращает значение ≤10 min И «p95 event-gateway за 72h» возвращает значение ≤500ms.
6. **PII-граница:** в `health.mcp_request_logs` нет полей `email`, `telegram_id`, `phone`, `payment_credentials`, request body. `user_id` = только `ory_sub` UUID. Соблюдение DP.ARCH.004 §2 П6.1.
7. **Anthropic correlation:** `health.anthropic_status_snapshots` обновляется ≤15 мин и доступен JOIN с `mcp_request_logs` по `time_bucket('5min', …)`.

## Архитектура (после ArchGate, вариант β)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Сервисы платформы (12 БД + ~10 workers/бот)                        │
│                                                                     │
│   ┌─────────────┐  ┌──────────────┐  ┌──────────────┐               │
│   │ event-      │  │ aist-bot     │  │ 4 MCP        │               │
│   │ gateway     │  │ (Railway)    │  │ Workers      │               │
│   │ (CF Worker) │  │              │  │ (CF Workers) │               │
│   └──────┬──────┘  └──────┬───────┘  └──────┬───────┘               │
│          │ structured     │                 │ structured            │
│          │ console.log    │ Langfuse        │ console.log           │
│          │ (whitelist)    │                 │ (whitelist)           │
└──────────┼────────────────┼─────────────────┼───────────────────────┘
           │                │                 │
           ▼                ▼                 ▼ Cloudflare Logpush
   ┌──────────────────────────────────────────────────────┐
   │ Better Stack (SaaS — owner of external observability)│
   │                                                      │
   │  ├ Uptime monitoring (probes 5-min из 13 регионов)   │
   │  ├ Status page (status.system-school.ru, см. DP.SC.144)  │
   │  ├ Logs aggregation (CF Workers через Logpush)       │
   │  ├ Composite uptime SLA «по девяткам» (см. DP.SC.144)│
   │  ├ Incidents detection (3+ fail подряд)              │
   │  └ Alert routing (webhook → AIST Bot)                │
   └─────────────────────┬────────────────────────────────┘
                         │
                         │ Webhook на инциденты
                         ▼
   ┌──────────────────────────────────────────────────────┐
   │ AIST Bot — TG DM команде (новый инцидент / recovery) │
   └──────────────────────────────────────────────────────┘

   ┌──────────────────────────────────────────────────────┐
   │ Платформенная Neon БД (на MVP — schema внутри;       │
   │  после P0/P1 — отдельная DB #8 health)               │
   │                                                      │
   │  schema `health` (узкая, только internal):           │
   │  └ internal_metrics                                  │
   │     • projection_lag_ms (от projection-worker        │
   │       DP.ROLE.034 для Ф9.6 reliability gate)         │
   │     • custom business metrics (events processed,     │
   │       reject_rate, schema validation failures)       │
   │                                                      │
   │  Опц. при появлении триггера JOIN observability ×    │
   │  business: `health.mcp_request_logs_projection`      │
   │  (узкая копия из Better Stack для SQL-JOIN с persona,│
   │  account, subscription_grants).                      │
   └─────────────────────┬────────────────────────────────┘
                         │
                         ▼
   ┌──────────────────────────────────────────────────────┐
   │ Grafana Cloud (datasource = Neon health.internal_*)  │
   │  + опц. datasource = Better Stack API (read-only)    │
   │  для unified dashboard «Platform Health»             │
   └──────────────────────────────────────────────────────┘
```

**Граница owner:**
- **Better Stack** — owner: probes, request logs, incidents, composite SLA, status page rendering, public subscriptions.
- **Neon `health.internal_metrics`** — owner: projection lag, custom business metrics (то, что Better Stack не знает, потому что они internal к нашему коду).
- **Grafana** — read-only consumer обоих (через datasource).
- **AIST Bot** — клиент Better Stack alert webhook, не owner данных.

**Когда узкая copy `mcp_request_logs_projection` ВСЁ-ТАКИ создаётся в Neon:**
- Триггер: появляется регулярная необходимость JOIN observability × business (например, security-аудит «какие user_id затронуты 401 за квартал, и кто из них с активной подпиской»).
- До триггера — JOIN'ы делаем через Better Stack export API (раз в неделю/квартал), не дублируем real-time.

## PII-граница

**Что пишем в `health.mcp_request_logs`:**
- `tool_name` (например, `personal_list_sources`)
- `status_code` (200/401/500)
- `error_code` (`unauthorized`/`jwt_invalid`/`backend_error`)
- `user_id` — **только `ory_sub` UUID** (нужен для инцидент-рекавери: «сколько user_X затронуто 401 за неделю»)
- `latency_ms`
- `request_id` (Cloudflare ray id для корреляции с tail)
- `request_at`

**Что НЕ пишем:**
- `email`, `telegram_id`, `phone` — PII, не нужны для observability
- `request_body`, `response_body` — могут содержать payment_credentials (DP.ARCH.004 §2 П6.1 = строже PII)
- `auth_token`, `session_id` — secrets

**Соответствие:** DP.ARCH.004 §2 П6.1 «PII vs payment_credentials». `user_id=ory_sub` входит в класс PII (доступ через JWT при retro-query, не в публичном dashboard).

## Режимы отказа

| Сбой | Поведение | Восстановление |
|------|-----------|----------------|
| `health` БД недоступна | Целевые сервисы продолжают работу. Логи Workers буферизуются Cloudflare Logpush (R2 destination, retry до 3 дней). uptime-collector retry'ит next-cycle. | Auto-recovery когда health БД доступна. Gap в данных = время недоступности. |
| Logpush недоступен | Tail Worker как fallback пишет напрямую в Neon. Если оба недоступны — request-level logs теряются (НЕ блокируем запросы пользователя). | Перезапуск Logpush через Cloudflare. Lost data = irrecoverable, но retro-query за оставшийся период работает. |
| Coллектор пинга timeout | Запись `is_up=false, error_msg='timeout'` в `uptime_checks`. После 3 подряд → `INSERT uptime_incidents`. | Сервис восстановился → `is_up=true` → `UPDATE uptime_incidents SET resolved_at=NOW()`. |
| TG алерты не доходят | Нет фолбэка — критично. Алерт остаётся в `health.alerts_pending` с retry. | Если `alerts_pending` накопилось >10 → автоматический e-mail (Q3+). |

## Out of scope

**Не обещаем (этим SC):**
- **Public status page для пользователей + composite uptime «по девяткам» + информирование пользователей (subscriptions, TG-канал)** — вынесено в **[DP.SC.144 User-Facing Platform Health](DP.SC.144-user-facing-platform-health.md)**. Реализуется тем же Better Stack instance, но обещание адресовано другому потребителю (пользователю, не команде).
- **AI-observability** (поведение агента, паттерны, P1-P11) — отдельный слой WP-217 (capture-bus + детекторы). Граница: WP-217 = семантические сигналы LLM-поведения; этот SC = синтаксические сигналы инфраструктуры.
- **APM / distributed tracing на уровне строк кода** — child WP-236 (OTel trace_id CHAR(32) в RAW→USER→LEARNING). Активация после первого production-инцидента, требующего кросс-слоевой трассировки.
- **Бизнес-метрики** (DAU, retention, conversion) — это journal/Metabase, не health.
- **Логи «всё подряд»** — пишем структурированные сигналы по контракту PII-границы. Free-form logging остаётся в Cloudflare/Railway tail (эфемерно).

## Митигация L2.6 Сохранность знаний (после ArchGate)

**Риск:** при смене SaaS теряется external observability history (probes, logs, incidents). 1 митигируемый ⚠️ из L2 шкалы ArchGate.

**Митигация:** квартальный export Better Stack snapshot → JSON в `DS-ecosystem-development/observability-archive/YYYY-Q*.json` (15 мин, ритуал /month-close в первый Пн квартала). Покрывает: composite uptime отчёты, инцидент-таймлайн, агрегаты latency. Logs полные не дублируются (объём, ценность падает).

## Связи

- **Реализуется ролью:** [DP.ROLE.035 Platform Observer](../02-domain-entities/DP.ROLE.035-platform-observer.md)
- **Реализуется WP:** [WP-244](../../../DS-my-strategy/inbox/WP-244-platform-observability.md)
- **Парный SC (для пользователей):** [DP.SC.144 User-Facing Platform Health](DP.SC.144-user-facing-platform-health.md) — composite SLA, public status page, информирование пользователей.
- **Использует данные от:** DP.SC.020 Event Ingest (event-gateway пишет structured logs), DP.SC.122 Rewards Projection (projection-worker latency для Ф9.6 reliability gate).
- **Карта БД:** DP.ARCH.004 v2.3 §3.8 (схема `health` минимизируется до `internal_metrics` + опц. `mcp_request_logs_projection` при триггере JOIN; перенос в отдельную DB #8 — после P0/P1).
- **Внешняя зависимость:** Better Stack SaaS (https://betterstack.com) — owner external observability data. ArchGate β зафиксирован 25 апр.
- **Комплементарно:** WP-217 AI-observability (другой слой наблюдаемости — поведение агента vs инфраструктура).
- **Child SC (при росте):** SC «Platform Notifier» (если alerter выделится в отдельную роль с маршрутизацией Slack/email/PagerDuty).

## Trace через 3 уровня

| Уровень | Что | Где |
|---------|-----|-----|
| **L4-Personal** (IWE) | capture-bus инциденты агента | `<repo>/inbox/incident-log-YYYY-MM.md` (HD «Лог рядом с исполнителем», DP.D.049) |
| **L2-Platform** (этот SC) | uptime + request logs + Anthropic status | schema `health` |
| **External** (Q3) | public-facing статус | SaaS (Better Uptime / Statuspage.io) |

Слои не дублируются (HD «Хранение факта ≠ Агрегация», WP-217 Ф22). Hub-and-Spoke: факт у исполнителя, агрегация в `health`, публикация во вне через SaaS.
