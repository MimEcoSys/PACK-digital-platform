---
id: DP.WP.013
name: Publication Schedule
type: work-product
status: draft
summary: "Расписание публикаций: посты со статусом ready → запланированные даты/время публикации в клубе"
created: 2026-02-25
trust:
  F: 2
  G: domain
  R: 0.5
epistemic_stage: emerging
related:
  produced_by: [S25]
  consumed_by: [S26, S27, R14]
  services: [S25, S26, S27]
---

# Publication Schedule

## 1. Определение

**Publication Schedule** — расписание публикаций контента в клубе (systemsworld.club), генерируемое Публикатором (R21). Daily Scan (S25) сканирует посты со статусом `ready` и формирует расписание; Scheduled Publish (S26) и Manual Publish (S27) исполняют его.

## 2. Назначение

Без расписания публикации хаотичны: то три поста в день, то неделя тишины. Publication Schedule обеспечивает: (1) равномерный ритм, (2) подогрев к мероприятиям, (3) предсказуемость для аудитории.

## 3. Структура

### 3.1. Хранение

DB-таблица `scheduled_publications`:

| Поле | Описание |
|------|----------|
| `id` | Уникальный ID записи |
| `post_path` | Путь к markdown-файлу поста |
| `scheduled_date` | Дата/время публикации |
| `status` | scheduled / published / cancelled |
| `discourse_topic_id` | ID опубликованного топика (после публикации) |

### 3.2. Визуализация

Бот показывает расписание по команде `/club schedule` с кнопками управления (🚀 опубликовать / ❌ удалить).

## 4. Рабочий процесс

```
Скан (S25, 03:00) → Расписание (DB) → Публикация (S26, */30 мин) → frontmatter update (status: published)
```

## 5. Критерии качества

| Критерий | Проверка |
|----------|----------|
| Ритм | Не более 1 поста в день? |
| Покрытие | Все ready-посты запланированы? |
| Подогрев | Есть подогрев к ближайшему мероприятию? |

## 6. Связанные документы

- [DP.MAP.002 S25-S27](../07-map/DP.MAP.002-iwe-service-catalog.md) — сервисы Daily Scan, Scheduled Publish, Manual Publish
