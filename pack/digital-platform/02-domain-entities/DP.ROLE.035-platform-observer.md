---
id: DP.ROLE.035
name: Platform Observer
type: role-description
status: draft
valid_from: 2026-04-25
summary: "Роль наблюдателя за здоровьем платформы — оркеструет Better Stack (external observability owner), AIST Bot (TG-алерты команде + автопостинг канал), Neon `health.internal_metrics` (узкая projection для JOIN с business)."
related:
  specializes: [U.RoleAssignment]
  component_of: [DP.ROLE.001]
  realizes: [DP.SC.123, DP.SC.124]  # internal observability + user-facing health
  uses:
    - DP.ARCH.004
    - DP.SC.020   # event-gateway как источник structured logs
    - DP.SC.122   # rewards projection как источник latency-метрик
external_dependency: "Better Stack SaaS — owner external observability data (probes, logs, incidents, composite SLA, status page rendering, public subscriptions). ArchGate β зафиксирован 25 апр 2026."
created: 2026-04-25
updated: 2026-11-14
---

# Platform Observer (DP.ROLE.035)

> **Kind:** Infrastructure Role (инфраструктурная роль, не доменная).
> **Owner Role:** Платформенная команда (R2 Архитектор + R5 CRM+оплата как стейкхолдеры алертов).

## 1. Миссия

Быть **единым агрегатором здоровья платформы**. Знать в любой момент: жив ли каждый сервис, какова его latency p50/p99, сколько ошибок 401/500 за окно T, коррелирует ли деградация с внешними зависимостями (Anthropic, Neon, Cloudflare). Инициировать алерты команде до жалобы пользователя.

**Граница:** observability инфраструктуры (синтаксические сигналы — HTTP, SQL, latency). НЕ AI-observability (поведение агента, паттерны P1-P11 — это [WP-217](../../../DS-my-strategy/inbox/WP-217-iwe-maintenance.md), другая роль).

## 2. Обязанности

| Обязанность | Метод | Триггер |
|-------------|-------|---------|
| Пинг каждого сервиса из `health.service_registry` | HTTP GET с timeout=10s | Каждые 5 мин (cron) |
| Запись результата пинга в `health.uptime_checks` | INSERT (latency_ms, status_code, is_up, error_msg) | После каждого пинга |
| Детекция инцидента | 3+ подряд `is_up=false` | Каждый пинг с проверкой окна |
| Запись инцидента в `health.uptime_incidents` | INSERT (started_at, severity), позже UPDATE (resolved_at, duration_min) | На 3-й fail / на восстановление |
| Приём structured logs от MCP Workers | Cloudflare Logpush (R2 → Neon) ИЛИ Tail Worker | Каждый MCP-tool вызов |
| Запись request-logs в `health.mcp_request_logs` | INSERT через batch (Logpush flushes) | Каждые 60s или 1000 событий |
| Поллинг Anthropic status | GET `https://status.anthropic.com/api/v2/summary.json` → INSERT `anthropic_status_snapshots` | Каждые 15 мин |
| Эмиссия TG-алерта при инциденте | POST в AIST Bot DM команды | На детекцию инцидента (`>3 fail`) или восстановление |
| Утренний digest на Day Open | SQL aggregate за вчера → формат для AIST Bot | Cron 08:00 (или Day Open hook) |
| **НЕ публикует наружу** — public status page = отдельный SaaS | — | — |

## 3. Полномочия

- **Пишет** в схему `health` (5 таблиц) — единственный writer (OwnerIntegrity).
- **Читает** structured logs от Workers (через Cloudflare Logpush destination).
- **Читает** Anthropic status (внешний публичный API).
- **Инициирует** TG-сообщения через AIST Bot DM команде (как клиент бота, не writer его БД).
- **Не интерпретирует** содержимое сообщений сервисов — пишет как есть с PII-фильтром на ingress.
- **Не блокирует** запросы пользователя — observability вне критического пути (writeback retry при недоступности `health`).

## 4. Границы роли

| Делает | НЕ делает |
|--------|-----------|
| Пингует все сервисы из реестра | Не модифицирует сами сервисы (read-only HTTP probe) |
| Пишет request-логи MCP Workers | Не пишет тело запроса/ответа (PII-граница, см. DP.SC.123 §PII) |
| Алертит команду в TG | Не алертит конечных пользователей (это public status page = SaaS) |
| Хранит данные ≥30 дней | Не хранит вечно — старше 90 дней архивируется/агрегируется |
| Коррелирует с Anthropic status | Не коррелирует с другими внешними (Cloudflare, Neon) — только Anthropic в MVP |
| Готовит данные для Grafana | Не визуализирует сам — Grafana отдельный read-consumer |
| Принимает фактические сигналы | Не предсказывает (нет ML/anomaly detection в MVP) |

## 5. Исполнители (после ArchGate β, 25 апр)

Роль реализуется **пятью компонентами**, большинство из которых SaaS (Better Stack), а не наш код. Композиция: Better Stack делает heavy-lifting, мы оркестрируем + дублируем то, что Better Stack не покрывает.

| # | Implementation | Что делает | Где работает | Когда активируется |
|---|----------------|------------|--------------|---------------------|
| **A** | **Better Stack monitors** | HTTP probes 5-min из 13 регионов; детекция 3+ fail подряд = incident; composite SLA расчёт по multiplicative product | Better Stack SaaS | Ф2 WP-244 (W18, ~1h конфигурация) |
| **B** | **Cloudflare Workers Logpush** | Перехват `console.log` от 4 MCP Workers + event-gateway → Better Stack Logs (R2 fallback при downgrade) | Cloudflare native (config 1 раз) | Ф3 WP-244 (W18-W19, ~1h) |
| **C** | **Better Stack status page** | Public rendering на status.system-school.ru (CNAME); composite uptime «по девяткам»; public subscriptions (email, RSS) | Better Stack SaaS | Ф2 WP-244 (вместе с monitors) |
| **D** | **Internal metrics writer** (наш код) | event-gateway / projection-worker → INSERT в `health.internal_metrics` (projection lag, custom business metrics, schema reject rate) | event-gateway (CF Worker) + projection-worker (Python Railway) — добавление 5-10 строк в существующий код | Ф3b WP-244 (W19, ~1h, координация с WP-253 Ф9.6) |
| **E** | **AIST Bot status poster** | Receives Better Stack webhook на incident lifecycle → постит в TG-канал @aisystant_status (для пользователей) + DM команде | aist-bot (Railway), новый handler ~50 LOC | Ф4 WP-244 (W19-W20, ~1.5h) |

**Что НЕ делаем сами (выкинуто после ArchGate):**
- ~~uptime-collector в Railway cron~~ (Better Stack делает probes сам, лучше)
- ~~Anthropic poller~~ (Better Stack умеет third-party status — настраивается как monitor)
- ~~SQL таблицы service_registry / uptime_checks / uptime_incidents / mcp_request_logs / anthropic_status_snapshots~~ (всё в Better Stack)
- ~~standalone alerter cron~~ (Better Stack alert routing встроен)

**Что осталось нашим кодом:**
- D (`internal_metrics` writer — единственный, что Better Stack не знает: business metrics)
- E (TG-канал автопостер — Better Stack умеет webhook, но интеграция с нашим TG-каналом через AIST Bot требует ~50 LOC handler)

**Важно:** все пять — реализации одной роли DP.ROLE.035. Если в будущем status poster выделится в сложный routing (Slack, email lists, PagerDuty) — отделяется как DP.ROLE.NNN «Platform Notifier» с собственным SC.

## 6. Связи

**Вход (потребитель обещаний других ролей):**
- **DP.ROLE.032 Event Ingester** — event-gateway шлёт structured logs через `console.log`, Logpush перехватывает.
- **DP.ROLE.034 Rewards Projector** — projection-worker шлёт latency/lag метрики через тот же канал.
- **MCP Workers** (gateway-mcp, personal-knowledge-mcp, knowledge-mcp, digital-twin-mcp) — каждый Worker логирует tool-invocation в `console.log`, Logpush собирает.
- **AIST Bot** (TG handler) — внешний source: Langfuse trace + custom events (AI-observability отдельным каналом, см. WP-217 + DP.ROLE.NNN «Behavior Observer» если будет создан).
- **External:** Anthropic status API, Cloudflare Logpush, Railway cron scheduler.

**Выход (поставщик обещаний другим ролям):**
- **Команда** (R2 Архитектор, R5 CRM+оплата) — read-consumer Grafana dashboard «Platform Health» + получатели TG-алертов.
- **AIST Bot** — receives DM-сообщения для пересылки команде (бот = транспорт, не источник).
- **Public Status Page (Q3+)** — **готовый SaaS** читает `health.service_registry` + `uptime_checks` (read-replica или API).
- **WP-253 Ф9.6 Reliability gate** — verifier читает `health.*` для PASS/FAIL решения по «zero data loss + p95 + projection lag» за 48-72h.

## 7. Measurable health (мета-наблюдаемость самой роли)

> Observer обязан наблюдать за собой — иначе деградация observability не видна.

- **Coverage:** % сервисов из DP.ARCH.004 §4.2 ✅, имеющих ≥1 запись в `uptime_checks` за последние 10 мин — алерт при <100%.
- **Logpush lag:** время между Cloudflare event и появлением в `mcp_request_logs` — алерт при >5 мин.
- **Alerter freshness:** время между `uptime_incidents.started_at` и TG-сообщением — SLO ≤5 мин.
- **PII reject count:** сколько сообщений отбито на ingress по PII-фильтру (должно быть 0 — иначе bug в источнике).
- **Anthropic poller success rate:** % успешных GET статусов — алерт при <95% за час (может означать что-то не так с публичным API).

## 8. Reference

- **Обещания (2):** [DP.SC.123 Platform Observability](../08-service-clauses/DP.SC.123-platform-observability.md) (internal, для команды) + [DP.SC.124 User-Facing Platform Health](../08-service-clauses/DP.SC.144-user-facing-platform-health.md) (public, для пользователей).
- **Карта БД:** DP.ARCH.004 v2.3 §3.8 (схема `health` минимизируется до `internal_metrics` после ArchGate; перенос в отдельную DB #8 — после P0/P1).
- **Реализация (после ArchGate β):**
  - **Better Stack instance** (SaaS, https://betterstack.com) — owner external observability data + status page + alerting. Аккаунт настраивается в Ф2.
  - **Cloudflare Logpush config** на 4 MCP Workers + event-gateway — destination = Better Stack Logs ingest. Настройка в Ф3.
  - **`health.internal_metrics`** — узкая Neon таблица, writer = event-gateway / projection-worker (5-10 строк добавления в существующий код). Создаётся в Ф3b.
  - **AIST Bot status poster handler** — `aist_bot_newarchitecture/src/handlers/status_poster.py` (~50 LOC), webhook receiver. В Ф4.
  - **Quarterly export script** — митигация L2.6 (см. DP.SC.123 §Митигация). `DS-ecosystem-development/scripts/observability-archive.sh` запускается ритуалом /month-close (1 раз/квартал, 15 мин).
- **Родительский РП:** [WP-244 Platform Observability](../../../DS-my-strategy/inbox/WP-244-platform-observability.md)
- **Координация:** WP-217 (AI-observability — другой слой), WP-250 (Q2 maintenance — режим работы), WP-253 (event-gateway источник, Ф9.6 потребитель `internal_metrics`), WP-236 (child WP-244 — OTel trace_id, активация после первого production-инцидента кросс-слоевой трассировки).
