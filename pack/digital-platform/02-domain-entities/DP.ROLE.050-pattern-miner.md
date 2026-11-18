---
id: DP.ROLE.050
name: Pattern Miner (Старатель паттернов)
alias: R33
type: role-description
status: draft
valid_from: 2026-05-17
summary: "Кластеризует trace'ы за период по (trace_features, outcome_features) join, формирует кандидатов AR.NNN с примерами, помечает status: pending-review. Никогда не создаёт правила автоматически."
related:
  specializes: [U.RoleAssignment]
  component_of: [DP.ROLE.001]
  realizes: [DP.SC.040]
  uses:
    - DP.ROLE.047 Trace Recorder    # источник trace
    - learning.domain_event         # outcome side join
    - WP-272 PACK-agent-rules       # target формат AR.NNN
    - DP.SOTA.022 §3                # pattern mining паттерны
    - DP.M.012 Machine-Check Postcondition  # для валидации draft AR
  downstream_consumers:
    - DP.ROLE.015 Captures Applier  # R15 принимает/отклоняет rule-кандидатов (адаптер A)
    - DP.ROLE.001 IWE Creator       # читает weekly report в Week Close
    - DP.ROLE.005 Architect          # monthly audit правил
    - executor-catalog.yaml reflexes:  # адаптер B (WP-423): reflex-кандидат, approve пилот
created: 2026-05-17
updated: 2026-06-21
wp: WP-295
---

# Pattern Miner — DP.ROLE.050 (R33 Старатель паттернов)

> # see DP.SC.040, DP.ROLE.050
>
> **Kind:** Analyst Role — производит кандидатов для human review, не финальные правила.
> **Owner Role:** IWE Platform — исполнитель: `scripts/trace-pattern-miner.py` + alerter rule + monthly audit CLI.

---

## 1. Миссия

Превращать сырьё из trace store в material для эволюции правил **и рефлексов** IWE: видеть, какие паттерны провалов / успехов повторяются за неделю-месяц, и предлагать кандидатов. Без этого учёт превращается в архив — материал есть, но не превращается в обучение.

**Два выходных адаптера (WP-423):** общий движок добычи, разные выходы — (A) rule-кандидат `AR.NNN.md` в PACK-agent-rules (читает агент в промпте, approve R15); (B) reflex-кандидат `executor-catalog.yaml reflexes:` (исполняемый код без LLM, approve пилот). Различаются ТОЛЬКО типом выхода / адресатом approve / классом приёмки / целевым файлом — не алгоритмом добычи (см. [DP.SC.040 §Выходные адаптеры](../08-service-clauses/DP.SC.040-pattern-miner.md)).

Аналогия: старатель на ручье. Промывает песок (trace), находит крупицы золота (повторяющиеся паттерны), показывает заказчику (R15 на apply-captures). Не принимает решений о выплавке слитков — только сортирует породу.

**Граница:** Pattern Miner никогда не создаёт правила автоматически. Точность автоматической атрибуции <10% на длинных трассах (AgenTracer 2025). Каждый кандидат — с phrasing «status: pending-review», финал — за человеком.

---

## 2. Обязанности

| Обязанность | Как выполняется |
|-------------|----------------|
| Weekly batch на Week Close | cron / skill вызывает `iwe miner weekly --week W{N}` |
| Читать trace за период | `learning.agent_trace.*` between dates |
| Join с outcome | `domain_event` за тот же период + `produced_artifact_ids` из session.end |
| Гибридный retrieval-скор для кластеризации | recency × similarity × importance × decision-relevance |
| Кластеризовать похожие trace | DBSCAN / HDBSCAN над hybrid score, не голый cosine |
| Считать `(frequency, severity, importance)` | per-cluster metrics |
| Формировать draft AR.NNN | frontmatter + примеры trace_id + cross-correlation outcome |
| Pending-review pack | extraction-report-совместимый формат `pattern-miner-W{N}.md` |
| Triggerный алерт rapid-cluster | continuous monitor (cron 6h), N≥3 одинаковых за 7 дней → TG |
| Monthly audit правил | `iwe miner audit --since 2026-04-01`: какие AR работают, какие мёртвые |
| Audit-loop калибровки | track accept/reject/defer rate; reject>60% → пересмотр алгоритма |
| Read-only по trace | никаких UPDATE/DELETE; все эффекты — отчёты в inbox |
| Формировать reflex-кандидат (адаптер B, WP-423) | детерминированный исполнимый класс из `gate-decisions.jsonl` / базы косяков → строка `reflexes: source:crystallized enabled:false` + smoke deny-fixture (DP.SC.040 SC.040.4); `enabled:true` требует replay на истории; никогда не включает сам |

---

## 3. Входы / Выходы

**Входы:**
- `learning.agent_trace.{session,decision,hypothesis}` за период.
- `learning.domain_event` за тот же период (для outcome join).
- `git log` (для cross-correlation с физическими артефактами).
- Активный реестр правил `PACK-agent-rules/rules/AR.NNN.md` (для monthly audit).

**Выходы:**
- **Weekly:** `DS-my-strategy/current/inbox/pattern-miner-W{N}.md` (extraction-report-совместимый, `status: pending-review`).
- **Triggerный:** `DS-my-strategy/current/inbox/pattern-miner-RAPID-YYYY-MM-DD.md` + TG-алерт через DP.ROLE.044 Почтальон.
- **Monthly audit:** `DS-my-strategy/current/inbox/pattern-miner-audit-YYYY-MM.md` (актив/мёртвые AR).
- **Audit-loop:** `DS-my-strategy/inbox/pattern-miner-calibration.md` (P/R метрики).

---

## 4. Архитектура (слои)

```
Источники
├── learning.agent_trace.* (trace до периода Т)
├── learning.domain_event (outcome side за тот же период)
└── PACK-agent-rules/rules/AR.NNN.md (активный реестр)
        │
        ▼
DP.ROLE.050 Pattern Miner
├── Loader            → read trace + domain_event за период
├── Join Builder      → (trace_features, outcome_features) совместный вектор
├── Hybrid Retrieval  → recency × similarity × importance × decision-relevance
├── Clusterer         → DBSCAN/HDBSCAN над hybrid score
├── Ranker            → frequency × severity × importance
├── Draft Generator   → draft AR.NNN frontmatter + examples
├── Reporter          → pattern-miner-W{N}.md / RAPID-*.md
├── Continuous Monitor → cron 6h: rapid-cluster detection
├── Monthly Audit     → активность правил + кандидаты на removal
└── Calibration       → P/R на основе R15 решений (accept/reject/defer)

Потребители
├── DP.ROLE.015 Captures Applier ← R15 на apply-captures
├── DP.ROLE.001 IWE Creator       ← R1 на Week Close
└── DP.ROLE.005 Architect          ← R5 на monthly iwe-rules-review
```

---

## 5. Ограничения (инварианты роли)

1. **Никогда не создаёт правила автоматически.** Все кандидаты — `status: pending-review`. Утверждает R15. Источник: AgenTracer 2025 (<10% accuracy на auto-attribution).
2. **Кластеризация по `(trace_features, outcome_features)`, не trace alone.** Голый embedding similarity ловит «похожее по форме», не «причинно релевантное». Источник: SOTA §3.
3. **Provenance каждого кандидата.** AR.NNN frontmatter содержит `derived_from: [trace_id_1, ...]`. Для аудита, replay, отката.
4. **Read-only по trace.** Никаких модификаций `agent_trace.*`. Только отчёты в inbox.
5. **Extraction-report формат.** Кандидаты пишутся как extraction-report-совместимые — R15 работает через стандартный apply-captures flow.
6. **Audit-loop калибровки.** Раз в 4 нед — отчёт P/R майнера. Reject>60% → пересмотр алгоритма (false-positive выше humano-acceptable).
7. **Triggerный алерт ≤24h.** От 3-го одинакового инцидента до TG не более суток. Иначе системные регрессии накапливаются.
8. **Cross-correlation обязательна.** Если SC.037 не записал `produced_artifact_ids` (severe drift), warning «trace data incomplete, candidates may be spurious» в отчёте.
9. **PII через crypto-shred унаследовано.** Майнер читает trace, в котором PII уже зашифрована (SC.037 контракт). Не дешифрует, только агрегирует.
10. **Открытый каталог.** Семантика паттерна определяется человеком на ревью. Майнер только кластеризует и приоритизирует.

---

## 6. Связи с другими ролями

| Роль | Отношение |
|------|-----------|
| DP.ROLE.047 Trace Recorder | Upstream provider: майнер не работает без полного trace + outcome join. Контракт SC.037 инв.6. |
| DP.ROLE.015 Captures Applier | Главный downstream: R15 на apply-captures принимает решения по кандидатам через стандартный extraction-report flow. |
| DP.ROLE.001 IWE Creator | Consumer: R1 на Week Close читает weekly отчёт + reagent на rapid-cluster алерты. |
| DP.ROLE.005 Architect | Consumer: R5 на monthly iwe-rules-review использует audit-отчёт для cleanup правил. |
| R47 Детектор (DP.SC.025) | Ортогональный: SC.025 real-time детекторы; SC.040 batch майнинг. Дополняют, не дублируют. |
| DP.ROLE.044 Почтальон | Sibling: TG-алерты на rapid-cluster через Почтальона. |
| WP-272 PACK-agent-rules | Target формат №1 (адаптер A): draft AR.NNN frontmatter совместим с реестром. |
| `executor-catalog.yaml reflexes:` (адаптер B) | Target формат №2 (WP-423): reflex-кандидат (исполняемый код) vs №1 = `AR.NNN` (поведенческое правило). Approve — пилот; `enabled:true` требует replay на истории (DP.SC.040 §Выходные адаптеры). |

---

## 7. Точки входа (интерфейсы)

### Weekly batch

```bash
iwe miner weekly --week W20
# → DS-my-strategy/current/inbox/pattern-miner-W20.md (status: pending-review)
```

### Triggerный (continuous, cron 6h)

```python
def rapid_cluster_monitor():
    clusters = miner.recent_clusters(window_days=7, min_size=3)
    for cluster in clusters:
        if not already_alerted(cluster.signature):
            emit_event("agent.miner.rapid_cluster", payload=cluster)
            send_tg_alert_via_dp_role_044(cluster)
            write_rapid_report(cluster)
            mark_alerted(cluster.signature)
```

### Monthly audit

```bash
iwe miner audit --since 2026-04-01
# → DS-my-strategy/current/inbox/pattern-miner-audit-2026-05.md
# Содержит:
# - Активные AR: сколько раз сработало, на каких trace, FP rate
# - Мёртвые AR: не сработали месяц → кандидат на removal
# - Сигнал по доменам: 5+ inactive AR в одном домене → возможно класс вышел из обращения
```

### Apply-captures flow (для R15)

```markdown
# Frontmatter weekly отчёта:
---
status: pending-review
capture_source: pattern_miner
capture_method: trace_clustering
week: W20
candidates:
  - draft_ar: AR.301
    pattern_type: incomplete-retrieval-on-long-context
    frequency: 5
    severity: minor
    examples: [trace_a1, trace_b2, trace_c3, trace_d4, trace_e5]
    cross_correlation:
      common_outcome: WP-progress-blocked
  - draft_ar: AR.302
    pattern_type: missing-postcondition-in-DayClose
    frequency: 3
    severity: critical
    examples: [trace_x9, trace_y8, trace_z7]
---
```

R15 проходит через apply-captures skill как через обычный extraction-report.

---

## 8. Метрики

| Метрика | Норма | Где брать |
|---------|-------|-----------|
| Weekly candidates count | ≥1 при активной работе агента | log iwe miner weekly |
| Accept rate (R15) | ≥40% | audit-loop |
| Reject rate | ≤30% | audit-loop (если >60% — пересмотр) |
| Defer rate | ≤30% | audit-loop |
| Rapid-cluster alert latency | ≤24h от 3-го инцидента | log + capture_log |
| Monthly audit cleanup rate | ≥1 мёртвый AR/мес | log iwe miner audit |
| PII leak в кандидатах | 0 hits | security audit B7.4 |
| Cross-correlation coverage | ≥90% candidates имеют outcome | weekly grep |

---

## 9. Открытые вопросы (для ArchGate Ф0.5)

1. **Кластеризация: DBSCAN vs HDBSCAN vs hierarchical?** На малых выборках (50 trace/нед) — HDBSCAN устойчивее к density variation. Калибровать после первой недели реальных данных.
2. **Similarity threshold для merge кластеров.** Старт 0.85, корректировать по reject-rate.
3. **Importance scoring.** Кто решает «важность» паттерна? Простой подход: severity × (frequency / median_frequency). Сложный: human-annotated 10-20 кейсов → train classifier.
4. **Audit-loop калибровка периодичность.** Monthly достаточно? Или quarterly для stability?
5. **Backfill пропусков cross-correlation.** Что делать, если в trace отсутствует `produced_artifact_ids` — silent skip, warning или попытка восстановить из git history?
