---
id: DP.FM.594
type: failure-mode
status: draft
created: "2026-10-11"
valid_from: "2026-10-11"
name: "Классификатор живости процесса: четыре универсальные ловушки — PermissionError ≠ «мёртв», первый basename в os.walk(), позиционная регулярка вместо json.loads, молчаливый fallthrough при отсутствии поля"
name_ru: "Классификатор живости процесса: четыре универсальные ловушки"
name_en: "Process-liveness classifier: four universal traps — PermissionError falsely means dead, first basename in os.walk(), positional regex instead of json.loads, missing field gives silent fallthrough"
summary: "Четыре универсальные ловушки в коде классификатора: (1) PermissionError при проверке файловой системы — ошибка доступа, а не признак мёртвого процесса; (2) os.walk() берёт первый чекаут с совпадающим basename, молча игнорируя остальные; (3) позиционная регулярка для разбора структурированного receipt ломается при любом изменении формата — нужен json.loads; (4) отсутствующее created_at даёт молчаливый fallthrough вместо явного needs-review статуса."
pack: PACK-digital-platform
domain: digital-platform / classifier
trust: medium
epistemic_stage: forming
source: "git commit 0bbfe70a6 в DS-my-strategy; peer-session 2026-10-10-06-wp530-tsekh-git-mak-sync (WP-530)"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:2324"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-11-inbox-check.md"
source_candidate: 3
related:
  see_also: ["DP.FM.481"]
tags: [classifier, process-liveness, permission-error, os-walk, basename, json-parsing, fallthrough, code-review]
schema_version: 1
---

# DP.FM.594 — Классификатор живости процесса: четыре универсальные ловушки

## Тезис

Четыре независимых класса ошибок, обнаруженных в одном ревью классификатора живости git-процессов (tsekh-git-mak-sync). Каждая ловушка воспроизводима независимо в любом подобном коде.

## Ловушка 1: PermissionError ≠ «процесс мёртв»

`PermissionError` при обращении к файловой системе означает ошибку прав доступа, не отсутствие процесса. Код, сворачивающий любой `PermissionError` в «not alive», даёт ложно-мёртвый результат для живых процессов, к файлам которых у текущего пользователя нет доступа.

**Исправление:** обрабатывать `PermissionError` отдельно — сигнал `permission-denied`, не `not-alive`.

## Ловушка 2: Первый basename в os.walk() молча игнорирует дубликаты

`os.walk()` при поиске репозитория по `basename` останавливается на первом совпадении. Если несколько чекаутов делят одно имя директории, классификатор работает только с первым найденным.

**Исправление:** собирать все совпадения, проверять каждый чекаут.

## Ловушка 3: Позиционная регулярка для структурированного receipt

Разбор JSON-структуры через позиционную регулярку (capture group по порядку полей) ломается при добавлении/перестановке полей. Результат — молчаливо неверное значение без ошибки.

**Исправление:** использовать `json.loads()` + именованный доступ к полям.

## Ловушка 4: Отсутствующее поле → молчаливый fallthrough

Отсутствие поля `created_at` в записи приводило к fallthrough к следующей ветке логики без явного статуса. Классификатор принимал «решение» без данных.

**Исправление:** явный `needs-review` статус при отсутствующем обязательном поле.
