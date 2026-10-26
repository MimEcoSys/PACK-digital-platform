---
id: DP.FM.672
type: failure-mode
status: draft
created: '2026-10-23'
valid_from: '2026-10-22'
pack: PACK-digital-platform
domain: digital-platform
schema_version: 1
trust: medium
epistemic_stage: forming
source: "пир-сессия MC-sessions 2026-10-22-15-git-mirror-ci-matrix (report.md §3-4); commit 8faeaf57 (FMT-exocortex-template, PR #1307)"
source_capture: DS-my-strategy/inbox/captures/2026-10.md:6213
extraction_report: DS-my-strategy/inbox/extraction-reports/2026-10-23-inbox-check-2.md
source_candidate: 1
name: "Пир-сессия согласовала решение «по описанию», проигнорировав частично раскатанный механизм в коде — непокрытый остаток и был живым источником инцидента"
name_ru: "Пир-сессия согласовала решение «по описанию», проигнорировав частично раскатанный механизм в коде — непокрытый остаток и был живым источником инцидента"
name_en: "A peer-session agreed on a solution 'by description', missing an already partially-rolled-out mechanism in the code — the uncovered remainder was the live incident source"
summary: "Пир-сессия (Kimi+Codex) согласовала перенос workflow в excluded_paths, рассуждая по описанию проблемы; при реализации обнаружилось, что per-job guard уже покрывал 5 из 7 job — непокрытые validate и guide-kit-drift были настоящим источником живого шума issue #850, а не отсутствие общего механизма."
related:
  see_also:
  - DP.M.565
tags:
- github-actions
- partial-coverage
- consensus-drift
- root-cause
---

# DP.FM.672 — Консенсус «по описанию» проигнорировал уже существующий частичный механизм

## Механизм

Пир-сессия обсуждала три варианта (A — только документация, B — заморозить доставку workflow через `excluded_paths`, C — полная поддержка зеркала с CI) и согласовала B, сравнивая варианты по описанию проблемы, а не по фактическому коду. При подготовке к реализации B обнаружилось: в `validate-template.yml` уже существует per-job guard (`if: github.repository == ...`, issue #1223), применённый к 5 из 7 job. Job `validate` и `guide-kit-drift` остались без guard'а — именно это и было настоящим источником живого шума issue #850, а не отсутствие общего механизма класса B.

## Историческое наблюдение

Commit `8faeaf57` (FMT-exocortex-template, PR #1307), сессия MC-sessions `2026-10-22-15-git-mirror-ci-matrix`. Решение B (заморозка через `excluded_paths`) решало бы проблему грубее (не запускать job в форке вообще) и не исправляло бы уже накопленные несовместимые зеркала; найденный частичный guard решал точнее и чинил оба случая (старые и новые зеркала).

## Контрмера и тест

Перед реализацией уже согласованного решения — искать в коде существующий механизм для той же проблемы: частичное покрытие (N из M единиц) типично, и непокрытый остаток часто и есть настоящая причина инцидента. Тест: «Применён ли уже похожий guard/механизм к части единиц этого класса? Если да — вероятная причина живого инцидента — непокрытые единицы, а не отсутствие механизма».

## Отличие от соседей

Не дубликат `DP.FM.056` (deprecated-но-referenced: рантайм читает путь до физического удаления — другой механизм) и `DP.FM.369` (one-way sync откатывает фиксы приёмника — другой механизм, регрессия sync-скрипта). Здесь — рассуждение «по описанию» в пир-сессии упускает уже частично раскатанный код-механизм.

## Происхождение

Пир-сессия MC-sessions `2026-10-22-15-git-mirror-ci-matrix` (report.md §3-4); commit `8faeaf57` (FMT-exocortex-template, PR #1307). WP-529 Ф223, issue #850, #1223, PR #1307. Захват: `DS-my-strategy/inbox/captures/2026-10.md:6213`.
