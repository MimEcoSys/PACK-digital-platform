---
id: DP.FM.572
type: failure-mode
status: draft
created: "2026-10-08"
valid_from: "2026-10-08"
name: "State machine раннера считает успехом только собственное терминальное завершение — «цель достигнута другим легитимным каналом» засчитывается как ошибка повторного действия"
name_ru: "State machine раннера считает успехом только собственное терминальное завершение — «цель достигнута другим легитимным каналом» засчитывается как ошибка повторного действия"
name_en: "Runner state machine recognises only its own terminal completion as success — 'goal already reached via another legitimate channel' is treated as a duplicate-action error"
summary: "Раннер quick-close не распознаёт как успех ситуацию, когда семафор уже закрыт тем же агентом другим легитимным путём (peer-conversation) до запуска раннера. После перехода в состояние running раннер лишается короткого пути cancel; попытка повторно закрыть уже отсутствующий семафор завершается терминально. Переносимо: state machine должна явно различать «цель ещё не достигнута» и «цель уже достигнута другим легитимным каналом»."
pack: PACK-digital-platform
domain: digital-platform / process-runner
schema_version: 1
trust: observed
epistemic_stage: forming
source: "git commit 6ad9a682 в DS-my-strategy (WP-484 Ф180)"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:1630"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-08-inbox-check-3.md"
source_candidate: 3
related:
  see_also: []
tags: [state-machine, runner, semaphore, duplicate-action, idempotency, quick-close]
---

# DP.FM.572 — Раннер принимает за ошибку цель, уже достигнутую другим легитимным каналом

## Тезис и механизм ошибки

State machine раннера знает только один путь к успеху — собственное терминальное завершение. Когда цель (закрытие семафора сессии) уже достигнута до или параллельно с запуском раннера другим легитимным каналом (peer-conversation → `session-guard.sh close`), раннер не распознаёт это как успех. Вместо этого он пытается выполнить уже выполненное действие и терминально падает («новый RUN требует точного открытого semaphore»).

Структурная причина: переход `close_obligation` в `running` при явном старте раннера закрывает короткий путь `cancel --action peer-session-close`, и graceful-ветка реагирует только на отсутствие WP, а не на отсутствие семафора.

## Диагностический принцип

В любой state machine раннера, где шаги неидемпотентны, нужен явный путь: «цель уже достигнута другим легитимным каналом» → успех, а не ошибка повторного действия.

## Проверка

«Если целевое состояние (семафор закрыт, файл создан, ресурс освобождён) уже достигнуто до запуска этого шага, раннер возвращает успех или ошибку?» Ошибка → риск DP.FM.572.

## Фикс

Добавить в graceful-ветку раннера проверку: «семафор отсутствует И это я сам его закрыл ранее легитимным путём» → успех. Либо сделать шаг idempotent: «семафор уже закрыт» = success в любом случае.

## Границы

Применимо к любому process-runner с state machine, где конечное состояние может быть достигнуто несколькими независимыми путями. Не ограничивается session-guard или семафорами.

## Связи

Источник: WP-484 Ф180; peer-session 2026-10-07-01-template-sync-failure-diagnosis.
