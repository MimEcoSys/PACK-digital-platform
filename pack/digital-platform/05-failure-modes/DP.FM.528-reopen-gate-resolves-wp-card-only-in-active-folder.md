---
id: DP.FM.528
type: failure-mode
status: draft
created: "2026-10-02"
valid_from: "2026-10-01"
name: "Шлюз переоткрытия искал карточку РП только в `inbox/`, а карточка закрытого РП лежит в архиве"
name_ru: "Шлюз переоткрытия искал карточку РП только в `inbox/`, а карточка закрытого РП лежит в архиве"
name_en: "The reopen gate looked for a WP card only in `inbox/`, while the card of a closed WP lives in the archive"
summary: "`wp-reopen-gate.sh` искал карточку только в `inbox/`, а для закрытого РП карточка лежит в `archive/wp-contexts/`. Актуализация была невозможна, протокол нельзя было выполнить при правке записи закрытия. Исправлено корневым коммитом 7b3373ea04 с тестом и ревью."
pack: PACK-digital-platform
domain: digital-platform / lifecycle-tooling
schema_version: 1
trust: medium
epistemic_stage: observed
source: "git commit 87162d90a в DS-my-strategy (корневое исправление 7b3373ea04 в iwe-local-config, wp-reopen-gate.sh), WP-530"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:84"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-02-inbox-check.md"
source_candidate: 1
related:
  see_also: ["DP.FM.440", "DP.FM.131", "DP.M.010", "DP.SC.033"]
tags: [lifecycle, gate, resolver, archive, wp-reopen, path-assumption]
---

# DP.FM.528 — Шлюз переоткрытия ищет карточку только в активной папке

## Симптом

Шлюз, который разрешает правку закрытых РП через протокол переоткрытия, не находил карточку: `wp-reopen-gate.sh` искал её только в `inbox/`, а у закрытого РП карточка лежит в `archive/wp-contexts/`. Актуализация была невозможна, и протокол нельзя было выполнить при правке записи закрытия.

## Причина

Объект при переходе стадии жизненного цикла (активный → архив) меняет место хранения, а резолвер карточки в шлюзе знал только «живой» путь. Шлюз отказывал именно тому классу объектов (закрытые РП), ради которого создан.

## Исправление и статус доставки

Исправлено корневым коммитом 7b3373ea04 (iwe-local-config) с тестом и ревью.

## Тест обнаружения

«Шлюз обслуживает стадию X; на стадии X объект лежит не там, где на стадии создания; резолвер знает только путь стадии создания?» Да → шлюз не работает по назначению. Тест шлюза должен включать объект в архивном состоянии.

## Связанные документы

- DP.M.010 и DP.SC.033: источник истины о стадиях РП и их хранилищах.
- DP.FM.440 (fail-safe гейт отказывает легитимному пути) и DP.FM.131 (неполный lifecycle-инструментарий): соседние механизмы; здесь инструмент стадии есть, но не находит объект после перехода.
- Источник: WP-530; коммит 87162d90a в DS-my-strategy.
