---
id: DP.SC.120
name: Приёмник платежей (Payment Receiver)
type: sc
status: draft
layer: L2-Platform
summary: "Webhook-приёмник: провайдеры (YooKassa, Stripe, Paybox) → verify → normalize → idempotent write → finance_payments (Neon)"
consumer: Участник (платит), Реестр подписок (subscription_grants), Gateway MCP (доступ), Бухгалтер (Metabase), Администратор (Directus)
created: 2026-04-16
updated: 2026-11-14
wp: WP-246
related:
  realizes: []
  extends: [DP.SC.112]
  source: "WP-246 Ф0"
---

# [DP.SC.120] Приёмник платежей (Payment Receiver)

## Обещание

**Держит:** владелец РП-246 (назначено пилотом 14.11.2026).

**Кому:** Платформа (все сервисы, читающие `finance_payments` и `subscription_grants`).

**Зачем:** Единая точка приёма оплат от внешних провайдеров. Изолирует бизнес-логику от специфики провайдеров. Обеспечивает real-time запись платежей в Neon вместо pull-sync с задержкой 10–40 мин.

**Что гарантирует:**

| Инвариант | Описание |
|-----------|----------|
| **Идемпотентность** | Один webhook = один платёж в `finance_payments`. Дублированные webhook (retry провайдера) не создают дубль записи |
| **Верификация** | Только подлинные webhook от провайдеров обрабатываются. Spoofed/replayed — отклоняются |
| **Нормализация** | Все провайдеры приведены к единому формату `finance_payments` (Anti-Corruption Layer) |
| **Время отклика** | HTTP 200 ≤ 1 секунды провайдеру. Запись в Neon ≤ 3 секунд (через `ctx.waitUntil`) |
| **Audit trail** | Каждый принятый webhook сохраняется с оригинальным payload |

**Что НЕ гарантирует:**
- Биллинг-логику (подписки, стажировки, продления) — это DP.SC.112
- Маршрутизацию по провайдерам (какой провайдер для какой валюты) — это решается при создании платежа, не при приёме
- Identity enrichment (привязка ory_id) — это Gateway OAuth (WP-231 Вариант A)

## Триггер

Webhook от провайдера (YooKassa, Stripe, Paybox, Tilda) при изменении статуса платежа.

## Входы

| Вход | Источник | Формат |
|------|---------|--------|
| Webhook `payment.succeeded` | YooKassa | JSON: `{type, event, object}` |
| Webhook `payment_intent.succeeded` | Stripe | JSON: Event с `data.object` |
| Webhook `payment.completed` | Paybox | JSON (формат Paybox) |
| Webhook оплаты | Tilda | JSON (формат Ecwid/Tilda) |

## Выходы

| Выход | Назначение | Формат |
|-------|-----------|--------|
| Запись в `finance_payments` | Neon (platform) | INSERT с нормализованными полями |
| Запись в `processed_webhooks` | Neon (platform) | INSERT event_id для дедупликации |
| HTTP 200 | Провайдеру | Подтверждение приёма |

## Время отклика

- **HTTP 200 провайдеру:** < 1 сек (до записи в Neon, через `ctx.waitUntil`)
- **Запись в Neon:** < 3 сек после получения webhook
- **Видимость в subscription_grants:** < 1 мин (через sync-subscriptions cron или trigger)

## Режим отказа

| Ситуация | Поведение |
|----------|-----------|
| Невалидная подпись / IP | HTTP 403, webhook отклонён, не записан |
| Дубль webhook (retry) | HTTP 200, skip обработки (idempotent) |
| Neon недоступен | HTTP 500, провайдер повторит (YooKassa: 24h, Stripe: 72h) |
| Неизвестный провайдер/формат | HTTP 400, залогировать raw payload |
| Частичная обработка (crash) | processed_webhooks INSERT первым → retry безопасен |

## Потребители (downstream)

| Потребитель | Что читает | Как |
|-------------|-----------|-----|
| **sync-subscriptions** (GHA cron) | `finance_payments` → upsert `subscription_grants` | SQL poll каждые 30 мин (будет < 1 мин) |
| **Gateway MCP** | `subscription_grants` | SELECT EXISTS при каждом MCP-запросе |
| **Metabase** | `finance_payments`, `subscription_grants` | Аналитические дашборды |
| **Directus** | `finance_payments` | Просмотр и ручное управление |
| **Бот** | `subscription_grants` | Проверка доступа, UI подписки |

---

## Сценарии использования

### Сценарий 1: Пользователь оплатил подписку через YooKassa (ch1 — РФ)

**Кто запускает:** YooKassa (webhook автоматически).
**Когда:** Пользователь на сайте Aisystant оплатил подписку БР картой.
**Зачем:** Зафиксировать факт оплаты и активировать подписку для Gateway.
**Контекст:** Пользователь уже зарегистрирован в Aisystant (есть email, suser_id). Может не иметь ory_id.

**Поток:**
1. YooKassa → POST `/webhook/yookassa` с `payment.succeeded`
2. Payment Receiver: verify IP ∈ {185.71.76.0/27, ...}
3. Normalize: `channel=1, amount, currency=RUB, purpose=SUBSCRIPTION, email`
4. INSERT `processed_webhooks` (event_id=yookassa_payment_id)
5. INSERT `finance_payments` (ON CONFLICT DO NOTHING)
6. HTTP 200
7. sync-subscriptions (≤ 1 мин) → upsert `subscription_grants`
8. Gateway MCP: `checkSubscription(ory_id)` → `true`

**Что потребитель делает с результатом:** Gateway разрешает доступ к платным tools. Metabase видит новый платёж в real-time.

### Сценарий 2: Международная оплата через Stripe (ch3 — Мир)

**Кто запускает:** Stripe (webhook автоматически).
**Когда:** Пользователь за рубежом оплатил подписку на stripe.com/aisystant.
**Зачем:** Обеспечить международные оплаты без зависимости от российской инфраструктуры.
**Контекст:** Aisystant Corp (USA). HMAC-verified. Пользователь имеет email.

**Поток:**
1. Stripe → POST `/webhook/stripe` с `payment_intent.succeeded`
2. Payment Receiver: verify HMAC-SHA256 signature
3. Normalize: `channel=3, amount, currency=USD, purpose=SUBSCRIPTION, email`
4. INSERT `processed_webhooks` + INSERT `finance_payments`
5. HTTP 200

**Что потребитель делает с результатом:** Аналогично сценарию 1. Дополнительно: Metabase видит USD-выручку отдельно для отчёта Corp.

### Сценарий 3: Бухгалтер проверяет reconciliation (Metabase)

**Кто запускает:** Бухгалтер (Гиляна) вручную.
**Когда:** Ежедневно/еженедельно — сверка.
**Зачем:** Убедиться что все оплаты от провайдеров попали в Neon. Найти расхождения.
**Контекст:** Metabase dashboard «Финансовая оперативка».

**Поток:**
1. Бухгалтер открывает Metabase dashboard
2. Видит: total finance_payments за день vs ожидаемое из провайдеров
3. Если расхождение: фильтр по `processed_webhooks` — какие event_id получены, какие processed
4. Если webhook потерян: GET API провайдера (recovery) → ручной INSERT

**Что потребитель делает с результатом:** Фиксирует расхождение, инициирует recovery.

### Сценарий 4: Бот принимает Stars-подписку (ch7)

**Кто запускает:** Пользователь через Telegram бот.
**Когда:** Нажал «Оплатить звёздами» в боте.
**Зачем:** Минимальное трение — оплата без email, без карты.
**Контекст:** Пользователь знает только telegram_id. Stars — не webhook Payment Receiver, а Bot API напрямую.

**Поток (вне Payment Receiver — через бота):**
1. Пользователь → `pre_checkout_query` → бот: `answerPreCheckoutQuery(ok=true)`
2. `successful_payment` → бот: INSERT `finance_payments` + `upsert_subscription_grant(telegram_id)`
3. Позже: Gateway OAuth → Вариант A: UPDATE ory_id по email

**Замечание:** Stars не проходит через Payment Receiver (Bot API, не webhook). Но результат тот же: запись в `finance_payments` + `subscription_grants`.

### Сценарий 5: Администратор вручную регистрирует B2B-платёж (ch8)

**Кто запускает:** Sales-менеджер / Администратор.
**Когда:** B2B-контракт с вузом или корпорацией, оплата банковским переводом.
**Зачем:** Зафиксировать платёж и выдать доступ группе.
**Контекст:** Directus UI, ручной ввод.

**Поток (вне Payment Receiver — через Directus):**
1. Администратор открывает Directus → finance_payments → Create
2. Заполняет: channel=8, amount, currency, purpose, email/telegram_id
3. Directus INSERT → finance_payments
4. sync-subscriptions → subscription_grants

**Замечание:** ch8 тоже не проходит через Payment Receiver (ручной ввод). Но результат тот же.

### Сценарий 6: Retry после сбоя Neon

**Кто запускает:** Провайдер (автоматически).
**Когда:** Neon был недоступен при первом webhook, провайдер retry через backoff.
**Зачем:** Гарантия доставки (at-least-once).
**Контекст:** YooKassa retry в течение 24h, Stripe — 72h.

**Поток:**
1. Первый webhook → Payment Receiver → Neon timeout → HTTP 500
2. Провайдер retry через exponential backoff
3. Второй webhook → Payment Receiver → Neon доступен → INSERT → HTTP 200
4. Если третий retry (дубль) → INSERT `processed_webhooks` UNIQUE violation → skip → HTTP 200

---

## Реализующий сервис

| Параметр | Значение |
|----------|---------|
| **Сервис** | Payment Receiver |
| **Runtime** | Cloudflare Worker (TypeScript) |
| **Репо** | `DS-MCP/payment-receiver/` (новый) |
| **База** | Neon `platform` (public.finance_payments, public.processed_webhooks) |
| **Роль Neon** | `payment_receiver_writer` (INSERT finance_payments, INSERT/UPDATE processed_webhooks) |
| **Secrets** | `DATABASE_URL` (Neon pooled), `STRIPE_WEBHOOK_SECRET`, `YOOKASSA_SHOP_ID` |
| **Мониторинг** | CF Analytics + processed_webhooks count + Metabase «Webhook Health» |

## Связь с другими SC

- **Расширяет DP.SC.112** (Подписка и оплата) — Payment Receiver = инфраструктурный слой, SC.112 = бизнес-логика
- **Питает DP.SC.025** (sync-subscriptions) — данные для upsert subscription_grants
- **Работает с DP.SC.114** (CRM) — Directus/Metabase читают те же данные
