---
id: DP.FM.578
type: failure-mode
status: draft
created: "2026-10-09"
valid_from: "2026-10-08"
name: "`gh pr create` не поддерживает `--json` ни в одной версии gh — номер PR нужно парсить из напечатанного URL"
name_ru: "`gh pr create` не поддерживает `--json` ни в одной версии gh — номер PR нужно парсить из напечатанного URL, не из второго вызова"
name_en: "`gh pr create` has no `--json` flag in any gh version — parse the PR number from the printed URL, not a second call"
summary: "Скрипт публикации падал каждый час на `gh pr create --json number --jq '.number'`: у подкоманды `pr create` флага `--json` нет ни в одной версии `gh` (в отличие от `pr view`/`pr list`). `gh` и так печатает URL созданного PR в stdout при успехе — номер извлекается оттуда без дополнительного вызова."
pack: PACK-digital-platform
domain: digital-platform / ci-cd-tooling
schema_version: 1
trust: observed
epistemic_stage: forming
source: "git commit 4683ff7 в DS-ai-systems (WP-529, пир-сессия 2026-10-08-01-template-sync-chronic-failure); независимо описано тем же утром в DS-my-strategy (commit 13c3066c3, inbox/bugs/bug-2026-10-08-template-sync-gh-pr-create-json-unknown-flag.md, status: resolved, иной предложенный фикс)"
related:
  see_also: [DP.FM.547, DP.M.300]
tags: [gh-cli, github, ci-cd, shell-scripting, pipefail]
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:1871"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-09-inbox-check.md"
source_candidate: 3
---

# DP.FM.578 — `gh pr create` не поддерживает `--json`

## Описание

`template-sync.sh` падал каждый час на `gh pr create --repo ... --json number --jq '.number'`. У подкоманды `pr create` CLI `gh` (проверено на 2.72.0) флага `--json` нет ни в одной версии — в отличие от `pr view`/`pr list`/`pr status`, у которых `--json` есть. При успешном создании PR `gh pr create` печатает в stdout полный URL созданного PR (`https://github.com/.../pull/N`); номер — последний сегмент `/pull/N` в этом выводе.

## Причина

`--json` реализован у части подкоманд `gh` (там, где команда возвращает структурированный список/объект), но не у `pr create`, которая по дизайну возвращает только URL как побочный эффект успеха. Предположение «у этой подкоманды должен быть тот же флаг, что у соседних» не было проверено по `gh pr create --help` до написания скрипта.

## Симптомы

- `gh pr create ... --json number` завершается ошибкой уровня CLI (неизвестный флаг) на любой установленной версии `gh`.
- Скрипт, рассчитывающий получить номер PR сразу из `pr create`, систематически падает на этом шаге при каждом запуске, а не эпизодически.

## Противодействие

1. Номер PR получать парсингом URL, который `gh pr create` печатает в stdout при успехе (последний `/pull/<N>`), а не дополнительным флагом самой команды.
2. Альтернатива (не принятая здесь, но валидная) — отдельный вызов `gh pr view --json number` после `pr create`; проще не плодить второй вызов, когда URL уже напечатан.
3. Парсинг номера из URL защищать от пустого совпадения (`|| true` под `pipefail`), чтобы отсутствие совпадения не обрывало счастливый путь — смежный, отдельно описанный класс (`DP.FM.547`).

## Границы

Специфично для `gh pr create`; не утверждает что-либо про `--json` у других подкоманд `gh` (`pr view`/`pr list` его поддерживают).

## Связи

- `DP.FM.547` — присваивание результата `grep` без `|| true` под `pipefail` ломает счастливый путь; применено здесь при защите парсинга URL от пустого совпадения.
- `DP.M.300` — `gh pr diff` на branch-on-branch вводит в заблуждение, нужен `checkout` + `git log`: смежный класс «поведение подкоманды `gh` не совпадает с интуитивным ожиданием».
- DS-репо-инцидент того же утра (`inbox/bugs/bug-2026-10-08-template-sync-gh-pr-create-json-unknown-flag.md`, resolved) — тот же баг, другой предложенный фикс (доп. вызов `gh pr view`); здесь зафиксирован принятый, более простой фикс как переносимое знание о самом `gh` CLI.

## Источник

git commit `4683ff7` в DS-ai-systems (WP-529, пир-сессия `2026-10-08-01-template-sync-chronic-failure`).
