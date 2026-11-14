---
id: DP.M.616
name: aiogram кэширует FSM state в data['raw_state'] до outer middleware — в middleware читать raw_state, не get_state()
type: method
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_aiogram_raw_state_cache.md (08.05; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [PACK-digital-platform, PACK-digital-platform]
---

# DP.M.616: raw_state в aiogram middleware вместо get_state()

## Правило
В middleware НЕ вызывать `await state.get_state()` — использовать `data.get('raw_state')`.

## Почему
`get_state()` делает FSM DB round-trip (~50-100мс на Neon). `data['raw_state']` уже готово к моменту outer middleware — бесплатно.

## Применять
Любой middleware, который только ЧИТАЕТ state (логирование, трейсинг).

## Исключение
Middleware должен ИЗМЕНИТЬ state или нужен актуальный state ПОСЛЕ изменения другим middleware — тогда `get_state()`.

## Бонус
`send_chat_action` в middleware — `asyncio.create_task(...)`, не `await`: иначе блокирует весь request (~200-500мс Telegram HTTP).
