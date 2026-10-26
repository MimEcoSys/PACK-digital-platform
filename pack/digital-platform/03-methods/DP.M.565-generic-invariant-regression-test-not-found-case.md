---
id: DP.M.565
name: "Генерик регресс-тест на инвариант по всему классу единиц (из реальных источников), а не на найденный случай — плюс отдельная проверка нетавтологичности"
name_ru: "Генерик регресс-тест на инвариант по всему классу единиц (из реальных источников), а не на найденный случай — плюс отдельная проверка нетавтологичности"
name_en: "A generic regression test for an invariant across the whole class of units (from real sources), not the found case — plus a separate non-tautology check"
type: method
pack: PACK-digital-platform
domain: digital-platform
status: draft
trust: medium
epistemic_stage: forming
created: '2026-10-23'
valid_from: '2026-10-22'
summary: "Вместо теста «у job X есть guard» — генерик-тест, читающий реальные workflow и манифест, проверяющий инвариант «любой job, зависящий от исключённого пути, несёт guard» по всем job; отдельный кейс доказывает, что проверка способна упасть (не тавтологична)."
schema_version: 1
related:
  see_also:
  - DP.FM.672
source: "commit 8faeaf57 (FMT-exocortex-template, scripts/tests/test_issue_850_fork_guard.sh); report.md §4 сессии 2026-10-22-15-git-mirror-ci-matrix"
source_capture: DS-my-strategy/inbox/captures/2026-10.md:6222
extraction_report: DS-my-strategy/inbox/extraction-reports/2026-10-23-inbox-check-2.md
source_candidate: 2
---

# DP.M.565 — Генерик регресс-тест на инвариант по классу, не на найденный случай

## Входы и выходы

Вход: баг «механизм X не применён к единице Y» (например, guard не применён к конкретному job), найденный и исправленный точечно. Выход: тест, читающий реальные конфигурационные файлы (не переписанные копии) и проверяющий инвариант по всему классу единиц, выведенный из реального источника, плюс отдельный негативный кейс, доказывающий, что тест способен упасть.

## Метод

1. После точечного фикса («job X теперь несёт guard») не писать тест вида «у job X есть guard» — он тавтологичен будущему такому же пропуску у другого job.
2. Извлечь из реальных файлов (workflow, манифест доставки) правило-инвариант: «любой job, чьи шаги ссылаются на путь из класса исключённых, обязан нести guard уровня job».
3. Тест читает актуальные файлы напрямую (`validate-template.yml`, `update-manifest.json`), не их заранее переписанные копии — иначе тест проверяет представление бага, а не живой код.
4. Добавить отдельный кейс (T3), доказывающий нетавтологичность — тест способен дать FAIL на намеренно некорректном входе.

## Проверенный прецедент

`scripts/tests/test_issue_850_fork_guard.sh` (commit `8faeaf57`): «extracts the real validate-template.yml and update-manifest.json... asserts every job whose steps reference a path from excluded_paths[] carries the canon-only guard at job level... deliberately generic... T3 доказывает, что проверка не тавтологична».

## Forces

Специфичность теста под один известный баг (быстрее написать) ↔ generic-тест на инвариант (медленнее написать, ловит будущие аналогичные пропуски у других единиц класса).

## Отличие от соседей

Связан с `DP.FM.672` (тот же инцидент — частичное покрытие guard'а, найденное пир-сессией); здесь — контрмера-метод (как писать регресс-тест), там — сам failure mode (почему решение «по описанию» его не поймало). Смежно с `DP.D.208` (нетавтологичность проверки вообще) — здесь конкретная техника для конфигурационных регресс-тестов, не общее различение.

## Происхождение

Commit `8faeaf57` (FMT-exocortex-template, `scripts/tests/test_issue_850_fork_guard.sh`); report.md §4 сессии MC-sessions `2026-10-22-15-git-mirror-ci-matrix`. WP-529 Ф223, issue #850. Захват: `DS-my-strategy/inbox/captures/2026-10.md:6222`.
