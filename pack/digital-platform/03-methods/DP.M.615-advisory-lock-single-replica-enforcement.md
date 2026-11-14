---
id: DP.M.615
name: Advisory lock как enforcement single-replica контракта для stateful workers с shared state в БД
type: method
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_advisory_lock_single_replica.md (WP-307 Ф8, 12.05; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [DP.SC.139, DP.FM.749, PACK-digital-platform]
---

# DP.M.615: pg_try_advisory_lock как single-replica enforcement

## Когда применять
Stateful worker с shared state в БД (poller, projection-worker), у которого accidental `scale 2` ломает ingestion (дубли) или метрики (двойной счёт), а hot-standby не нужен.

## Паттерн
При старте процесса, ДО любой работы, на dedicated connection (не из pool — иначе lock освободится при возврате коннекта):
```python
locked = await conn.fetchval("SELECT pg_try_advisory_lock($1)", KEY)
if not locked:
    raise SystemExit(75)  # EX_TEMPFAIL — платформа может ретраить
```
Lock session-scoped: освобождается автоматически при close/crash. Failure mode явный (crash-loop с ERROR), не silent corruption.

## Свойства
- Non-blocking (`pg_try_…`), не висит в ожидании.
- Не требует таблицы/DDL — pure runtime.
- Это enforcement single-replica контракта, НЕ leader election: для failover с hot-standby — lease-based lock или consul/zookeeper.

## Конвенция ключей (IWE)
`42` + последние 3 цифры WP-номера (420220 — bridge-2-events-poller W2; 420277 — multi-domain-projection-worker W3).

## Обязательное сопровождение
SCALING.md рядом с сервисом: «видишь advisory_lock_busy → railway scale 1». Оператор не должен дебажить crash-loop без подсказки.
