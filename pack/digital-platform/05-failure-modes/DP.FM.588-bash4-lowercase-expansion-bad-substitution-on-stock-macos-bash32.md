---
id: DP.FM.588
name_ru: "Синтаксис параметрического расширения bash 4+ (`${var,,}`) падает `bad substitution` на системном bash 3.2.57 (macOS default)"
name_en: "bash 4+ parameter-expansion syntax (`${var,,}`) fails with 'bad substitution' on the stock bash 3.2.57 shipped with macOS"
summary: "Понижение регистра строки через `${name,,}` (требует bash 4.0+) завершалось ошибкой парсера `bad substitution` при выполнении на системном `/bin/bash` версии 3.2.57 — дефолтная версия, поставляемая Apple на macOS без Homebrew. Другой механизм, чем отсутствие бинарника (DP.FM.431/DP.FM.503): здесь не хватает синтаксической возможности самого интерпретатора."
type: failure-mode
status: draft
created: "2026-10-09"
valid_from: "2026-10-09"
pack: PACK-digital-platform
domain: digital-platform / shell-portability
schema_version: 1
trust: observed
epistemic_stage: forming
related:
  see_also: [DP.FM.431, DP.FM.503, DP.METHOD.059]
source: "git commit 0954bfba в FMT-exocortex-template (issue #1108)"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:2061"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-10-inbox-check.md"
source_candidate: 5
tags: [bash, macos, portability, parameter-expansion, bad-substitution]
---

# DP.FM.588 — bash4-синтаксис `${var,,}` падает на стоковом bash 3.2.57 (macOS)

## Симптом

Понижение регистра строки через `${name,,}` — синтаксис, требующий bash версии 4.0 или новее, — завершалось ошибкой разбора `bad substitution` при запуске на системном `/bin/bash` 3.2.57, который Apple поставляет по умолчанию на macOS (заморожен на последней GPLv2-версии; современный bash ставится только отдельно, обычно через Homebrew).

## Причина

Скрипт был написан и проверен на машине с современным bash (4+), где `${var,,}`/`${var^^}` работают штатно. На стоковом macOS без установленного через Homebrew современного bash системный `/bin/bash` остаётся версии 3.2 — синтаксис не распознаётся парсером этой версии: ошибка возникает на этапе разбора самой конструкции, не на этапе её выполнения, то есть не просто «неправильный результат», а неочевидное сообщение парсера.

## Тест обнаружения

«Скрипт использует bash-синтаксис, требующий версию 4+ (`${var,,}`, `${var^^}`, `declare -A`, `wait -n`, `mapfile`), и должен выполняться на стоковом macOS без гарантии установки современного bash через Homebrew?» Да → риск падения с ошибкой разбора парсера, а не просто «функция работает неправильно».

## Противодействие

Заменить версия-зависимый синтаксис на POSIX-совместимую конструкцию (для понижения регистра — `tr '[:upper:]' '[:lower:]'` или `awk`), либо явно объявить современный bash обязательной зависимостью и fail-fast с понятным сообщением при его отсутствии — не оставлять синтаксическую ошибку парсера единственным сигналом. Найдено статическим guard-линтером того же раунда исправлений, который сразу поймал ещё 2 аналогичных нарушения в другом коде репозитория.

## Связи

- **DP.FM.431** (отсутствие `timeout` при прямом вызове) и **DP.FM.503** (`flock` misdiagnosis) — тот же аудит (issue #1108) и тот же корневой класс допущения «GNU/Homebrew-инструмент или современный bash доступен на стоковом macOS», но другой механизм: там — отсутствующий БИНАРНИК, здесь — отсутствующий СИНТАКСИС самого интерпретатора.
- **DP.METHOD.059** (bash 3.2 portability, python3 heredoc) — смежная область переносимости на bash 3.2, другой конкретный механизм (heredoc/embedded python, не parameter expansion).

## Происхождение

git commit `0954bfba` в FMT-exocortex-template (issue #1108).
