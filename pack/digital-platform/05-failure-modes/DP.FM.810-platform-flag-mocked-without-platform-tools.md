---
id: DP.FM.810
name: "Тест подменяет признак платформы, но не её утилиты: на настоящей другой ОС он падает при верном поведении"
name_ru: "Тест подменяет признак платформы без её утилит"
name_en: "A test mocks the platform flag but not the platform tools and fails on the real other OS"
type: failure-mode
status: draft
created: "2026-11-21"
valid_from: "2026-11-11"
pack: PACK-digital-platform
domain: digital-platform / test-portability
schema_version: 1
trust: observed
epistemic_stage: forming
related:
  see_also: [VR.FM.055]
source: "захват находок 11.11.2026; scripts/tests/test_dry_run_gate.py"
source_capture: "DS-my-strategy/inbox/captures/2026-11.md — «Тест, зависящий от машины автора, ложно падает у других…»"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-11-20-inbox-check-5.md"
source_candidate: 3
---

# Подмена признака платформы без подмены её инструментов

## Симптом

По захвату, тесты подменяют `uname` на Linux/CYGWIN и падают на настоящем macOS: код под подменой вызывает GNU `stat -c`, которого на macOS нет, хотя проверяемое поведение верно.

## Механизм

Подменён признак «мы на Linux», а платформенно-зависимые команды остались настоящими. Тест проверяет несуществующее сочетание «признак одной ОС + утилиты другой».

## Противодействие

Подменять признак ОС и зависимые от неё команды вместе. Это мера из разбора кандидата, а не подтверждённое изменение тестов.

## Границы

Первая часть исходного захвата — путь к реестру правил из `$HOME` автора — уже покрыта VR.FM.055. Эта карточка относится к тестированию программного кода, которое манифест PACK-verification прямо исключает из своей области; поэтому она размещена здесь, а не в продолжении VR.FM.055.
