---
id: DP.FM.336
name: "Resource-picker отбирает по recency без фильтра active-status"
type: failure-mode
status: active
valid_from: 2026-07-11
source: "WP-7 D6; FMT-exocortex-template commit 448daac; DS-ai-systems commit 170910f"
related:
  see_also: []
tags: [resource-picker, recency, active-status, archived, DayPlan, WeekPlan]
---

# DP.FM.336 — Resource-picker отбирает по recency без фильтра active-status

## Симптом

Агент/инструмент открывает «не тот» артефакт — архивный план прошлой недели вместо текущего, закрытый WP-context вместо активного. Воспроизводится двумя независимыми системами с одинаковым критерием выбора «самый новый по дате».

## Механизм

```python
# Антипаттерн: только recency
dayplan = get_latest_by_date("current/Plan W*.md")

# Фикс: recency + active-status
dayplan = get_latest_by_date(
    "current/Plan W*.md",
    filter=lambda f: not is_closed(f) and days_since(f) <= 7
)
```

В системах с архивированием (DayPlan → archive/, WeekPlan → closed) «последний по дате» = «последний созданный», включая уже закрытые артефакты.

## Когда срабатывает

- Артефакты архивируются (или помечаются закрытыми) без физического удаления
- Picker выбирает по `max(mtime)` или `max(date_in_filename)`
- Артефакт закрыт давно, но дата в имени файла > дата текущего открытого артефакта

## Фикс

Добавить explicit active-status filter наряду с recency:
1. Проверить `closed_date` отсутствует в frontmatter ИЛИ
2. Дата файла ≤ N дней назад ИЛИ
3. Файл находится в «активной» директории (не `archive/`)

## Вариант: «самый свежий» среди одновременно активных ресурсов параллельных сессий

Если ресурсы принадлежат параллельным сессиям и все активны одновременно, фильтр active-status не помогает: активны все кандидаты, а «самый свежий» принадлежит не обязательно нужной сессии. Нужен адресный поиск по идентификатору сессии (владельца), а не выбор по давности. Пример: пир-пайплайн Kimi по РП-568/538 писал в изолят РП-561, потому что preflight брал самый свежий `kimi-*.open`.

## Тест

«Picker нашёл артефакт по "последнему" критерию — он всё ещё активен?» Нет → вероятно DP.FM.336.
