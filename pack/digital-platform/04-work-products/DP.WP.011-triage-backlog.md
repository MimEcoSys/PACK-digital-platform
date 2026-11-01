---
id: DP.WP.011
name: Triage Backlog
type: work-product
status: draft
summary: "Приоритизированный backlog техдолга: баги, UX-проблемы, knowledge gaps — из Triage Session"
created: 2026-02-25
trust:
  F: 2
  G: domain
  R: 0.5
epistemic_stage: emerging
related:
  produced_by: [S30]
  consumed_by: [R6, R14]
  services: [S29, S30]
---

# Triage Backlog

## 1. Определение

**Triage Backlog** — приоритизированный список задач техдолга, формируемый Триажёром (R7) на сессии триажа (S30). Агрегирует входы из Auto-Triage (S29), Unsatisfied Questions Report (DP.WP.009), fleeting-notes и captures.

## 2. Назначение

Без backlog'а техдолг решается реактивно: «что сломалось сейчас». Triage Backlog даёт: (1) приоритизацию по severity, (2) классификацию (bug / UX / knowledge gap), (3) оценку бюджета.

## 3. Структура

### 3.1. Расположение

Живёт в WP-context file зонтичного РП техдолга:
```
DS-my-strategy/inbox/WP-{N}-bot-techdebt.md
```

### 3.2. Формат записи

| Поле | Описание |
|------|----------|
| Задача | Краткое описание |
| Тип | bug / UX / knowledge-gap / performance / cleanup |
| Severity | critical / high / medium / low |
| Источник | S29 auto-triage / WP.009 / fleeting-note / capture |
| Бюджет | Оценка в часах |
| Статус | pending / in_progress / done |

## 4. Рабочий процесс

```
Intake (S29 auto / manual) → Triage Session (S30) → Backlog → Sprint (WP-debt) → Done → Удаление из backlog
```

## 5. Критерии качества

| Критерий | Проверка |
|----------|----------|
| Актуальность | Done-задачи удалены? Новые intake обработаны? |
| Приоритизация | Critical/high решаются первыми? |
| Размер | 10-20 пунктов (больше = нужна чистка) |

## 6. Связанные документы

- [DP.WP.009](DP.WP.009-unsatisfied-questions-report.md) — один из входов backlog'а
- [DP.MAP.002 S30](../07-map/DP.MAP.002-iwe-service-catalog.md) — сервис Triage Session
