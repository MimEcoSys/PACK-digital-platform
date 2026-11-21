---
id: DP.SOTA.044
name: "Виджеты Telegram Bot API 10.4: HTML-интерфейс в сообщении с обновлением данных"
name_ru: "Виджеты Telegram Bot API 10.4"
name_en: "Telegram Bot API 10.4 widgets: an HTML interface in a message with data updates"
type: sota
pack: PACK-digital-platform
domain: digital-platform / telegram-delivery
status: draft
trust: confirmed
epistemic_stage: observed
created: "2026-11-21"
valid_from: "2026-11-09"
summary: "Официальный снимок на 09.11.2026: боты могут отправлять HTML-виджеты и обновлять их данные; в production виджеты отправляются только в личные чаты и не могут быть пересланы."
schema_version: 1
related:
  see_also: [DP.SOTA.042]
tags: [telegram, bot-api, widgets, delivery-channel]
source: "Telegram Bot API changelog, 09.11.2026, Bot API 10.4: https://core.telegram.org/bots/api-changelog#november-9-2026"
source_capture: "DS-my-strategy/inbox/captures/2026-11.md — «Виджеты Telegram Bot API 10.4…»"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-11-21-inbox-check.md"
source_candidate: 3
---

# Виджеты Telegram Bot API 10.4

## Подтверждённый снимок на 09.11.2026

По официальному журналу изменений Telegram:
- боты могут отправлять сообщения с HTML-виджетами;
- метод `editMessageWidgetData` обновляет данные виджета в сообщении;
- в production виджеты можно отправлять только в личные чаты;
- отправленные виджеты имеют защищённое содержимое и не могут быть пересланы.

## Граница

Проверено по официальному журналу 21.11.2026. Лимит 16 «тяжёлых» элементов и невозможность изменить разметку после отправки этим источником не подтверждены и в вендорский снимок не включены.
