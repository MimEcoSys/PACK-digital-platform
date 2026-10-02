---
id: DP.FM.524
type: failure-mode
status: draft
created: "2026-10-02"
valid_from: "2026-09-26"
name: "Правка исходников без пересборки закоммиченного bundle: в main лежал bundle с заглушками"
name_ru: "Правка исходников без пересборки закоммиченного bundle: в main лежал bundle с заглушками"
name_en: "Editing sources without rebuilding the committed bundle: main still held a bundle with placeholders"
summary: "Сервис отдаёт страницы гида и `llms.txt` из закоммиченного `bundle/`, а не из исходников. Коммит 4b482f1 обновил только `src/guide-pages/*.md`; в main по-прежнему лежали заглушки «текст ещё не написан». Тесты (30/30) шли на фикстурах и содержимого bundle не касались; дефект поймало холодное ревью по `grep` и живому запуску сервера."
pack: PACK-digital-platform
domain: digital-platform
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit 4b482f1 и 9bbbd0a в open.system-school.ru (WP-581); пир-сессия 2026-09-26-01-wp581-guide-content-handoff"
source_capture: "DS-my-strategy/inbox/captures/2026-09.md:4663"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-09-28-inbox-check-3.md"
source_candidate: 4
related:
  see_also: ["DP.M.486"]
tags: [build-artifact, committed-bundle, rebuild, stale-artifact]
---

# DP.FM.524 — Правка исходников без пересборки закоммиченного bundle

## Симптом

Сервис отдаёт страницы гида и `llms.txt` из закоммиченного в git `bundle/`. Коммит 4b482f1 обновил только `src/guide-pages/*.md`. В main по-прежнему лежал bundle с заглушками «текст ещё не написан», хотя `git log` показывал, что контент обновлён.

## Причина

Исходники и закоммиченный build-выход живут отдельно, а пересборка (`npm run build:bundle`) — отдельный шаг, который README требует после правки страниц. Тесты прошли на фикстурах (lint, build, test 30/30, content-lint) и содержимого bundle не касались, поэтому зелёный результат не говорил об обновлении артефакта, который читает сервис.

## Как нашли

Холодное ревью: `grep "ещё не написан" bundle/llms.txt` и живой запуск сервера. Сборка заняла около 8 секунд.

## Тест обнаружения

«После правки исходников bundle пересобран, и в нём нет старого текста? Фактическая выдача проверена живым запросом (`/go/fpf/<slug>`, `/llms.txt`)?» Нет → в main лежит старый артефакт. Применимо к репозиториям, где build-выход коммитится и раздаётся как есть; там, где сборка идёт автоматически на каждом деплое, правка исходников и пересборка неразделимы.

## Связанные документы

- Источник: коммиты 4b482f1 и 9bbbd0a в `open.system-school.ru` (WP-581, гид FPF).
