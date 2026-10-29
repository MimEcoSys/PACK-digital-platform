---
id: DP.FM.694
name: "Запасной вариант ограничения времени без timeout: wait на убитом сторожевом процессе возвращает 143 и роняет вызывающего под set -e"
name_ru: "Запасной вариант ограничения времени без timeout: wait на убитом сторожевом процессе возвращает 143 и роняет вызывающего под set -e"
name_en: "A fallback time limit without timeout: wait on a killed watcher process returns 143 and aborts the caller under set -e"
type: failure-mode
pack: PACK-digital-platform
domain: digital-platform / shell-scripts
status: draft
trust: medium
epistemic_stage: forming
created: "2026-10-29"
valid_from: "2026-10-28"
summary: "В run_limited (macOS bash 3.2, без timeout) строка wait на только что убитом сторожевом процессе возвращает 143. Под set -e голый вызов функции завершает скрипт с кодом 143, хотя команда прошла успешно. Вызовы внутри if, || и $(...) дефект маскируют."
schema_version: 1
source: "файл scripts/lib/run-limited.sh в iwe-local-config (закрытие сессии 2026-10-28)"
---

# DP.FM.694 — Запасной вариант ограничения времени без timeout: wait на убитом сторожевом процессе роняет вызывающего под set -e

## Симптом

В `run_limited` (macOS bash 3.2, без `timeout`) строка `wait "$watcher"` возвращает 143, так как сторожевой процесс только что убит. `set -e; run_limited 3 true; echo after` не печатает `after` и завершается с кодом 143, хотя команда прошла успешно.

## Механизм

Статус `wait` на убитом процессе — не успех (128 + номер сигнала SIGTERM); под `set -e` «голый» вызов роняет скрипт. Вызовы внутри `if`, `||` и `$(...)` дефект маскируют, потому что `set -e` в них не действует.

## Тест обнаружения

«Есть ли вызов функции под `set -e` вне `if`/`||`? Проверялся ли он «голым»?» Тест на вызове в `if` дефект не покажет.

## Противодействие

Делать `wait` устойчивым к `set -e` (`wait ... || true`) и убрать хвостовой `sleep`. В файле источника ожидание сторожевого процесса записано как `wait "$watcher" 2>/dev/null || true`.

## Границы

Один скрипт, bash 3.2 на macOS. Карточка не утверждает, что тот же статус возникает в других оболочках.

## Источник

Файл `scripts/lib/run-limited.sh` в iwe-local-config; закрытие сессии 2026-10-28. Конкретный commit не указан: в источнике названный хэш относился к другому изменению.
