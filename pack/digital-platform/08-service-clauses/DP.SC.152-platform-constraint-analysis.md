---
id: DP.SC.152
name: Анализ ограничения ИТ-платформы (platform-bottleneck)
name_ru: Анализ ограничения ИТ-платформы
name_en: Platform Constraint Analysis
type: sc
status: draft
layer: L4-Personal
summary: "Стратег или CTO получает Constraint Brief с конкретной C2-подсистемой из MAP.002, где максимальное число failing SC, + Stage Dependency Map для устранения. Отличие от SC.045: target жёстко ограничен C2 ИТ-платформой, SC-scan идёт по MAP.002 (12 подсистем, SC.001-SC.151), не по произвольному конвейеру."
consumer: Стратег (DP.ROLE.012), CTO, Диагност (DP.ROLE.042 — для границы C2 vs behaviour)
created: 2026-05-21
updated: 2026-05-21
related:
  specializes: DP.SC.045        # универсальный анализ ограничения — родительский SC
  realizes: []
  uses:
    - DP.ROLE.054               # Аналитик ограничений — носитель
    - DP.WP.016                 # Stage Dependency Map — формат выхода
    - DP.MAP.002                # IWE Service Catalog — источник подсистем и SC-групп
    - .claude/skills/platform-bottleneck
  see_also:
    - DP.SC.045                 # анализ любого конвейера (родитель)
    - DP.SC.044                 # event ingest — типичная SC, первой уходящая в failing
wp: WP-313
---

# [DP.SC.152] Анализ ограничения ИТ-платформы

## Правило (инвариант)

> Нарушение любого = провал SC.

- **Target = C2 ИТ-платформа.** Скилл работает только с системой типа «ИТ-платформа как сервисный каталог» (MAP.002). Для когортного или учебного конвейера — DP.SC.045.
- **SC-scan через MAP.002.** Ф2 идёт по группам SC из MAP.002 (12 подсистем). Прямой поиск failing по группам, не произвольный поиск.
- **Bottleneck = C2 подсистема, не абстракция.** Constraint Brief обязан называть конкретную подсистему MAP.002 (например: «C2.S05 Learning Progress» или «C2.S08 Gamification»). Без привязки к MAP.002 = провал Ф3.
- **Stage Dependency Map привязан к C2 подсистемам.** Этапы Stage Map = подсистемы или группы подсистем MAP.002. Не abstract работа.
- **NBR после любого EC injection.** Унаследовано от SC.045.
- **Calibration record обязателен.** `DS-my-strategy/inbox/bottleneck-pick-runs/<date>-platform.yaml`

---

## Обещание

**Кому:**
- **Стратег (DP.ROLE.012)** — «какая C2 подсистема сейчас является Herbie для wave-rollout / retention D30?»
- **CTO** — «где технический долг создаёт максимальное SC-трение для пользователей?»
- **Диагност (DP.ROLE.042)** — «это C2 issue или behaviour issue?» → граница ответственности

**Зачем:**
- Платформа имеет 12 подсистем и 56 сервисов (MAP.002) — выбор вручную = cognitive overload
- SC-группировка по подсистемам позволяет найти системный Herbie, не symptom
- Без этого: приоритизация спринтов = ad-hoc (recency bias, sexy work bias)

**Что получит:**

```
{
  "platform_card": {
    "subsystems_scanned": 12,
    "sc_failing_count": N,
    "data_freshness": "..."
  },
  "constraint_brief": {
    "bottleneck_subsystem": "C2.S{NN} <name>",
    "failing_sc": ["DP.SC.NNN", ...],
    "trichotomy": "work_flow | work_process | work_execution",
    "class": "policy | resource | cognitive",
    "signals": {...}
  },
  "stage_dependency_map": {
    "stages": [...],   // этапы = C2 подсистемы или группы
    "edges": [...]
  }
}
```

**Триггер:** Явный вызов `/platform-bottleneck [--horizon <wave|quarter>] [--subsystem <C2.SNN>]`

**Время отклика:** ≤20 мин (MAP.002 pre-load добавляет ~5 мин к SC.045)

**Режим отказа:**
- MAP.002 не найден → «Не нашёл MAP.002. Проверь путь.» → СТОП
- Все подсистемы зелёные → «Все C2 SC работают. Bottleneck не в платформе — проверь когортный конвейер (/bottleneck-pick)»
- Данные устарели (>7 дней без git-активности в DS-IT-systems) → ⚠️ добавить к output, не останавливаться

---

## Свидетельства (критерий приёмки)

| Критерий | Как проверить |
|----------|---------------|
| Constraint Brief называет конкретную C2 подсистему | grep «C2.S» в output |
| SC-failing список не пуст (≥1 SC) | calibration YAML `sc_failing` не пустой |
| Stage Map имеет ≥2 этапа | calibration YAML `stage_dependency_map.num_stages ≥ 2` |
| Стратег принял выбор без редиректа | calibration YAML `was_correct: true` (заполняется на Week Close) |

---

## Сценарии использования

### СЦ-1: Strategy Session (Стратег)
«Открываю Strategy Session — какая C2 подсистема тормозит wave-rollout?»
→ `/platform-bottleneck --horizon wave-1`
→ Получает: Constraint Brief + Stage Map → входит в Strategy Session с готовым bottleneck-анализом

### СЦ-2: Sprint Planning (CTO)
«Планирую следующие 2 недели. Где технический долг максимально влияет на пользователей?»
→ `/platform-bottleneck --horizon quarter`
→ Получает: топ-3 подсистемы по failing SC → приоритизированный бэклог подсистем

### СЦ-3: Diagnosis boundary (Диагност, DP.ROLE.042)
«Пилот не прогрессирует — это C2 не работает или поведение пилота?»
→ `/platform-bottleneck --subsystem C2.S05` (подсистема, связанная с пилотом)
→ Получает: SC-status для подсистемы → если SC работают = behaviour issue; если failing = C2 issue
