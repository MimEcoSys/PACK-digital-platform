---
id: DP.ROLE.075
name: Доставщик (Delivery Policy Layer)
type: role-description
status: draft
valid_from: 2026-06-11
summary: "Слой политики исходящих: единая воронка всех сообщений пользователю. Применяет глобальный потолок по классу, приоритет, дедуп-по-всем и hard-gate предпочтений, затем передаёт транспорту (DP.ROLE.044) для физической доставки."
related:
  specializes: [U.RoleAssignment]
  component_of: [DP.ROLE.001]
  realizes: [DP.SC.177]
  uses:
    - DP.ROLE.044   # Notification Dispatcher — транспорт (физическая доставка exactly-once)
    - learning.domain_event  # журнал отправок + дедуп (WP-152/WP-253)
  downstream_consumers:
    - In-bot отправители (~20) — получают {notification_id, status}
    - Внешний платформенный producer (РП117, будущее) — через owned enqueue-контракт
created: 2026-06-11
updated: 2026-06-11
wp: WP-418
---

# Доставщик (Delivery Policy Layer) — DP.ROLE.075

> # see DP.SC.177, DP.ROLE.075
>
> **Kind:** Policy/Gatekeeper Role — единая воронка исходящих. Решает ПРОПУСТИТЬ ли сообщение, с каким приоритетом и когда; не интерпретирует содержимое по смыслу, читает только метаданные (класс, приоритет, dedup_key).
> **Owner Role:** IWE Platform — исполнитель сейчас: модуль `NotificationService` в @aist_me_bot (Railway). Спроектирован под извлечение в платформенный сервис при появлении второго канала/runtime.

---

## 1. Миссия

Быть единственной дверью, через которую физически уходят все сообщения пользователю, чтобы платформа могла дать обещание «не больше N сообщений в день», расставить приоритеты (урок важнее нуджа) и единообразно уважать предпочтения.

Аналогия: сортировочный центр почты с регулировщиком потока. Транспорт-Диспетчер (DP.ROLE.044) — почтовое отделение, которое доставляет письмо ровно один раз. Доставщик — сортировка перед ним: решает, какие письма пропустить сегодня, в каком порядке, не дубль ли это, не отписался ли получатель. Доставщик ставит транспорт себе в подчинение, а не заменяет его.

**Граница:** Доставщик не решает, ЧТО и КОГДА слать по смыслу (это Nudge Engine, DP.SC.116/РП117), не доставляет физически (это транспорт DP.ROLE.044), не владеет категориями opt-out (владеет DP.SC.116 — Доставщик их применяет).

---

## 2. Обязанности

| Обязанность | Как выполняется |
|-------------|----------------|
| Принять запрос от любого отправителя | In-bot: вызов `NotificationService.send(user, class, content_spec, priority, dedup_key)`. Внешний (будущее): owned `enqueue`-контракт |
| Применить hard-gate предпочтений | Opt-out по категории (данные DP.SC.116) → до очереди; `critical` обходит |
| Проверить дедуп | Тот же `dedup_key` в окне класса → не ставить вторую отправку |
| Проверить потолок класса | `capped` ≤2/день суммарно: COUNT по `learning.domain_event` + advisory-lock на `(user, day)` |
| Решить queued / suppressed | Под потолком → очередь; сверх → `suppressed` + лог причины (не молча) |
| Поставить в приоритетную очередь | INSERT в приватную таблицу-очередь с полем `priority` |
| Передать транспорту | Drain-loop: сортировка по приоритету → вызов DP.ROLE.044 (физическая доставка) |
| Зафиксировать исход | `learning.domain_event`: `notification_sent` / `notification_suppressed` (reason) |

---

## 3. Входы / Выходы

**Входы (от отправителя):**
- `user_id: string` — кому
- `class: enum` — `critical | must-deliver | transactional | capped | ops-alert`
- `content_spec: object` — канало-нейтральный (текст + опц. абстрактные действия/ссылки), БЕЗ `chat_id`/`reply_markup`
- `priority: int` — 1 (высш) … 4; служебно избыточен с классом, но допускает override внутри класса
- `dedup_key: string` — ключ идемпотентности/дедупа

**Выходы:**
- `notification_id: int`
- `status: queued | suppressed | sent | failed`
- `reason?: string` — при `suppressed` (cap-exceeded / opt-out / duplicate)

**Артефакты в Neon:**

| Таблица | Что пишет |
|---------|-----------|
| `notification_queue` (приватная, pgqueuer-ready) | Очередь: `id, user_id, class, payload(jsonb), priority, dedup_key, scheduled_at, locked_at, attempts, status` |
| `learning.domain_event` | `notification_sent` / `notification_suppressed` (reason) — источник истины для потолка и дедупа |

---

## 4. Архитектура (слои)

```
Отправители
├── In-bot (~20): scheduler, марафон, Лента, OAuth, Навигатор, Онбордер  → прямой вызов send()
└── Внешний platform producer (РП117, будущее)                          → owned enqueue API (НЕ raw SQL)
        │
        ▼
Доставщик (DP.ROLE.075) — слой политики
├── PreferenceGate  → opt-out hard-gate (категории DP.SC.116)
├── Dedup           → dedup_key в окне класса
├── ClassCap        → COUNT по journal + advisory_xact_lock(user, day); capped ≤2/день
├── Priority queue  → INSERT в notification_queue (приватная)
└── Drain-loop      → сортировка по priority → передача транспорту
        │
        ▼
Транспорт-Диспетчер (DP.ROLE.044) — физическая доставка exactly-once → Telegram
```

---

## 5. Ограничения (инварианты роли)

1. **Единая воронка.** Прямая отправка в обход Доставщика запрещена (после миграции Ф3 — 0 точек прямого `bot.send_message` вне dispatch-адаптера).
2. **Глобальный потолок.** Лимит `capped` считается по всем отправителям суммарно, не per-sender. Это и есть гарантия, которую один отправитель дать не может.
3. **Канало-агностичный вход.** Контракт не протекает Telegram-спецификой. Нарушение → болезненный retrofit при втором канале (Ф5).
4. **Очередь приватна.** Внешние producers НЕ пишут в таблицу напрямую — только через owned `enqueue`-контракт. Shared-table как кросс-сервисный контракт запрещён (антипаттерн integration-database, ArchGate Ф1).
5. **Не молчать при suppress.** Любое подавление логируется с причиной.
6. **Без перф-дубля.** Потолок считается по журналу, отдельной таблицы-квоты нет (OwnerIntegrity).

---

## 6. Связи с другими ролями

| Роль | Отношение |
|------|-----------|
| DP.ROLE.044 Notification Dispatcher | **Подчинённый транспорт.** Доставщик применяет политику, затем зовёт Диспетчер для физической доставки exactly-once |
| DP.SC.116 Уведомления и nudges (Nudge Engine, РП117) | **Вышестоящий «мозг».** Решает что/когда слать, владеет opt-out категориями. Доставщик enforce-ит, не решает |
| DP.ROLE.045 Dispatcher (очередь task'ов) | Не путать: DP.ROLE.045 — очередь агентских task'ов; DP.ROLE.075 — очередь исходящих сообщений пользователю |
| Навигатор (MIM.R.007), DP.ROLE.041 Аттестатор, Онбордер (РП406) | Потребители: шлют через Доставщик, не напрямую |

---

## 7. Точки входа (интерфейсы)

### In-bot контракт (сейчас)

```python
NotificationService.send(
    user_id: str,
    klass: str,           # critical | must-deliver | transactional | capped | ops-alert
    content_spec: dict,   # канало-нейтральный: {"text": ..., "actions": [...]} — без chat_id/reply_markup
    priority: int,        # 1..4
    dedup_key: str,
) -> dict  # {notification_id, status, reason?}
```

### Owned `enqueue`-контракт (будущее, при РП117)

Узкий API/RPC, которым владеет Доставщик как consumer; внутри пишет в свою приватную очередь. Внешний producer не знает схему очереди. Направление владения: consumer владеет интейком (как Novu/Knock), потому что политика доставки живёт у Доставщика.

---

## 8. История

- **WP-418 Ф1** (ArchGate, peer-сессия 2026-06-11-41): архитектура слоя согласована (build-thin, модуль в боте, 5 классов, COUNT-счётчик, приватная очередь).
- **WP-418 Ф2** (этот паспорт + DP.SC.177): класс-модель детализирована, роль и обещание формализованы (IntegrationGate шаги 1-3).
- **WP-418 Ф3** (предстоит): реализация `NotificationService` + миграция 107 точек.
