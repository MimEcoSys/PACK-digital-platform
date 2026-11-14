---
id: DP.M.620
name: Эшелонированная защита asyncio listener'ов от idle-stall — 5 координированных слоёв, один таймаут не защищает
type: method
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_idle_stall_layered_defense.md (инцидент 27.05, commit 1f21b5a; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [DP.FM.764, DP.FM.765, PACK-digital-platform]
---

# DP.M.620: пять слоёв защиты от idle-stall

## Антипаттерн
Один `wait_for(process_event, timeout=60)`: извлекает event из очереди, cursor не advance, periodic replay только на старте → event теряется до рестарта. Хуже stall'а: stall запаздывает, silent skip теряет.

## Пять слоёв
| Слой | Назначение |
|---|---|
| A. `command_timeout` на asyncpg connect/pool | прерывает зависший acquire/execute (мс-с) |
| C. Unconditional alive-heartbeat в loop | liveness каждые N сек, включая idle; startup heartbeat обязателен |
| D. `wait_for` per event — fast path | один зависший event не блокирует loop (секунды) |
| E. Periodic `replay_from_cursor` в loop — slow path | подбирает потерянные (lost NOTIFY, cancel от D, container freeze) |
| F. Idempotency contract | UPDATE/UPSERT only + guard `event_id<=cursor` — replay безопасен |

## Инвариант таймаутов
`command_timeout < PROCESS_EVENT_TIMEOUT < PERIODIC_REPLAY_INTERVAL` (напр. 30с < 60с < 300с).

## Тонкости
- `last_replay = now` обновлять ДО try, не в success-ветке (иначе ERROR-спам при transient failure).
- Cursor advance строго ПОСЛЕ успешного apply (иначе partial failure оставляет cursor впереди данных).
- Re-queue в except не нужен — маскирует отсутствие periodic replay; лучше структурный слой E.
