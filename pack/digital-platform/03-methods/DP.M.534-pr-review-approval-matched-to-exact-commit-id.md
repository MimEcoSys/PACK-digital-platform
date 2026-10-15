---
id: DP.M.534
name: "GitHub PR review одобрение матчится по точному commit_id промотируемого кода, а не по номеру/состоянию PR — иначе stale force-pushed approval проходит как действующее"
name_ru: "GitHub PR review одобрение матчится по точному commit_id промотируемого кода, а не по номеру/состоянию PR — иначе stale force-pushed approval проходит как действующее"
name_en: "GitHub PR review approval must be matched against the exact commit_id of the promoted code, not the PR number/state — otherwise a stale force-pushed approval passes as valid"
type: method
pack: PACK-digital-platform
domain: digital-platform / release-verification
trust: medium
epistemic_stage: forming
status: draft
created: "2026-10-15"
valid_from: "2026-10-15"
source: "git commit 6a42c4e5 в aist_bot_newarchitecture"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:3600"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-15-inbox-check-3.md"
source_candidate: 1
tags: [github, pr-review, release-gate, fail-closed, toctou, force-push]
schema_version: 1
summary: "GitHubSourceCandidateResolver проверяет не только что PR в approved-состоянии, но что одобрение числится за точным commit_id, который сейчас промотируется — иначе force-push после одобрения протаскивает непроверенный код под старой подписью review."
---

# DP.M.534 — Review-одобрение матчится по точному commit_id, не по состоянию PR

## Проблема

Гейт промоции доверяет внешнему review API (GitHub/GitLab) как сигналу «ревью пройдено». Если одобрение привязывается к PR как долгоживущей сущности («PR в approved-состоянии»), а не к конкретному коммиту, то force-push поверх уже одобренного кода (с произвольным, в т.ч. непроверенным содержимым) формально проходит гейт — review API продолжает показывать «approved», хотя одобрение выдавалось на другой код.

## IPO-паттерн

| Элемент | Описание |
|---|---|
| Входы | PR/review-статус от стороннего API + точный commit_id промотируемого кода |
| Обработка | Проверить не только состояние PR (approved, head/base/open), но и что сохранённое одобрение зарегистрировано РОВНО за этим commit_id, а не за более ранним состоянием той же ветки |
| Выходы | Промоция разрешена только если одобрение валидно именно для текущего коммита; иначе — явный отказ (stale approval), не тихий проход |

## Прецедент

`GitHubSourceCandidateResolver` (WP-562 Ф3.4) проверяет release-кандидата локальным `git fetch`+`rev-parse` против `candidate_ref`/`base_ref` (TOCTOU-safe, fail-closed на протухшую ссылку) и дополнительно требует, чтобы одобрение ревью числилось за тем же точным `commit_id`, что промотируется сейчас, а не просто «PR в одобренном состоянии». Отдельная проверка `head/base/open` отклоняет несвязанные PR, а привязка к `commit_id` отклоняет stale force-pushed approval.

## Тест применимости

«Гейт промоции доверяет стороннему review-API по состоянию PR (approved), без проверки, что это одобрение выдано РОВНО на коммит, который сейчас промотируется?» Да → риск: force-push после одобрения протащит непроверенный код под старой подписью.

## Связи

WP-562 Ф3.4, peer-session 2026-10-14-17-wp562-release-contour.
