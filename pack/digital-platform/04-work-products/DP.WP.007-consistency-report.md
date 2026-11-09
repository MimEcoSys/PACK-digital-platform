---
id: DP.WP.007
name: Consistency Report
type: work-product
status: draft
summary: "Отчёт проверки согласованности Pack-репо и downstream: расхождения, битые ссылки, дупликаты"
created: 2026-02-25
trust:
  F: 2
  G: domain
  R: 0.5
epistemic_stage: emerging
related:
  produced_by: [S20]
  consumed_by: [R5]
  services: [S20]
---

# Consistency Report

## 1. Определение

**Consistency Report** — отчёт проверки согласованности между Pack-репо и downstream-репо, генерируемый Синхронизатором (R8). Выявляет расхождения, битые ссылки, устаревшие ссылки и дупликаты.

## 2. Назначение

Pack — source-of-truth, downstream — производные. Без проверки согласованности: downstream расходится с Pack, ссылки ломаются, терминология дрейфует.

## 3. Структура

| Секция | Описание |
|--------|----------|
| Scope | Какие Pack и downstream-репо проверялись |
| Расхождения | Список: файл Pack ↔ файл downstream, в чём различие |
| Битые ссылки | Ссылки в downstream на несуществующие Pack-сущности |
| Дупликаты | Одинаковый контент в разных местах |
| Сводка | Метрики: total checks, pass, fail, warnings |

## 4. Рабочий процесс

```
Запуск (S20, по запросу) → Генерация отчёта → Ревью (R5 Архитектор) → Исправление → Закрытие
```

## 5. Критерии качества

| Критерий | Проверка |
|----------|----------|
| Полнота | Все Pack-downstream пары проверены? |
| Точность | Расхождения реальны (нет false positive)? |
| Actionability | Каждое расхождение содержит путь к исправлению? |

## 6. Связанные документы

- [DP.MAP.002 S20](../07-map/DP.MAP.002-iwe-service-catalog.md) — сервис Consistency Check
