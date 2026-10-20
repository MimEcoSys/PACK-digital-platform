---
id: DP.M.544
name: "GRANT ... WITH INHERIT TRUE перед DROP OWNED BY при откате временных Postgres-ролей"
name_ru: "GRANT ... WITH INHERIT TRUE перед DROP OWNED BY при откате временных Postgres-ролей"
name_en: "GRANT ... WITH INHERIT TRUE before DROP OWNED BY when rolling back temporary Postgres roles"
summary: "DROP OWNED BY <роль> проверяет has_privs_of_role у исполнителя, не одно лишь членство без наследования прав — и не удовлетворяется тем, что сама роль-читатель объявлена NOINHERIT. Порядок отката: GRANT <роль> TO CURRENT_USER WITH INHERIT TRUE → DROP OWNED BY на каждую роль → DROP ROLE ... RESTRICT (не CASCADE), чтобы необнаруженные посторонние зависимости останавливали транзакцию явной ошибкой, а не исчезали молча."
type: method
pack: PACK-digital-platform
domain: digital-platform / postgresql
trust: medium
epistemic_stage: forming
status: draft
created: "2026-10-17"
valid_from: "2026-10-16"
source: "git commit 79550f7 в neon-migrations (WP-578 Ф19, peer-session 2026-10-16-20-wp578-advance-open)"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:4273"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-17-inbox-check-3.md"
source_candidate: 3
tags: [postgres, drop-owned-by, inherit, role-privileges, migration-rollback, neon]
schema_version: 1
---

# DP.M.544 — GRANT ... WITH INHERIT TRUE перед DROP OWNED BY при откате ролей

## Проблема

Откат миграции, создававшей временные Postgres-роли, использует `DROP OWNED BY <роль>` для удаления принадлежащих ей объектов перед `DROP ROLE`. Эта команда проверяет `has_privs_of_role` у исполнителя, а не просто членство в роли без наследования прав — и не удовлетворяется тем, что сама роль-читатель объявлена `NOINHERIT` (это ограничивает роль, а не того, кто от её имени выполняет `DROP OWNED`).

## IPO-паттерн

| Элемент | Описание |
|---|---|
| Входы | Временная Postgres-роль, подлежащая удалению вместе со своими объектами |
| Обработка | Непосредственно перед откатом: `GRANT <роль> TO CURRENT_USER WITH INHERIT TRUE` → `DROP OWNED BY <роль>` на каждую роль → `DROP ROLE ... RESTRICT` (не `CASCADE`) |
| Выходы | Роль и её объекты удалены; если остались посторонние зависимости — транзакция останавливается явной ошибкой (`RESTRICT`), не стирает их молча (`CASCADE`) |

## Когда применять

Откат миграции, создающей Postgres-роли с явным `NOINHERIT`, когда исполнитель не имеет более широких административных прав: перед `DROP OWNED BY` ему нужно предоставить членство в каждой удаляемой роли с `WITH INHERIT TRUE`. `RESTRICT` вместо `CASCADE` на последующем `DROP ROLE` — чтобы необнаруженные зависимости останавливали откат, а не исчезали вместе с ролью.

## Связи

- Источник: WP-578 Ф19, peer-session 2026-10-16-20-wp578-advance-open.
