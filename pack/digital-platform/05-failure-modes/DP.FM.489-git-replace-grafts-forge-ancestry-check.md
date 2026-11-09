---
id: DP.FM.489
type: failure-mode
status: active
created: "2026-09-21"
valid_from: "2026-09-21"
name: "git replace/grafts подделывают проверку ancestry «уже доставлено» без изменения origin"
name_ru: "git replace/grafts подделывают проверку ancestry «уже доставлено» без изменения origin"
name_en: "git replace/grafts overlays forge the already-delivered ancestry check without touching origin"
summary: "Локальные git replace и legacy grafts меняют видимый граф объектов и заставляют ancestry-проверку принять недоставленный коммит за опубликованный."
pack: PACK-digital-platform
domain: digital-platform / multi-agent-git-coordination
schema_version: 1
trust: medium
epistemic_stage: observed
source: "git commits 28e5d1e, ca2f2cc, 4eb2fef в iwe-local-config; 6ead5fe03 в DS-my-strategy"
source_capture: "DS-my-strategy/inbox/captures/2026-09.md:2882"
related:
  see_also: [DP.D.316, DP.M.414, DP.METHOD.249]
tags: [git, ancestry, security, merge-base, multi-agent-coordination]
---

# DP.FM.489 — git replace/grafts подделывают проверку ancestry

## Механизм ошибки

Проверка доставки доверяет `git merge-base --is-ancestor` как доказательству публикации на `origin`. `git replace` и `.git/info/grafts` локально подменяют видимый объект-вершину: недоставленный коммит добавляется родителем и после этого читается как уже влитый, хотя origin не менялся. Механизм подтверждён для обоих путей подмены.

## Диагностический принцип

Ancestry-проверка доказывает состояние origin только при явно отключённых локальных переписываниях графа: `GIT_NO_REPLACE_OBJECTS=1` и `GIT_GRAFT_FILE=/dev/null`. Переменные нужно передать и в пересобранное окружение подпроцесса.

## Проверка

«Вызов git, отвечающий на вопрос о доставке, выполняется с отключёнными replace/grafts?» Нет — локальный граф может дать ложное доказательство публикации.

## Границы и связи

Применимо к решениям «уже опубликовано / можно пропустить», основанным на ancestry. `DP.D.316` разводит доставку коммита и содержимого; `DP.METHOD.249` комбинирует content и ancestry в другом сценарии.

## Происхождение

Источник: WP-7 Ф160–Ф163 и WP-484.
