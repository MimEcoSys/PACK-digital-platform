---
id: DP.M.509
type: method
status: draft
created: "2026-10-09"
valid_from: "2026-10-09"
name_ru: "Единая классификация «грязного» git-чекаута (mirror/queue/automation/real) через общий модуль вместо голого числа изменённых путей в каждом guard-скрипте по-своему"
name_en: "Unified dirty-checkout classification (mirror/queue/automation/real) via a shared module, instead of each guard script counting changed paths its own way"
summary: "Три независимых guard-скрипта (session-guard.sh --isolate, destructive-guard.sh AR.306, git-dirty-guard.sh/tsekh1-git-sync.sh) классифицировали «грязь» git-дерева каждый по-своему и печатали голое число изменённых путей без разбивки — разные сессии видели 30/56/68 путей на разных хостах и репортили одно и то же состояние пилоту как новую находку каждый раз. Общий модуль canon-state.sh классифицирует грязные пути на 4 категории (mirror/queue/automation/real) и даёт один и тот же человекочитаемый паспорт инцидента с единым incident_id везде, откуда вызывается."
pack: PACK-digital-platform
domain: digital-platform / git-infrastructure
schema_version: 1
trust: medium
epistemic_stage: forming
related:
  see_also: [DP.M.500]
source: "git commit 7fd4715 в iwe-local-config"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:1989"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-09-inbox-check-4.md"
source_candidate: 2
tags: [git, dirty-state, guard-script, shared-classifier, incident-id]
---

# DP.M.509 — Единая классификация «грязного» git-чекаута через общий модуль

## Проблема

Три независимых guard-скрипта (`session-guard.sh --isolate`, `destructive-guard.sh` AR.306, `git-dirty-guard.sh`/`tsekh1-git-sync.sh`) классифицировали «грязь» git-дерева каждый по-своему и печатали только голое число изменённых путей без разбивки по причине. Разные сессии на разных хостах видели 30/56/68 путей и репортили пилоту одно и то же состояние как новую находку при каждой встрече — отсутствие единой классификации и единого incident_id размножало один инцидент на много «новых» алертов.

## Метод

Общий модуль `scripts/lib/canon-state.sh` классифицирует грязные пути на 4 категории:

| Категория | Смысл |
|-----------|-------|
| `mirror` | Зеркальная/служебная копия, не рабочие изменения |
| `queue` | Файлы очереди/обработки в процессе |
| `automation` | Изменения, оставленные автоматикой/скриптами |
| `real` | Настоящие незакоммиченные рабочие изменения |

Любой вызывающий guard-скрипт получает один и тот же человекочитаемый «паспорт» инцидента и один и тот же `incident_id` для одного и того же состояния — независимо от того, какой из трёх скриптов его обнаружил первым.

## Тест применимости

«Больше одного скрипта в системе принимает решение на основе того, "грязно" ли git-дерево, и каждый считает/классифицирует это по-своему?» Да → заменить параллельные ad-hoc проверки одним общим классификатором с устойчивой схемой категорий и единым incident_id.

## Связи

- **DP.M.500** (Reuse content-based classifier over parallel git-state heuristic) — тот же общий принцип («не строить параллельный ad-hoc классификатор, распространить/разделить один общий») применён к другой конкретной задаче (безопасная перезапись файла шаблона vs классификация грязного дерева для guard-скриптов). Два независимых случая одного архитектурного паттерна за одну неделю (WP-485/592 и WP-538/545) — кандидат на обобщение в отдельный принцип при появлении третьего прецедента.

## Происхождение

git commit `7fd4715` в iwe-local-config. WP-538, WP-545.
