---
id: DP.ROLE.032
name: Регистратор событий
name_ru: Регистратор событий
name_en: Event Ingester
aliases:
  - Event Ingester
type: role-description
status: draft
valid_from: 2026-04-24
summary: "Роль единого приёмника доменных событий обучения от всех источников — гарантирует идемпотентность, валидацию и защиту от PII на входе в learning.domain_event"
related:
  specializes: [U.RoleAssignment]
  component_of: [DP.ROLE.001]
  realizes: [DP.SC.020]
  uses:
    - DP.ARCH.004
created: 2026-04-24
updated: 2026-11-22
---

# Регистратор событий (DP.ROLE.032)

> **Прежнее имя** — «Event Ingester»; переименовано решением пилота 22.11.2026 (DP.ROLE.001 §3.6, РП-616 Ф4).

> **Kind:** Infrastructure Role (инфраструктурная роль, не доменная).
> **Owner Role:** Платформенная команда (source-of-truth — карта БД DP.ARCH.004).

## 1. Миссия

Быть **единственной точкой входа** для доменных событий обучения в Neon-архитектуру. Изолировать источники от деталей хранения, гарантировать идемпотентность и валидность, защищать БД от утечки PII.

## 2. Обязанности

| Обязанность | Метод | Триггер |
|-------------|-------|---------|
| Приём POST /events от источников | DP.SC.020 §Архитектура | Каждый запрос от LMS/бота/MCP/скилла/aggregator |
| Валидация payload по JSON Schema | Schema lookup по `(source, event_type)` | Каждый POST |
| PII reject на ingress | Whitelist полей в schema | Каждый POST с недопустимым полем |
| Дедупликация по `(source, external_id)` | UNIQUE index + ON CONFLICT DO NOTHING | Каждый POST с external_id |
| Retry handshake при недоступности Neon (MVP) | 503 → источник делает exponential backoff | Neon connection failure |
| Буферизация через CF Queues (Phase 2) | CF Queues поверх event-gateway | При росте нагрузки ×100 или кросс-БД проекции |
| Эмиссия trace в Langfuse | OTel instrumentation | Каждый POST |

## 3. Полномочия

- **Пишет** в `learning.domain_event` — единственный writer этой таблицы (OwnerIntegrity).
- **Отвергает** запросы с невалидным payload (HTTP 400).
- **Не интерпретирует** event_type — передаёт в domain-слой (projection-worker) как есть.
- **Не изменяет** payload после валидации (immutability).

## 4. Границы роли

| Делает | НЕ делает |
|--------|-----------|
| Принимает события | Не инициирует события (только источники) |
| Валидирует форму (schema) | Не валидирует смысл (это projection-worker при чтении) |
| Дедуплицирует по ключу | Не rebuild'ит проекции (rewards, leaderboards) |
| MVP: возвращает 503 при отказе Neon (источник retry'ит) | Не буферизует события в MVP (CF Queues добавляется в Phase 2) |
| Лог в security.reject_log при PII | Не решает кому показывать события (это Gateway MCP с JWT) |

## 5. Исполнители

| Исполнитель | Когда | Режим |
|-------------|-------|-------|
| **event-gateway** (Cloudflare Worker) | Prod. Все источники | HTTP endpoint, 24/7 |
| Human (разработчик) | Разовый backfill / ручной replay | CLI-скрипт с флагом `--source=*` |

## 6. Связи

**Вход (потребитель обещаний других ролей):**
- **Bridge-1 Worker** (DP.ROLE.033 — создаётся вместе с Ф9.3 WP-253) — читает LMS, POST-ит в Event Ingester.
- **Bot Event Writer** (внутри aist-bot, после рефакторинга Ф9.5) — POST-ит события команд/слотов.
- **MCP Tool Handlers** (knowledge-mcp, twin-mcp) — POST-ят tool-invocation события.
- **IWE Skill Events** (`/personal-guide-start`, capture-flow) — POST-ят skill events.
- **Journal Aggregator** (WP-253 Ф9.6) — читает `journal.event` raw, POST-ит derived events.

**Выход (поставщик обещаний другим ролям):**
- **Rewards Projection** ([DP.ROLE.034](./DP.ROLE.034-rewards-projector.md) — draft с 24 апр, WP-253 Ф9.3) — LISTEN на learning.domain_event, пишет в rewards.point_balances.
- **Indicators Calculator** — читает learning.domain_event для baseline/RCS.
- **Analytics/Metabase** — read-replica learning.domain_event.

## 7. Measurable health

- **Ingress rate** (events/min) per source — в Grafana
- **Reject rate** (% events с PII или schema fail) — алерт при >1%
- **Buffer depth** (events в queue при Neon down) — алерт при >1000
- **p95 latency** POST /events — SLO ≤500ms
- **Drift ingress vs domain_event** (ingested vs persisted count) — алерт при >1% за 1h

## 8. Reference

- **Обещание:** DP.SC.020 Event Ingest
- **Карта БД:** DP.ARCH.004 v2.2 §8 (writer `learning.domain_event` = event-gateway)
- **Реализация:** `DS-MCP/event-gateway/` (Cloudflare Worker + Neon pooled connection)
- **Родительский РП:** WP-253 Ф9 MVP-greenfield
