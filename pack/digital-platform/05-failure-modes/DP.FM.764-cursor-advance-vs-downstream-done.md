---
id: DP.FM.764
name: Новая downstream-функция в polling-воркере с persistent cursor не действует ретроактивно — нужен backfill plan при деплое
type: failure-mode
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_cursor_advance_vs_downstream_done.md (WP-310, 15-16.05; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [DP.M.620, PACK-digital-platform]
---

# DP.FM.764: cursor advance ≠ downstream done

## Симптом
Воркер обработал 7 переходов и продвинул cursor; downstream-функция (enqueue в очередь) появилась в коде через 5 часов после этого. Cursor правильный, 7 переходов потеряли downstream — очередь пустая, в логах нет ошибок.

## Причина
Новая downstream-функция не действует задним числом: cursor двигается только вперёд, обработанные строки не пере-обрабатываются.

## Что делать при деплое
1. Перед merge оценить retro-эффект: «повторит ли воркер обработку уже пройденных строк?» — почти всегда нет.
2. Решить явно: (а) backfill SQL в downstream-таблицу для обработанных строк (с маркером source для аудита); (б) сдвинуть cursor назад (риск двойного срабатывания других downstream); (в) принять gap.
3. Backfill — отдельным шагом, с явным маркером.

## Симптомы gap
Cursor продвинут + downstream-таблица пуста за тот же период + в логах нет ошибок. Тест: `COUNT(source > cursor) = 0` + `COUNT(downstream WHERE source_marker=…)=0` → gap есть.
