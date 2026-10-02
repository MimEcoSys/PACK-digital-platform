---
id: DP.SC.019
name: Автономная работа IWE (Cloud Runtime)
type: sc
status: draft
layer: L4-Personal
summary: "Опциональная облачная топология IWE: ночная автоматика, мультиустройственный доступ и управление через Telegram"
consumer: Пользователь IWE (L4-Personal)
created: 2026-03-20
updated: 2026-10-02
related:
  realizes: [S61, S62]
  uses: [DP.ARCH.001]
  extends: [DP.SC.007, DP.SC.107]
  source: "WP-138"
---

# DP.SC.019 — Автономная работа IWE (Cloud Runtime)

## Обещание

**Кому:** Пользователю IWE, который явно выбрал облачную топологию. Локальный IWE работает полноценно без Cloud Runtime.

**Зачем:** В локальной топологии автоматика, требующая работающего Mac, не запускается, когда он спит или выключен. Облачная топология по выбору пользователя добавляет непрерывный запуск и доступ с другого устройства.

**Что получит:**
- Автоматика IWE работает 24/7 независимо от состояния компьютера
- Просмотр планов и добавление заметок через Telegram с любого устройства
- Синхронизация cloud ↔ local через git (source of truth не меняется)
- Отказоустойчивость: Mac потерян — IWE продолжает работать

**Критерий приёмки:**
1. Ночная автоматика (scheduler) отрабатывает при выключенном Mac ≥7 дней подряд без сбоев
2. Через Telegram: `/plan` показывает DayPlan, `/note <текст>` создаёт заметку — задержка <3 сек
3. Утром при включении Mac: `git pull` получает все изменения от cloud runtime

## Архитектура: два уровня

### Базовый (по явному включению пользователем)

```
GitHub Actions (cron) → bash-скрипты (без LLM)
  ├── reindex.sh — переиндексация knowledge-mcp
  ├── template-sync.sh — синхронизация с шаблоном
  ├── update.sh — Pack→DS propagation
  ├── backup — memory/, CLAUDE.md → git
  └── $0/мес (бесплатный tier GitHub Actions)
```

Не требует Claude API. Обычные bash-скрипты в GitHub Actions по расписанию.

### Продвинутый (opt-in, выделенный сервер)

```
NixOS на Hetzner (dedicated/VPS) → декларативная конфигурация
  ├── configuration.nix — весь сервер описан в git
  ├── ZFS — сжатие данных на лету (текст в 2-3x меньше)
  ├── Шифрование — из коробки
  ├── Автоматический rollback при ошибке деплоя
  ├── cron → bash-скрипты (reindex, sync, backup)
  ├── Claude Agent SDK → strategist, note-review, week-review
  ├── Telegram Gateway — /plan, /note, /status
  └── ~€30-50/мес (Hetzner dedicated auction) + ~$30-90/мес (Claude API Haiku)
```

Конфигурация в git → шаблонизируемость. Правишь `configuration.nix` → деплоишь → работает или откатывается на предыдущую версию.

### Разделение задач (что требует LLM, а что нет)

| Задача | Нужен Claude? | Уровень | Стоимость |
|--------|:---:|---------|-----------|
| reindex.sh | Нет | Базовый | $0 |
| template-sync.sh | Нет | Базовый | $0 |
| update.sh (propagation) | Нет | Базовый | $0 |
| backup (memory, CLAUDE.md) | Нет | Базовый | $0 |
| extractor inbox-check | Нет | Базовый | $0 |
| **strategist morning** | **Да** | Продвинутый | ~$1-3/день |
| **note-review** | **Да** | Продвинутый | ~$0.5-1/день |
| **week-review (пн)** | **Да** | Продвинутый | ~$1-3/неделю |

## Реализующие сервисы (MAP.002)

| Сервис | Название | Роль | Вход | Выход | Триггер |
|--------|----------|------|------|-------|---------|
| S61 | Cloud Scheduler | R8 Синхронизатор | Расписание + конфиг | Запуск задач | ⏰ cron (GitHub Actions / VPS) |
| S62 | IWE Telegram Gateway | R8 Синхронизатор | Команда пользователя | Ответ (план, статус, заметка) | ⚡ Telegram-команда |

## Пользовательский путь

> Пользователь разворачивает полноценный локальный IWE из шаблона. Если он выбирает облачную топологию, то явно включает базовый Cloud Runtime через `setup/optional/setup-cloud-scheduler.sh` (GitHub Actions); продвинутый уровень — отдельный выбор (deploy.sh на VPS).

| # | Шаг | Кто | Сервис |
|---|-----|-----|--------|
| 1 | Создать репо из шаблона FMT-exocortex-template (Use this template) → `bash setup/optional/setup-cloud-scheduler.sh` | Пользователь | — |
| 2 | GitHub Actions cron запускает bash-скрипты по расписанию (reindex, sync, backup) | S45 Cloud Scheduler | GitHub Actions |
| 3 | Утром пользователь включает Mac, делает `git pull` — получает результаты ночной работы | Пользователь | — |
| 4 | (Продвинутый) `deploy.sh` на VPS — разворачивает полный cloud runtime с Claude Agent SDK | Пользователь | — |
| 5 | (Продвинутый) Strategist генерирует DayPlan ночью через Claude API | S45 Cloud Scheduler | Claude Agent SDK |
| 6 | (Продвинутый) Через Telegram: `/plan` — просмотр, `/note текст` — заметка | Пользователь | S46 TG Gateway |

### Пример: Telegram-команды

```
Пользователь: /plan
Бот: 📋 DayPlan 20 марта 2026 (Пятница)

| # | РП | Статус |
|---|-----|--------|
| 77/78 | Саморазвитие | pending |
| 129 | Мультиканальная публикация | in_progress |
| 138 | Cloud runtime | in_progress |

⏱ Бюджет: ~4h осталось

Пользователь: /note проверить интеграцию calendar-mcp с cloud runtime
Бот: ✅ Заметка записана в inbox/fleeting-notes.md
```

## Связь с другими обещаниями

- Расширяет **[DP.SC.007]** Автоматический ОРЗ-цикл — добавляет cloud execution
- Расширяет **[DP.SC.107]** Мультиповерхностный доступ — добавляет Telegram + mobile
- Потребляет **S17** Scheduler Dispatch (та же логика, другой runtime)
- Питает **[DP.SC.017]** Адаптивное задание на день (DayPlan из облака)

## Фазы реализации

| Фаза | Что | Для кого | Зависимости | Бюджет |
|------|-----|----------|-------------|--------|
| **Ф0** | GitHub Actions workflows для bash-скриптов | Выбравшие Cloud Runtime | — | 4-6h |
| **Ф1** | VPS deploy.sh + Claude Agent SDK strategist | Продвинутые | Claude API key | 8-12h |
| **Ф2** | Telegram Gateway (/plan, /note, /status) | Продвинутые | Ф1 + Telegram bot token | 8-12h |
| **Ф3** | PWA Dashboard | Продвинутые | Ф1 | 20-40h |
