---
id: DP.FM.520
type: failure-mode
status: draft
created: "2026-10-02"
valid_from: "2026-09-24"
name: "Inner-middleware aiogram не срабатывает, если у события нет ни одного handler"
name_ru: "Inner-middleware aiogram не срабатывает, если у события нет ни одного handler"
name_en: "An aiogram inner middleware does not run when the event has no handler"
summary: "Middleware, зарегистрированный через dp.edited_message.middleware(...), не выполнялся: aiogram запускает inner-middleware только вокруг совпавшего handler, а для edited_message в проекте handler не было. Правки сообщений участника не попадали в архив переписки. Замена на outer_middleware исправила это; подтверждено чтением исходников aiogram и двумя regression-тестами."
pack: PACK-digital-platform
domain: digital-platform / bot-framework
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit 49424544 в aist_bot_newarchitecture (WP-578, пир-сессия 2026-09-24-01-wp578-mentor-bot-fixes); git commits 9b82945d и 5cddfb3b (WP-498 Ф17); отчёты Экстрактора 2026-09-26-inbox-check кандидат 4 и 2026-10-02-inbox-check-2 кандидат 1"
source_capture: "DS-my-strategy/inbox/captures/2026-09.md:3750"
related:
  see_also: ["DP.FM.074", "DP.FM.495"]
tags: [aiogram, middleware, event-dispatch, outer-middleware, dedup]
---

# DP.FM.520 — inner-middleware aiogram не срабатывает без handler на событие

## Симптом

Для записи правок сообщений участника в архив переписки middleware был зарегистрирован через `dp.edited_message.middleware(...)`. Правки в архив не попадали. Регистрация проходила без ошибки.

## Причина

В aiogram inner-middleware выполняется только вокруг совпавшего handler, а у `dp.edited_message` в проекте не было ни одного handler. Middleware физически не вызывался. Подтверждено чтением исходников aiogram и двумя regression-тестами.

## Антипаттерн → Паттерн

- **Антипаттерн:** регистрировать через `.middleware(...)` (inner) логику, которая должна работать для события независимо от наличия handler.
- **Паттерн:** для такой логики использовать `outer_middleware(...)`; в источнике замена на него исправила проблему. Для inner и outer выбор осознанный: inner срабатывает вокруг совпавшего handler, outer не зависит от handler.

Уровень регистрации задаёт кардинальность срабатывания. Тот же корень проявился в другом случае (WP-498 Ф17): дедупликация апдейтов по `update_id`, зарегистрированная как inner-middleware, срабатывала на каждый подобранный handler. Handler `on_mentor_dm_free_text` поднимал `SkipHandler` для всех, кто не наставник; проход следующего handler видел тот же `update_id`, считал апдейт дублем и отбрасывал его, и запасной обработчик не отвечал никогда. Правило из источника: дедупликацию делать outer-middleware для наблюдателей message и callback_query; дешёвые проверки выносить в фильтр роутера; `SkipHandler` оставлять редким путям, иначе inner-цепочка (rate limit, трассировка, архив) отрабатывает дважды.

## Тест обнаружения

«Middleware зарегистрирован на тип события, и есть ли для этого типа хотя бы один handler?» Нет → inner-middleware не выполнится. «Дедупликация или другая логика один-на-апдейт стоит в inner-middleware при нескольких возможных handler?» Да → она сработает на каждый подобранный handler.

## Связанные документы

- Источник: git commit `49424544` в aist_bot_newarchitecture (WP-578); для абзаца про дедупликацию git commits `9b82945d` и `5cddfb3b` (WP-498 Ф17).
- DP.FM.074 (handler написан, но не зарегистрирован в router: другой разрыв подключения), DP.FM.495 (глобальный обработчик глотает исключение без журнала: родственный молчаливый отказ в обработке событий).
