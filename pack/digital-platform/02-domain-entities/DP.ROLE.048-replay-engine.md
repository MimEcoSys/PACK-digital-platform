---
id: DP.ROLE.048
name: Воспроизводитель сессий
name_ru: Воспроизводитель сессий
name_en: Replay Engine
aliases:
  - Replay Engine
  - Машина повторов
alias: R31
type: role-description
status: draft
valid_from: 2026-05-17
summary: "Восстанавливает состояние агента на момент T из trace + событий, создаёт fork-сессию. Детерминированное воспроизведение через checkpoint + reseed. Read-only по исходному trace."
related:
  specializes: [U.RoleAssignment]
  component_of: [DP.ROLE.001]
  realizes: [DP.SC.038]
  uses:
    - DP.ROLE.047 Trace Recorder  # источник trace
    - learning.domain_event       # физические события до T
    - learning.agent_trace.*      # ментальный слой до T
    - WP-253 event sourcing       # инфраструктура
    - DP.SOTA.022 §1              # snapshot/replay паттерны
  downstream_consumers:
    - DP.ROLE.001 IWE Creator     # agent в fork-сессии
    - DP.ROLE.005 Architect       # для архитектурного «что-если»
    - DP.ROLE.049 Path Coordinator # multi-path форки = N replay'ев от одной точки
created: 2026-05-17
updated: 2026-11-22
wp: WP-295
---

# Воспроизводитель сессий — DP.ROLE.048

> **Прежнее имя** — «Replay Engine», «Машина повторов»; переименовано решением пилота 22.11.2026 (DP.ROLE.001 §3.6, РП-616 Ф4); номер R из заголовка убран — он занят другими ролями (DP.ROLE.001 §3.6 п. 1, §3.7).

> # see DP.SC.038, DP.ROLE.048
>
> **Kind:** Reconstructor Role — собирает прошлое состояние из событий.
> **Owner Role:** IWE Platform — исполнитель: CLI `iwe replay` + библиотека `restore_context()` + snapshot writer.

---

## 1. Миссия

Дать возможность взять любое событие из истории, восстановить состояние агента на момент его принятия и пройти альтернативной веткой — для архитектурных «что-если», воспроизведения багов, учебных кейсов.

Аналогия: VCS-time-machine. Не меняет прошлое, не делает работу — даёт чистую среду, идентичную моменту T, в которой можно начать заново. Любая запись новой сессии = новая ветка, родительская не страдает.

**Граница:** Replay не воспроизводит внешний мир — live API на момент T могут быть недоступны или ответить иначе. Используются кешированные ответы из trace; если их нет — explicit warning, не silent re-fetch.

---

## 2. Обязанности

| Обязанность | Как выполняется |
|-------------|----------------|
| Принимать `event_id` для replay | CLI `iwe replay <event-id> --fork [--branch name] [--message ...]` |
| Загружать snapshot ≤ T | поиск ближайшего snapshot до event_id, чтение из `agent_trace.snapshot` |
| Доигрывать хвост событий [snapshot, T] | чтение `domain_event` + `agent_trace.*` between |
| Собирать восстановленный контекст | initial prompt + список «прочитанных» файлов на момент T + открытые гипотезы |
| Reseed недетерминизма | использовать тот же seed/temperature/timestamp; override через `--new-seed N` явно |
| Создавать fork-сессию | новая запись в `agent_trace.session` с `parent_event_id` |
| Поддерживать parent-child граф | FK constraint + `iwe trace tree <root-id>` визуализация |
| Snapshot writer | каждые 20-50 решений или 5-10 мин в `agent_trace.snapshot` (сериализованное состояние) |
| Retention-проверка | при попытке replay'а удалённого события — explicit error «events removed by retention policy» |
| Audit лог forks | каждый fork = git commit с `parent_event_id` + `selector_decision` |

---

## 3. Входы / Выходы

**Входы:**
- `event_id` (target момент).
- Опциональные параметры: `--branch name`, `--message reason`, `--new-seed N`, `--new-temperature T`, `--allow-stale-cache`.
- Из `agent_trace.snapshot` (ближайший до T) + `agent_trace.*` (хвост до T) + `domain_event` (физические события до T).

**Выходы:**
- Восстановленный контекст (сериализованный prompt + file list + hypotheses + nondeterminism params).
- Новая `agent_trace.session` запись с `parent_event_id`.
- `agent_trace.fork_session` запись с метаданными форка (selector_decision, branch_name, forked_at).
- CLI output `iwe trace tree` — визуализация дерева форков.

---

## 4. Архитектура (слои)

```
Источник данных
├── learning.domain_event (физические события до T)
├── learning.agent_trace.* (ментальный слой до T)
└── learning.agent_trace.snapshot (checkpoints)
        │
        ▼
DP.ROLE.048 Replay Engine
├── Snapshot Loader  → ближайший до event_id
├── Event Tail       → события между snapshot и T
├── Context Builder  → assemble восстановленного контекста
├── Nondeterminism   → reseed из payload (DP.ROLE.047 контракт)
├── Fork Writer      → new session с parent_event_id
├── Tree Visualizer  → iwe trace tree
└── Snapshot Writer  → каждые 20-50 решений / 5-10 мин (через recorder hook)

Потребители
├── DP.ROLE.001 IWE Creator    ← fork-сессия для «что-если»
├── DP.ROLE.005 Architect       ← баг-репродукция, учебные случаи
└── DP.ROLE.049 Path Coordinator ← multi-path = N replay'ев одной точки
```

---

## 5. Ограничения (инварианты роли)

1. **Read-only по исходному trace.** Replay никогда не модифицирует `domain_event` или родительскую `agent_trace.session`. Все эффекты — в новые fork-записи.
2. **Детерминированность до момента T.** Прочитанные события — только `created_at <= T`. Никаких более поздних. Это обеспечивает воспроизводимость.
3. **Все источники недетерминизма из trace.** Без override используются ТЕ ЖЕ значения. Override = explicit flag (никаких имплицитных reseed).
4. **Parent-child граф append-only.** Удаление родителя запрещено до удаления всех потомков. FK constraint в БД + application guard.
5. **Snapshot-aware.** Длинные replay'и (≥1000 событий) обязаны использовать snapshot. O(длина истории) без snapshot = деградация >30s, недопустимо.
6. **Retention-aware с explicit error.** Если события за период удалены — error «events removed by retention policy», не silent partial.
7. **External API responses — cached or warning.** Live re-fetch только с `--allow-stale-cache` flag.
8. **State файловой системы — git history.** Replay читает файлы из git commit ≤T, не текущее состояние диска.

---

## 6. Связи с другими ролями

| Роль | Отношение |
|------|-----------|
| DP.ROLE.047 Trace Recorder | Upstream provider: replay не работает без полного trace с зафиксированным недетерминизмом. Жёсткий контракт по SC.037 инв.8. |
| DP.ROLE.049 Path Coordinator | Sibling: multi-path = N независимых fork'ов от одной точки запуска. Caller передаёт N event_id (один на путь). |
| DP.ROLE.050 Pattern Miner | Sibling: pattern miner может запрашивать replay для проверки гипотез о причинах провалов («что если в этой сессии не было шага X»). |
| DP.ROLE.001 IWE Creator | Главный consumer: восстановленный контекст инжектируется в новую сессию для прохождения альтернативной ветки. |
| WP-253 (Event Sourcing) | Инфраструктурный upstream. Replay поверх существующего event sourcing pipeline. |

---

## 7. Точки входа (интерфейсы)

### Fork-replay для R1

```bash
# Архитектурный «что-если»
iwe replay evt_a1b2c3 --fork \
    --branch "wp-N-alt-B" \
    --message "Try approach B instead of A on ArchGate"

# Баг-репродукция
iwe replay evt_x9y8z7 --fork \
    --branch "bug-repro-2026-05-17"

# Учебный случай (read-only контекст)
iwe replay evt_q1w2e3 --fork \
    --branch "training-kimikode" \
    --read-only-context
```

### Визуализация дерева форков

```bash
iwe trace tree session_abc123
# Output:
# session_abc123 (origin, 2026-05-06)
# ├── session_def456 (fork, 2026-05-10) — selector_decision: human_override
# │   └── session_ghi789 (fork, 2026-05-15) — selector_decision: archgate_winner
# └── session_jkl012 (fork, 2026-05-12) — selector_decision: bug_repro
```

### Snapshot writer (background, через recorder hook)

```python
def maybe_snapshot(session, last_snapshot_at):
    if decisions_since_snapshot >= 20 or minutes_since_snapshot >= 5:
        state = serialize_agent_state(session)
        agent_trace.snapshot.insert(session_id, T, state)
```

---

## 8. Метрики

| Метрика | Норма | Где брать |
|---------|-------|-----------|
| Восстановление контекста latency p50 | ≤2 сек | log iwe replay |
| Восстановление контекста latency p99 | ≤5 сек | log iwe replay |
| Failed replays (event not found, retention) | <2% | log + capture_log |
| Determinism test (replay × 2 на одном event_id) | byte-equal | weekly smoke |
| Snapshot coverage (sessions с ≥1 snapshot) | ≥80% длинных | grep agent_trace.snapshot |
| Fork tree depth | ≤5 в типичном случае | iwe trace tree |

---

## 9. Открытые вопросы (для ArchGate Ф0.5)

1. **Snapshot policy** — каждые 20-50 решений или 5-10 мин? Какой из триггеров primary? (Сейчас: 20 решений as primary, 10 мин как fallback.)
2. **Fork-метаданные таблица** — отдельная `agent_trace.fork_session` со ссылкой на `agent_trace.session` или поле в session?
3. **External API cache scope** — все tool calls или только некоторые типы (deterministic-by-input)?
4. **Live re-fetch policy** — кто решает, что safe re-fetch? Per-tool whitelist или explicit user flag?
