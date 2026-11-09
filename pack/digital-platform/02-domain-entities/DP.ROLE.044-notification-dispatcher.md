---
id: DP.ROLE.044
name: Notification Dispatcher
type: role-description
status: draft
valid_from: 2026-05-16
summary: "Транспортный слой исходящих уведомлений платформы: принимает запросы от любых потребителей (пользователь, агент, воркер), ставит в очередь, доставляет в Telegram exactly-once, подтверждает статус."
related:
  specializes: [U.RoleAssignment]
  component_of: [DP.ROLE.001]
  realizes: [DP.SC.134]
  uses:
    - DP.ROLE.035   # Platform Observer — смежная роль (status notifications)
    - notification_log  # idempotency шина (WP-152)
    - reminders         # scheduling queue (legacy, действующая)
    - learning.domain_event  # event log (WP-253)
  downstream_consumers:
    - Пользователь платформы — получает TG-сообщение
    - Claude-агент — получает {reminder_id, status} через MCP
    - Платформенный воркер — получает {reminder_id, status} через internal API
created: 2026-05-16
updated: 2026-05-16
wp: WP-320
---

# Notification Dispatcher — DP.ROLE.044

> # see DP.SC.134, DP.ROLE.044
>
> **Kind:** Transport Role — принимает запросы, управляет очередью, доставляет. Без бизнес-логики, без интерпретации содержимого.
> **Owner Role:** IWE Platform — исполнитель: @aist_me_bot (Railway) + mcp.aisystant.com.

---

## 1. Миссия

Быть надёжным транспортом между намерением отправить сообщение и фактом получения его пользователем в Telegram.

Аналогия: почтовое отделение. Не читает письма, не решает что писать — только принимает, хранит до нужного момента и доставляет. Гарантирует: письмо дойдёт ровно один раз и в нужное время.

**Граница:** Dispatcher не разбирает natural language, не хранит задачи, не управляет подписками. Он получает готовый текст и время — и отвечает за доставку.

---

## 2. Обязанности

| Обязанность | Как выполняется |
|-------------|----------------|
| Принять запрос от потребителя | MCP-tool `send_telegram_message` / bot command `/remind` / internal API |
| Валидировать: пользователь известен, chat_id есть | `SELECT chat_id FROM users WHERE account_id = $1` |
| Создать idempotency_key | `reminder:{chat_id}:{schedule_at}:{hash(text)}` |
| Записать в очередь | INSERT INTO `reminders` (chat_id, text, scheduled_for) |
| Подтвердить принятие | Вернуть `{reminder_id, scheduled_at, status: queued}` |
| Доставить в нужное время | Scheduler: `SELECT ... WHERE scheduled_for <= NOW() AND sent = FALSE FOR UPDATE SKIP LOCKED` |
| Отправить TG-сообщение | `POST api.telegram.org/bot{TOKEN}/sendMessage` |
| Зафиксировать статус | UPDATE reminders SET sent = TRUE + INSERT INTO `learning.domain_event` |
| Retry при отказе | 3× с backoff 10s / 30s / 90s → после 3 неудач status = failed |

---

## 3. Входы / Выходы

**Входы (от потребителя):**
- `text: string` — текст сообщения (обязательный)
- `schedule_at?: datetime` — когда доставить (если не указан — немедленно)
- `user_id?` — для платформенных воркеров (если не указан — текущий пользователь сессии)

**Выходы:**
- `reminder_id: int` — идентификатор записи в `reminders`
- `scheduled_at: datetime` — когда будет доставлено
- `status: queued | sent | failed`

**Артефакты в Neon:**

| Таблица | Что пишет |
|---------|-----------|
| `bot_data.reminders` | Очередь: запись при принятии, `sent=TRUE` при доставке |
| `public.notification_log` | Idempotency guard (до полного перехода на domain_event, WP-253) |
| `learning.domain_event` | `event_type=notification_sent` при успешной доставке |

---

## 4. Архитектура (слои)

```
Потребители
├── MCP-tool send_telegram_message   ← Claude-агент / пользователь через claude.ai/VS Code
├── Bot command /remind               ← пользователь через @aist_me_bot в Telegram
└── Internal API                      ← платформенные воркеры (stage_evaluator, etc.)
        │
        ▼
Dispatcher (DP.ROLE.044)
├── Validator   → chat_id lookup в Neon
├── Queue       → INSERT INTO reminders
├── Scheduler   → Railway cron, каждую минуту
│     └── SELECT ... FOR UPDATE SKIP LOCKED → Telegram Bot API
└── Logger      → learning.domain_event
```

---

## 5. Ограничения (инварианты роли)

1. **Exactly-once.** Дублирование запрещено через idempotency_key. Повторный запрос с тем же key → тот же reminder_id, без второй отправки.
2. **Без интерпретации содержимого.** Dispatcher передаёт текст как есть. NL-разбор («через час») — задача вышестоящего агента.
3. **Не молчать при отказе.** Статус `failed` всегда фиксируется и возвращается потребителю.
4. **Только зарегистрированные пользователи.** Если chat_id не найден — немедленный отказ с объяснением.

---

## 6. Связи с другими ролями

| Роль | Отношение |
|------|-----------|
| DP.ROLE.075 Доставщик (Delivery Policy Layer) | **Вышестоящий слой политики** (WP-418): применяет потолки/приоритет/дедуп/предпочтения, затем зовёт Dispatcher для физической доставки exactly-once. Dispatcher остаётся чистым транспортом |
| DP.ROLE.035 Platform Observer | Смежная: Observer → status уведомления (системные). Dispatcher → пользователь-инициированные + агентские |
| DP.ROLE.041 Attestator | Потребитель Dispatcher: сообщает пользователю о новой ступени |
| Навигатор (MIM.R.007) | Потребитель: может отправить напоминание о ритуале через Dispatcher |
| DP.SC.116 Уведомления и nudges | Смежный SC: платформа-инициированные (SC.116) vs потребитель-инициированные (SC.134). Транспортный слой один |

---

## 7. Точки входа (интерфейсы)

### MCP-tool `send_telegram_message`

```json
{
  "name": "send_telegram_message",
  "description": "Отправить сообщение пользователю в Telegram. Если schedule_at указан — поставить в очередь.",
  "input_schema": {
    "text": { "type": "string", "description": "Текст сообщения" },
    "schedule_at": { "type": "string", "format": "datetime", "description": "ISO 8601, опционально" },
    "user_id": { "type": "string", "description": "account_id пользователя, опционально" }
  },
  "output": {
    "reminder_id": "int",
    "scheduled_at": "datetime",
    "status": "queued | sent | failed"
  }
}
```

### Bot command `/remind`

```
/remind [текст] [время]

Примеры:
  /remind позвонить в IND через 2 часа
  /remind check-in рейс KL1234 20 мая 18:00
  /remind list                              — показать активные напоминания
  /remind cancel 42                         — отменить reminder_id=42
```

Парсинг времени: regex для явных форматов (`ЧЧ:ММ`, `ДД мес ЧЧ:ММ`); для «через X» — расчёт от `NOW()`. LLM-парсинг опционально для сложных случаев.
