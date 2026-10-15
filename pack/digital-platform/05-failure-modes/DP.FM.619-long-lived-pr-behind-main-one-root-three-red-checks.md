---
id: DP.FM.619
type: failure-mode
status: draft
created: "2026-10-13"
valid_from: "2026-10-13"
name: "Застрявший долгоживущий PR с конфликтом и тремя красными проверками — один корень: отставание от main после среза релиза"
name_ru: "Застрявший долгоживущий PR с конфликтом и тремя красными проверками — один корень: отставание от main после среза релиза"
name_en: "A stuck long-lived PR with conflict and three red checks has one root: falling behind main after a release cut"
summary: "PR #1202 стоял с конфликтом в CHANGELOG, просроченным сгенерированным манифестом и записью журнала под неверным заголовком release — три разных на вид дефекта, один корень: ветка давно не ребейзилась от main, прошедшего через срез релиза."
pack: PACK-digital-platform
domain: digital-platform / release-pipeline
schema_version: 1
trust: observed
epistemic_stage: forming
source: "git commit 0b587e253 в DS-my-strategy (WP-7 Ф226) + git commit 8b4f39bc в FMT-exocortex-template (PR #1202, fix(changelog): move entry under [Unreleased])"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:3130"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-13-inbox-check-4.md"
source_candidate: 3
related:
  see_also: [DP.METHOD.202]
tags: [changelog, release-cut, stale-branch, manifest-drift, long-lived-pr]
---

# DP.FM.619 — Долгоживущий PR против среза релиза: три красных проверки, один корень

## Симптом

PR #1202 стоял одновременно с конфликтом и тремя красными проверками: (1) конфликт в CHANGELOG.md — независимые дописывания разных PR в одну точку; (2) просроченный сгенерированный манифест (`update-manifest.json`), не перегенерированный после чужих мерджей на main; (3) запись журнала изменений без номера PR и под заголовком уже датированного релиза, а не под `[Unreleased]` (гейт `check-changelog-entry.sh` требует запись именно там).

## Причина

PR открыт до среза релиза v0.41.8; пока он стоял, main ушёл вперёд — релиз переименовал секцию `[Unreleased]` в датированную `[0.41.8]` и завёл новую пустую `[Unreleased]`, поэтому запись PR при будущем мердже оказалась бы внутри уже выпущенного релиза; параллельные PR дописывали в ту же точку CHANGELOG (конфликт); сгенерированный артефакт устарел относительно main. Три проверки выглядят как три разных дефекта, но чинятся одним порядком — все три являются проявлениями одного отставания от main.

## Противодействие

Единый порядок разморозки долгоживущего PR в репозитории с автосрезом релизов: слить main → перегенерировать производные артефакты (манифест) → перенести запись журнала изменений под текущий `[Unreleased]` с номером PR → прогнать тесты и валидатор локально → пушить.

## Тест обнаружения

«PR стоит дольше, чем прошло срезов релиза с момента его создания, и красных проверок больше одной одновременно?» Да → диагностика начинается с подсчёта отставания от main (сколько релизов срезано с момента ветвления), а не с разбора каждой красной проверки по отдельности.

## Связи

- Соседний, не дубль: capture того же периода «Слившийся PR без записи в CHANGELOG [Unreleased] красит гейт» — там запись отсутствует, здесь присутствует, но под неверным заголовком после среза релиза.
- `DP.METHOD.202` (manifest-only version check) — смежный класс pre-release проверок, другой конкретный триггер (version-string mismatch, не staleness-от-main триада).

## Источник

WP-7 Ф226, WP-545 Ф15, FMT-exocortex-template PR #1202, `check-changelog-entry.sh`, `update-manifest.json`; git commit 0b587e253 (DS-my-strategy), 8b4f39bc (FMT-exocortex-template).
