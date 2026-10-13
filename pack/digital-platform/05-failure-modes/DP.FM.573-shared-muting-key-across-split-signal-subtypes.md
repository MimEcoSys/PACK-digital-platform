---
id: DP.FM.573
type: failure-mode
status: draft
created: "2026-10-08"
valid_from: "2026-10-08"
name: "Расщепление одного вида сигнала на под-виды без разделения ключей заглушения — управление одним под-видом молча управляет и остальными"
name_ru: "Расщепление одного вида сигнала на под-виды без разделения ключей заглушения — управление одним под-видом молча управляет и остальными"
name_en: "Splitting a signal kind into sub-types without splitting the muting keys — muting one sub-type silently mutes all others sharing the same key"
summary: "При введении нового под-вида сигнала (calendar_meeting_prep) поверх уже существующего (calendar_free_window) оба разделяли общий namespace ключей disabled:/snooze: по исходному kind. Заглушение одного под-вида через «Не предлагать» молча гасило и второй. Фикс — разделить candidate.kind на отдельные значения с независимыми ключами. Переносимо: при расщеплении сигнала каждый под-вид должен получить собственный ключ управления."
pack: PACK-digital-platform
domain: digital-platform / secretary-signal-design
schema_version: 1
trust: observed
epistemic_stage: forming
source: "git commit b9283ca56 в DS-my-strategy (WP-389 Ф6)"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:1648"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-08-inbox-check-3.md"
source_candidate: 5
related:
  see_also: []
tags: [signal-split, muting-key, shared-namespace, silent-suppression, secretary]
---

# DP.FM.573 — Расщепление сигнала без разделения ключей заглушения: молчаливое подавление второго под-вида

## Тезис и механизм ошибки

При введении нового под-вида сигнала поверх существующего оба наследуют общий namespace ключей управления (disabled:/snooze:), если явно не разделить. В результате заглушение одного под-вида через пользовательское действие («Не предлагать») молча заглушает и второй, хотя пользователь действовал только на первый.

Обнаружено в ходе code review до публикации (WP-389 Ф6, сигнал `calendar_meeting_prep` введён поверх `calendar_free_window`).

## Диагностический принцип

При расщеплении одного `kind` сигнала на несколько под-видов, использующих общую инфраструктуру управления по ключу `kind`, каждый под-вид должен получить собственный независимый ключ — иначе управление одним подразумевает управление всеми.

## Проверка

«Новый под-вид сигнала использует тот же ключ disabled:/snooze:/… что и родительский или соседний вид? Тогда их управление связано?» Да → риск DP.FM.573.

## Фикс

Разделить `candidate.kind` на отдельные значения (`calendar_meeting_prep`, `calendar_free_window`) с независимыми ключами управления до публикации. Не наследовать ключ по умолчанию при введении нового под-вида.

## Границы

Применимо к любой системе сигналов/уведомлений, где виды управляются по namespace-ключу (kind, type, category). Не ограничивается Secretary или Telegram-ботом.

## Связи

Источник: WP-389 Ф6; пир-сессия 2026-10-07-12-wp389-secretary-next-phase (Kimi+Codex).
