---
id: DP.M.037
title: "Lifecycle репо пилота personal-guide: 4 цикла с контрактами"
type: method
pack: digital-platform
status: draft
trust: 0.8
epistemic_stage: observed
valid_from: 2026-05-13
related: [DP.IWE.002, DP.IWE.006]
---

# DP.M.037 — Lifecycle репо пилота personal-guide

## Описание

Метод создания и развития персонального репо пилота (`personal-guide`), синхронизированного с платформой через GitHub App. Четыре цикла с явными контрактами.

## Forces

_Какие конкурирующие давления удерживает метод._

| Force | Tension |
|-------|---------|
| Скорость SLA reindex (≤30 сек после push) ↔ полнота переиндексации (эмбеддинги, search index) на каждый push | Жёсткий SLA подталкивает к дешёвой/частичной переиндексации, но неполный индекс подрывает саму цель цикла Reindex |
| Обещание GDPR right-to-delete (≤72ч, 4 шага) ↔ явное разделение Персоны (репо+embeddings) и Память.Derived (Neon events), которая НЕ удаляется автоматически | 4-шаговая процедура выглядит исчерпывающей, но Инварианты прямо указывают: события в Neon требуют отдельного запроса — «полное» удаление за 72ч на деле покрывает не весь user-data footprint |
| Экономия checksum-based refresh (пропуск rebuild при совпадении) ↔ риск устаревания дистрибуции при ложном совпадении checksum | Цикл Skill distribution refresh запускается ≥30 дней и полагается на checksum как единственный сигнал необходимости обновления |

## Циклы

| Цикл | Триггер | Контракт (SLA) |
|------|---------|----------------|
| **Reindex** | git push в репо | ≤30 сек до обновления индексов |
| **История** | Пересборка руководства | Архивация в history/ на шаге 5 render |
| **Skill distribution refresh** | Повторный render ≥30 дней | Checksum-based: обновление только при изменении |
| **GDPR right-to-delete** | Запрос пилота | ≤72 часа: 4 шага |

## GDPR Right-to-Delete (4 шага)

1. Uninstall GitHub App
2. Delete repo
3. Purge indexes (embeddings, search index)
4. Delete webhook records

## Инварианты

- GDPR-flow разделяет **Персону** (репо + embeddings) и **Память.Derived** (user_events в Neon) — удаляются отдельно.
- Lifecycle-spec явно указывает, что **НЕ удаляется автоматически** (Neon events требуют отдельного запроса).
- Checksum-based refresh предотвращает лишние rebuild при повторных render'ах.

## Bias-Annotation

_Куда систематически съезжает внимание практикующего. Статус карточки — `draft`: пометка `tentative` по прецеденту SA.METHOD.001 (WP-448 Ф12)._

| Bias | Direction of distortion |
|------|--------------------------|
| _(tentative)_ Ранние шаги GDPR-flow воспринимаются как завершение работы | Внимание концентрируется на шагах 1-2 (Uninstall GitHub App, Delete repo) — видимом, «решение принято» действии — и съезжает от шагов 3-4 (Purge indexes, Delete webhook records) как от технической рутины, которую можно доделать позже в рамках 72ч окна; именно шаг 3 реализует обещанное «репо + embeddings удалены» из Инвариантов, но по факту исполняется с меньшим приоритетом, чем видимый uninstall |
| _(tentative)_ Недоверие к checksum-based экономии | При повторном render'е (цикл Skill distribution refresh) внимание смещается к «на всякий случай перекопировать всё» вместо доверия checksum-сравнению — переоценивая риск устаревания и недооценивая cost повторных rebuild |

## Применимость

Паттерн применим к любому пользовательскому репо, синхронизированному с платформой через GitHub App. Ключевое: lifecycle-spec должен явно называть, что НЕ удаляется автоматически.

## Связи

- Сущность: DP.IWE.006 Personal Guide Channels
- Template: DP.IWE.002 (IWE template/setup)
- WP: WP-309 Ф2-Ф6

---

> 2026-07-27 — миграция на обогащённый формат карточки (Forces + Bias-Annotation), WP-448 Ф12 Батч 3 (суб-батч 2). Эталон формата: `SPF/pack-template/03-methods/_method-card-template.md`.
