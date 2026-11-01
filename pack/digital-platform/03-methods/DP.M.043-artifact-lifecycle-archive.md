---
id: DP.M.043
name: "Рабочий процесс обращения с генерируемыми артефактами: явный archive-шаг с retention-окном"
type: method
status: active
valid_from: 2026-05-14
source: "WP-149 Ф-feedback-loop, DS-autonomous-agents commit d34cc88"
---

# DP.M.043: Рабочий процесс обращения с генерируемыми артефактами — явный archive-шаг с retention-окном

## Проблема

Без archive-шага папка `daily/` копится → агент при следующем render читает все исторические файлы как «текущие» → context window раздувается + устаревший HorizonContext засоряет daily следующего дня.

## Паттерн

При каждом периодическом render-событии: сначала archive → затем creation.

## Forces

_Какие конкурирующие давления удерживает метод._

| Force | Tension |
|-------|---------|
| Узкое retention-окно (шаг 1: «текущая неделя», «последние 7 дней» — держит `daily/` компактным, ограничивает context window) ↔ достаточность истории для feedback-loop (Читалка ищет `*-reflection.md` за те же 7 дней) | Слишком узкое окно теряет reflection до того, как reflection-reader успеет её прочитать; слишком широкое — возвращает проблему раздувания, которую метод решает |
| Archive строго ДО creation (Инварианты: «archive-шаг предшествует creation-шагу») ↔ простота реализации post-creation archive («допишем в конце функции») | Post-creation archive проще запрограммировать, но оставляет устаревший HorizonContext в daily следующего дня хотя бы на один цикл — ровно та проблема, которую паттерн устраняет |

## Шаги

1. **Определить retention-окно** (пример: «текущая неделя», «последние 7 дней»)
2. **Вызвать archive-функцию** при render-событии (weekly render, day-open)
3. **archive-функция** перемещает артефакты older than retention window из `daily/` в `history/`
4. **Читалка** работает по `history/` в retention-окне: ищет `*-reflection.md` за 7 дней

## Инварианты

- Archive-шаг предшествует creation-шагу (не post-creation)
- Retention-окно явно задано в коде (не «всё кроме последнего»)
- Archive ≠ delete: `history/` сохраняет файлы; feedback-loop агента читает из `history/`

## Bias-Annotation

_Куда систематически съезжает внимание практикующего._

| Bias | Direction of distortion |
|------|--------------------------|
| «7 дней» переносится по умолчанию | При применении паттерна к новому агенту (Применимо: session log rotation, email digest history) внимание съезжает к копированию конкретного числа «7 дней» из personal-guide-render кейса вместо расчёта retention-окна под собственный use case — Инварианты требуют явности окна, но не требуют конкретного значения |
| Тест воспринимается как галочка, не как end-to-end проверка | «Убей процесс после archive-шага → подними» описан как простой чек, но внимание смещается на проверку «функция archive_old_daily существует и не падает», а не на факт, что reflection-reader реально находит файлы в `history/` после настоящего перезапуска |

## Тест

Убей процесс после archive-шага → подними → reflection-reader находит ожидаемые файлы в `history/` = паттерн применён корректно.

## Применимо

Personal-guide-render, любой агент с rolling-window контекстом: weekly plan archives, session log rotation, email digest history. Порог применения: >14 артефактов одного типа ИЛИ ожидается накопление за >1 месяц.

## Связи

- Реализован в: `DS-autonomous-agents/personal_guide_agent.py` (archive_old_daily)
- Используется с: AS.M.016 (Reflection-driven daily personalization) — рефлексии перемещаются в history/, не теряются

---

> 2026-07-27 — миграция на обогащённый формат карточки (Forces + Bias-Annotation), WP-448 Ф12 Батч 3 (суб-батч 2). Эталон формата: `SPF/pack-template/03-methods/_method-card-template.md`.
