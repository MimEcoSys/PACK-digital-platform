---
id: DP.ROLE.034
name: Начислитель баллов
name_ru: Начислитель баллов
name_en: Rewards Projector
aliases:
  - Rewards Projector
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
updated: 2026-11-22
---

# Начислитель баллов (DP.ROLE.034)

> **Прежнее имя** — «Rewards Projector»; переименовано решением пилота 22.11.2026 (DP.ROLE.001 §3.6, РП-616 Ф4).

> **Kind:** Infrastructure Role (инфраструктурная роль — проекция, не домен).
> **Owner Role:** Платформенная команда (source-of-truth — карта БД DP.ARCH.004 §3.12).
> **Current executor (с 8 мая 2026):** `multi-domain-projection-worker` (LISTEN/NOTIFY, повторное чтение от курсора, несколько проекций). Legacy `rewards-projection-worker` (отдельная проекция баллов) decommission'd 17 мая 2026 после backfill 100% (WP-311 Ф-Close).

## 1. Миссия

Держать `rewards.point_balances` как **точную проекцию** `learning.domain_event` через `reference.reward_rules` — идемпотентно, с гарантией catch-up после downtime, без дрифта относительно источника.

> **Архит. TODO (~2h, отдельный WP после WP-327 Этапа 4):** добавить колонку `earned_total` в `point_balances`. Сейчас `points` = earned − spent (убывает при использовании бонусов). После добавления: `points` → текущий бонусный баланс; `earned_total` → никогда не убывает = настоящие Баллы для лидерборда. Тогда `/balance` будет показывать два числа: «Баллы (заработано всего): N» + «Бонусы (доступно к оплате): M».

## 2. Обязанности

| Обязанность | Метод | Триггер |
|-------------|-------|---------|
| Приём уведомлений | LISTEN `domain_event_added`, затем чтение события по id | При записи нового события |
| Матчинг события ↔ правила | Применение действующих `reference.projection_rules` к payload | Для каждого полученного или повторно прочитанного события |
| Применение начисления | Запись начисления и обновление баланса в одной транзакции БД наград | После совпадения с правилом |
| Сохранение курсора | Обновление курсора проекции в памяти, затем пакетная запись в `learning.processed_events` | После успешного применения; отдельно от транзакции наград |
| Startup replay от cursor | fetch_events_since(last_event_id) | При старте worker'а |
| Periodic replay от cursor | fetch_events_since(last_event_id) | После переподключения и периодически |
| Refresh rules cache | SELECT `reference.projection_rules` WHERE enabled каждые 60s | Периодически в main loop |
| Идемпотентность на повторах | Проверка курсора и идемпотентное применение в БД наград | Всегда |
| Graceful shutdown | SIGINT/SIGTERM → доработать текущий event → close connections | Деплой / рестарт |

## 3. Полномочия

- **Пишет** в `rewards.point_balances` как единственный исполнитель проекции баллов и ведёт её курсор в `learning.processed_events` (OwnerIntegrity).
- **Читает** `learning.domain_event` по id из уведомления и при повторном проходе от курсора; загружает действующие `reference.projection_rules` в кэш.
- **Не интерпретирует** payload в домене — только матчит по правилам (decoupling «что случилось» от «как награждать»).
- **Не изменяет** правила или события — только проецирует.

## 4. Границы роли

| Делает | НЕ делает |
|--------|-----------|
| Проецирует events → balance | Не приёмщик событий (это DP.ROLE.032 Event Ingester) |
| Применяет правила MVP-матчинга (equality subset) | Не валидирует форму события (это event-gateway) |
| Записывает начисление и баланс в одной транзакции БД наград; курсор сохраняет отдельно | Не хранит историю начислений (это POINTS_EVENT ledger, Phase 2) |
| Catch-up через replay от cursor | Не rebuild'ит balance с нуля автоматически (ручной CLI `runner.py replay`) |
| Обновляет кэш правил проекции раз в 60s | Не изменяет правила проекции |
| Обрабатывает reward_kind='points' (MVP) | Не обрабатывает 'achievement' (MVP пропускает, Phase 2 — отдельный projector) |

## 5. Исполнители

| Исполнитель | Когда | Режим |
|-------------|-------|-------|
| **multi-domain-projection-worker** (Python 3.11+ asyncpg, LISTEN/NOTIFY + replay от курсора) | Production (current) с 8 мая 2026 | Railway long-running service, 24/7. Обрабатывает уведомления, на старте и периодически дочитывает события; ведёт курсоры проекций в `learning.processed_events` по `projection_name`. |
| ~~rewards-projection-worker~~ (Python 3.11+ asyncpg, LISTEN/NOTIFY) | ~~24 апр — 17 мая 2026~~ | **Decommission'd 17 мая** после backfill 100% (WP-311 Ф-Close). Cursor в `rewards.processed_events.point_balances`. |
| Human (разработчик) | Разовый rebuild projection после incident | CLI `python runner.py replay` |

### Смена исполнителя (8–17 мая 2026)

Прежний отдельный исполнитель баллов был остановлен после перехода к общему исполнителю нескольких проекций. Оба получают уведомления LISTEN/NOTIFY; нынешний исполнитель дополнительно дочитывает события от отдельного курсора каждой проекции (`learning.processed_events.projection_name`) на старте, после переподключения и периодически. Проблема сетевого LISTEN через Neon-pooler в прежней конфигурации описана в `feedback_neon_pooler_listen_notify.md`; в текущем коде есть переподключение и повторное чтение от курсора.

## 6. Связи

**Вход (потребитель обещаний других ролей):**
- **Event Ingester** (DP.ROLE.032) — пишет `learning.domain_event` и уведомляет о новом событии; проектор также дочитывает события от своего курсора.
- **Администратор правил** — ведёт `reference.reward_rules`, которые использует расчётная функция наград; проектор загружает отдельно `reference.projection_rules` для маршрутизации событий.

**Выход (поставщик обещаний другим ролям):**
- **Бот команда `/points`** — два числа: `rewards.point_balances.points` (текущий баланс, бонусы) + вычисляемые бонусы `min(points, Σ(days_at_qual_i × cap_i))`. После добавления `earned_total` — также показывать earned_total (баллы).
- **Gateway MCP `/twin`** — читает balance для Persona.snapshot.
- **Metabase BI** — read-only на `point_balances` для дашбордов.
- **Qualification Projector** (Phase 2, отдельная роль) — потенциально триггерится по balance milestones.

## 7. Measurable health

- **Processing latency p95** (`INSERT learning.domain_event` → завершение `UPDATE rewards.point_balances`) — целевой SLO ≤1s; для текущего исполнителя требуется отдельный замер под нагрузкой
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
- **Реализация (current):** `DS-IT-systems/multi-domain-projection-worker/` (Python 3.11+, asyncpg, LISTEN/NOTIFY + replay от курсора)
- **Реализация (legacy):** `DS-IT-systems/rewards-projection-worker/` — repo сохраняется как архив, не deployed
- **Расчётная функция:** `rewards.compute_effective_amount()` PG-функция (миграция 205-rewards-compute-effective-amount.sql)
- **Родительский РП:** WP-121 (правила + Neon impl), WP-311 (realtime emitter + wave-1 smoke), WP-307 W3 (split multi-domain)
