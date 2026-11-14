---
id: DP.FM.766
name: Имя колонки в FDW-таблице не карта в справочник — проверять, что физически пишет writer-сервис, иначе ×2.5 ошибка в проде
type: failure-mode
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_fdw_writer_semantics.md (WP-327 Ф3, 20.05; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [AR.201, PACK-digital-platform]
---

# DP.FM.766: FDW writer-семантика ≠ структура таблицы

## Симптом
`indicators.calculated_profile.qualification_level INT` по имени выглядит как ссылка на справочник reference.qualification_level (11 ступеней). Реально writer (profiler, другой репо) пишет числовую часть LMS L-кода (L7 → 7, шкала из 8 степеней + предучебных, коллизия L2/L25=2). Smoke на реальном человеке: скидка занижена ×2.5.

## Правило
Никогда не доверять имени колонки в FDW-таблице как карте в справочник без проверки writer'а. Conjunctive check:
1. Найти writer колонки в коде (`grep -rn "UPDATE <table> SET <column>"`).
2. Прочитать, что именно он пишет (вычисляет/копирует/парсит).
3. Сравнить с предполагаемым source-of-truth.
4. Расхождение — зафиксировать в context-файле до использования.

## Долгосрочно
OwnerIntegrity-запись для каждой shared колонки: «column X в таблице Y → writer = Z, формат = …, source-of-truth = …». Для FDW обязательно — writer живёт в другом репо и эволюционирует независимо.
