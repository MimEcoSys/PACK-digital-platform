---
id: DP.ROLE.047
name: Архивариус решений
name_ru: Архивариус решений
name_en: Trace Recorder
aliases:
  - Trace Recorder
alias: R30
type: role-description
status: draft
valid_from: 2026-05-17
summary: "Записывает рассуждения LLM-агента (гипотезы, выбор, обоснование) в append-only журнал. Single source of truth для retrieval, replay, pattern mining. Не блокирует hot path."
related:
  specializes: [U.RoleAssignment]
  component_of: [DP.ROLE.001]
  realizes: [DP.SC.037]
  uses:
    - DP.M.060            # атомарные ВДВ-шаги — атом trace
    - learning.agent_trace.*   # storage
    - event-gateway       # async upload
    - DP.SC.025 capture-bus pattern  # writer hook аналогия
  downstream_consumers:
    - DP.ROLE.048 Replay Engine  # читает trace до момента T
    - DP.ROLE.050 Pattern Miner  # кластеризует по (trace, outcome)
    - DP.ROLE.001 IWE Creator    # retrieval API при OnSessionStart
created: 2026-05-17
updated: 2026-11-22
wp: WP-295
---

# Архивариус решений — DP.ROLE.047

> **Прежнее имя** — «Trace Recorder»; переименовано решением пилота 22.11.2026 (DP.ROLE.001 §3.6, РП-616 Ф4); номер R из заголовка убран — он занят другими ролями (DP.ROLE.001 §3.6 п. 1, §3.7).

> # see DP.SC.037, DP.ROLE.047
>
> **Kind:** Recorder Role — фиксирует факт, не интерпретирует его.
> **Owner Role:** IWE Platform — исполнитель: hook Claude Code (`PostToolUse`/`Stop`) + projection-worker в `multi-domain-projection-worker`.

---

## 1. Миссия

Гарантировать, что **ни одно решение агента не теряется** между моментом принятия и моментом, когда его можно прочитать через CLI / retrieval API. Журнал = первичный материал для аудита, replay, обучения.

Аналогия: судебный стенографист. Не оценивает доводы сторон, не выбирает, что записать — фиксирует **всё**, что произнесено. Если стенограмма пропустила реплику — потеря материала, не вердикта.

**Граница:** Recorder не оценивает качество решения (это работа R23 Аудитор / R25 Рецензент), не предлагает альтернатив (это R32 Координатор путей), не выводит паттернов (это R33 Старатель). Только запись + lookup.

---

## 2. Обязанности

| Обязанность | Как выполняется |
|-------------|----------------|
| Перехватывать решения агента | `PostToolUse` hook в Claude Code, фильтр на decision-paterns (явное «решаю X», отбрасывание гипотезы) |
| Сериализовать в NDJSON | `~/IWE/.claude/logs/agent-trace/<session-id>.ndjson`, append-only |
| Фиксировать недетерминизм | model, temperature, top_p, seed, timestamp с мс, ответы внешних API (cached) |
| Закрытие сессии | `Stop` hook собирает `session.end` с `produced_artifact_ids` (git diff, closed WP, обновлённые контексты) |
| Async upload в event-gateway | event_types `agent.session.start`, `agent.decision`, `agent.hypothesis_rejected`, `agent.session.end` |
| Projection в `learning.agent_trace.*` | через `multi-domain-projection-worker` handler |
| Crypto-shred PII | поля payload с email/uuid/имена шифруются per-subject ключом |
| CLI `iwe trace show/search/upload` | чтение из Neon + локальный NDJSON backfill |
| Hybrid retrieval API | recency × similarity × importance × decision-relevance |
| OnSessionStart hook | инъекция top-3 похожих trace'ов в контекст агента |

---

## 3. Входы / Выходы

**Входы:**
- Harness JSON от Claude Code `PostToolUse`/`Stop` hooks (tool_name, tool_input, cwd, hook_event_name).
- Кешированные ответы внешних API (если агент вызывал tool — записать ответ для replay).

**Выходы:**
- `~/IWE/.claude/logs/agent-trace/<session-id>.ndjson` (primary, immediate, не теряется offline).
- `learning.agent_trace.session` / `decision` / `hypothesis` (secondary, через async upload).
- `~/IWE/.claude/logs/capture_log.jsonl` — операционный лог самой записи (fired/skip/error/latency).
- CLI output (`iwe trace show`, `iwe trace search`).
- Контекст агента на OnSessionStart (injection похожих trace'ов).

---

## 4. Архитектура (слои)

```
Источники
├── Claude Code harness (PostToolUse, Stop hooks)
├── Внешние API (через tool wrapper — cache response для replay)
└── Atomic ВДВ-шаги (DP.M.060) — каждый = атом trace
        │
        ▼
DP.ROLE.047 Trace Recorder
├── Hook        → ~/IWE/.claude/hooks/agent-trace-recorder.sh
├── NDJSON      → атомарная запись в локальный файл (append-only)
├── Async upload → event-gateway (agent.*)
├── Projection  → learning.agent_trace.* (через worker)
├── PII shred   → per-subject crypto-key
├── CLI         → iwe trace show/search/upload
└── Retrieval API → hybrid score (recency × similarity × importance × decision-relevance)

Потребители
├── DP.ROLE.048 Replay Engine   ← reads до момента T
├── DP.ROLE.050 Pattern Miner   ← reads + join с domain_event
└── DP.ROLE.001 IWE Creator     ← reads через OnSessionStart inject
```

---

## 5. Ограничения (инварианты роли)

1. **Writer не блокирует hot path.** Latency ≤100ms на запись локально. Async upload — вне критического пути. Любая ошибка → exit 0, лог в capture_log.
2. **Append-only, immutable.** UPDATE/DELETE запрещены. Корректировка = compensating event `decision_revised` со ссылкой на исходный event_id.
3. **Все источники недетерминизма зафиксированы.** Без этого SC.038 (replay) не работает детерминированно — это контракт между ролями.
4. **PII через crypto-shredding.** Никакого plaintext email/uuid в `agent_trace.*` payload. Утечка = security incident.
5. **Один шаг = один decision event.** Не группировать несколько решений в один event (нарушает DP.M.060 + ломает кластеризацию pattern miner'а).
6. **Trace ↔ produced_artifacts join при `session.end`.** Не lazy — нужно для причинности на стороне pattern miner.
7. **Атомарная запись NDJSON.** Append через O_APPEND, без частичных записей. Партиции по session-id для параллелизма.
8. **Retention-aware.** События старше hot-retention (TBD: 30 дней) переезжают в warm; warm > 6 мес → cold S3; cold > 2 года → drop с pre-aggregated patterns. Без этого storage растёт линейно навсегда.

---

## 6. Связи с другими ролями

| Роль | Отношение |
|------|-----------|
| DP.ROLE.048 Replay Engine | Downstream consumer: читает trace до T для восстановления контекста. Контракт: SC.037 инв.8 (недетерминизм фиксирован). |
| DP.ROLE.050 Pattern Miner | Downstream consumer: читает trace + join с domain_event. Контракт: SC.037 инв.6 (produced_artifacts при session.end). |
| DP.ROLE.049 Path Coordinator | Sibling: при multi-path каждый из N путей пишет собственный trace branch (parent_session_id). |
| DP.ROLE.001 IWE Creator | Потребитель retrieval API при OnSessionStart. Контракт: ≤500ms latency lazy. |
| DP.ROLE.045 Agent Task Dispatcher | Sibling: dispatcher пишет audit-trail в git, recorder пишет trace в Neon. Не пересекаются (физический vs ментальный слой). |
| R47 Детектор (DP.SC.025) | Ортогональный: ловит **факты провалов** на harness-событиях. Recorder фиксирует **рассуждения** между событиями. Не дублируют. |

---

## 7. Точки входа (интерфейсы)

### Запись decision event (для агента)

Hook автоматически перехватывает; ручной emit:
```python
trace.record_decision(
    hypothesis="Replay через checkpoint",
    rejected=["Replay через full re-execution"],
    rationale="O(длина истории) vs O(snapshot+tail)",
    refs=["DP.SOTA.022 §1"]
)
```

### Чтение (для аналитика / R1)

```bash
iwe trace show <session-id>          # полный trace сессии
iwe trace search "ArchGate WP-N"     # семантический поиск
iwe trace tree <root-session-id>     # дерево форков (если есть)
```

### Retrieval (для OnSessionStart)

```python
similar = trace.retrieve(
    context=current_task,
    weights={"recency": 0.3, "similarity": 0.3, "importance": 0.2, "decision_relevance": 0.2},
    limit=3
)
inject_into_context(similar)
```

---

## 8. Метрики

| Метрика | Норма | Где брать |
|---------|-------|-----------|
| Writer latency p50 | ≤30ms | capture_log.jsonl |
| Writer latency p99 | ≤100ms | capture_log.jsonl |
| Async upload lag | ≤5 мин | cross-DB diff (NDJSON count vs Neon count) |
| Sessions without `produced_artifact_ids` | <5% | weekly grep |
| PII leak detector | 0 hits/нед | security audit B7.4 |
| Retrieval API p50 | ≤500ms | log API calls |

---

## 9. Открытые вопросы (для ArchGate Ф0.5)

1. **Где живёт `agent_trace`** — схема в `learning` (prелим. ставка) vs отдельная БД `agent_observability` vs схема в `health` (WP-244 область).
2. **Bridge с DP.SC.025 capture-bus** — общий event-type prefix `agent.*` или раздельные (`capture.*` vs `trace.*`)?
3. **Retention** — hot 30 дней / warm 6 мес / cold S3 ≤2 года; кто owner cleanup'а?
4. **Sharding по агенту** — Claude vs Kimikode (DP.ROLE.039 peer) в одну схему или раздельно? Если раздельно — `agent_id` колонка обязательна.
