---
id: DP.M.567
name: "Вход хэша из внешней записи — замороженный allowlist полей, а не «всё, что есть сейчас»"
name_ru: "Вход хэша из внешней записи — замороженный allowlist полей, а не «всё, что есть сейчас»"
name_en: "Hash input from an external record is a frozen field allowlist, not 'everything present now'"
summary: "Когда fingerprint/content_hash собирается из полей внешней записи (каталог, ответ API), набор полей фиксируется именованной константой. Новое поле источника не попадает в хэш, пока отдельное решение не добавит его в список — иначе тихий дрейф инвалидирует все прежние сравнения."
type: method
status: draft
pack: PACK-digital-platform
domain: digital-platform / content-addressing
trust: empirical
epistemic_stage: pattern
valid_from: "2026-10-22"
created: 2026-10-23
schema_version: 1
related:
  see_also:
  - DP.M.174
  - AS.M.027
source_capture: DS-my-strategy/inbox/captures/2026-10.md:6373
extraction_report: DS-my-strategy/inbox/extraction-reports/2026-10-23-inbox-check-5.md
source_candidate: 3
---

# DP.M.567 — Замороженный allowlist полей для входа хэша

## Вход
Внешняя запись (catalog-запись, API-ответ), из которой строится `content_hash` / fingerprint.

## Метод
1. Выбрать полный перечень полей, участвующих в хэше, и зафиксировать его именованной константой (пример: `_RECIPE_PAYLOAD_FIELDS = ("seed_id", "bottleneck", "domain", "priority", "description", "covers_gaps")`).
2. Собирать вход хэша только по этому списку; прочие поля источника игнорировать.
3. Расширение списка — отдельное решение с учётом того, что прежние хэши перестанут совпадать.
4. Если запись нужно получить повторно, брать её тем же путём, что и соседний код, но проецировать на allowlist, а не передавать целиком.

## Выход
Хэш, стабильный при добавлении полей в источник.

## Основание
WP-521 Ф6 (Путь B, program_fragment): `select_assignment()` отдавал только метаданные выбора, полная запись добиралась из каталога по (chosen, program).

## Связи
- DP.M.174 (идемпотентность по хэшам), AS.M.027 — смежные методы.
