---
id: DP.FM.628
type: failure-mode
status: draft
created: "2026-10-15"
valid_from: "2026-10-15"
name: "Проверка «чужой worktree блокирует коммит» обязана сверять принадлежность репозитория — иначе worktree совсем другого репо ложно помечает коммит как конфликтующий"
name_ru: "Проверка «чужой worktree блокирует коммит» обязана сверять принадлежность репозитория — иначе worktree совсем другого репо ложно помечает коммит как конфликтующий"
name_en: "An 'another worktree blocks this commit' check must verify repository ownership first — otherwise a worktree of a totally unrelated repo falsely flags the commit as conflicting"
summary: "При нескольких одновременно открытых изолированных worktree разных WP на одном хосте, check 6a (worktree-mismatch comparison) смотрел на ЛЮБОЙ активный semaphore на хосте, независимо от того, какому репозиторию принадлежит его зарегистрированный worktree. Чужой изолированный worktree совершенно другого репозитория мог заставить проверку считать текущий коммит конфликтующим, хотя они не связаны. Фикс сверяет git-common-dir (origin remote как fallback) ДО того, как worktree вообще рассматривается."
pack: PACK-digital-platform
domain: digital-platform / session-guard
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit 4c77dcc в iwe-local-config"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:3850"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-15-inbox-check-8.md"
source_candidate: 4
related:
  see_also: ["DP.FM.576", "DP.FM.627"]
tags: [git, worktree, session-guard, false-positive, multi-repo]
---

# DP.FM.628 — Worktree-mismatch check обязан сверять принадлежность репозитория

## Тезис и механизм ошибки

При нескольких одновременно открытых изолированных worktree разных WP на одном хосте, проверка 6a (worktree-mismatch comparison) смотрела на ЛЮБОЙ активный semaphore на хосте, независимо от того, какому репозиторию принадлежит его зарегистрированный worktree. Изолированный worktree совершенно ДРУГОГО репозитория мог заставить проверку решить, что текущий коммит конфликтует с ним — ложное срабатывание, не связанное с реальным репозиторием коммита.

## Диагностический принцип

«Есть какой-то зарегистрированный worktree на хосте» ≠ «есть worktree именно ЭТОГО репозитория у ЭТОГО коммита» — смешение этих двух предикатов даёт ложные совпадения при нескольких параллельных репозиториях/сессиях на одном хосте.

## Проверка

«Сверяется ли git-common-dir (или origin remote как fallback) ДО того, как worktree вообще рассматривается как потенциальный конфликт?» Нет → риск ложного срабатывания DP.FM.628 при любой параллельной сессии на том же хосте, работающей с ДРУГИМ репозиторием.

## Границы

Применимо к хостам с несколькими одновременно открытыми изолированными worktree РАЗНЫХ репозиториев (не разных WP одного репозитория — там сверка общая и корректна). Эскалация до hard-block этим фиксом не возвращена — исправлена только сверка принадлежности репозитория.

## Связи

- `DP.FM.576` — смежная тема «проверка владения/конфликта путает представления worktree», другой механизм: там — `scope_clean` даёт ложный `ownership_ambiguous` для сессионных карточек в изолированной копии (блокирует закрытие при фактически готовой доставке); здесь — check 6a путает worktree чужого репозитория с конфликтующим.
- `DP.FM.627` — тот же инцидент-кластер (canon sync review 2026-10-15), другой механизм (там — снэпшот молча устаревает после reset).
- Источник: WP-530 Ф94, peer-session 2026-10-15-26-wp530-ostatki-revision.
