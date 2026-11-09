---
id: DP.D.067
name: Card ≠ Append-only Event (Aggregate-card vs Event-stream в event sourcing)
kind: Distinction
status: active
created: 2026-05-17
sources:
  - WP-295 commit 65b29b4 (DP.SC.037 inv.2 — pre-implementation smoke)
  - Session 2026-05-17 (event sourcing schema review)
related:
  applies_to: [DP.SC.037, DP.SOTA.022]
---

# DP.D.067: Card ≠ Append-only Event

## Distinction

В event sourcing сосуществуют **два разных рода сущностей**, для которых нужны **разные
инварианты хранения**:

- **Append-only events** — `decision`, `hypothesis`, `tool_call`, `snapshot`, `fork_session`.
  UPDATE/DELETE запрещены. Корректировка только через **compensating event** (новая запись,
  отменяющая предыдущую). Inv: «после записи факт не меняется».
- **Aggregate-cards** — `session`, любая «карточка с состояниями» (start/identification
  поля immutable, closing-fields мутируют **один раз** при `session.end`). Inv:
  «после `end`-перехода значение фиксируется и больше не меняется».

## Distinction Test

> «Может ли сущность иметь промежуточное состояние (между start и end) и финальное
> состояние (после end)?»

- **Да** → card с closing-mutation. Inv: «closing-fields мутируют один раз при end».
- **Нет** (факт записан как есть, корректировка только compensating-записью) → append-only
  event. Inv: «после записи факт не меняется».

## Граница

Применение единого инварианта «append-only, immutable» ко всем сущностям контракта
одинаково приводит к contract-vs-schema противоречию: session **должна** обновляться
(ended_at, closed_status, produced_artifact_ids), но контракт запрещает UPDATE → блокер
реализации.

Этот блокер выявлен в WP-295 pre-implementation smoke (commit 65b29b4): session
не вписалась в append-only invariant из DP.SOTA.022. Resolution — разделить инвариант
по роду сущности.

## Why It Matters

- DDD-aggregate ≠ event stream. Event stream **питает** aggregate проекциями, но aggregate
  сам по себе — **card**, не event.
- Контракт обязан различать рода сущностей и задавать инварианты раздельно. Иначе
  типичный паттерн: «append-only для events, closing-mutation для cards» становится
  невыразимым — придётся выбирать или единый append-only (session ломается), или единый
  mutable (события теряют immutability).

## Применимо к

- `agent_trace` schema (WP-295) — events vs session-aggregate.
- Любая система с (started/ended)-периодами: WP-cards, день-открытие/закрытие, заказы,
  тренировочные сессии, диагностические циклы.
- Event sourcing проекты в Pack-digital-platform.

## Связи

- DP.SC.037 §3 inv.2 (agent-trace) — конкретное применение distinction.
- DP.SOTA.022 (event sourcing) — родительский SoTA; этот distinction уточняет когда
  append-only применяется, когда нет.
- DP.D.065 (Orthogonal distinctions) — пример ортогональной декомпозиции инварианта
  по роду сущности.
