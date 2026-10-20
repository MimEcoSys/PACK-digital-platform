---
id: DP.FM.634
type: failure-mode
status: draft
created: "2026-10-16"
valid_from: "2026-10-15"
name_ru: "Совпадение владельца семафора недостаточно для решения «карточка осиротела» при обратном relocate — нужна отдельная, уже протестированная проверка устаревания"
name_en: "Semaphore owner match alone cannot decide an orphaned card on reverse relocate — a separate, already-tested staleness check is required"
summary: "При обратном relocate-card (canonical→isolated) единственным критерием сначала было совпадение владеющего semaphore. Ревью (Kimi, round 2) указало: это не отличает брошенную карточку от той, которую владелец сейчас активно продвигает. Закрыто переиспользованием уже существующего и протестированного критерия устаревания _is_orphan(), а не новым механизмом."
pack: PACK-digital-platform
domain: digital-platform
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit 6673201f7 в DS-my-strategy (WP-7 Ф229, peer-session 2026-10-15-04-wp7-f229-relocate-card-fix)"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:3877"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-16-inbox-check.md"
source_candidate: 2
related:
  see_also: ["DP.FM.590", "DP.FM.603", "DP.FM.614"]
tags: [semaphore, orphan-detection, relocate-card, owner-match, staleness-check]
---

# DP.FM.634 — Совпадение владельца не отличает брошенную карточку от активно продвигаемой

## Симптом

При обратном relocate-card (canonical→isolated) единственным критерием была проверка совпадения владеющего semaphore. Критерий не отличал карточку, которую владелец бросил, от той, которую он в этот момент активно продвигает.

## Причина

Owner-match отвечает на вопрос идентичности («чей это semaphore») — не на вопрос активности («жив ли сейчас этот владелец»). Код использовал ответ на первый вопрос как ответ на второй.

## Фикс

Обратная ветка `_relocation_state_ok` дополнительно требует `_is_orphan()` — уже существующий и протестированный в системе критерий устаревания — переиспользованный, а не передобытый заново.

## Тест обнаружения

«Критерий, решающий судьбу карточки (брошена/активна), проверяет только совпадение владельца, или также независимый признак активности/устаревания этого владельца?» Только первое → риск спутать «другой владелец» с «тот же владелец, но бездействующий».

## Переносимый принцип

Когда система уже имеет протестированный критерий устаревания/активности для одного направления операции, код для симметричного/обратного направления той же операции должен переиспользовать этот критерий, а не вводить под тем же именем задачи более слабую проверку (совпадение идентичности).

## Связи

- Найдено при ревью (Kimi, round 2) в рамках WP-7 Ф229.
- `DP.FM.590` (semaphore-match-any-active-not-scoped-to-repo-session), `DP.FM.603` (own-open-semaphore-counts-as-live-writer), `DP.FM.614` (resume-cleanup не покрывал трекаемый мусор мёртвого владельца) — тот же общий класс «семафор/очистка отвечает не на тот вопрос об устаревшем владельце», каждый раз другой конкретный механизм.

## Источник

Git commit `6673201f7` в DS-my-strategy (WP-7 Ф229, peer-session 2026-10-15-04-wp7-f229-relocate-card-fix).
