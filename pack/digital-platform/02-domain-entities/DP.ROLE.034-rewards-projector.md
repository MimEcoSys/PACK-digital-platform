---
id: DP.ROLE.034
name: Rewards Projector
type: role-description
status: draft
valid_from: 2026-04-24
summary: "Роль проектора баллов: читает learning.domain_event, применяет reference.reward_rules через compute_effective_amount, пишет в rewards.point_balances идемпотентно через cursor"
related:
  specializes: [U.RoleAssignment]
  component_of: [DP.ROLE.001]
  realizes: [DP.SC.122]
  uses:
    - DP.ARCH.004
    - DP.SC.020
    - DP.ECON.001
created: 2026-04-24
updated: 2026-11-14
---

# Rewards Projector (DP.ROLE.034)

> **Kind:** Infrastructure Role (инфраструктурная роль — проекция, не домен).
> **Owner Role:** Платформенная команда (source-of-truth — карта БД DP.ARCH.004 §3.12).
> **Current executor (с 8 мая 2026):** `multi-domain-projection-worker` (polling-cursor, multi-projection). Legacy `rewards-projection-worker` (LISTEN/NOTIFY single-projection) decommission'd 17 мая 2026 после backfill 100% (WP-311 Ф-Close).

## 1. Миссия

Держать `rewards.point_balances` как **точную проекцию** `learning.domain_event` через `reference.reward_rules` — идемпотентно, с гарантией catch-up после downtime, без дрифта относительно источника.

> **Архит. TODO (~2h, отдельный WP после WP-327 Этапа 4):** добавить колонку `earned_total` в `point_balances`. Сейчас `points` = earned − spent (убывает при использовании бонусов). После добавления: `points` → текущий бонусный баланс; `earned_total` → никогда не убывает = настоящие Баллы для лидерборда. Тогда `/balance` будет показывать два числа: «Баллы (заработано всего): N» + «Бонусы (доступно к оплате): M».

## 2. Обязанности

| Обязанность | Метод | Триггер |
|-------------|-------|---------|
| Опрос событий от курсора | Чтение новых `learning.domain_event` по курсору проекции в `learning.processed_events` | В цикле текущего исполнителя |
| Матчинг события ↔ правила | `match_condition` subset-match на payload | Для каждого прочитанного события |
| Атомарное применение | INSERT .. ON CONFLICT UPDATE balance + UPDATE cursor в одной tx | После match'а ≥1 правила |
| Startup replay от cursor | fetch_events_since(last_event_id) | При старте worker'а |
| Refresh rules cache | SELECT reward_rules WHERE active каждые 60s | Периодически в main loop |
| Идемпотентность на повторах | cursor-check перед apply + UNIQUE ключ в balance | Всегда |
| Graceful shutdown | SIGINT/SIGTERM → доработать текущий event → close connections | Деплой / рестарт |

## 3. Полномочия

- **Пишет** в `rewards.point_balances` как единственный исполнитель проекции баллов и ведёт её курсор в `learning.processed_events` (OwnerIntegrity).
- **Читает** новые `learning.domain_event` от курсора и `reference.reward_rules` (через cached SELECT).
- **Не интерпретирует** payload в домене — только матчит по правилам (decoupling «что случилось» от «как награждать»).
- **Не изменяет** правила или события — только проецирует.

## 4. Границы роли

| Делает | НЕ делает |
|--------|-----------|
| Проецирует events → balance | Не приёмщик событий (это DP.ROLE.032 Event Ingester) |
| Применяет правила MVP-матчинга (equality subset) | Не валидирует форму события (это event-gateway) |
| Атомарный cursor + balance в одной tx | Не хранит историю начислений (это POINTS_EVENT ledger, Phase 2) |
| Catch-up через replay от cursor | Не rebuild'ит balance с нуля автоматически (ручной CLI `runner.py replay`) |
| Cache rules 60s | Не пишет rules (admin через Directus; reference read-only) |
| Обрабатывает reward_kind='points' (MVP) | Не обрабатывает 'achievement' (MVP пропускает, Phase 2 — отдельный projector) |

## 5. Исполнители

| Исполнитель | Когда | Режим |
|-------------|-------|-------|
| **multi-domain-projection-worker** (Python 3.11+ asyncpg, polling-cursor) | Production (current) с 8 мая 2026 | Railway long-running service, 24/7. Polling cursor multi-projection (rewards/payment/learning/persona/subscription/indicators). Cursor в `learning.processed_events` по `projection_name`. |
| ~~rewards-projection-worker~~ (Python 3.11+ asyncpg, LISTEN/NOTIFY) | ~~24 апр — 17 мая 2026~~ | **Decommission'd 17 мая** после backfill 100% (WP-311 Ф-Close). Cursor в `rewards.processed_events.point_balances`. |
| Human (разработчик) | Разовый rebuild projection после incident | CLI `python runner.py replay` |

### Изменение механизма доставки (8 мая 2026)

Legacy LISTEN/NOTIFY → polling-cursor. Причины:
1. **Сетевой LISTEN не выживал** при Neon-pooler (PgBouncer transaction-mode маскировал FATAL как transient — см. `feedback_neon_pooler_listen_notify.md`).
2. **Multi-projection** в одном воркере: вместо N процессов с N подключениями — один процесс с per-projection cursor (`learning.processed_events.projection_name`).
3. **Backfill = polling** по определению — единый механизм для realtime и catch-up.

Семантика проекции (Section 2 Обязанности) не изменилась. Изменилась доставка.

## 6. Связи

**Вход (потребитель обещаний других ролей):**
- **Event Ingester** (DP.ROLE.032) — пишет `learning.domain_event`; проектор периодически читает новые события от своего курсора.
- **Admin через Directus** — пишет `reference.reward_rules` (read-only для Projector).

**Выход (поставщик обещаний другим ролям):**
- **Бот команда `/points`** — два числа: `rewards.point_balances.points` (текущий баланс, бонусы) + вычисляемые бонусы `min(points, Σ(days_at_qual_i × cap_i))`. После добавления `earned_total` — также показывать earned_total (баллы).
- **Gateway MCP `/twin`** — читает balance для Persona.snapshot.
- **Metabase BI** — read-only на `point_balances` для дашбордов.
- **Qualification Projector** (Phase 2, отдельная роль) — потенциально триггерится по balance milestones.

## 7. Measurable health

- **Processing latency p95** (`INSERT learning.domain_event` → завершение `UPDATE rewards.point_balances`) — целевой SLO ≤1s; для текущего исполнителя с опросом требуется отдельный замер
- **Cursor lag** (`MAX(learning.domain_event.id) - learning.processed_events.last_event_id` для проекции баллов) — алерт при >10 за >5 мин
- **Rule refresh age** (время с последнего SELECT reward_rules) — алерт при >120s (2× refresh period)
- **Replay rate** (events/s при startup catch-up) — SLO ≥100 events/s
- **Balance invariant violations** (rollbacks из-за CHECK points>=0) — алерт при >0 за 1h (rule design error)
- **Drift** (`SUM(points) vs Σ applied reward_rules for all events`) — еженедельная consistency check

## 8. Reference

- **Обещание:** [DP.SC.122 Rewards Projection](../08-service-clauses/DP.SC.122-rewards-projection.md)
- **Доменная модель:** [DP.ECON.001 Points Engine](./DP.ECON.001-points-engine.md) §1.5 (формула v2)
- **Писатель событий:** [DP.SC.020 Event Ingest](../08-service-clauses/DP.SC.044-event-ingest.md) / [DP.ROLE.032 Event Ingester](./DP.ROLE.032-event-ingester.md)
- **Карта БД (current):** `learning.processed_events` (writer: multi-domain-projection-worker, per-projection cursor), `rewards.point_balances` (writer: тот же воркер), `rewards.applied_events` (writer: `rewards.compute_effective_amount()` PG-функция)
- **Карта БД (legacy, decommission'd 17 мая):** `rewards.processed_events.point_balances` (cursor) — rewards-projection-worker (DS-IT-systems/rewards-projection-worker/)
- **Реализация (current):** `DS-IT-systems/multi-domain-projection-worker/` (Python 3.11+, asyncpg, polling-cursor)
- **Реализация (legacy):** `DS-IT-systems/rewards-projection-worker/` — repo сохраняется как архив, не deployed
- **Расчётная функция:** `rewards.compute_effective_amount()` PG-функция (миграция 205-rewards-compute-effective-amount.sql)
- **Родительский РП:** WP-121 (правила + Neon impl), WP-311 (realtime emitter + wave-1 smoke), WP-307 W3 (split multi-domain)
