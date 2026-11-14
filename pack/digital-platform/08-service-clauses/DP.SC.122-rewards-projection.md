---
id: DP.SC.122
name: Rewards Projection (точная проекция баллов по доменным событиям)
type: sc
status: draft
layer: L2-Platform
summary: "Точная идемпотентная проекция из learning.domain_event в rewards.point_balances по reference.reward_rules через опрос событий от курсора"
consumer: Читатели баланса баллов — бот (`/points`), gateway-mcp (`/twin`), Метабаза, будущий UI
created: 2026-04-24
updated: 2026-11-14
related:
  realizes: [WP-121, WP-311]
  uses: [DP.ARCH.004, DP.SC.020, DP.ECON.001]
  source: "WP-253 Ф9.3 MVP-greenfield — IntegrationGate для projection-worker; WP-311 Ф0a актуализация 17 мая (consumer /balance → /points, realizes WP-121+WP-311)"
---

# DP.SC.122 — Rewards Projection

## Обещание

**Кому:** читателям баланса баллов пользователей — бот (команда `/points`), gateway-mcp инструмент `/twin`, Метабаза (BI), будущий Web UI.

**Зачем:** до этого баллы считались в двух местах — legacy `payment-registry.points_*` и экспериментальный скилл-handler. Расхождение между ними = споры «сколько у меня баллов на самом деле». Нужен **единственный источник истины** — пересчёт из событий по опубликованным правилам.

**Что получит потребитель:**
- Запрос `SELECT points FROM rewards.point_balances WHERE account_id = $1` даёт актуальное значение в пределах **≤1 секунды** после записи события в `learning.domain_event`.
- Баллы **всегда** равны сумме начислений по всем сработавшим `reference.reward_rules` для всех событий с этим `account_id` (контрактно — не эвристика, пересчитываемо).
- Повтор одного события **не удваивает** баланс (идемпотентность через cursor).
- Downtime проекции ≤15 мин не теряет события — после рестарта replay с cursor закрывает gap.

## Критерий приёмки

1. **Latency p95 ≤1s** между `INSERT learning.domain_event` и `UPDATE rewards.point_balances` под нагрузкой 10 events/s. Это сохранённая цель обещания; достижение её текущим исполнителем с опросом событий от курсора требует отдельного измерения.
2. **Идемпотентность:** повтор обработки того же `domain_event.id` не изменяет баланс — обновление курсора и баланса в одной транзакции, проверка курсора перед применением.
3. **Gap recovery:** после перезапуска исполнитель читает курсор проекции из `learning.processed_events` и применяет все события с `id > cursor` — 10k events за ≤60s.
4. **Determinism:** при одинаковой истории событий и одинаковых `reward_rules` (valid_from/to неизменны) финальный `point_balances` идентичен при повторном чтении событий — правила отсортированы по `rule_id`, события — по `id`.
5. **Business invariant:** `CHECK (points >= 0)` не нарушается — при попытке увести в минус транзакция откатывается, cursor не двигается, событие возвращается при replay.
6. **Observability:** каждое применение правила → structured log с `event_id`, `rule_id`, `account_id`, `amount`; расхождение `events_processed` vs `domain_event count` >0.1% за 1h → TG-алерт.

## Архитектура

```
event-gateway (DP.ROLE.032) ─── INSERT learning.domain_event
                                       │
                                       ▼
  ┌───────────────────────────────────────────────────────┐
  │ multi-domain-projection-worker (DP.ROLE.034, Railway) │
  │                                                       │
  │   poll: cursor := get_cursor(processed_events)         │
  │         events := fetch_events_since(cursor)          │
  │         for event in events ordered by id:            │
  │           apps := match(event, cached_rules)          │
  │           tx: update point_balances + cursor          │
  │                                                       │
  │   startup: дочитать события от курсора                │
  │   loop: обновлять правила из reference каждые 60 с   │
  └───────────────────────────────────────────────────────┘
                                       │
                                       ▼
                        rewards.point_balances ← читают бот/gateway/Metabase
```

## Матчинг правил

Правило `reference.reward_rules` применяется если:
1. `rule.trigger_event == event.event_type` (строгое равенство).
2. `rule.match_condition` — `NULL` (unconditional) **ИЛИ** subset-match: каждая пара `(key, value)` из condition присутствует в `event.payload` со строгим равенством (без type coercion).
3. Правило активно: `valid_from <= now() AND (valid_to IS NULL OR valid_to > now())` — проверяется при загрузке правил из БД (не в матчере).
4. Событие имеет `account_id` — иначе некого награждать, правило пропускается.

Несколько правил могут сработать на одно событие — все применяются (суммируются в balance).

## Режимы отказа

| Сбой | Поведение | Восстановление |
|------|-----------|----------------|
| Neon learning недоступен | Опрос событий приостанавливается | После восстановления исполнитель дочитывает события от курсора |
| Neon rewards недоступен | Транзакция откатывается, курсор не двигается | Следующий опрос или рестарт повторяет чтение от курсора |
| Neon reference недоступен | Используется cached rules (последний успешный fetch) | Через 60s будет попытка refresh |
| Правило уводит в минус | CHECK (points >= 0) блокирует, tx rollback | Ручной разбор (rule design error) — incident |
| Worker crash | Systemd/Railway рестарт, startup replay от cursor | ≤60s gap recovery |
| Опрос событий временно прерван | Курсор остаётся на последнем применённом событии | Следующий успешный опрос дочитывает пропущенные события |

## Граница ответственности

| projection-worker делает | Не делает |
|--------------------------|-----------|
| Опрос событий от курсора | Не принимает входящие события (это event-gateway, DP.SC.020) |
| Применяет reward_rules → point_balances | Не создаёт правила (это admin через Directus) |
| Обеспечивает idempotency через cursor | Не валидирует payload (это event-gateway) |
| Replay от cursor на старте | Не rebuild'ит balance с нуля (только forward) — rebuild = отдельный CLI `replay --from=0` |
| Атомарная tx (balance + cursor) | Не обрабатывает achievement (Phase 2 — отдельный projection) |
| Cache rules 60s | Не пишет rules (read-only для reference) |

## История исполнителей (2026)

| Период | Исполнитель | Состояние |
|--------|-------------|-----------|
| 24 апр — 17 мая | `rewards-projection-worker` (legacy, Python+asyncpg+LISTEN/NOTIFY на Railway) | Decommissioned 17 мая после backfill 100% (WP-121 Ф-Close, WP-311 Ф3.5) |
| с 8 мая (overlap) → текущий | `multi-domain-projection-worker` (WP-307 W3, polling-cursor multi-projection) | Production. Realtime + новый источник истины для cursor |

**Семантика проекции не изменилась.** Изменился способ доставки (LISTEN/NOTIFY → polling-cursor) и зона ответственности (один воркер на 1 БД → один воркер на N доменов). См. также DP.ROLE.034.

## Related

- **Роль:** [DP.ROLE.034 Rewards Projector](../02-domain-entities/DP.ROLE.034-rewards-projector.md)
- **Доменная модель:** [DP.ECON.001 Points Engine](../02-domain-entities/DP.ECON.001-points-engine.md) — формула, инварианты, потоки
- **Писатель событий:** [DP.SC.020 Event Ingest](./DP.SC.044-event-ingest.md) (event-gateway)
- **Реализация (current):** `DS-IT-systems/multi-domain-projection-worker/` (Python 3.11+ asyncpg, Railway, polling-cursor)
- **Реализация (legacy, decommission'd 17 мая):** `DS-IT-systems/rewards-projection-worker/`
- **Расчётная функция:** `rewards.compute_effective_amount()` PG-функция (миграция 205-rewards-compute-effective-amount.sql)
- **Карта БД:** DP.ARCH.004 v2.3 §3.12 (reader `learning.domain_event`, writer `rewards.point_balances`, курсор проекции в `learning.processed_events`)
- **Связанные РП:** WP-121 (правила и Neon-импл), WP-311 (первый исполнитель), WP-307 W3 (нынешний исполнитель)
