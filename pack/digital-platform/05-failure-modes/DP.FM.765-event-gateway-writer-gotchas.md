---
id: DP.FM.765
name: Четыре грабли writer-pipeline event-gateway → projection: jq // falsy на false, tformat vs format, cursor advance после schema_invalid (out-of-order), PII bypass для strict-schema sources
type: failure-mode
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_event_gateway_writer_gotchas.md (WP-295 Ф1, 17.05; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [DP.M.619, DP.CONCEPT.009, PACK-digital-platform]
---

# DP.FM.765: writer-pipeline gotchas

## 1. jq `//` трактует false как falsy
`.inserted // empty` для `{"inserted": false}` возвращает empty → uploader репортит FAILED при 200 idempotent.
- **Паттерн:** `if has("inserted") or has("idempotent") then "yes" else empty end`.

## 2. `git log --pretty=format:` не ставит \n между коммитами
>1 коммита склеиваются в одну строку массива.
- **Паттерн:** `--pretty=tformat:`.

## 3. Cursor advance после schema_invalid → out-of-order
BIGSERIAL id по порядку приёма, не логического времени: retry session_start позже session_end → FK violations на projection (parent не существует).
- **Митигации:** атомарная batch-отправка related events; consumer сортирует по payload.emitted_at (оконная обработка); retry с reset cursor до первого события сессии.

## 4. PII bypass для strict-schema sources
FORBIDDEN_FIELDS блокировал легитимный UUID (`session_id` — UUID агентской сессии, не пользовательский).
- **Паттерн:** env `PII_SCAN_BYPASS_SOURCES` — explicit whitelist источников со strict JSON Schema (`additionalProperties: false`) и собственным PII handling (crypto-shred); source check ДО piiInBody scan. Defense-in-depth для остальных источников сохранён.
