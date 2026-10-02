---
id: DP.FM.523
type: failure-mode
status: draft
created: "2026-10-02"
valid_from: "2026-09-26"
name: "`timeout` без `--kill-after` не ограничивает процесс, игнорирующий TERM: замок держится, пока жив процесс, а не заданный срок"
name_ru: "`timeout` без `--kill-after` не ограничивает процесс, игнорирующий TERM: замок держится, пока жив процесс, а не заданный срок"
name_en: "`timeout` without `--kill-after` does not bound a process that ignores TERM: a held lock lasts as long as the process lives, not the configured deadline"
summary: "Сетевые операции гейта и брокера под удерживаемым замком были обёрнуты в `timeout N git fetch ...`. `timeout` по умолчанию посылает только SIGTERM; процесс, игнорирующий TERM, продолжает работать после срока, и замок держится до его естественного завершения. Воспроизведено синтетически: `timeout 0.2` завершился через 2.12 с для процесса, игнорирующего TERM и работающего 2 с. Исправление: `timeout --kill-after=5s N ...` в обоих скриптах."
pack: PACK-digital-platform
domain: digital-platform
schema_version: 1
trust: empirical
epistemic_stage: pattern
source: "session-transcript 2026-09-26 (холодное ревью review-01.md) + git diff за сессию (IWE@e0dd985e5f, WP-530 Ф66)"
source_capture: "DS-my-strategy/inbox/captures/2026-09.md:4586"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-09-28-inbox-check-2.md"
source_candidate: 1
related:
  see_also: ["DP.FM.491"]
tags: [timeout, kill-after, sigterm, lock, deadline]
---

# DP.FM.523 — `timeout` без `--kill-after` не ограничивает процесс, игнорирующий TERM

## Симптом

Сетевые операции гейта и брокера под удерживаемым замком были обёрнуты в `timeout N git fetch ...`. Холодное ревью указало, что `timeout` без `--kill-after` может удерживать замок WP-lock дольше заданного срока, если дочерний процесс игнорирует TERM.

## Причина

`timeout` по умолчанию посылает только SIGTERM. Процесс, который TERM игнорирует, после срока продолжает работать, и замок держится до естественного завершения этого процесса, а не до истечения заданного таймаута. Что именно git-транспорт игнорирует TERM, в источнике не показано; воспроизведён только механизм на синтетическом процессе.

## Проверка воспроизведением

Синтетический процесс, игнорирующий TERM и работающий 2 секунды: `timeout 0.2 <процесс>` завершился через 2.12 секунды.

## Исправление

`timeout --kill-after=5s N ...` в обоих скриптах (гейт и брокер).

## Тест обнаружения

«Есть ли под удерживаемым замком вызов `timeout` без `--kill-after`?» Да → срок не гарантирован, если процесс игнорирует TERM. Проверка: запустить под `timeout` процесс, специально игнорирующий TERM, и сравнить фактическое время с заданным сроком.

## Связанные документы

- DP.FM.491 (trap очистки, зарегистрированный до захвата, снимает чужой замок): там сигнал доходит и реакция слишком широка; здесь сигнал TERM процесс игнорирует, и замок держится дольше срока.
- Источник: WP-530 Ф66, review-01.md.
