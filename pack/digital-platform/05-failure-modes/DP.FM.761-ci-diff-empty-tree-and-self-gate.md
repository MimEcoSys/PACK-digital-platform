---
id: DP.FM.761
name: CI-дифф против HEAD~1 падает на первом коммите репозитория — fallback на empty-tree hash; content-гейт ловит собственное описание политики
type: failure-mode
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_ci_diff_base_empty_tree_fallback.md (WP-493 Ф9, 19.07; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [PACK-digital-platform, PACK-digital-platform]
---

# DP.FM.761: CI-дифф на первом коммите и самолюбование гейта

## Симптом 1
`git diff HEAD~1` → `fatal: bad revision` на initial commit у любого нового репозитория/ветки с CI-гейтом на диффе.

## Паттерн
Fallback-цепочка заканчивается на git empty-tree hash `4b825dc642cb6eb9a060e54bf8d69288fbee4904` (константа для любого репозитория): `git rev-parse HEAD~1 2>/dev/null || echo "$EMPTY_TREE"`.

## Симптом 2 (того же found-on-first-run класса)
Regex/PII-гейт, ищущий паттерны в диффе, ловит СОБСТВЕННОЕ описание политики (методологический текст гейта с примерами «n=3, removing one participant leaves n=2»).

## Паттерн
Любой content-based CI-гейт тестировать на диффе, содержащем описание самого гейта; policy-файлы с порогами в примерах — в explicit exclude-листе, иначе гейт душит сам себя.
