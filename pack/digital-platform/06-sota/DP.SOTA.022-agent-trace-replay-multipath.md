---
id: DP.SOTA.022
name: "Agent Trace, Replay & Multi-Path Execution"
type: sota
status: draft
summary: "SOTA-обзор архитектурных паттернов для журнала решений LLM-агентов, повтора (replay) и параллельного многопутевого исполнения (multi-path / best-of-N). Дополняет DP.SOTA.015 (telemetry layer) — этот документ про rationale layer."
created: 2026-05-17
edition: "2026-05"
trust:
  F: 3
  G: external
  R: 0.7
related:
  integrates_with: [DP.SOTA.015, DP.SOTA.013, DP.SOTA.014]
  referenced_by: [WP-295]
tags: [agent-trace, event-sourcing, replay, multi-path, best-of-n, pattern-mining, memory]
---

# DP.SOTA.022 — Agent Trace, Replay & Multi-Path Execution

## Метаданные

draft | 2026-05-17 | источник: parallel sub-agent research (event sourcing + multi-path + memory) в рамках WP-295 Ф0.1

## Положение относительно [[DP.SOTA.015]]

DP.SOTA.015 описывает **telemetry layer** AI-систем (Traces / Metrics / Logs / Evaluations) — стандарт OpenTelemetry GenAI SIG, платформы Langfuse / Phoenix / Helicone. Этот документ — **rationale layer**: что записывать о *рассуждении* агента (гипотезы, отброшенные пути, обоснования), как воспроизводить (replay), как параллелить (multi-path), как добывать паттерны из накопленного. Слои дополняют друг друга, не пересекаются по содержанию.

## Статус SOTA

Emerging. Каждая из трёх под-областей имеет зрелый отраслевой консенсус (event sourcing — 10+ лет, multi-path — после ToT/AlphaCode 2022-2023, memory — после Generative Agents 2023), но их объединение в единый agent rationale stack — задача 2025-2026. Production-патrtern зафиксирован в работах AgentRR (arXiv 2505.17716), LangGraph Time Travel, Letta (production-fork MemGPT).

## Три под-области

### 1. Event Sourcing & Replay

| Инструмент | Модель | Когда правильный выбор | Граница |
|------------|--------|------------------------|---------|
| **EventStoreDB / Kurrent** | event-native append-only журнал стримов + проекции | Богатая бизнес-логика, аудит как ценность (финансы, ordering, claims) | Кластер сложен; экосистема инструментов уже реляционной |
| **Temporal / Cadence** | durable execution — workflow-код плюс history, replay через детерминированное повторение | Оркестрация шагов (LLM-вызов → tool use → retry → human approval → таймер) | History cap 50K events / 50MB на исполнение; деградация уже от ~10K — реальный потолок длительности одного workflow |
| **Apache Kafka + ksqlDB** | event log + материализованные представления | High-throughput интеграция сервисов | Не event store: log compaction оставляет только последнее значение на ключ; полный history — отдельная инфра (S3 через Connect / Tiered Storage) |
| **Datomic** | неизменная БД с `as-of`/`since`/`history` запросами | Time-travel над структурированными данными без отдельной event-инфры | На 40+ млрд datoms нестабильные query times; high-churn атрибуты убивают индекс — нужен явный `:db/noHistory true` |

### 2. Multi-Path / Best-of-N

| Подход | Идея | Где сияет | Граница |
|--------|------|-----------|---------|
| **Tree of Thoughts** (Yao 2023) | дерево «мыслей» + value-функция + BFS/DFS с backtracking | Длинный горизонт + явная верификация промежуточного состояния (Game of 24: 4% → 74%) | Дорого, нужна осмысленная промежуточная метрика |
| **AlphaCode** (DeepMind 2022, Science) | sample-and-rank: 100K кандидатов → unit-тесты → кластеризация → представители | Дешёвая внешняя верификация (executable tests) | Не применим без verifier; AlphaCode 2: ×2 решений за 10 попыток |
| **Multi-agent debate** (Du 2023) | N экземпляров видят ответы соседей, корректируются за 2-3 раунда | Математика, фактология (+несколько %); гетерогенные модели A-HMAD 2025: +4-6 п.п. сверху, +9 п.п. на GSM-8K | Не всегда бьёт single-agent baseline при равном compute (ICLR 2025 blogpost: 5 MAD-фреймворков — нестабильно) |
| **Self-consistency** (Wang 2022) | N reasoning chains → majority vote | Дискретный финальный ответ (число, метка); +17.9% на GSM8K | Не работает для open-ended артефактов |
| **Constitutional AI** (Anthropic 2022-2023) | N кандидатов → AI-судья по принципам → preference pairs | Удешевление data-collection для preference learning; «принципы как критерий» — прямой паттерн селектора | RLAIF-цикл, не runtime best-of-N сам по себе |
| **Reflexion** (Shinn 2023) | решение → фидбек → словесная рефлексия в эпизодическую память → повтор | HumanEval: 80% → 91% pass@1; ортогонально multi-path, комбинируется поверх top-1 | Не помогает там, где сбой = «исследовано не то пространство» — конвергирует в неправильное место |

### 3. Pattern Mining & Memory

| Подход | Архитектура | Зрелость | Применимо как |
|--------|-------------|----------|---------------|
| **Generative Agents** (Park 2023, UIST) | поток наблюдений + периодические рефлексии (importance-trigger) + retrieval = recency × similarity × importance | Reference architecture; production-fork'и используют формулу retrieval | Базовая формула гибридного retrieval |
| **Voyager** (Wang 2023) | skill library из исполняемых функций + auto-curriculum + iterative prompting | Reference; плоский индекс деградирует нелинейно — нужна иерархия | Skill-каталог с hierarchical routing |
| **MemGPT → Letta** (Packer 2023; production fork 2024) | core memory ↔ archival/recall memory с явным paging-ом | Production-ready; на LoCoMo бенчмарке Letta + filesystem обгоняет Mem0 + KG | Hierarchical memory с paging, не flat vector store |
| **Reflexion long-term** | буфер вербальных рефлексий + инъекция в next trial | Reference, ортогонален episodic memory | Session-end reflection как обязательный мини-этап Close-протокола |
| **LangSmith Insights / Phoenix anomaly detection** | авто-кластеризация trace по failure mode + manual triage | Production (2025-2026); ни одна платформа не закрывает full lifecycle | Кандидаты-паттерны для review, не auto-rule generation |

## Что брать (отраслевой консенсус, 8 паттернов)

1. **Append-only + immutable events + snapshots каждые N шагов.** Никаких UPDATE/DELETE на событиях — корректировка через compensating event. Снапшоты (предлагаемая отправная точка для WP-295: каждые 20-50 решений) обязательны: без них fork-replay даёт O(длина истории).
2. **Weak schema + upcasters + crypto-shredding.** JSON с tolerant readers + цепочка upcasters в момент чтения — единственная жизнеспособная стратегия эволюции схемы на горизонте года (Overeem 2021, JSS). PII через per-subject ключ → удаление ключа = «забвение»; latch'ить с первого дня под GDPR (B7.3 совместимо).
3. **Гибридный retrieval (recency × similarity × importance × decision-relevance).** Чистый cosine similarity по embedding'ам ловит «похожее по форме», но не «причинно релевантное». LongMemEvalS (ICLR 2025): retrieval-stage оптимизации дают +9.4 п.п. — больше, чем оптимизация ingestion.
4. **Trace ↔ domain_event join на этапе записи, не retrieval.** При закрытии trace писать пары `(trace_id, produced_artifact_ids)` — git commits, файлы, исходы РП. Pattern miner кластеризует по `(trace_features, outcome_features)` совместно. Это даёт причинность, а не корреляцию по эмбеддингу.
5. **Multi-path: N=3 как старт, не N=10. Гетерогенность моделей > клоны.** Inference Scaling Laws (arXiv 2408.00724, ICLR 2025): резкое выполаживание после 3-5 кандидатов на open-задачах без verifier. Смешать Opus + Sonnet + Sonnet (другой seed/темп) > три Opus с разными seed (A-HMAD 2025: +4-6 п.п.).
6. **Селектор: LLM-as-Judge с принципами + pairwise + permutation randomization.** Constitutional AI-pattern напрямую применим: ЭМОГССБ как «конституция». Обязательно: pairwise, не batch-ranking; randomize order (position bias ≥10% accuracy shift); judge видит артефакты, не хеши. Для критических решений — ensemble судей или human-in-the-loop.
7. **Cluster-then-pick + Reflexion-loop поверх top-1.** Если из N кандидатов несколько кластеризовались — судить между кластерами, не между всеми (AlphaCode-pattern). После выбора лучшего — один цикл self-critique по принципам и revision (Reflexion, дёшево, прирост подтверждён).
8. **Pattern miner = гибридный workflow, не auto-rule generation.** Майнер кластеризует trace'ы и формирует кандидатов-паттернов с примерами (5-10 trace), но утверждает человек. SOTA по failure attribution в multi-agent traces (AgenTracer 2025): полная автоматизация даёт <10% accuracy на длинных трассах.

## Что НЕ брать / границы (5 анти-паттернов)

1. **Real-time replay миллионов событий без snapshots.** В Kafka Streams реcоздание state store при rebalance → минуты деградации latency. В EventStoreDB / Datomic — аналогично. Snapshots обязательны.
2. **Best-of-N без budget guard.** Reward-hacking при больших N: селектор оптимизирует прокси, кривая «accuracy от N» уплощается и разворачивается вниз (Inference Scaling Laws 2024-2025). Token-budget circuit breaker + early-stop по согласию первых 3 кандидатов — обязательный wrapper.
3. **Naive majority vote на open-ended артефактах.** Работает только когда финал — дискретная метка. Для архитектур, эссе, дизайнов нужен явный judge с pairwise-сравнением.
4. **Полностью автоматическая генерация правил без human review.** LLM-as-judge без эталона от эксперта дрейфует; AgenTracer и follow-up 2025 — <10% accuracy. Practical workflow: SME даёт оценки → конвертируются в judge-evaluator, но эталон остаётся за человеком.
5. **Flat vector store при росте библиотеки skills/trace.** Точность выбора деградирует нелинейно — фазовый переход. Hierarchical routing (по домену / типу РП / роли) + MemGPT/Letta paging — заложить с первого дня, не латать потом.

## Применимо к WP-295 — карта решений для ArchGate Ф0.5

| Архитектурный выбор | Рекомендация на основе SOTA |
|---------------------|------------------------------|
| **Модель хранения** | Гибрид: Temporal-style execution log (для replay шагов) + EventStoreDB-style domain trace (для аудита решений). НЕ смешивать слои — разные процессы создания и развития и потребители |
| **Snapshot policy** | Каждые 20-50 решений или 5-10 минут (отправная точка, калибровать по реальной длине трасс) |
| **Schema evolution** | Weak schema (JSON) + upcasters на чтении. Жёсткая схема (Protobuf strict) → боль через 3 месяца |
| **PII / GDPR** | Crypto-shredding с первого дня (per-subject key + tombstone). Совместимо с B7.3 — закрывает PII-блокер ArchGate |
| **Fork-replay недетерминизма** | Checkpoint + reseed: при записи фиксировать ВСЕ источники недетерминизма (timestamps, LLM-sampling выборы, random seeds, ответы внешних API). Без этого fork даёт другой результат не из-за «другой ветки», а из-за технического шума |
| **Multi-path N** | N=3 base, гетерогенные модели (Opus + Sonnet + Sonnet/другой-seed). Budget guard: per-task token-cap, early-stop по кластеризации первых кандидатов |
| **Селектор** | LLM-as-Judge ЭМОГССБ; pairwise + permutation randomization; для критических — ensemble или human-in-the-loop |
| **Retrieval API** | recency × similarity × importance × decision-relevance; join с domain_event обязателен на записи |
| **Memory hierarchy** | core memory ↔ archival/recall (MemGPT/Letta pattern); filesystem backend как baseline |
| **Session-end reflection** | Обязательная мини-фаза Close-протокола: что получилось, что нет, какой урок, какой паттерн. Это denoised сигнал для pattern miner — ему не нужно реконструировать «что хотел сделать агент» из сырой трассы |
| **AR.NNN provenance** | Каждое предложенное правило ссылается на конкретные trace_id из которых выведено — для replay, audit, отката |
| **High-churn fields** | Помечать not-history (промежуточные LLM-вызовы, token counts). Не делать time-travel бесплатным по умолчанию (грабли Datomic) |

## Открытые вопросы для ArchGate (Ф0.5)

1. **Granularity Temporal-style execution log vs EventStoreDB-style domain trace** — два сервиса или один с разными streams в одной БД?
2. **Hierarchical memory keying** — по домену, по типу РП, по роли, по фазе? Какая ось первичная?
3. **Selector budget** — статический per-task tier (trivial=N1 / closed=N3-5 / open=N5-10) или динамический по согласию кандидатов?
4. **PII tombstone retention** — формально GDPR не считает «зашифрованные без ключа» удалёнными; нужен ли физический rewrite стрима для highly regulated доменов?

## Источники (≤10)

- [Event Sourcing is Not For Everyone — Kurrent / EventStoreDB blog, 2025](https://docs.eventsourcingdb.io/blog/2025/11/27/event-sourcing-is-not-for-everyone/)
- [An Empirical Characterization of Event Sourced Systems and Their Schema Evolution — Overeem et al., JSS 2021 (arXiv 2104.01146)](https://arxiv.org/abs/2104.01146)
- [Temporal — Safely deploying changes to Workflow code](https://docs.temporal.io/develop/safe-deployments)
- [AgentRR: Get Experience from Practice — LLM Agents with Record & Replay (arXiv 2505.17716)](https://arxiv.org/abs/2505.17716)
- [Tree of Thoughts — Yao et al., NeurIPS 2023 (arXiv 2305.10601)](https://arxiv.org/abs/2305.10601)
- [AlphaCode — Competition-Level Code Generation, Science 2022](https://www.science.org/doi/10.1126/science.abq1158)
- [Constitutional AI — Anthropic, arXiv 2212.08073](https://arxiv.org/abs/2212.08073)
- [Reflexion — Shinn et al., NeurIPS 2023 (arXiv 2303.11366)](https://arxiv.org/abs/2303.11366)
- [Inference Scaling Laws — arXiv 2408.00724, ICLR 2025](https://arxiv.org/abs/2408.00724)
- [Benchmarking AI Agent Memory: Is a Filesystem All You Need? — Letta blog, 2024-2025](https://www.letta.com/blog/benchmarking-ai-agent-memory)

## Связанные сущности

- [[DP.SOTA.015]] — telemetry layer (Traces / Metrics / Logs / Evaluations), комплементарен
- [[DP.SOTA.013]] — world models (внутренняя модель агента о среде)
- [[DP.SOTA.014]] — MCP standard (транспорт tool calls, упоминается в trace events)
- [[DP.M.060]] — атомарные ВДВ-шаги (предусловие: post-condition на шаг = атом trace)
- [[WP-295]] — потребитель этого SOTA-документа на Ф0.5 ArchGate
