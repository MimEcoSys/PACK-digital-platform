---
id: DP.WP.014
name: Validation Report
type: work-product
status: draft
summary: "Отчёт валидации: проверка шаблона экзокортекса (S24) или Pack-сущности (S38) на соответствие стандарту"
created: 2026-02-25
trust:
  F: 2
  G: domain
  R: 0.5
epistemic_stage: emerging
related:
  produced_by: [S24, S38]
  consumed_by: [R9, R2]
  services: [S24, S38]
---

# Validation Report

## 1. Определение

**Validation Report** — отчёт проверки артефакта на соответствие стандарту. Два варианта:
- **Template Validation (S24):** проверка FMT-exocortex-template на полноту и корректность после синхронизации
- **WP Validation (S38):** проверка Pack-сущности на соответствие SPF-спецификации

## 2. Назначение

Без валидации: шаблон может разойтись с платформой (битые файлы, устаревшие промпты), а Pack-сущности — нарушить структуру (пропущенный frontmatter, неверные ссылки).

## 3. Структура

| Секция | Описание |
|--------|----------|
| Target | Что проверялось (шаблон / Pack-сущность) |
| Checks | Список проверок с результатами (pass/fail/warning) |
| Failures | Детали каждого fail: что ожидалось, что получено |
| Summary | Total checks, pass, fail, warnings |
| Verdict | Pass (все критические ok) / Fail (есть critical fail) |

## 4. Рабочий процесс

```
Запуск (S24 после S23 / S38 по запросу) → Проверки → Отчёт → Исправление (если fail) → Re-run
```

## 5. Критерии качества

| Критерий | Проверка |
|----------|----------|
| Полнота проверок | Все обязательные поля/файлы проверены? |
| Zero false positive | Fail = реальная проблема? |
| Быстрота | Валидация <30 сек? |

## 6. Связанные документы

- [DP.MAP.002 S24](../07-map/DP.MAP.002-iwe-service-catalog.md) — сервис Template Validation
- [DP.MAP.002 S38](../07-map/DP.MAP.002-iwe-service-catalog.md) — сервис WP Validation
