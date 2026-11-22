---
id: DP.ROLE.049
name: Координатор путей
name_ru: Координатор путей
name_en: Path Coordinator
aliases:
  - Path Coordinator
alias: R32
type: role-description
status: draft
valid_from: 2026-05-17
summary: "Разворачивает N кандидатов параллельно на open-loop задачах с разными моделями/seed, координирует селектор, обеспечивает budget guard и сохранение всех путей в trace для последующего анализа."
related:
  specializes: [U.RoleAssignment]
  component_of: [DP.ROLE.001]
  realizes: [DP.SC.039]
  uses:
    - DP.ROLE.047 Trace Recorder  # каждый путь = своя trace branch
    - DP.ROLE.048 Replay Engine   # каждый путь стартует от одной точки
    - DP.M.005 ArchGate           # ЭМОГССБ как «конституция» селектора
    - DP.SOTA.022 §2              # multi-path/best-of-N паттерны
  downstream_consumers:
    - DP.ROLE.001 IWE Creator     # инициатор multi-path
    - DP.ROLE.058 Артефактор      # 3 формулировки РП
    - DP.ROLE.005 Architect       # 3 архитектурных альтернативы
    - DP.ROLE.025 Reviewer        # 3 структуры поста/deck
created: 2026-05-17
updated: 2026-11-22
wp: WP-295
---

# Координатор путей — DP.ROLE.049

> **Прежнее имя** — «Path Coordinator»; переименовано решением пилота 22.11.2026 (DP.ROLE.001 §3.6, РП-616 Ф4); номер R из заголовка убран — он занят другими ролями (DP.ROLE.001 §3.6 п. 1, §3.7).

> # see DP.SC.039, DP.ROLE.049
>
> **Kind:** Coordinator Role — управляет N исполнителями, не выполняет содержательную работу.
> **Owner Role:** IWE Platform. Текущий прототип — CLI `~/IWE/scripts/iwe-multipath.py`; skill `/multi-path`, запись всех путей и жёсткий предел затрат ниже описаны как целевой способ работы, не как проверенная поставка.

---

## 1. Миссия

На open-loop задачах (архитектура, формулировки, творческие артефакты) — генерировать N альтернатив параллельно через разные модели/seed, дать арбитру выбрать лучшего по принципам ЭМОГССБ, и сохранить все пути для анализа. Без этого один путь = один результат, нет сравнения — невозможно отличить «хороший выбор» от «единственный найденный».

Аналогия: продюсер кастинга. Не играет роли (это актёры-кандидаты), не выбирает финалиста (это режиссёр-судья) — организует процесс: набирает претендентов с разным бэкграундом, обеспечивает равные условия пробы, передаёт записи режиссёру в правильном порядке, не даёт перерасходовать бюджет.

**Граница:** Coordinator не пишет финальный результат (это делают spawned кандидаты), не оценивает их (это селектор R23/R25), не принимает финального решения (это R1 / автор задачи). Только координация.

---

## 2. Обязанности

| Обязанность | Как выполняется |
|-------------|----------------|
| Принимать запрос параллельных путей | Сейчас CLI `iwe-multipath.py run` с `--n`, `--selector`, `--budget`, `--models`; skill `/multi-path` запланирован |
| Проверять verification_class | отказ на trivial/closed-loop с явным сообщением |
| Выбирать гетерогенные модели | default: Opus + Sonnet + Sonnet/другой-seed |
| Spawn'ить N субагентов | через Task tool с разными prompt seeds и моделями параллельно |
| Включать budget guard | per-task token-cap + global limit + early-stop при кластеризации |
| Собирать N результатов | ждать все или early-stop по согласию первых 3 |
| Cluster-then-pick | если 2+ кандидата сошлись (similarity > порога) — судить между кластерами |
| Вызывать селектор | pairwise с permutation randomization; default R23 Аудитор Haiku, R25 Рецензент для творческих |
| Reflexion-loop поверх top-1 | один цикл self-critique по принципам ЭМОГССБ + revision |
| Сохранять все пути в trace | через DP.ROLE.047, каждый путь = fork от одной точки |
| Сравнительный отчёт | таблица «кандидат / выбор судьи / комментарий» для аудита |
| Pricing-aware policy | прозрачное объявление до запуска (N × estimated_cost) |

---

## 3. Входы / Выходы

**Входы:**
- Параметры skill: `<задача>` + `--n 3 --selector archgate --budget 5000tokens [--models opus,sonnet,sonnet]`.
- Контекст текущей сессии (промпт, файлы, открытые гипотезы).
- WP-context для определения `verification_class` (открытый файл с frontmatter).

**Выходы:**
- N trace-веток в `agent_trace.fork_session` с `selector_decision` (выбран / отброшен / human-override).
- Финальный артефакт = top-1 после Reflexion-loop.
- Сравнительный отчёт `multi-path-report-<task-id>.md` в inbox.
- Audit: запись принципов селектора, pairwise-comparisons, обоснование выбора.

---

## 4. Архитектура (слои)

```
Инициатор
├── DP.ROLE.001 IWE Creator (пилот) ← `/multi-path "..."`
├── DP.ROLE.058 Артефактор          ← inner-loop при создании РП
└── DP.ROLE.005 Architect           ← на ArchGate
        │
        ▼
DP.ROLE.049 Path Coordinator
├── Gate Check       → verification_class ∈ {open-loop, problem-framing}
├── Model Picker     → default: Opus + Sonnet + Sonnet/другой-seed
├── Budget Estimator → N × estimated_cost → объявить до запуска
├── Spawner          → Task tool parallel (sub-agents)
├── Budget Guard     → token-cap per кандидат + global limit
├── Early-stop       → согласие первых 3 → terminate остальные
├── Cluster-then-pick → similarity-based merge перед селектором
├── Selector caller  → pairwise + permutation randomization
├── Reflexion-loop   → один цикл self-critique поверх top-1
└── Reporter         → multi-path-report.md + trace branches

Селекторы
├── R23 Аудитор Haiku (default, ЭМОГССБ)
├── R25 Рецензент Sonnet (творческие артефакты)
├── Ensemble (3 judges) для критических решений
└── Human-in-the-loop (R1) при tie

Trace
└── DP.ROLE.047 Trace Recorder ← каждый путь пишется как fork-branch
```

---

## 5. Ограничения (инварианты роли)

1. **Только open-loop / problem-framing.** Отказ на trivial/closed-loop. Проверка по `verification_class` WP-context. Снимает 75% риска не окупиться N×compute.
2. **N=3 default, не N=10.** Расширение через explicit flag. N>5 = подтверждение пользователя. Источник: Inference Scaling Laws ICLR 2025.
3. **Гетерогенность кандидатов.** Default — разные модели. Override через `--models` явно. Три клона одной модели = explicit user choice, warning «N клонов даёт меньше, чем гетерогенные».
4. **Селектор pairwise + permutation randomization.** Batch-ranking запрещён. Каждая пара сравнивается дважды с randomized order.
5. **Cluster-then-pick.** Похожие кандидаты — судить между кластерами, не между всеми. Иначе breaks AlphaCode-pattern.
6. **Reflexion-loop поверх top-1.** Один цикл, не итерации. Дешевле и надёжнее (Reflexion 2023: 80%→91%).
7. **Budget guard обязателен.** Per-task token-cap + global limit + early-stop. Без этого reward-hacking при больших N.
8. **Все trace сохраняются.** Проигравшие кандидаты — материал для pattern miner. Удаление запрещено.
9. **Judge не self-evaluates.** Запрещён сценарий «один из кандидатов = судья». Селектор — отдельная роль.
10. **Принципы судьи декларированы.** Селектор получает явный список (ЭМОГССБ + контекст задачи). Без этого +5-7% self-enhancement bias.

---

## 6. Связи с другими ролями

| Роль | Отношение |
|------|-----------|
| DP.ROLE.047 Trace Recorder | Downstream: каждый путь пишется как branch. Все N — включая проигравших. |
| DP.ROLE.048 Replay Engine | Sibling: multi-path = N независимых replay'ев от одной начальной точки. |
| DP.ROLE.050 Pattern Miner | Downstream: использует trace проигравших кандидатов для обнаружения «классов плохих решений». |
| R23 Аудитор / R25 Рецензент | Внутренние селекторы. Контракт: pairwise + permutation randomization. |
| DP.ROLE.058 Артефактор | Главный inner-caller: при создании сложного РП = `/multi-path "формулировки"`. |
| DP.ROLE.005 Architect | Caller: на ArchGate = `/multi-path "3 architectural alternatives"`. |
| DP.ROLE.025 Reviewer | Caller + Selector: при подготовке поста = `/multi-path "структуры"`. |
| WP-203 (Оркестратор) | Potentially-conflicts: WP-203 — общий оркестратор; multi-path coordinator — частный случай. На ArchGate Ф0.5: разделение — multi-path живёт в WP-295, WP-203 может его использовать. |

---

## 7. Точки входа (интерфейсы)

### Базовый запуск (для R1)

```bash
/multi-path "Architecture for X" --n 3 --selector archgate --budget 5000
```

### С heterogeneous-моделями

```bash
/multi-path "Структура поста о Y" --n 3 --models opus,sonnet,sonnet --selector reviewer --budget 3000
```

### Inner-loop (для Артефактора)

```python
formulations = multi_path(
    task="Сформулировать РП для X",
    n=3,
    selector="lightweight",  # быстрый judge без ensemble
    budget=2000
)
# returns: best + alternatives + comparison_report
```

### Сравнительный отчёт

`multi-path-report-<task-id>.md`:
```markdown
# Multi-path report: <task-id>

## Кандидаты
| # | Модель | Seed | Стоимость | Кратко |
|---|--------|------|-----------|--------|
| 1 | Opus | default | $0.18 | Подход A: классический event sourcing |
| 2 | Sonnet | default | $0.04 | Подход B: гибрид Temporal-style + EventStore |
| 3 | Sonnet | 42 | $0.04 | Подход C: чистый Temporal без domain trace |

## Pairwise сравнения (selector: R23 Аудитор, ЭМОГССБ)
- 1 vs 2: победил 2 (+эволюционируемость, =остальное)
- 1 vs 3: победил 1 (+сохранность, +модульность)
- 2 vs 3: победил 2 (+гомеостаз, +модульность)

## Ranking
1. **Подход B** (winner)
2. Подход A
3. Подход C

## Reflexion-loop revision
[доработка top-1 по слабым местам]
```

---

## 8. Метрики

| Метрика | Норма | Где брать |
|---------|-------|-----------|
| Success rate (3/3 кандидатов завершились) | ≥85% | log multi-path runs |
| Budget guard triggered | редко (<10% runs) | budget guard log |
| Early-stop (cluster согласие) | ≥30% runs | log |
| Selector tie rate | <5% | log |
| Median cost per run | per task type | per-task token usage |
| Reflexion revision changed top-1 substantively | ≥40% | manual sample audit |
| Trace coverage всех N путей | 100% | grep agent_trace.fork_session |

---

## 9. Открытые вопросы (для ArchGate Ф0.5)

1. **Selector budget** — статический per-task tier (trivial=1 / closed=3-5 / open=5-10) или динамический по согласию первых кандидатов?
2. **Ensemble of judges** — когда обязателен? Critical-flag в task или autodetect по budget impact?
3. **Cluster threshold** — similarity > 0.85 для merge? Калибровать на реальных кейсах.
4. **Reflexion-loop bypass** — для очень дешёвых задач (≤500 tokens на кандидата) Reflexion может удваивать стоимость без выигрыша. Threshold для skipping?
