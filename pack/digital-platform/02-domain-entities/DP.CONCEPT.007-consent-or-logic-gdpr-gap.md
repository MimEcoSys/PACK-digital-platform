---
id: DP.CONCEPT.007
name: OR-объединение двух таблиц согласия (boolean + revoked_at) молчаливо игнорирует отзыв — GDPR-дыра; правильно миграция + single source of truth
type: domain-entity
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_consent_or_logic_gdpr_gap.md (05.06; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [DP.CONCEPT.006, PACK-digital-platform]
---

# DP.CONCEPT.007: OR-логика согласия — fail-open к отзыву

## Дыра
Две таблицы согласия: legacy (`opt_in: bool`) и новая (`consent_grant` с `revoked_at`). OR/UNION-объединение: пользователь отзывает через consent_grant (revoked_at), но `tracking_consent.opt_in` остаётся true → OR вернёт true. Отзыв проигнорирован — нарушение GDPR-инварианта fail-closed.

## Правило
При объединении двух таблиц с разной семантикой отзыва (boolean vs revoked_at) OR-логика ВСЕГДДА создаёт дыру. Правильный путь:
1. Идемпотентная миграция: `INSERT INTO consent_grant SELECT ... WHERE opt_in = true ON CONFLICT DO NOTHING`.
2. Чтение — только `consent_grant WHERE revoked_at IS NULL` (single source of truth).
3. Dual-write — временно, до следующей фазы.

## Тест
«Если пользователь отзовёт согласие — OR вернёт false?» Нет → дыра.
