---
id: DP.SC.144
name: User-Facing Platform Health (информирование пользователей о здоровье платформы)
type: sc
status: draft
layer: L2-Platform
summary: "Public status page (status.system-school.ru) с composite uptime «по девяткам» (формат 99.847%), real-time информирование пользователей об инцидентах через email/RSS subscriptions + TG-канал @aisystant_status. Реализуется через Better Stack SaaS."
consumer: Конечные пользователи платформы (ученики, волонтёры, core-team, потенциальные клиенты, инвесторы) — все, кто может зависеть от доступности платформы.
created: 2026-04-25
updated: 2026-11-14
related:
  realizes: [WP-244]  # требования R1 + R2
  uses: [DP.SC.123]  # internal observability как источник probes
  complementary: [DP.SC.123]
  source: "WP-244 расширение 25 апр (требования R1 информирование пользователей + R2 composite SLA «по девяткам») + ArchGate β"
---

# DP.SC.144 — User-Facing Platform Health

## Обещание

**Кому:** конечным пользователям платформы — ученикам, волонтёрам, core-team, потенциальным клиентам, инвесторам. Любой, кому важно знать «работает ли платформа Aisystant сейчас».

**Зачем:** пользователь не должен узнавать о проблеме платформы из своих жалоб в поддержку. Когда сервис деградирует, пользователь хочет (а) **видеть**, что мы знаем о проблеме, (б) понимать **масштаб** (полный outage / частичный / отдельный сервис), (в) получать **уведомление** о восстановлении. Без этого: ощущение «бот сломался — это надолго или нет?», падение доверия, всплеск support-запросов.

Дополнительно: composite SLA «по девяткам» — публичный показатель надёжности платформы. Это **сигнал зрелости** для инвесторов, B2B-партнёров, потенциальных учеников.

**Что получит потребитель:**
- **Public status page** на `status.system-school.ru` (custom domain CNAME на Better Stack):
  - Список сервисов с цветовой индикацией (зелёный/жёлтый/красный)
  - История инцидентов за 90 дней
  - Real-time детали активного инцидента (что задето, начало, ETA восстановления, обходные пути)
  - Composite uptime «по девяткам» (см. ниже)
- **Composite uptime метрика** в формате `99.847%` (3 знака после точки = «3 девятки + 847»):
  - Расчёт: multiplicative product per-service uptime по critical-path сервисам, weighted by criticality (см. §Расчёт)
  - Окна: за 24h, 7d, 30d, 90d, 1 год — все одновременно отображаются
  - Source-of-truth — Better Stack SLA reports
- **Подписки на инциденты** — пользователь сам выбирает канал:
  - Email subscription (Better Stack встроенный)
  - RSS feed (Better Stack встроенный)
  - **TG-канал @aisystant_status** (Better Stack webhook → AIST Bot poster, автопостит каждый incident start/update/resolve)
  - In-app banner в `@aist_me_bot` при критическом инциденте (опц., если детектируем что бот всё-таки жив)
- **Время реакции:**
  - От инцидента (`is_up=false × 3` детекция Better Stack) до публикации на status page: ≤2 мин (автоматическая)
  - От инцидента до TG-канал поста: ≤3 мин (Better Stack webhook + AIST Bot обработка)
  - Manual incident update от команды (комментарий «работаем над фиксом»): по мере появления, не SLA

## Критерий приёмки

1. **status.system-school.ru работает**, отображает ≥5 critical-path сервисов (event-gateway, aist-bot webhook, gateway-mcp, payment-receiver, Neon health), каждый с историей за 30+ дней.
2. **Composite uptime отображается** в формате `99.XYZ%` (3 знака после точки). Метод расчёта зафиксирован (см. §Расчёт). Окна: 24h, 7d, 30d, 90d.
3. **Email subscription работает:** пользователь подписался → получает email при start/update/resolve каждого инцидента.
4. **TG-канал @aisystant_status работает:** Better Stack webhook → AIST Bot poster → пост в канал. От инцидента до поста ≤3 мин на тестовом инциденте.
5. **RSS feed валиден** (W3C validator passes).
6. **Custom domain CNAME** настроен правильно (HTTPS, валидный сертификат от Let's Encrypt через Better Stack).
7. **Branding:** логотип Aisystant + цвета бренда + ссылки на основной домен. Не дефолтное Better Stack оформление.
8. **Composite uptime под нагрузкой:** при росте до 22 monitors (12 БД + 10 workers) расчёт остаётся корректным (Better Stack handles scaling).

## Расчёт composite uptime

**Формула (multiplicative product, weighted by criticality):**

Per-service uptime: `U_i = (uptime_seconds_i / window_seconds) × 100%`

Composite:
```
U_composite = Π U_i^(w_i / Σw_j)  для всех critical-path сервисов
```

Где `w_i` — вес сервиса по критичности (1-5 шкала). Альтернативно (проще):
```
U_composite = min(U_critical_services)  # worst-of по critical-path
```

**Что считается critical-path** (можем перевести деградацию в видимое пользователю):
- event-gateway (без него — потеря событий)
- aist-bot webhook (без него — бот не отвечает)
- gateway-mcp (без него — Claude Code не работает)
- payment-receiver (без него — нельзя купить)
- Ory Hydra (без него — login не работает)

**Что НЕ critical-path** (не влияет на user-facing):
- knowledge-mcp (read-only, кэш)
- digital-twin-mcp (опц. для UI)
- LMS-bridge (lazy sync)
- projection-worker rewards (баланс обновится с задержкой, не блокирует)

**Решение между multiplicative и min:**
- Multiplicative — точнее, отражает «cumulative experience» пользователя (если бот 99% И платёж 99% → composite ≈ 98%)
- Min worst-of — пессимистичнее, проще объяснить
- **Better Stack по умолчанию multiplicative.** Используем его out-of-box.

**Формат отображения:**
- На status page: `99.847% uptime over 30 days`
- В Grafana команды: ту же метрику + per-service breakdown
- В TG-канал inцидентa: `Total uptime impact this incident: 0.034% (32 минуты deg.)`

## Информирование пользователей — каналы

| Канал | Кто настраивает | Что получает | Латентность |
|-------|------------------|--------------|-------------|
| **status.system-school.ru** | автоматически (Better Stack) | визуальный статус всех сервисов, история, composite uptime | ≤2 мин (auto) |
| **Email subscriptions** | пользователь сам (форма на status page) | start/update/resolve email | ≤3 мин |
| **RSS feed** | пользователь сам (RSS reader) | XML feed инцидентов | ≤2 мин (auto) |
| **TG-канал @aisystant_status** | команда (создаёт канал, AIST Bot — admin); пользователь подписывается | автопост каждый incident lifecycle event | ≤3 мин |
| **In-app banner в боте** (опц., post-MVP) | автоматически (AIST Bot слушает webhook) | UX-подсказка «у нас инцидент с X, обходной путь Y» | ≤5 мин |

**Команда (опц., для большой деградации):** ручное обновление инцидента в Better Stack UI — добавляет message «работаем над причиной», который автоматически распространяется по всем каналам.

## Режимы отказа

| Сбой | Поведение | Восстановление |
|------|-----------|----------------|
| Better Stack down | Status page недоступен. Probes не идут. AIST Bot не получает webhook. | Better Stack имеет свой status.betterstack.com — мы его пингуем (status check на нашей стороне через Cloudflare Workers cron). Альтернативный канал: ручной TG-пост от команды. |
| TG webhook delivery fail | Сообщения в канал не приходят. Email/RSS работают как fallback. | Better Stack retry до 5 раз. AIST Bot имеет idempotency на duplicate webhook. |
| Composite uptime неточный | Отображается, но цифра расходится с realtime. Пользователь видит выше/ниже истинного. | SLA reports из Better Stack пересчитываются 1 раз/час; обновление страницы вернёт корректное значение. |
| Custom domain (CNAME) недоступен | status.system-school.ru не открывается; пользователь идёт на дефолтный Better Stack URL (status-betterstack-uptime.com/...). | DNS fix; на главной странице aisystant.ru явная ссылка на резервный URL. |

## Конфиденциальность инцидентов

**Что показываем публично:**
- Имя сервиса (gateway-mcp, aist-bot)
- Уровень degradation (degraded / outage)
- Время начала / окончания
- Composite SLA influence
- Manual message от команды (если решили публиковать)

**Что НЕ показываем:**
- Числа пользователей затронутых (пока не больше N)
- Конкретные ID запросов / users
- Internal causes (Neon connection pool exhausted) — до пост-мортема и решения команды
- PII / payment_credentials в любом виде

**Решение между transparency и privacy:** по умолчанию transparency-first (показываем достаточно, чтобы пользователь понимал «что и насколько»), но без internal details, которые могут (а) запутать, (б) использоваться атакующими.

## Out of scope

- **Internal observability** для команды (probes, logs, projection lag) — это [DP.SC.123](DP.SC.123-platform-observability.md).
- **Платные tier features Better Stack:** custom branding до уровня enterprise, white-label, SAML SSO для команды — на free tier не критично, рассмотрим при росте.
- **Push-нотификации в браузер** (Web Push API) — техзадача, не приоритетна, добавляется при появлении web-UI (после WP-188 Ф10.0 Landing).
- **SMS-нотификации** — слишком дорого + не нужно для нашей аудитории.
- **24/7 on-call** для команды — отдельная роль, не покрывается этим SC. Сейчас on-call = best-effort (Tseren днём, никто ночью).

## Эволюция доставки (push ↔ pull, 25 апр 2026)

**Контекст:** Better Stack free tier не предоставляет outgoing webhooks (escalation policies = $29/мес). При активации WP-244 Ф4 25 апр обнаружено это ограничение.

**Решение (без upgrade):** observability-webhook CF Worker переключён с push (webhook receiver) на **pull (Cron Trigger)** — каждую минуту опрашивает Better Stack `/api/v2/incidents`, новые incidents (id > last_seen в KV cursor) форматирует и отправляет в TG-канал и DM.

**Контракт DP.SC.124 не изменён:** Better Stack остаётся owner observability data; CF Worker теперь pull-consumer вместо push-receiver. Это **implementation detail доставки**, не нарушение ArchGate β.

**Метрики доставки:**
| | push (escalation policy) | pull (cron) |
|---|---|---|
| Latency инцидент → TG | 5-15 сек | 60-90 сек |
| Стоимость | $29/мес | $0 |
| Интервал опроса | event-driven | 1 минута |
| Зависимость от Better Stack tier | upgrade required | работает на free |

**Триггер возврата на push:** апгрейд Better Stack до paid tier (например при росте команды до ≥3 человек с реальной on-call rotation) → переключение pull → push занимает ~5 минут (env-var переключение MODE + создание escalation policy в Better Stack UI).

**Где живёт implementation:** `DS-MCP/observability-webhook/src/poller.ts` (~120 LOC), Cron `* * * * *`, KV `OBSERVABILITY_STATE` для cursor.

## Связи

- **Парный SC (для команды):** [DP.SC.123 Platform Observability](DP.SC.123-platform-observability.md) — internal observability, источник probes для status page.
- **Реализуется ролью:** [DP.ROLE.035 Platform Observer](../02-domain-entities/DP.ROLE.035-platform-observer.md) implementations C+E (status page rendering + alert routing).
- **Реализуется WP:** [WP-244](../../../DS-my-strategy/inbox/WP-244-platform-observability.md) фазы Ф2 (настройка Better Stack) + Ф4 (alert routing) + Ф7 (TG-канал @aisystant_status).
- **Внешняя зависимость:** Better Stack SaaS (https://betterstack.com) — пишет, агрегирует, рендерит status page, рассылает email/RSS.
- **Использует AIST Bot:** для постинга в TG-канал @aisystant_status (webhook receiver).
- **Связь с UI:** в будущем (web-UI после Ф10.0 Landing) — banner на главной странице aisystant.ru при активном инциденте (lazy fetch status.system-school.ru API).

## Маркетинговый аспект

Composite uptime метрика — это **публичный сигнал зрелости платформы**. На лендинге (после WP-188 Ф10.0) можно показывать «99.95% uptime последние 30 дней» как один из proof-points. Это не основной маркетинговый посыл, но рабочий вторичный сигнал для B2B и инвесторов.

> «Aisystant — платформа развития интеллекта с публичной прозрачностью работы. status.system-school.ru обновляется в реальном времени, инциденты документируются, метрика SLA публикуется ежемесячно.»

Это создаёт ожидание operational excellence, что мотивирует команду поддерживать высокий uptime — побочный эффект публичности.
