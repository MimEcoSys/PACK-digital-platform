---
id: DP.FM.532
type: failure-mode
status: draft
created: "2026-10-05"
valid_from: "2026-10-02"
name: "Исчерпание лимита раундов tool-use отдаёт пользователю черновой текст модели вместо ответа через force-text fallback"
name_ru: "Исчерпание лимита раундов tool-use отдаёт пользователю черновой текст модели вместо ответа через force-text fallback"
name_en: "Exhausting the tool-use round limit returns the model's pre-tool-result draft text instead of routing through the existing force-text fallback"
summary: "generate_with_tools() может исчерпать max_tool_rounds, не дойдя до return/break внутри цикла — единственный способ попасть в эту точку — чтобы stop_reason последнего раунда был tool_use, то есть текст модели в этом раунде написан ДО результата инструмента. Старый fallback отдавал этот черновой текст прямо пользователю вместо существующего force-text fallback, рассчитанного именно на этот случай. Отдельно: защитная инструкция «не печатай синтаксис tool-call» стояла только в трёх из шести ролей на общем коде."
pack: PACK-digital-platform
domain: digital-platform / aist-bot
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit d06083e2 в aist_bot_newarchitecture (+ 60fa66b1, WP-7 Ф188); peer-session 2026-10-02-04"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:467"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-05-inbox-check.md"
source_candidate: 3
related:
  see_also: [DP.FM.529]
tags: [aist-bot, tool-use, llm-agent, fallback, prompt-audit]
---

# DP.FM.532 — Выход по лимиту раундов tool-use отдаёт черновик вместо force-text fallback

## Симптом

Пользователю в живой переписке показан необработанный черновик обращения к `search_knowledge` вместо ответа бота.

## Причина

`generate_with_tools()` может исчерпать `max_tool_rounds`, не дойдя до `return`/`break` внутри цикла — единственный путь в эту точку требует, чтобы `stop_reason` последнего раунда был `tool_use`: текст модели в этом раунде написан ДО того, как модель увидела результат инструмента. Старый fallback на выходе по лимиту отдавал этот текст пользователю напрямую, минуя существующий force-text fallback, спроектированный именно под этот случай.

## Исправление

1. Выход по исчерпанию `max_tool_rounds` маршрутизируется через существующий force-text fallback, а не отдаёт текст раунда со `stop_reason=tool_use` напрямую.
2. Защитная инструкция «не печатай синтаксис tool-call», ранее стоявшая только в трёх ролевых промптах (t1-t3) из шести, использующих тот же код consultation-пути, распространена на остальные (navigator/diagnostician/mentor).

## Тест обнаружения

«У раунда, на котором цикл вышел по лимиту, `stop_reason == tool_use`?» Да → текст этого раунда непригоден как финальный ответ, обязан идти через force-text fallback.

## Границы

Специфично для циклов tool-use с жёстким лимитом раундов. Аудит защитных промпт-инструкций по всем ролям на общем коде — действие общего применения, не только для этого бага.

## Связанные документы

- DP.FM.529 — поиск по базе знаний использует буквальный текст короткого ответа, а не тему диалога (смежный класс дефектов того же consultation-пути aist_bot).
- Источник: WP-7 Ф188, коммит d06083e2 (+60fa66b1) в aist_bot_newarchitecture; peer-session 2026-10-02-04.
