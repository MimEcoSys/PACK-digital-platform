---
id: DP.SC.045
name: Анализ ограничения системы (TOC)
name_ru: Анализ ограничения системы (TOC)
name_en: Constraint Analysis (TOC)
type: sc
status: draft
layer: L4-Personal
summary: "Потребитель (пилот / Стратег / Декомпозитор / Навигатор) получает на выходе пятифазного ВДВ-каскада три артефакта: System Card (классификация системы-конвейера), Constraint Brief (описание ограничения с trichotomy + class), Stage Dependency Map (план работы как dependency graph без дат и часов). SC-first: первой проверяется работоспособность функциональных обещаний, не структура pending-РП."
consumer: Пилот (R1 IWE Creator), Стратег (R26), Декомпозитор (R29), Навигатор (R27), Диагност (DP.ROLE.042 — частный случай для учебного конвейера)
created: 2026-05-20
updated: 2026-05-20
related:
  realizes: []
  uses:
    - DP.ROLE.054                  # Аналитик ограничений — носитель
    - DP.WP.016                    # Stage Dependency Map — формат одного из выходов
    - DP.M.061                     # Bottleneck-Shift Detection — поддерживающий метод
    - PD.PRINC.046                 # Mental Model as Constraint (Tendon)
    - MIM.FM.011                   # Policy treated as Resource (Schragenheim)
    - .claude/skills/bottleneck-pick
  see_also: [DP.SC.132]            # Диагностика ученика — специализация для учебного конвейера
wp: WP-313
---

# [DP.SC.045] Анализ ограничения системы (TOC)

## Правило (инвариант)

> Что ВСЕГДА должно выполняться. Нарушение = провал SC.

- **Идентификация системы-конвейера обязательна.** Без классификации (учебный / работ / когортный конвейер) signal-scan не запускается. Output без указания типа системы = провал Ф1.
- **SC-first порядок.** Ф2 «Scan promises» выполняется ДО Ф3 «Identify constraint». Документо-центричный анализ (что pending в РП) без предварительной проверки функциональных обещаний потребителя — анти-паттерн.
- **Trichotomy + class — обязательны в Constraint Brief.** Trichotomy (Tendon): Work Flow / Work Process / Work Execution. Class: Policy / Resource / Cognitive. Exploit-strategy зависит от обеих осей.
- **NBR после любого EC injection.** 3 negative branches + trim каждой. Без NBR — провал Ф4.
- **Stage Dependency Map — без дат и часов.** Только структурная зависимость: узлы=этапы, рёбра=жёсткая зависимость, параллельность=внутри узла. Не PERT (без оценок), не Gantt (без дат), не Kanban (без статусов).
- **External-зависимости — явные.** Если этап зависит от работ в другом РП / репо / внешнего поставщика — явное external-ребро.
- **Calibration record — обязателен.** Каждое применение → YAML в `DS-my-strategy/inbox/bottleneck-pick-runs/<date>-<target>.yaml`.
- **PII не пишутся в Calibration record.** Имена пилотов когорты, raw-тексты переписки, email — не сохраняются. Используются только UUID и числовые сигналы.

---

## Обещание

**Кому:**
- **Пилот (R1 IWE Creator)** — главный потребитель: «открыл WP-NNN → получил обоснованный выбор bottleneck → план этапов → сделал»
- **Стратег (R26 / DP.ROLE.012)** — при отборе НЭП на стратегической сессии: «какое направление сейчас bottleneck для роста системы»
- **Декомпозитор (R29 / DP.ROLE.053)** — последовательно: Аналитик идентифицирует этапы, Декомпозитор декомпозирует каждый на физические артефакты с приёмкой
- **Навигатор (R27)** — при ответе пилоту «с чего начать»: использует `bottleneck_slot` Аналитика как контекст
- **Диагност (DP.ROLE.042)** — частный случай специализации: для учебного конвейера применяет FORM.089 RCS вместо общего signal-scan

**Зачем:**
- **Пилоту** — обоснованный выбор без когнитивных искажений (sunk cost, sexy work bias, recency). Защита от подмены продукта каналом доставки.
- **Стратегу** — диагностика «где сейчас Herbie системы» как вход в стратегическое решение.
- **Декомпозитору** — границы каждого этапа из Stage Dependency Map = вход для декомпозиции на физические артефакты.
- **Навигатору** — bottleneck-знание для нарративной адаптации фазы дуги.

**Что получит:** Три артефакта на выходе пятифазного ВДВ-каскада:

```
{
  "system_card": {
    "type": "учебный_конвейер | конвейер_работ | когортный_конвейер",
    "target": "<target-ref>",
    "promises": ["DP.SC.NNN: status", ...],
    "current_state": {...},
    "data_freshness": "..."
  },
  "constraint_brief": {
    "description": "...",
    "trichotomy": "work_flow | work_process | work_execution",
    "class": "policy | resource | cognitive",
    "signals_fired": ["queue_accumulation", "flow_efficiency", ...],
    "tool_selected": "five_steps | ec | five_steps_ec_nbr",
    "ec_injection": "..." | null,
    "nbr_trims": [...]
  },
  "stage_dependency_map": {
    "stages": [
      {"id": "stage_1", "label": "...", "parallel_works": [...], "external_deps": [...]},
      ...
    ],
    "edges": [
      {"from": "stage_1", "to": "stage_2", "type": "hard_dependency"},
      ...
    ]
  }
}
```

**Триггер:** Явный вызов `/bottleneck-pick --target <ref>` пилотом или другой ролью. Опциональные параметры: `--horizon`, `--depth`, `--scope`.

**Время отклика:** ≤15 мин для опытного применения (после калибровки); до 30 мин на первых применениях.

**Режим отказа:**
- target не найден → «Не нашёл `<target>`. Проверь номер или путь.» → СТОП.
- target = done-РП → «`<target>` уже закрыт. Укажи активный РП.» → СТОП.
- target пустой (нет структуры) → «Нет структуры для анализа в `<target>`.» → СТОП.
- Данные устарели (>7 дней без git-активности) → добавить ⚠️ к signal-scan, не останавливаться.
- EC не сходится (пустые assumptions) → fallback к Five Steps, отметить в output.
- Все кандидаты не agent-actionable → сообщить, без сценария.

---

## Свидетельства (критерий приёмки)

**Данные** (что фактически существует):

| Критерий | Как проверить |
|----------|--------------|
| 3 артефакта на выходе | Output content в чате: System Card + Constraint Brief + Stage Dependency Map присутствуют |
| Trichotomy + class заданы | grep `trichotomy:` AND `class:` в Constraint Brief |
| Stage Map без дат/часов | `grep -E '\b(due\|start\|end\|hours?\|days?_required\|deadline):' <stage-map>` — должно быть 0 матчей (точные имена полей, не подстрока). |
| External-зависимости явные | grep `external_deps:` в Stage Map; если есть external — указан target |
| Calibration record создан | `ls DS-my-strategy/inbox/bottleneck-pick-runs/<date>-*.yaml` после применения |
| SC-first порядок выполнен | В System Card есть `promises` section до Constraint Brief |

**Контекст** (при каких условиях обещание действует):

| Условие | Проверка |
|---------|---------|
| Скилл `/bottleneck-pick` зарегистрирован | `ls .claude/skills/bottleneck-pick/SKILL.md` |
| Аналитик в Pack оформлен | `ls PACK-digital-platform/pack/digital-platform/02-domain-entities/DP.ROLE.054-*.md` |
| Stage Dependency Map формат описан | `ls PACK-digital-platform/pack/digital-platform/04-work-products/DP.WP.016-*.md` |
| Calibration директория существует | `mkdir -p DS-my-strategy/inbox/bottleneck-pick-runs/` |

---

## Сценарии использования

### Сценарий 1: Зонтичный РП (ведущий)

**Триггер:** Пилот открывает зонтичный РП (например, WP-250 с 9 направлениями A-И) и спрашивает «что делать сначала».

**Поток:**
1. Пилот вызывает `/bottleneck-pick --target WP-250 --horizon wave-1`
2. Аналитик Ф1 классифицирует target как **конвейер работ** (зонтичный РП с направлениями)
3. Ф2 сканирует DP.SC, связанные с WP-250 (например, DP.SC.020 personal-development-program, DP.SC.132 learner-diagnostics): «Доставка персонального руководства работает? Диагностика проводится? Stage transitions фиксируются?»
4. Ф3 на основе SC-failing identif top-3 кандидата по signal-scan; trichotomy=Work Flow, class=Operational
5. Ф4 выбирает Five Steps + EC (есть policy-маркеры между «опереться на текущих 9 ранних пилотов» vs «расширить до 50 ожидающих»)
6. Ф5 строит Stage Dependency Map: stage_1=«activation 9 ранних пилотов» (параллельно: руководства + bot-сообщения + check-in); stage_2=«wave-rollout 5→15→30» (зависит от stage_1 ≥50% conversion); external_dep=«WP-310 Аттестатор daily-run работает»

**Результат:** Пилот видит обоснованный выбор «activation, не tech-фичи» + понимает зависимости + есть calibration record для проверки через 2 недели.

### Сценарий 2: Эпик с фазами

**Триггер:** Пилот ведёт эпик (например, WP-188 с 18 фазами и активной wave-1) и хочет выбрать следующую фазу.

**Поток:**
1. Пилот вызывает `/bottleneck-pick --target WP-188 --horizon wave-1`
2. Аналитик Ф1: классифицирует как **конвейер работ** (эпик с фазной структурой)
3. Ф2 сканирует обещания эпика (например, «когорта получает Day Open каждое утро»): какие из них сломаны?
4. Ф3 signal-scan по 18 фазам с фильтром horizon=wave-1; top-3 кандидата
5. Ф4 выбирает Five Steps (нет policy-конфликта, очевиден слабейший этап) + NBR (есть риск преждевременного broadcast)
6. Ф5 Stage Dependency Map: stage_1=«smoke на solo-pilot», stage_2=«broadcast wave-1», stage_3=«monitoring + feedback collection»; внешних зависимостей нет

**Результат:** Выбор фазы Ф17.9 (TG-broadcast) с предохранителями NBR.

### Сценарий 3: Стратегическая сессия (Стратег)

**Триггер:** Еженедельная стратегическая сессия. Стратег готовит вопросы для пилота: «какое из 14 направлений работы сейчас bottleneck?»

**Поток:**
1. Стратег вызывает `/bottleneck-pick --target DS-my-strategy --scope direct+related`
2. Аналитик Ф1: классифицирует как **конвейер работ всего governance-хаба** (множество активных РП)
3. Ф2 сканирует обещания governance: «WP-REGISTRY актуален? WeekPlan ≤200 строк? Inbox чистый? Strategy.md обновлён?»
4. Ф3 signal-scan по 14 направлениям; trichotomy=Work Process (внутри отдельного направления), class=Policy
5. Ф4 EC: «расширять направление A или закрывать долги по направлению Б?»; injection с NBR
6. Ф5 Stage Dependency Map: с приоритетом 1-2 этапов на ближайшую неделю

**Результат:** Стратег получает обоснованный input для НЭП-обсуждения с пилотом.

### Сценарий 4: Учебный конвейер пилота (Диагност-специализация)

**Триггер:** Диагност (DP.ROLE.042) получает запрос от пилота «какая моя ступень и что фиксить первым».

**Поток:**
1. Диагност вызывает `/bottleneck-pick --target rcs-profile:<account_id> --horizon next-stage`
2. Аналитик Ф1: классифицирует как **учебный конвейер пилота** (FORM.089 RCS)
3. Ф2 сканирует FORM.089-обещания: какие cp-срезы заполнены, какие пустые?
4. Ф3 signal-scan специфичный для RCS: stage_raw bottleneck, Δ baseline за 4 недели, gap до следующей ступени, dependency между слотами
5. Ф4 EC при двух кандидатах («качать W сейчас или сначала M4 quality?»); NBR обязателен (особенно для «нанять Диагноста» = elevate без exploit)
6. Ф5 Stage Dependency Map: stage_1=«заполнить слот W через рефлексию», stage_2=«нарастить M2 через ритм Strategy Sessions» (зависит от заполненного W); external_dep=«WP-310 stage_evaluator daily-run»

**Результат:** Пилот получает обоснованный выбор слота + понимание дуги развития + skip-вход для следующей ступени.

---

## Связанные документы

- [DP.ROLE.054](../02-domain-entities/DP.ROLE.054-constraint-analyst.md) — носитель методики (Аналитик ограничений / Constraint Analyst, R30)
- [DP.WP.016](../04-work-products/DP.WP.016-stage-dependency-map.md) — формат одного из выходов (карта этапов с зависимостями)
- [DP.M.061](../03-methods/DP.M.061-bottleneck-shift-detection.md) — bottleneck-shift detection после устранения tech-блокера
- [DP.SC.132](./DP.SC.132-learner-diagnostics.md) — диагностика ученика (специализация для учебного конвейера)
- [PD.PRINC.046](../../../../../PACK-personal/pack/personal-development/02-domain-entities/principles/PD.PRINC.046-mental-model-as-constraint.md) — Mental Model as Constraint (Tendon)
- [WP-313](../../../../../DS-my-strategy/inbox/WP-313-bottleneck-skill-toc.md) — родительский РП
- `.claude/skills/bottleneck-pick/SKILL.md` — инструмент-носитель алгоритма
