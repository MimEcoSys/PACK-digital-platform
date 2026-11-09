---
id: DP.M.512
type: method
status: draft
created: "2026-10-10"
valid_from: "2026-10-10"
name: "Перенос владения функции в PostgreSQL: временный GRANT CREATE на схему → ALTER … OWNER TO → REVOKE"
name_ru: "Перенос владения функции в PostgreSQL: временный GRANT CREATE на схему → ALTER … OWNER TO → REVOKE"
name_en: "Postgres function ownership transfer: temporary GRANT CREATE on schema, ALTER ... OWNER TO, then REVOKE"
summary: "ALTER FUNCTION ... OWNER TO требует у новой роли-владельца права CREATE на схему функции. Грант выдаётся временно непосредственно перед миграцией и отзывается сразу после."
pack: PACK-digital-platform
domain: digital-platform / postgres-migrations
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit 5c7efad54 в DS-my-strategy (WP-567)"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-10-inbox-check-5.md"
source_candidate: 3
tags: [postgres, ownership, grant, migration, preflight]
---

# DP.M.512 — Временный CREATE на схему для переноса владения функцией

## Контекст

Миграция передаёт владение функцией новой роли (`rewards_points_engine_owner`). PostgreSQL для `ALTER FUNCTION ... OWNER TO` требует, чтобы новая роль-владелец имела право `CREATE` на схему, где лежит функция. Заранее этот грант выдан не был; расхождение «preflight проверял другое право» всплыло только при живом запуске.

## Метод

1. Preflight проверяет именно транзитивно нужный грант: `CREATE` новой роли на схему функции, а не только существование роли и прав на саму функцию.
2. Если гранта нет — выдать временно: `GRANT CREATE ON SCHEMA <schema> TO <new_owner>`.
3. Выполнить миграцию (`ALTER FUNCTION ... OWNER TO <new_owner>`).
4. Сразу отозвать: `REVOKE CREATE ON SCHEMA <schema> FROM <new_owner>`.

## Почему временно

Право `CREATE` на схему нужно только для самого `ALTER`; постоянный грант расширяет привилегии роли без причины. Последующий отзыв безопасен — владение уже перенесено.

## Тест

«Перечислены ли в preflight все права, которые SQL-команда требует транзитивно (от целевой роли к схеме/объекту), а не только очевидные?»
