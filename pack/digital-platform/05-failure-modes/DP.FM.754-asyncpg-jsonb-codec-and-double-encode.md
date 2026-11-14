---
id: DP.FM.754
name: asyncpg не декодирует jsonb автоматически — нужен set_type_codec на каждый connection; при активном кодеке не json.dumps параметр (double-encode)
type: failure-mode
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_asyncpg_jsonb_codec.md (WP-310 Ф4, 18.05; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [DP.FM.755, PACK-digital-platform]
---

# DP.FM.754: asyncpg jsonb — кодек и double-encode

## Симптом
jsonb-колонки приходят сырыми JSON-строками: `dict(row["col"])` падает `dictionary update sequence element #0 has length 1`. Или наоборот — в БД оказывается строка `"{\"key\": val}"` вместо объекта.

## Причина
1. asyncpg 0.29 не декодирует jsonb автоматически — кодек регистрируется на КАЖДЫЙ connection отдельно (`conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")`), соседние коннекшны его не наследуют.
2. При активном кодеке asyncpg сам сериализует dict — переданная уже сериализованная строка сериализуется второй раз.

## Антипаттерн → Паттерн
- **Антипаттерн:** `json.dumps(obj)` в параметр на коннекшне с кодеком; полагаться, что кодек на одном коннекшне действует на все.
- **Паттерн:** с регистрацией кодека передавать dict напрямую; регистрировать на каждый conn.

## Тест обнаружения
Двойной encode в БД: `SELECT ... WHERE jsonb_typeof(col) = 'string'` — 'string' означает double-encode. Исправление: `SET col = (col#>>'{}')::jsonb`.
