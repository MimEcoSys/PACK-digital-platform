---
id: DP.FM.755
name: Backfill «проба, затем полный» без ON CONFLICT откатывает весь полный прогон — sample-строки первыми дают UniqueViolation и Postgres роняет всю транзакцию
type: failure-mode
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_backfill_sample_then_full_needs_on_conflict.md (23.07; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [DP.FM.754, PACK-digital-platform]
---

# DP.FM.755: sample→full backfall без ON CONFLICT

## Симптом
Полный прогон бэкфилла вставил 0 из ~12 600 строк: полный запрос с тем же ORDER BY первыми встретил строки пробы, первый же duplicate дал UniqueViolation, Postgres отклонил все последующие операции транзакции. Fails safe (rollback), но молча обнуляет смысл sample-проверки.

## Причина
Баг проявляется только на ВТОРОМ запуске скрипта против той же цели. Проверка «sample run работает» его не ловит — ни dry-run, ни execute в изоляции.

## Антипаттерн → Паттерн
- **Антипаттерн:** plain INSERT в одной транзакции; идемпотентность «потом добавим».
- **Паттерн:** любой one-time скрипт, который может быть запущен дважды (sample→full, resume после частичного сбоя) — с `ON CONFLICT (unique_columns) DO NOTHING` с первой версии.

## Тест обнаружения
Отдельный вопрос ревью: «идемпотентен ли этот скрипт при повторном запуске?» — так же, как «есть ли у фикса неявный верхний предел».
