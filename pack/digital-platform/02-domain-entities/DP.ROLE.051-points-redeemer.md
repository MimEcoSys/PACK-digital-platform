---
id: DP.ROLE.051
name: Points Redeemer (Burn-эмиттер баллов)
type: role-description
status: draft
valid_from: 2026-05-17
summary: "Роль burn-эмиттера: при чекауте резервирует баллы в rewards.redeemed_events; при webhook'е оплаты подтверждает или откатывает резерв; эмитирует event 'points_redeemed' для projection-worker. Не writer point_balances."
related:
  specializes: [U.RoleAssignment]
  component_of: [DP.ROLE.001]
  realizes: [DP.SC.141]
  uses:
    - DP.SC.112
    - DP.SC.122
    - DP.ECON.001
    - DP.ROLE.034
created: 2026-05-17
---

# Points Redeemer (DP.ROLE.051)

> **Kind:** Infrastructure Role (инфраструктурная роль — burn-эмиссия событий, не доменная логика).
> **Owner Role:** Платформенная команда.
> **Current executor:** функции в `aist_bot_newarchitecture/db/queries/redeem.py` (новый модуль, не отдельный сервис).

## 1. Миссия

Превращать намерение пилота «применить бонусы» в надёжный двухфазный коммит: **резерв → подтверждение/откат**. Гарантировать атомарность относительно платёжного шлюза и отсутствие двойного списания. Не быть writer'ом `point_balances` (за это отвечает [DP.ROLE.034](DP.ROLE.034-rewards-projector.md) через projection).

> **Различение:** применяются **бонусы** (= `min(points, Σ(days_at_qual_i × cap_i))`), а не «баллы» напрямую. Баллы (earned_total) — геймификация, не тратятся. Бонусы — лояльность, тратятся при оплате. См. DP.ECON.001 §1.1.

## 2. Обязанности

| Обязанность | Метод | Триггер |
|-------------|-------|---------|
| Расчёт доступной скидки | `available_discount(account_id, requested_amount_rub)` → возвращает `{copilka_pts, ceiling_pts, discount_pts, discount_rub, qualification}` | UI чекаута запрашивает |
| Резерв баллов | `reserve_burn(account_id, payment_id, points)` → INSERT redeemed_events(status='reserved') + decrement available (SELECT FOR UPDATE) | Пилот применил скидку, ДО `YooKassa.create_payment` |
| Подтверждение резерва | `confirm_burn(payment_id)` → UPDATE status='confirmed' + `post_event(type='points_redeemed')` через event-gateway | webhook `payment.succeeded` / TG `successful_payment` |
| Откат резерва | `rollback_burn(payment_id, reason)` → UPDATE status='rolled_back' + emit reverse event | webhook `payment.canceled` ИЛИ cron timeout 30 мин |
| Очистка истёкших резервов | `rollback_expired_reservations()` → находит `status='reserved' AND reserved_at < now() - 30min` → rollback каждого | Cron каждые 5 мин |
| Идемпотентность | UNIQUE constraint на `payment_id` в redeemed_events. INSERT ... ON CONFLICT DO NOTHING на повторных вызовах | Всегда |
| Snapshot квалификации | Сохранять `qualification_snapshot` при reserve_burn (как в applied_events) | reserve_burn |

## 3. Полномочия

- **Пишет** в `rewards.redeemed_events` — единственный writer этой таблицы (OwnerIntegrity).
- **Эмитирует** события `points_redeemed` / `points_burn_rolled_back` / `points_redeem_late_webhook` **через event-gateway** (`helpers/dual_write.post_event()`), а НЕ direct INSERT в `learning.domain_event`. Соответствие [DP.SC.020 Event Ingest](../08-service-clauses/DP.SC.044-event-ingest.md): writer learning.domain_event = только [DP.ROLE.032 Event Ingester](DP.ROLE.032-event-ingester.md). Любой эмиттер событий → через единый endpoint event-gateway.
- **Читает** `rewards.point_balances` (через SELECT FOR UPDATE для расчёта доступности).
- **Читает** `reference.qualification_multipliers` через FDW `_foreign_reference` (для daily_cap и множителей).
- **Читает** `indicators.calculated_profile.qualification_level` через FDW `_foreign_indicators` (для определения степени МИМ пилота).
- **НЕ пишет** в `point_balances` — это только projection-worker'а (DP.ROLE.034) задача.
- **НЕ пишет** в `learning.domain_event` напрямую — только через event-gateway client.

## 4. Границы роли

| Делает | НЕ делает |
|--------|-----------|
| Резервирует и подтверждает burn-операции | Не начисляет баллы (это DP.ROLE.034) |
| Эмитирует event `points_redeemed` в learning.domain_event | Не пишет напрямую в `point_balances` (через projection) |
| Гарантирует idempotency по `payment_id` | Не приёмщик платежей (это oauth_server + handlers) |
| Откат по timeout 30 мин | Не отвечает за саму оплату (это YooKassa / TG Stars) |
| Snapshot квалификации в момент резерва | Не пересчитывает квалификацию (это Профилировщик, DP.ROLE.116) |
| Audit-trail каждого статусного перехода | Не делает финансовую отчётность (это Бухгалтер через Metabase) |

## 5. Исполнители

| Исполнитель | Когда | Режим |
|-------------|-------|-------|
| **Функции `db/queries/redeem.py`** в `aist_bot_newarchitecture` | Production | In-process, вызываются из handlers (workshop, showcase) + webhook handler |
| **Cron-задача `rollback_expired_reservations`** в `core/scheduler.py` | Каждые 5 мин | APScheduler, idempotent |
| Human (admin через Directus) | Разовый refund при споре | Manual UPDATE через audit-логированный flow |

**Почему не отдельный сервис:** burn-операция требует доступа к контексту чекаута (handler уже имеет `account_id`, `chat_id`, `seminar_code`). Выделение в micro-service усложнило бы сетевое взаимодействие без выигрыша. При росте нагрузки (>1000 burn/мин) — выделить в отдельный сервис как Phase 2.

## 6. Связи

**Вход (потребитель обещаний других ролей):**
- **handlers/workshop.py + handlers/showcase.py** — вызывают `reserve_burn()` при чекауте.
- **oauth_server.yookassa_webhook_handler** — вызывает `confirm_burn()` после `payment.succeeded`.
- **DP.ROLE.034 Rewards Projector** — поставляет актуальный баланс через `point_balances`.

**Выход (поставщик обещаний другим ролям):**
- **DP.ROLE.034 Rewards Projector** — потребляет event `points_redeemed` в learning.domain_event, проецирует на `point_balances`.
- **Бот команды `/points`** — отображает историю списаний через JOIN `redeemed_events`.
- **Бухгалтер через Metabase** — финансовая отчётность по burn-операциям.
- **Audit (WP-237 retention 7 лет)** — `redeemed_events` как финансовый журнал.

## 7. Measurable health

- **Reserve latency p95** (UI кнопка → reserved INSERT) — SLO ≤400ms (Neon-pooler TLS handshake + SELECT FOR UPDATE + INSERT + commit)
- **Confirm latency p95** (payment.succeeded webhook → confirmed + event-gateway POST) — SLO ≤600ms
- **Idempotency violations** (попытки повторного INSERT с тем же payment_id) — alert при >0 в день (правильно блокируются UNIQUE)
- **Expired reservations rate** (rolled_back vs confirmed) — норма <10%; alert при >20% (UX проблема)
- **Balance invariant** (`point_balances.balance >= 0`) — alert при rollback'е CHECK constraint
- **Snapshot consistency** (qualification_snapshot в redeemed_events vs текущая в calculated_profile) — еженедельный consistency check
- **Stuck reservations** (`status='reserved' > 31 мин`) — alert при >0 (cron не сработал)

## 8. Reference

- **Обещание:** [DP.SC.141 Зачёт баллов в оплату](../08-service-clauses/DP.SC.141-points-redemption.md)
- **Реализация:** `aist_bot_newarchitecture/db/queries/redeem.py` (skeleton WP-327 Ф1), миграция `neon-migrations/mvp/226-rewards-redeemed-events.sql`
- **Координирует с:** [DP.ROLE.034 Rewards Projector](DP.ROLE.034-rewards-projector.md) (writer point_balances)
- **Регулируется:** [DP.ECON.001 Points Engine](DP.ECON.001-points-engine.md) (§3.2 множители, §6 курс конвертации)

## 9. Различения

- **Баллы ≠ Бонусы ≠ Ступень.** Баллы (earned_total) — геймификация, никогда не убывают, начисляет DP.ROLE.034. Бонусы = `min(points, Σ(active_days_at_qual_i × daily_cap_i))` — лояльность, тратятся при оплате, конвертирует DP.ROLE.051. Ступень = cp-профиль (13 срезов, FORM.089), определяет daily_cap. Источник событий один (Activity Hub), правила обработки разные.
- **Burn-эмиттер ≠ Writer point_balances.** Эмиттер пишет в ledger (`redeemed_events`) + event (`learning.domain_event`). Writer point_balances — только projection-worker. Альтернатива «расширить DP.ROLE.034 с apply_burn» отклонена 17 мая 2026 (выбор пользователя, см. WP-327 Этап 1 решение OwnerIntegrity).
- **Резерв ≠ Списание.** Резерв = намерение, отменяемое. Списание = подтверждённое уменьшение бонусного баланса. UI должен показывать «зарезервировано» / «списано» по-разному.
- **`payment_id` ≠ `event_id`.** Идемпотентность burn — по `payment_id` (один платёж = одно списание). Идемпотентность grant — по `event_id` (один event = одно начисление). Не путать.
