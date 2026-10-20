---
id: DP.FM.629
type: failure-mode
status: draft
created: "2026-10-16"
valid_from: "2026-10-15"
name: "Стоковый macOS bash 3.2 не приглушает errexit внутри sourced-файла под pipefail, как bash 4.4+/5 — отсутствующий необязательный ключ конфигурации молча убивает весь вызывающий пайплайн"
name_ru: "Стоковый macOS bash 3.2 не приглушает errexit внутри sourced-файла под pipefail, как bash 4.4+/5 — отсутствующий необязательный ключ конфигурации молча убивает весь вызывающий пайплайн"
name_en: "Stock macOS bash 3.2 does not suspend errexit inside a sourced file under pipefail the way bash 4.4+/5 do — a missing optional config key silently kills the whole calling pipeline"
summary: "grep необязательного ключа backup_dir: в params.yaml возвращает 1, когда ключа нет (штатный случай); под pipefail это останавливает весь пайплайн целиком, а bash 3.2 (дефолтный /bin/bash на macOS) не гасит errexit внутри sourced-файла так, как делают bash 4.4+/5 — тихо убивая вызывающий скрипт. Фикс — || true на весь пайплайн, а не только на grep."
pack: PACK-digital-platform
domain: digital-platform / shell-scripting
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit 3acbbad9 в FMT-exocortex-template; WP-7 Ф231, issue #1235"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:3918"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-16-inbox-check-2.md"
source_candidate: 1
related:
  see_also: [DP.FM.547, DP.FM.457, DP.FM.518, DP.FM.588, DP.FM.208]
tags: [shell, bash32, macos, pipefail, errexit, sourced-file, optional-config-key, silent-failure]
---

# DP.FM.629 — bash 3.2 (macOS) не гасит errexit в sourced-файле под pipefail

## Тезис и механизм ошибки

`grep` необязательного ключа `backup_dir:` в `params.yaml` возвращает код 1, когда ключа нет — штатный случай для установки без локального override. Под `set -euo pipefail` это останавливает весь пайплайн чтения конфигурации целиком. Усугубляющий фактор: `/bin/bash` на macOS по умолчанию — ветка 3.2 (последняя версия до перехода FSF на GPLv3), которая не приглушает `errexit` внутри sourced-файла так, как это делают bash 4.4+/5 — поэтому ошибка не остаётся локализованной в sourced-скрипте, а тихо убивает вызывающий процесс (`backup-icloud.sh`).

## Границы

Применимо к shell-пайплайну, который (а) читает необязательный ключ через `grep`/аналог, (б) работает под `pipefail`/`errexit`, и (в) sourced из другого скрипта, который может запускаться под дефолтным `/bin/bash` macOS (3.2), а не под явно установленным bash 4+. На раннерах с bash 4+/5 по умолчанию тот же код мог бы вести себя иначе (ошибка осталась бы локализованной в sourced-контексте).

## Тест обнаружения

«Pipeline читает необязательный ключ конфигурации через `grep`/`egrep` под `pipefail`, и скрипт может быть sourced в контексте, где интерпретатор — стоковый `/bin/bash` macOS (3.2)?» Да, и нет `|| true` на весь пайплайн (не только на отдельную команду) → риск тихой смерти вызывающего скрипта именно на штатном «ключа нет» случае.

## Противодействие

`|| true` на весь пайплайн чтения опционального ключа (не только на `grep`), либо явный gate на интерпретатор bash 4+, либо перенос такой логики в язык, не зависящий от version-specific errexit-семантики.

## Связи

- `DP.FM.547`, `DP.FM.457` — тот же класс «pipefail превращает штатный `grep`-без-совпадения в фатальный выход», другой конкретный путь данных (прямое присваивание / SIGPIPE против sourced-файла); здесь добавляется version-specific фактор bash 3.2 vs 4.4+.
- `DP.FM.518`, `DP.FM.588`, `DP.FM.208` — тот же субстрат «стоковый macOS bash 3.2 ведёт себя иначе, чем ожидает автор», другой конкретный механизм (brace expansion / lowercase expansion / IFS) — здесь: errexit-suspension в sourced-файле.

## Происхождение

git commit `3acbbad9` в FMT-exocortex-template; WP-7 Ф231, issue #1235. Тот же коммит чинит ещё 3 issue того же дня похожей природы (регистронезависимое сравнение имён файлов; устаревший конфиг с прошлой установки, выигрывающий у текущего из-за однолокационного поиска) — не описаны здесь отдельно, требуют собственной проверки при повторном появлении.
