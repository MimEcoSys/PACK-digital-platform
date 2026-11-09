---
id: DP.FM.589
type: failure-mode
status: draft
created: "2026-10-11"
valid_from: "2026-10-11"
name: "Цикл обновления переустанавливает только экземпляры с включённым auto — установленные с auto:false остаются с устаревшей конфигурацией автозапуска"
name_ru: "Цикл обновления переустанавливает только экземпляры с включённым auto — установленные с auto:false годами остаются с устаревшей конфигурацией автозапуска"
name_en: "Update loop reinstalls only auto-enabled instances — auto:false installs keep a stale autostart config indefinitely"
summary: "Переустановка файла автозапуска (launchd plist) при обновлении фильтровала роли по auto:true; роли с auto:false не обновлялись, и их plist годами оставался без переменной, добавленной в новой версии, что давало ложный диагноз «конвейер не найден». Обновление должно охватывать все установленные экземпляры независимо от auto, сохраняя состояние loaded/unloaded."
pack: PACK-digital-platform
domain: digital-platform / installation-update
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit 10f7bbbb в FMT-exocortex-template (#1143, #1178, WP-529)"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md (auto:false)"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-11-inbox-check-2.md"
source_candidate: 2
related:
  see_also: []
tags: [update, install, autostart, stale-config]
---

# DP.FM.589 — Обновление охватывает только auto-экземпляры

## Тезис и механизм ошибки

Цикл переустановки при обновлении проверял только `auto: true`. Роль, поставленная до версии 0.40.0 с `auto: false`, не переустанавливалась; её файл автозапуска остался без переменной `IWE_SCRIPTS` (добавлена в 0.40.0). Стратег диагностировал «конвейер не найден» ложно.

## Исправление

Обнаруживать установленные экземпляры независимо от `auto` (по `PLIST_DST=` в install.sh и наличию файла на диске) и обновлять их конфигурацию, сохраняя состояние loaded/unloaded (`IWE_SKIP_LOAD`).

## Проверка

«Фильтр цикла обновления зависит от флага автоматического режима, а не от факта установки экземпляра?» Да → класс DP.FM.589.

## Связи

- WP-529 #1143, #1178.
