---
id: DP.METHOD.042
name: Сценарии использования concept-графа агентами в runtime
type: method
status: draft
valid_from: 2026-04-24
summary: "4 сценария применения concept-графа агентами платформы IWE: Claude Code (я), автор Pack, ролевые агенты бота (Портной/Оценщик/Навигатор), учебная траектория. Каждый описан по шаблону IntegrationGate шаг 2: потребитель → триггер → запрос → использование → observable-сигнал."
related:
  realizes: [DP.SC.121]
  uses: [DP.SOTA.019, DP.SOTA.017, DP.METHOD.031]
  informs: [WP-242, WP-222, WP-227]
  source: "WP-242 Ф8.1, ритуал согласования 24 апр 2026"
created: 2026-04-24
updated: 2026-07-27
---

# DP.METHOD.042 — Сценарии использования concept-графа агентами в runtime

> **see DP.SC.121, DP.SOTA.019**
>
> Артефакт IntegrationGate шаг 2: «кто запускает, когда, зачем, в каком контексте, что делает с результатом».
> Цель: развернуть обещание SC.121 до операциональной спецификации, достаточной для реализации и observability.

## §1 Шаблон описания сценария

Каждый сценарий описан по 6 полям (совместимо с шаблоном IntegrationGate):

1. **Потребитель** — какой агент + какая роль (из `02-domain-entities/DP.ROLE.*`)
2. **Триггер** — какой входной сигнал активирует использование графа
3. **Данные на входе** — что агент уже знает до обращения к графу
4. **Запрос к графу** — какой MCP-tool вызывается, с какими параметрами
5. **Использование результата** — как чанки + граф-контекст встроены в ответ
6. **Observable-сигнал** — что логируется в `platform.health.graph_usage_events`

## §2 Приоритеты сценариев

Порядок сценариев = порядок развёртывания (Ф8.4+ WP-242). Первый сценарий — первый пилот; последний — после стабилизации метрик.

| # | Сценарий | Приоритет | Режим SC.121 | Ф8.N |
|---|---------|-----------|--------------|------|
| 1 | Я в Claude Code | **1 (пилот)** | (a) всегда + (b) для 4 подслучаев | Ф8.4 |
| 2 | Автор Pack (я через Claude Code) | **2** | (a) + (b) «редактирование Pack» | Ф8.4-Ф8.5 |
| 3 | Портной в проде | **3** | (a) + (b) «Pack-обучение» для Tailor-mode | Ф8.8 |
| 4 | Оценщик / Навигатор | **4-5** | (a) + (b) по контексту | Ф8.8 |
| 5 | Учебная траектория (prereq/specializes) | **6** (опционально, после validation) | (a) + (b) «учебная последовательность» | Ф8.9 |

## Forces

_Какие конкурирующие давления удерживает метод._

| Force | Tension |
|-------|---------|
| Полнота graph-запроса (§3: 4-шаговый запрос search → concept_ids → neighbors → status) ↔ latency-бюджет (§8.2: вызов graph-tool не должен добавлять >20% к базовой латентности) | Больше шагов даёт точнее ontology-grounding, но каждый — доп. round-trip к MCP-tool; при превышении бюджета решение — кешировать neighbors, не урезать шаги |
| Приоритизация по готовности данных (§2: сценарий 5 «Учебная траектория» — приоритет 6, отложен) ↔ давление специфицировать все 5 сценариев с одинаковой полнотой (единый 6-польный шаблон §1) | Метод сознательно откладывает сценарий с недостаточными данными (33 ребра prerequisite, §7) вместо форсирования полной детализации по шаблону наравне со сценарием 1 |
| PII-безопасность лога (§8.3: `query_text` не логируется в открытом виде) ↔ ценность observable-сигнала для отладки (каждый сценарий логирует concept_ids, edge_types, latency_ms) | Детальный лог полезен для диагностики graph usage, но сырой текст пользовательского запроса нельзя писать в health-БД — метод жертвует частью диагностической ценности ради PII-гигиены |

## §3 Сценарий 1. Я в Claude Code (приоритет 1, первый пилот)

- **Потребитель:** я (opus-4.7 / sonnet-4.6) в `claude code` как Claude Code-агент, исполняющий роли R1 Стратег, R24 Архитектор, R10 Аудитор (контекстно).
- **Триггер:** пользователь задаёт вопрос, ответ на который требует Pack-знания. Примеры:
  - «Что такое X?» → определение + соседи
  - «Чем X отличается от Y?» → дифференциация (граф: общие предки/свойства)
  - «Где в Pack описано Z?» → локализация концепта
  - «Проверь, нет ли противоречий в моей формулировке» → сравнение с онтологией
- **Данные на входе:** текст запроса пользователя, контекст текущей сессии (WP, ветка, недавние правки), список открытых файлов.
- **Запрос к графу:**
  - Шаг 1: `knowledge_search(query=<текст>, top_k=10)` — получить чанки-кандидаты (embedding).
  - Шаг 2: извлечь `concept_ids` из metadata чанков.
  - Шаг 3: `knowledge_concept_neighbors(concept_ids=[...], edge_types=[specializes, part_of, related], depth=1-2)` — получить соседей.
  - Шаг 4 (опц., для режима b): `knowledge_concept_status(concept_ids=[...])` — свежесть/superseded/misconception.
- **Использование результата:**
  - Режим (a): отфильтровать superseded/deprecated/misconception из authoritative-утверждений ответа.
  - Режим (b): добавить в текст ответа 1-3 ближайших концепта + коды `[DP.*]` + file:line ссылки.
  - Формат ссылок: markdown `[DP.SC.121](pack/.../DP.SC.121-ontology-grounded-answers.md)`.
- **Observable-сигнал:**
  - `graph_usage_events` row: `agent_id=claude-code`, `scenario=1`, `concept_ids_retrieved=[...]`, `concept_ids_cited=[...]`, `edge_types_used=[...]`, `citation_rate = cited / retrieved`, `stale_used_count`, `misconception_used_count`, `latency_ms`.
  - Агрегат: `ontology_citation_rate` по режиму (b).

## §4 Сценарий 2. Автор Pack (приоритет 2)

- **Потребитель:** я через Claude Code в роли R?? Pack-Author (или R1 Стратег в режиме правки Pack).
- **Триггер:** явный запрос на правку/расширение Pack:
  - «Добавь концепт Z в Pack»
  - «Проверь, какие рёбра стоит добавить к [DP.D.050]»
  - «Найди orphan-концепты» / «найди suspicious edges»
  - «Есть ли дубликат для этого понятия?»
- **Данные на входе:** предложение на правку Pack (текст), список недавно изменённых файлов.
- **Запрос к графу:**
  - Для проверки дубликатов: `knowledge_concept_search_by_name(name=<RU или EN>, fuzzy=true)` + `knowledge_concept_embedding_neighbors(embedding=..., top_k=5)`.
  - Для предложения рёбер: `knowledge_concept_neighbors(concept_id=..., depth=2, include_weak=true)` + сравнить с FPF-корнями (DP.METHOD.031).
  - Для orphan-аудита: `knowledge_graph_orphans()` → вернуть концепты без рёбер.
  - Для suspicious-аудита: `knowledge_graph_suspicious_edges()` → вернуть рёбра с низкой confidence или кроссязыковые без нормализации.
- **Использование результата:**
  - Предложить автору: «похожий концепт уже есть — [DP.D.XXX]» / «стоит добавить ребро `related →` к [U.System]».
  - Сгенерировать diff в Pack-файле (Edit-tool), **не коммитить автоматически** — автор подтверждает.
- **Observable-сигнал:** `graph_usage_events` с `scenario=2`, `edit_suggestions_accepted`, `edit_suggestions_rejected`, `orphans_found`, `suspicious_found`, `dup_prevented_count`.
- **Связь с регрессом 24 апр** (orphans 9→20, suspicious 3→8, WP-242 §Ф6): этот сценарий — основной механизм диагностики. Запустить при первой реализации.

## §5 Сценарий 3. Портной в проде (приоритет 3)

- **Потребитель:** R?? Портной (DP.ROLE.NNN, draft), запускается в боте `@aist_me_bot` или через `/tailor` в IWE.
- **Триггер:** пользователь запросил адаптацию контента/маршрута под свою ступень или контекст:
  - «Что мне почитать про X?» (пользователь ступень 2, домен «Личное развитие»)
  - «Объясни X на моём уровне»
  - «Построй маршрут до ступени 3»
- **Данные на входе:** `user_profile` (ступень из RCS, предпочтения, недавняя активность из activity-hub), запрос пользователя, `target_concept` (извлечён из запроса через LLM).
- **Запрос к графу:**
  - Шаг 1: `knowledge_concept_resolve(query_text=<X>)` → normalize к concept_id.
  - Шаг 2: `knowledge_concept_neighbors(concept_id=target, edge_types=[prerequisite, specializes], depth=2)` → найти предпосылки и специализации.
  - Шаг 3: `knowledge_guide_for_concept(concept_id=target, level=<ступень>)` → найти подходящие руководства (RCS-aware).
  - Шаг 4: `knowledge_concept_status(concept_ids=[...])` — отфильтровать superseded.
- **Использование результата:**
  - Построить ответ с объяснением на уровне ступени + 1-2 рекомендации руководств + следующий шаг (если есть prereq, не освоен → начать с него).
  - Режим (b) активен всегда для Портного — это Pack-обучение.
- **Observable-сигнал:** `graph_usage_events` с `scenario=3`, `agent_id=tailor`, `user_level`, `target_concept_id`, `prereq_chain_depth`, `guide_recommendations_count`, `recommendation_accepted` (если user кликнул/попросил ещё).
- **Зависимость:** DP.SC.121 × WP-222 (Портной без tailor-mcp) × WP-104 (RCS для ступени).

## §6 Сценарий 4. Оценщик / Навигатор (приоритет 4-5)

### 4.1 Оценщик

- **Потребитель:** R?? Оценщик (DP.ROLE.NNN), проверяет РП/решения/работы пользователя.
- **Триггер:** пользователь отправил артефакт на проверку («оцени мою схему», «проверь задание»).
- **Данные на входе:** артефакт пользователя + эталонный концепт (что должно быть).
- **Запрос к графу:** `knowledge_concept_criteria(concept_id=target)` → извлечь критерии приёмки + `knowledge_concept_neighbors` для соседей «чего не хватает».
- **Использование:** сравнение артефакта с критериями + подсказки по отсутствующим аспектам (на основе соседей).
- **Observable:** `eval_concept_id`, `criteria_coverage`, `missing_aspects_hinted`.

### 4.2 Навигатор

- **Потребитель:** Навигатор (MIM.R.007).
- **Триггер:** вопрос «с чего начать» / «что дальше» / «зачем мне это».
- **Данные на входе:** ступень пользователя, активная программа (ЛР), недавняя траектория.
- **Запрос к графу:**
  - `knowledge_concept_path(from=<текущая ступень>, to=<цель>, edge_type=prerequisite)` → траектория.
  - `knowledge_concept_worldview_phase(concept_id=target)` → фаза дуги (PD.FORM.087).
- **Использование:** ответ по дуге нарратива (Навигатор-скилл + граф даёт реалистичность «что следующее»).
- **Observable:** `phase_transition_hint_count`, `path_recommendation_accepted`.

## §7 Сценарий 5. Учебная траектория (приоритет 6, опциональный)

- **Потребитель:** R?? Сборщик-траектории (DP.ROLE.NNN — может возникнуть после обкатки 1-4).
- **Триггер:** запрос «собери курс X» / «полный путь от ступени 2 до ступени 3».
- **Данные на входе:** стартовая точка + целевая точка + ограничения (бюджет времени, предпочитаемый формат).
- **Запрос к графу:** комбинация `knowledge_concept_path(prerequisite)` + `knowledge_concept_neighbors(specializes)` для покрытия всех узлов маршрута.
- **Использование:** сгенерированный план обучения с конкретными руководствами/упражнениями на каждый концепт.
- **Observable:** `trajectory_length`, `trajectory_coverage_gap` (сколько концептов остались без руководств).
- **Причина низкого приоритета:** требует устойчивых prerequisite-рёбер (сейчас всего 33 ребра типа prerequisite — недостаточно). Активируется после Ф8.7 feedback-loop.

## §8 Общие правила для всех сценариев

1. **Fallback при недоступности графа** (HD «Snapshot ДО действия»): любой timeout / 5xx от `knowledge_concept_*` tool → ответ идёт через `knowledge_search` + пометка «без ontology-grounding» в `graph_usage_events.fallback_reason`.
2. **Latency-бюджет** (DP.SOTA.019): 1 вызов graph-tool не должен добавлять >20% к базовой латентности ответа. Если добавляет — кешировать neighbors в Redis/memory.
3. **PII-безопасность** (B7.3 WP-212): в `graph_usage_events` не логируется `query_text` в открытом виде (хэш или обобщение). Только concept_ids, tool_name, counts.
4. **Owner event** (HD #49 «Системная БД ≠ Health-хранилище»): события графа пишутся в `platform.health.graph_usage_events` (DB #8), не в БД knowledge-mcp.

## Bias-Annotation

_Куда систематически съезжает внимание практикующего. Статус карточки — `draft`: пометка `tentative` по прецеденту SA.METHOD.001 (WP-448 Ф12)._

| Bias | Direction of distortion |
|------|--------------------------|
| _(tentative)_ Fallback-путь недооценивается при проектировании сценария | Описание 5 сценариев (§3-§7) фокусируется на happy-path (граф доступен, запрос успешен); fallback (§8.1: timeout/5xx → `knowledge_search` без ontology-grounding) добавлен отдельным общим правилом постфактум, а не как явное поле в 6-польном шаблоне §1 — при реализации внимание рискует не заложить fallback в каждый сценарий отдельно |
| _(tentative)_ Сценарий 1 перетягивает детализацию на себя | Сценарий 1 «Я в Claude Code» одновременно и первый пилот (Ф8.4), и наиболее подробно расписан (§3, конкретные MCP-запросы); при реализации Ф8.4+ внимание смещается к его доработке, а сценарии 3-5 (Портной/Оценщик/Навигатор, §5-§7) остаются короче и с плейсхолдерами `DP.ROLE.NNN`, не дописанными вслед за прогрессом сценария 1 |

## §9 Reference-параметры MCP-tools

Точный набор tool'ов и их сигнатуры — в `DS-MCP/knowledge-mcp/README.md` после реализации Ф8.4+. Ниже — проектная спецификация (может уточняться):

| Tool | Параметры | Возвращает | Сценарии |
|------|-----------|-----------|----------|
| `knowledge_search` | query, top_k, filters | chunks + concept_ids | все (базовый) |
| `knowledge_concept_neighbors` | concept_ids[], edge_types[], depth | neighbor concepts + edges | 1, 2, 3, 4 |
| `knowledge_concept_status` | concept_ids[] | status, superseded_by, misconception | все (a) |
| `knowledge_concept_resolve` | query_text | normalized concept_id | 3, 4, 5 |
| `knowledge_concept_path` | from, to, edge_type | ordered path | 4.2, 5 |
| `knowledge_graph_orphans` | — | orphan concept list | 2 |
| `knowledge_graph_suspicious_edges` | — | edges with low confidence | 2 |
| `knowledge_concept_criteria` | concept_id | criteria list | 4.1 |
| `knowledge_guide_for_concept` | concept_id, level | guide recommendations | 3 |

## §10 Связь

- **Реализует** DP.SC.121 (Ontology-grounded answers).
- **Опирается на** DP.SOTA.019 (паттерны Graph-RAG runtime), DP.SOTA.017 (гигиена графа), DP.METHOD.031 (FPF-маппинг концептов).
- **Информирует** WP-242 Ф8.2 (системный план), WP-222 (Портной), WP-227 (/twin).
- **Откроет** новую роль `graph-traversal-tool` (owner?) — создаётся в Ф8.3 ArchGate как часть IntegrationGate шаг 3.

---

> 2026-07-27 — миграция на обогащённый формат карточки (Forces + Bias-Annotation), WP-448 Ф12 Батч 3 (суб-батч 2). Эталон формата: `SPF/pack-template/03-methods/_method-card-template.md`.
