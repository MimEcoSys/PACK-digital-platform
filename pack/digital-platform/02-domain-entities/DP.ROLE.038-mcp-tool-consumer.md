---
id: DP.ROLE.038
name: Подборщик инструментов
name_ru: Подборщик инструментов
name_en: MCP Tool Consumer
aliases:
  - MCP Tool Consumer
type: role-description
status: draft
valid_from: 2026-05-11
summary: "Посредник между LLM-клиентом (бот) и платформенными MCP-серверами: загружает актуальный список tool через discovery (tools/list), кэширует с TTL, фильтрует по tier, передаёт в Claude API без hardcoded списков в коде."
related:
  specializes: [U.RoleAssignment]
  realizes: [DP.SC.129]
  uses:
    - DP.SC.025   # capture-bus для логирования fallback-событий
created: 2026-05-11
updated: 2026-11-22
wp: WP-5
---

# Подборщик инструментов (DP.ROLE.038)

> **Прежнее имя** — «MCP Tool Consumer»; переименовано решением пилота 22.11.2026 (DP.ROLE.001 §3.6, РП-616 Ф4).

<!-- see DP.SC.129, WP-5 #16 -->

> **Kind:** Platform Client Role — клиентская роль платформы, посредник между LLM и инструментарием MCP-серверов.
> **Owner Role:** Платформенная команда (Архитектор + R21 Publisher как стейкхолдер).

## 1. Миссия

Быть **единственным посредником** между LLM-клиентом (бот, экзокортекс, web-app) и актуальным инструментарием платформенных MCP-серверов. Гарантировать: LLM всегда получает актуальный, tier-отфильтрованный список tool без жёстко закодированных JSON-схем в коде клиента.

**Граница:** только discovery и tier-фильтрация. НЕ интерпретирует результаты вызовов tool (это LLM), НЕ маршрутизирует вызовы (это gateway_mcp._call), НЕ хранит историю вызовов.

## 2. Обязанности

| Обязанность | Метод | Триггер |
|-------------|-------|---------|
| Bootstrap-загрузка списка tool | JSON-RPC `tools/list` на каждый MCP-сервер | Старт процесса клиента |
| TTL-обновление кэша | Background refresh (fire-and-forget) | `cache.timestamp + 15min < now()` при входящем запросе |
| Tier-фильтрация | По naming convention: `admin_*` → только T4, `subscriber_*` → T2+, остальные → все | При каждом `get_for_tier(tier)` |
| Fallback при недоступности MCP | Last-known-good кэш (TTL до 1h) или пустой список | MCP-сервер недоступен или timeout |
| Логирование fallback-событий | `phase: "mcp_discovery_fallback"` через capture-bus | При использовании stale-кэша |

## 3. Полномочия

- **Вызывает** `tools/list` на платформенных MCP-серверах (Aisystant MCP, personal-knowledge-mcp, gateway-mcp).
- **Читает** tier пользователя из профиля (T0–T4).
- **Пишет** в in-memory `tools_cache` (одна запись на MCP-сервер, timestamp + list).
- **Не вызывает** сами tool (это LLM через gateway_mcp._call).
- **Не хранит** состояние между перезапусками процесса (кэш in-memory, не Redis).

## 4. Границы роли

| Делает | НЕ делает |
|--------|-----------|
| Discovery через `tools/list` | Не hardcode-ит JSON-схему ни одного tool |
| Tier-фильтрация на стороне клиента (defense in depth) | Не заменяет server-side access control |
| Background refresh (не блокирует текущий запрос) | Не ждёт завершения refresh перед ответом LLM |
| Fallback на кэш при network fail | Не выбрасывает исключение если кэш stale > 1h — возвращает пустой список |
| Оставляет hybrid-обёртки (knowledge_search с 401-fallback) вне своей логики | Не ломает существующие hardcoded обёртки при переходе |

## 5. Артефакты

**Входы:**
- `tools/list` JSON-RPC response от каждого MCP-сервера (список ToolDescriptor с name, description, inputSchema)
- Tier пользователя (T0–T4)

**Выходы:**
- `List[ToolDescriptor]` — tier-отфильтрованный список для передачи в Claude API как `tools=[...]`
- Лог-событие `mcp_discovery_fallback` при использовании stale-кэша

## 6. Носители (carriers)

**Реализация в текущем клиенте (aist_bot):**
- `clients/gateway_mcp.py` — метод `list_tools() -> List[ToolDescriptor]` + `_tools_cache: ToolsCache`
- `engines/shared/consultation_tools.py` — функция `get_tools_for_tier(tier, user_id)` заменяет статические TOOL_* константы

**Решение по Q1 (cache location):** in-memory достаточно для single-instance бота; при переходе на multi-instance — shared Redis через DP.ARCH.004, но не сейчас.

**Решение по Q3 (tier-фильтр):** naming convention (`admin_*`, `subscriber_*`) — без изменений Aisystant MCP API. Если понадобится гранулярность — расширить до явных тегов (`tags: ["free", "subscriber"]`) в tool-descriptor на сервере; это backward-compatible.

## 7. Метрики

- `mcp_tools_list_duration_ms{mcp_server}` — время одного `tools/list` roundtrip
- `mcp_tools_cache_hit_rate` — доля запросов из кэша (цель > 90%)
- `mcp_tools_count{mcp_server, tier}` — количество доступных tool на tier
- `mcp_discovery_fallback_total` — счётчик использований stale-кэша

## 8. Связи

- **Реализует:** [DP.SC.129](../08-service-clauses/DP.SC.129-generic-mcp-tool-discovery.md) Generic MCP Tool Discovery
- **Использует:** DP.SC.025 capture-bus для fallback-логирования
- **Носитель:** R21 Publisher (бот @aist_me_bot, @aist_pilot_me)
- **WP:** WP-5 #16

## 9. Открытые вопросы

~~Q2 из DP.SC.129~~ — закрыт: роль владеет discovery (это DP.ROLE.038), не R21 Publisher напрямую.
~~Q1~~ — закрыт: in-memory кэш для single-instance.
~~Q3~~ — закрыт: naming convention, с явным путём расширения до тегов.

Остаётся до ArchGate Ф4:
- Нужен ли ArchGate для self-scoring ЭМОГССБ перед реализацией, или хватает IntegrationGate Ф1-Ф3? (DP.SC.129 не требует полного ArchGate, но Безопасность §Б чеклиста — да, т.к. tier-фильтрация = access control).
