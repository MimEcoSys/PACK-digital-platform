---
id: DP.M.621
name: Webhook handler с CHECK-защищённой таблицей — обязательный split-transaction, иначе retry-loop провайдера
type: method
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_split_transaction_for_late_webhook.md (WP-327 Ф2, 17.05; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [PACK-digital-platform, PACK-digital-platform]
---

# DP.M.621: split-transaction для webhook + CHECK constraint

## Правило
Webhook handler с атомарным UPDATE через CHECK-защищённую таблицу — разделить на две транзакции с try/except CheckViolationError. Иначе webhook-retry-loop.

## Почему
Атомарная транзакция при CHECK violation откатывает ВСЁ, включая UPDATE статуса записи о платеже. Webhook видит non-2xx → провайдер ретраит (ЮКасса — до 10 попыток за 24ч) → бесконечный цикл.

## Порядок
1. Tx1: UPDATE status='confirmed' на ledger-таблице → COMMIT.
2. Tx2: UPDATE на CHECK-защищённой таблице (напр. point_balances, CHECK points >= 0) внутри `try: … except asyncpg.CheckViolationError`.
3. При violation: admin alert через event-gateway (не direct INSERT), return HTTP 200 — webhook не ретраит.
4. Admin вручную восстанавливает баланс или делает refund.
