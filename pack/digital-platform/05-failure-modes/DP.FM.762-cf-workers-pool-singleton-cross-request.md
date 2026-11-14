---
id: DP.FM.762
name: Модульный синглтон Pool/соединения к БД в Cloudflare Workers ломается «I/O on behalf of a different request» — время жизни пула = один запрос
type: failure-mode
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_cloudflare_workers_pool_singleton_cross_request.md (knowledge-mcp #231, 10.07; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [DP.M.617, PACK-digital-platform]
---

# DP.FM.762: cross-request pool в CF Workers

## Симптом
~30% запросов падают HTTP 500 минуя прикладной try/catch: `Cannot perform I/O on behalf of a different request`. Первый фикс (pool.on('error')) не помог — причина не обрыв соединения.

## Причина
CF привязывает I/O-объект к контексту открывшего его запроса. Модульный синглтон `let pool` в глобальной области, переиспользуемый между запросами, убивает чужие запросы. `wrangler tail` во время воспроизведения ловит точный текст быстрее статического аудита.

## Антипаттерн → Паттерн
- **Антипаттерн:** модульный синглтон Pool/клиент между запросами; «просто добавить обработчик ошибки».
- **Паттерн:** время жизни пула — ровно один входящий запрос: создать в начале, переиспользовать внутри его цепочки вызовов, закрыть в finally. Полное пересоздание на каждый DB-вызов безопасно, но дорого при цепочках (18-22с вместо мс).

## Тест обнаружения
Любой будущий CF-сервис с постоянным соединением к БД: grep на `let .*: Pool | null = null` вне функций.
