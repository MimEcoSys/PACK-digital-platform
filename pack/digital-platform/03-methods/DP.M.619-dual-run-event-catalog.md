---
id: DP.M.619
name: Strangler dual-write требует полного каталога domain events (create/update/delete) на каждую целевую сущность, не только основной поток
type: method
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_dual_run_event_catalog_gaps.md (WP-228 Ф32, 14.05; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [DP.FM.765, PACK-digital-platform]
---

# DP.M.619: полный event-каталог при dual-run

## Инцидент
После cutover LMS→Neon dual-write emit'ил только `payment_received.v1`. Autopay-cron продлевал контракты, но `subscription_renewed.v1` в Neon не шёл: 0 строк в `subscription.contract_event` за 6 недель при 668 контрактах — state drift (деньги видны, продления нет).

## Признак до бизнес-ущерба
Пустая event-таблица через >7 дней при активных операциях — статистически невозможно = красный флаг.

## Правило проектирования dual-write
1. Перечислить ВСЕ domain events legacy, меняющие состояние сущностей (не только «деньги»/happy path).
2. Для каждой целевой БД: какие event-types нужны writers/projection? Минимум три категории на сущность: create (`payment_received`), update (`subscription_renewed`, `cancelled`), delete/revoke (`refunded`, `tool_revoked`).
3. После cutover мониторить наполнение event-таблиц: алерт при <expected_min за 7 дней.
4. Backfill-стратегия заранее: как восполнить пропущенные, если event-type добавлен post-cutover.
