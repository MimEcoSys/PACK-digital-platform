---
id: DP.ROLE.054
name: R30 Аналитик ограничений
name_en: Constraint Analyst
type: role-description
status: draft
valid_from: 2026-05-20
summary: "Носитель методики TOC (Goldratt Five Focusing Steps + Tendon TameFlow Replenishment Cycle + Dettmer Thinking Processes). Идентифицирует систему-конвейер, сканирует функциональные обещания (SC-first), находит ограничение, выбирает TOC-инструмент и выдаёт план работы как карту этапов с зависимостями (без дат/часов). Универсален: применим к учебному конвейеру пилота, конвейеру работ (РП/эпик/проект/репо), когортному конвейеру."
related:
  specializes: [U.RoleAssignment]
  component_of: [DP.ROLE.001]
  realizes: [DP.SC.045]
  uses:
    - DP.WP.016                      # Stage Dependency Map (формат выхода)
    - DP.M.061                       # Bottleneck-Shift Detection (поддерживающий метод)
    - PD.PRINC.046                   # Mental Model as Constraint (Tendon)
    - MIM.FM.011                     # Policy treated as Resource (Schragenheim)
    - .claude/skills/bottleneck-pick # инструмент-носитель алгоритма
  downstream_consumers:
    - DP.ROLE.001 IWE Creator (пилот)  — открывает зонтичный РП, получает выбор bottleneck + карту этапов
    - DP.ROLE.012 Стратег              — при отборе НЭП на стратегической сессии
    - DP.ROLE.042 Диагност             — частный случай для системы-ученика: bottleneck_slot cp-профиля (FORM.089)
    - DP.ROLE.053 Декомпозитор (R29)     — Аналитик идентифицирует ограничение, Декомпозитор декомпозирует на стадии с физическими артефактами
created: 2026-05-20
updated: 2026-05-20
wp: WP-313
---

# Аналитик ограничений — DP.ROLE.054

> # see DP.SC.045, DP.ROLE.054, DP.WP.016
>
> **Kind:** Analytical Role — анализирует систему, не управляет ею. Не носитель работы по устранению ограничения (это другие роли: Стратег, Декомпозитор, исполнитель РП).
> **Owner Role:** IWE Platform — исполнитель: скилл `/bottleneck-pick` (text-based, headless или интерактивно), вызывается через LLM-агента в режиме экзокортекса.

---

## 1. Миссия

Гарантировать, что при работе со сложной системой (учебный конвейер пилота, конвейер работ, когортный конвейер) выбор следующего фокуса работы основан на **обоснованной идентификации ограничения** по методике TOC — а не на интуиции, sunk cost, sexy work bias или recency.

Аналогия: технолог конвейерного производства, который проходит по всему конвейеру и говорит «вот тут самое узкое место, нет смысла ускорять остальные станки — они в норме». Не строит станков, не нанимает рабочих, не закупает запчастей — только показывает, где Herbie и какой класс ограничения мешает.

**Граница:** Аналитик НЕ:
- выполняет работу по устранению ограничения (это исполнительные роли)
- принимает архитектурные решения (это ArchGate / Стратег)
- определяет приоритеты НЭП (это Стратег + пилот)
- даёт рекомендации по саморазвитию (это Навигатор (MIM.R.007), который использует bottleneck_slot Аналитика как вход)

---

## 2. Обязанности

| Обязанность | Как выполняется |
|-------------|----------------|
| Идентифицировать систему-конвейер | Принимает `--target`, классифицирует тип системы (см. §3) |
| Собрать актуальное состояние | git log за 7 дней, метрики из Neon, content-файлы (PROCESSES.md, WP-context, SC-карты) |
| Сканировать функциональные обещания (SC-first) | Перечислить DP.SC для системы → для каждого тест «работает / сломано / частично» |
| Применить signal-scan по 6 сигналам TameFlow | Queue accumulation, Flow Efficiency, handover count, buffer consumption, policy markers, cognitive freeze |
| Классифицировать ограничение | Trichotomy (Tendon): Work Flow / Work Process / Work Execution; Class: Policy / Resource / Cognitive |
| Выбрать TOC-инструмент | Decision tree: Five Focusing Steps / EC / Five Steps + EC + NBR |
| Построить карту этапов | DP.WP.016 Stage Dependency Map: узлы = этапы, рёбра = жёсткая зависимость, параллельность внутри узла, внешние зависимости явно |
| Сформировать Constraint Brief | Описание, тип, обоснование сигналами, выбранный инструмент с trace |
| Зафиксировать применение | Calibration YAML в `inbox/bottleneck-pick-runs/<date>-<target>.yaml` для последующей precision-оценки |
| Сигнализировать о bottleneck-shift | При повторном применении к той же системе после устранения предыдущего ограничения — переоценка по DP.M.061 |

---

## 3. Системы-конвейеры (3 класса)

> **Принцип:** система ≠ поток. Система — конвейер-носитель; поток — то, что в ней циркулирует.

| Класс системы | Объект-конвейер | Поток через конвейер | Источник истины |
|---------------|------------------|------------------------|------------------|
| **Учебный конвейер пилота** | RCS-машина пилота (FORM.089) | Учебные циклы / W-рефлексии / lesson-completed | `learning.cp_assessments` + `digital_twins.data` |
| **Конвейер работ** | Pipeline РП внутри зонтика, фаз эпика, или репо | Поток РП (inbox → in_progress → done) | `WP-REGISTRY.md` + `inbox/WP-*.md` |
| **Когортный конвейер** | Adoption-machine продукта: onboarding → activation → habituation | Поток пилотов через стадии adoption | Activity Hub events + `learning.stage_transitions` |

**Идентификация типа системы** — обязательный первый ВДВ-шаг (см. §5). Без неё нельзя выбрать релевантные сигналы и применимый класс TOC-инструмента.

---

## 4. Входы / Выходы

**Входы (от потребителей):**
- `target-ref` — идентификатор системы-конвейера: WP-NNN, project-name, repo-path, или `rcs-profile:<account_id>` для системы-ученика
- `--horizon` (опционально) — wave-1 / week / quarter / next-stage
- `--depth` (опционально) — 1 (Five Steps only) / 2 (+ EC для конфликтующих кандидатов)
- `--scope` (опционально) — direct / direct+related / full (глубина графа связей)

**Выходы (3 артефакта):**

| Артефакт | Содержание | Куда пишется |
|----------|------------|---------------|
| **System Card** | Тип системы, обещания (SC-карта), потребители, текущее состояние, свежесть данных | inline в чат + раздел в calibration YAML |
| **Constraint Brief** | Описание ограничения, trichotomy, класс (Policy/Resource/Cognitive), сигналы signal-scan, выбранный TOC-инструмент с trace, NBR-результат | inline в чат + calibration YAML |
| **Stage Dependency Map** (DP.WP.016) | План работы как dependency graph: узлы=этапы, рёбра=жёсткая зависимость, параллельность внутри узла, external-рёбра к РП в других репо | inline в чат + опционально в `inbox/WP-NNN/stage-map.md` |

**Артефакты в git:**

| Файл / папка | Что пишет |
|--------------|-----------|
| `DS-my-strategy/inbox/bottleneck-pick-runs/<date>-<target>.yaml` | Calibration record (precision tracking) |
| `DS-my-strategy/inbox/WP-NNN/stage-map.md` (опционально) | Persisted Stage Dependency Map для зонтичного РП |

---

## 5. Алгоритм работы — пятифазный ВДВ-каскад

> Принцип ВДВ (DP.M.060): выход фазы = вход следующей. Каждый вход и выход — физический артефакт (файл, секция в чате, запись в БД).

| # | Фаза | Вход (артефакт) | Действие | Выход (артефакт) |
|---|------|------------------|----------|--------------------|
| **Ф1** | **Identify system** | target-ref от потребителя | Классифицировать тип системы (учебный / работ / когортный); собрать PROCESSES, WP-context, метрики; зафиксировать свежесть данных | **System Card** (тип, обещания, потребители, current state) |
| **Ф2** | **Scan promises (SC-first)** | System Card | Перечислить функциональные обещания (DP.SC для системы) → для каждого тест: «работает? сломано? частично?» → пометить кандидатов из «не работает» | **SC-status map** (каждое обещание + статус + сигналы) |
| **Ф3** | **Identify constraint** | SC-status map + структура работ (направления / фазы / РП) | Signal-scan по 6 сигналам TameFlow для top-кандидатов из Ф2; классифицировать trichotomy + Policy/Resource/Cognitive | **Constraint Brief draft** (top-3 кандидата + классификация + сигналы) |
| **Ф4** | **Choose TOC tool** | Constraint Brief draft | Decision tree: Five Focusing Steps / EC / Five Steps + EC; обязательный NBR после injection | **TOC tool trace** (выбранный инструмент + assumptions + injection + NBR-trim) |
| **Ф5** | **Compose stage map** | Constraint Brief + TOC tool trace + список зависимостей (включая external) | Построить dependency graph: узлы=этапы, параллельность=внутри узла, рёбра=жёсткая зависимость, external-рёбра явные | **Stage Dependency Map** (DP.WP.016 формат) |

**Принцип SC-first (Ф2 перед Ф3):** документо-центричный подход «что pending в РП» подменяет продукт каналом доставки. Правильно — начинать с «какое функциональное обещание не работает у потребителя». Канал — следствие, не цель.

---

## 6. Ограничения (инварианты роли)

1. **System ≠ поток.** Аналитик ВСЕГДА классифицирует систему-конвейер (3 класса §3) перед signal-scan. Без идентификации системы trichotomy не определяется. Нарушение: «нашёл bottleneck в потоке РП» без указания, в каком конвейере (зонтик WP-NNN? репо проекта? стадия adoption?) = провал Ф1.
2. **SC-first перед WP-сканированием.** Сначала функциональные обещания (Ф2), потом структура работ (Ф3). Иначе риск принять канал доставки за продукт (источник: эпизод WP-250 19 мая 2026 — bottleneck-анализ по pending РП дал «марафон главный блокер», SC-сканирование показало «продукт ещё не готов открывать новым пилотам»).
3. **Trichotomy + class — обязательны.** Output без классификации (Work Flow / Process / Execution × Policy / Resource / Cognitive) — провал Ф3. Exploit-strategy зависит от обеих осей.
4. **NBR после любого EC injection.** 3 negative branches + trim каждой. Нарушение — riding solo на одной гипотезе без проверки.
5. **Stage Dependency Map — без дат и часов.** Только структурная зависимость: узлы=этапы, рёбра=«следующий этап после предыдущего», параллельность=внутри узла. Не PERT (без оценок), не Gantt (без дат), не Kanban (без статусов).
6. **External-зависимости — явные.** Если этап зависит от работ в другом РП / другом репо / внешнего поставщика — явное external-ребро с указанием источника.
7. **Constraint Replenishment Cycle (Tendon).** После устранения ограничения — обязательная переоценка (Ф1 заново). Не «следующая задача из списка», а заново через DP.M.061 bottleneck-shift detection. Tech-блокер ≠ Operational ≠ Usage ≠ Поведенческий слой.
8. **Calibration tracking.** Каждое применение → YAML в `bottleneck-pick-runs/`. Через 5-10 runs — precision-оценка (target ≥70% правильных bottleneck по retrospective).

---

## 7. Связи с другими ролями

| Роль | Отношение |
|------|-----------|
| **DP.ROLE.001 IWE Creator (пилот)** | Главный потребитель: открывает зонтичный РП или эпик, запрашивает выбор bottleneck |
| **DP.ROLE.012 Стратег (R1)** | Использует Аналитика на стратегической сессии при отборе НЭП — «какое из дисциплин-направлений сейчас bottleneck» |
| **DP.ROLE.042 Диагност** | Частный случай: для системы-ученика Аналитик = другая инсталляция той же методики (FORM.089 как специализация signal-scan); Диагност реализует Аналитика для одного класса систем |
| **DP.ROLE.053 Декомпозитор (R29)** | Sibling-роль: Аналитик идентифицирует ограничение и этапы плана; Декомпозитор декомпозирует этапы на физические артефакты с чеклистами приёмки |
| **Навигатор (MIM.R.007)** | Потребитель: при ответе пилоту «с чего начать» использует `bottleneck_slot` Аналитика для контекстуализации |

**Различие с Декомпозитором:** Аналитик отвечает на **«куда смотреть»** (какое ограничение, какие этапы, какие зависимости). Декомпозитор отвечает на **«как сделать»** (каждый этап на физические артефакты с приёмкой). Sequencing: Аналитик → Декомпозитор.

**Различие с Диагностом:** Диагност = специализация Аналитика на систему «учебный конвейер пилота». Использует FORM.089 RCS вместо общего signal-scan, диалог ≤5 вопросов вместо git/Neon-probe. Один алгоритм TOC, разные параметры.

---

## 8. Точки входа (интерфейсы)

### Вызов скилла (для потребителя)

```bash
# Зонтичный РП с направлениями
/bottleneck-pick --target WP-250

# Эпик с фазами + горизонт
/bottleneck-pick --target WP-188 --horizon wave-1

# Проект целиком (РП внутри репо)
/bottleneck-pick --target DS-IT-systems --scope direct+related

# Учебный конвейер пилота (через Диагноста-специализацию)
/bottleneck-pick --target rcs-profile:<account_id> --horizon next-stage
```

### Workflow внутри роли (псевдокод)

```python
def constraint_analyst_cycle(target, horizon, depth, scope):
    # Ф1 Identify system
    system_card = classify_system_and_collect_context(target, scope)

    # Ф2 Scan promises (SC-first)
    sc_status = scan_service_clauses(system_card)
    sc_failing = [sc for sc in sc_status if sc.status != "works"]

    # Ф3 Identify constraint
    candidates = signal_scan(sc_failing, system_card.structure, horizon)
    classified = classify_trichotomy_and_class(candidates)
    top3 = filter_agent_actionable(classified)

    # Ф4 Choose TOC tool
    tool = decision_tree(top3, depth)
    if tool.uses_ec:
        ec_result = build_evaporating_cloud(top3[0])
        nbr_result = negative_branch_reservation(ec_result.injection)

    # Ф5 Compose stage map
    stage_map = build_dependency_graph(
        constraint=top3[0],
        tool_output=tool,
        external_deps=collect_external_dependencies(system_card)
    )

    # Calibration
    write_calibration_yaml(target, top3[0], tool, stage_map)

    return ConstraintAnalysisResult(system_card, top3, tool, stage_map)
```

---

## 9. Метрики

| Метрика | Норма | Где брать |
|---------|-------|-----------|
| Precision bottleneck-выбора | ≥70% правильных по retrospective | Calibration YAML `was_correct` после 2 недель |
| % применений с принятым пилотом выбором (без редиректа) | ≥80% | Calibration YAML `action_taken` |
| Throughput change after fix | положительный | Calibration YAML `observed_throughput_change_after_2w` |
| Среднее время Ф1→Ф5 | ≤15 мин (для опытного применения) | Логи скилла |
| Bottleneck-shift detection rate | 100% повторных применений к той же системе после fix | Calibration YAML — повторные target |

---

## 10. Открытые вопросы (для пересмотра после 5-10 применений)

1. **Auto-classification system type.** Сейчас тип системы определяется потребителем через target-формат (`WP-NNN` → конвейер работ, `rcs-profile:...` → учебный конвейер). Можно ли вывести автоматически из контекста?
2. **SC-карты для всех типов систем.** Для конвейера работ SC-карта есть (DP.SC.001-149). Для когортного конвейера — частично. Для учебного — FORM.089. Нужна единая методика SC-сканирования.
3. **Stage Dependency Map persistence.** Когда сохранять карту в репо как файл, когда оставлять inline? Критерий — переиспользование в следующих сессиях.
4. **Связь с ArchGate.** Если bottleneck = архитектурное решение (тип Policy) — auto-call `/archgate`? Сейчас manual.
5. **Связь с Декомпозитором.** Если bottleneck требует open-loop работы ≥3h — auto-call Декомпозитора для декомпозиции этапов на физические артефакты? Сейчас manual.

---

## 11. История

| Дата | Событие |
|------|---------|
| 2026-05-13 | WP-313 Ф1-Ф6: research TOC literature (Goldratt, Dettmer, Schragenheim, Tendon), SKILL.md `/bottleneck-pick`, Smoke 1 WP-250, Smoke 2 WP-188, Staging S-42 |
| 2026-05-19 | Эпизод WP-250 v8→v9: documentary-centric анализ дал ложного «марафон-bottleneck»; SC-first подход выявил настоящее ограничение (operational gap). Источник DP.M.061 bottleneck-shift detection. |
| 2026-05-20 | Ф11: формализация роли DP.ROLE.054 + DP.SC.045 + DP.WP.016. IntegrationGate §1-3 (обещание → сценарии → роль). Финальное имя: «Аналитик ограничений» (R30). |

---

## 12. TOC literature crosscheck (выбор имени)

| Источник | Имя в литературе | Роль в IWE |
|----------|------------------|------------|
| Goldratt «The Goal» 1984 | **Jonah** | Метафора-вдохновитель, сократический наставник. Подходит для нарратива, не для technical id |
| Dettmer «Logical Thinking Process» 2007 | **Constraint Manager** | Формальный носитель Thinking Processes. Близко к делу |
| Schragenheim «Throughput Economics» 2019 | **TOC Analyst** | Аналитик решений по TOC |
| Tendon «Tame Your Work Flow» 2020 | Distributed (нет выделенной роли) | TameFlow: Pursuit of Flow Efficiency = распределённая команда |
| Goldratt S&T Tree 2009 | **S&T Tree Planner** | Тот, кто строит Strategy & Tactics tree |

**Финальное имя:** «Аналитик ограничений» / Constraint Analyst — общее, операционное, не привязано к конкретной школе TOC, удобно ложится в русский ряд других ролей (Стратег, Диагност, Аттестатор, Декомпозитор).
