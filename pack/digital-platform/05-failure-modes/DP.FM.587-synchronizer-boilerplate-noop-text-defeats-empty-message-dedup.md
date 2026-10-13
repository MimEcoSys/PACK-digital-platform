---
id: DP.FM.587
name_ru: "Синхронизатор шлёт boilerplate-текст на штатный no-op вместо пустого сообщения — лишает себя готового механизма дедупа по пустому сообщению"
name_en: "A synchronizer sends boilerplate text on a routine no-op run instead of an empty message — defeating the already-available empty-message dedup mechanism"
summary: "Два сценария синхронизатора (Knowledge Feeder git-diff-feed/session-close-feed и code-scan) слали Telegram-сообщение даже когда нечего репортить («Новых кандидатов нет», «Репо с коммитами: 0» на каждый тик) — пойман дубль с разницей 16 минут в одном дампе пилота. Фикс — возвращать пустое сообщение при отсутствии новизны тем же механизмом, которым notify.sh уже пропускает отправку пустого сообщения в сценарии inbox-check."
type: failure-mode
status: draft
created: "2026-10-09"
valid_from: "2026-10-09"
pack: PACK-digital-platform
domain: digital-platform / notification-design
schema_version: 1
trust: observed
epistemic_stage: forming
related:
  see_also: [DP.FM.586]
source: "git commit 3b6c7ad в FMT-exocortex-template"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:2043"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-10-inbox-check.md"
source_candidate: 3
tags: [notification-design, no-op, empty-message, dedup, synchronizer]
---

# DP.FM.587 — Синхронизатор должен молчать на штатном no-op, не слать boilerplate

## Симптом

Два независимых сценария синхронизатора — Knowledge Feeder (`git-diff-feed`/`session-close-feed`) и `code-scan` — слали Telegram-уведомление на каждом тике/прогоне, даже когда реально нечего репортить: фиксированный текст «Новых кандидатов нет» и «Репо с коммитами: 0» соответственно. В живом дампе пилота это дало дубль одного и того же «пустого» сообщения с разницей 16 минут.

## Механизм

`notify.sh` уже содержит механизм пропуска отправки при пустом сообщении — тот же механизм, которым пользуется сценарий inbox-check. Два других сценария синхронизатора не были приведены к этому контракту: вместо того, чтобы на no-op-прогоне вернуть пустую строку (и дать `notify.sh` естественно пропустить отправку), они формировали непустой boilerplate-текст, который `notify.sh` обязан был отправить — механизм дедупа по пустому сообщению существовал, но не применялся этими двумя путями.

## Паттерн исправления

Любой сценарий синхронизатора, формирующий сообщение для `notify.sh`, на штатном no-op-прогоне (ничего нового не найдено) должен вернуть пустое сообщение, а не фиксированный текст-заглушку «ничего нового» — прогон, который реально что-то нашёл, продолжает слать уведомление как обычно.

## Тест обнаружения

«Сценарий синхронизатора на no-op-прогоне формирует непустой текст («ничего нового», «0 изменений» и т.п.) вместо пустой строки, при наличии в системе общего механизма пропуска отправки пустых сообщений?» Да → синхронизатор лишает себя уже доступного ему дедупа и рискует дублировать «пустые» уведомления на соседних тиках.

## Связи

- **DP.FM.586** — тот же аудит шума уведомлений (peer-session 2026-10-09-02-notification-spam-readable), другой аспект: не решение слать/не слать, а формулировка текста уже отправляемого алерта.

## Происхождение

git commit `3b6c7ad` в FMT-exocortex-template. WP-538, peer-session 2026-10-09-02-notification-spam-readable.
