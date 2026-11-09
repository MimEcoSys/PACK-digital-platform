---
id: DP.FM.670
type: failure-mode
status: draft
created: '2026-10-23'
valid_from: '2026-10-22'
pack: PACK-digital-platform
domain: digital-platform
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit 9bd6352 (iwe-local-config), 6b44036b (FMT-exocortex-template, PR #1308); MC-sessions 2026-10-22-17-wp561-drift-f46-49-prioritize; WP-561 Ф46, issue #1280"
source_capture: DS-my-strategy/inbox/captures/2026-10.md:6177
extraction_report: DS-my-strategy/inbox/extraction-reports/2026-10-23-inbox-check.md
source_candidate: 2
name: "Белый список обходов гейта мёртв со дня мерджа: разрешающая ветка проверяет поле, которое путь открытия никогда не писал"
name_ru: "Белый список обходов гейта мёртв со дня мерджа: разрешающая ветка проверяет поле, которое путь открытия никогда не писал"
name_en: "A gate's bypass whitelist is dead on arrival: the allow branch checks a field the open path never wrote"
summary: "session-open-gate.sh проверял housekeeping-причину по полю harness_session_id, которое housekeeping-семафоры никогда не писали — разрешающая ветка гейта не срабатывала ни разу с момента мерджа, обнаружено только при расширении списка причин."
related:
  see_also:
  - DP.FM.264
tags:
- session-guard
- whitelist
- semaphore
- gate
- dead-code
---

# DP.FM.670 — Белый список обходов гейта мёртв со дня мерджа

## Механизм

Гейт `session-open-gate.sh` в режиме `--housekeeping` проверяет причину обхода против закрытого whitelist (`ALLOWED_HOUSEKEEPING_REASONS`), сопоставляя её с полем `harness_session_id` в семафоре. Housekeeping-семафоры (day-open, day-close, week-close, month-close и другие) никогда не писали это поле — разрешающая ветка гейта была недостижима для ВСЕХ housekeeping-причин с момента мерджа Ф46, не только для новой.

## Историческое наблюдение

Обнаружено 22.10.2026 (MC-sessions 2026-10-22-17-wp561-drift-f46-49-prioritize) при расширении whitelist новой причиной (`update-delivery`) и холодном ревью — Ф46 считался закрытым и смёрженным, но разрешающая ветка гейта ни разу не сработала за всё время существования. Семафор создавался зеркально plain-open путём, который не писал ключ, по которому гейт ищет совпадение.

## Контрмера и тест

Тест для любого гейта с разрешающей (allow) и запрещающей (deny) веткой: обе ветки должны быть живьём проверены отдельно, не только запрещающая. Ключ сопоставления (здесь — `harness_session_id`) должен писаться ВСЕМИ путями создания семафора/записи, включая тот, что гейт фактически проверяет при allow.

Тест на обнаружение: grep по коду создания семафора на предмет записи ключа, который читает allow-ветка гейта; живой прогон allow-сценария (не только deny) до того, как фича считается закрытой.

## Отличие от соседей

`DP.FM.264` — housekeeping-семафор без поля `slug:` (другой ключ, другой lookup — ломает `note-file --slug`, не allow/deny гейта доступа). Здесь — другое поле (`harness_session_id`) и другой потребитель (whitelist-проверка причины обхода), тот же общий класс «housekeeping-семафор не пишет поле, которое ожидает читающий код», другой конкретный механизм и другие последствия.

## Происхождение

git commit 9bd6352 (iwe-local-config), 6b44036b (FMT-exocortex-template, PR #1308); отчёт MC-sessions `2026-10-22-17-wp561-drift-f46-49-prioritize`. WP-561 Ф46, issue #1280. Захват: `DS-my-strategy/inbox/captures/2026-10.md:6177`.
