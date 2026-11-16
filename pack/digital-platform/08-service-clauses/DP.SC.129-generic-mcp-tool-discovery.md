---
id: DP.SC.129
name: Generic MCP Tool Discovery (бот → платформенные MCP)
type: sc
status: draft
layer: L2-Platform
summary: "Бот получает актуальный список tool из платформенных MCP при старте и периодически, без hardcoded списков в коде"
consumer: R21 Publisher (бот) + любой LLM-клиент платформы
created: 2026-05-11
updated: 2026-11-16
wp: WP-5
related:
  realizes:
    - DP.ARCH.001  # эволюционируемость L2 платформы
  uses:
    - DP.SC.025    # capture-bus (для логирования fail-loadов)
  extends: []
---

# [DP.SC.129] Generic MCP Tool Discovery

<!--
  WP-5 #16. Решает: добавление tool на сервер Aisystant MCP не должно
  требовать N правок в каждом LLM-клиенте (бот, web-app, экзокортекс).
  Корень: hardcoded TOOL_* descriptors + Python-обёртки `_call(name, args)`.
-->

## Правило (инвариант)

- [ ] LLM-клиент **не содержит** hardcoded списка tool-name/JSON-Schema из MCP-сервера. Список tool строится в runtime через `tools/list` JSON-RPC.
- [ ] Новый tool на платформенном MCP-сервере становится доступен LLM-клиенту **без правок кода клиента** (только перезапуск/кэш-инвалидация).
- [ ] Fallback при недоступности MCP-сервера: клиент использует кэшированный список tool (TTL ≤ 1h) или подмножество, помеченное `essential: true`.
- [ ] Tier-фильтрация tool происходит **на стороне клиента** через naming convention (`admin_*`, `subscriber_*`) или явные теги в tool-descriptor, а не через ручной список allowlist.

## Обещание

**Держит:** владелец РП-5 (назначено пилотом 16.11.2026). Обещание остаётся черновиком до живого подтверждения третьего условия правила: 29.10, 02.11 и 04.11 после запуска бота список инструментов загружался пустым; исправление выпущено 09.11 (aist_bot PR #372 в пилотного бота, PR #378 в боевого), отсутствие пустых загрузок после него не проверено, заявка — во входящих РП-5.

**Кому:** LLM-клиенты платформы (R21 Publisher / @aist_me_bot, @aist_pilot_me; будущие web-app, экзокортекс)

**Зачем:** Эволюционируемость L2 — добавление новой возможности на сервере (новый tool) распространяется на всех клиентов автоматически. Сейчас 3 новых concept-tool Aisystant MCP (`knowledge_concept_status`, `knowledge_concept_search_by_name`, `knowledge_concept_expand`) недоступны боту, потому что в `engines/shared/consultation_tools.py` прописан hardcoded список.

**Что получит:** Метод `get_available_tools(tier, user_id) -> List[ToolDescriptor]`, возвращающий JSON-Schema совместимый список из платформенных MCP, отфильтрованный по tier пользователя. Список передаётся в Claude API как параметр `tools=[...]`.

**Триггер:**
- При старте клиента — bootstrap-загрузка
- При первом обращении пользователя после рестарта — lazy refresh
- Периодически — TTL-обновление кэша (раз в 15 мин)

**Время отклика:** ≤500ms для cached lookup, ≤3s для cold load (network roundtrip к MCP-серверу).

**Режим отказа:**
- MCP-сервер недоступен → клиент использует last-known-good кэш (TTL до 1h)
- Кэш пуст + сервер недоступен → клиент возвращает пустой список + логирует error; LLM работает без tool (degraded mode), отвечает текстом
- Tool возвращает 5xx → клиент помечает tool как stale, ретраит со следующего round

## Свидетельства (критерий приёмки)

**Данные:**

| Критерий | Как проверить |
|----------|--------------|
| `consultation_tools.py` не содержит hardcoded TOOL_* descriptors | `grep -E "TOOL_SEARCH_KNOWLEDGE\|TOOL_SEARCH_GUIDES\|TOOL_GET_BOT_INFO" engines/shared/consultation_tools.py` → 0 матчей |
| Новый tool на MCP-сервере появляется у бота без правок кода | Развернуть `knowledge_concept_status` на mcp.aisystant.com → бот вызывает tool при подходящем вопросе |
| Cache TTL соблюдается | `tools_cache.timestamp + 15min > now()` для всех cached записей |

**Контекст:**

- Применимо для платформенных MCP (Aisystant MCP, personal-knowledge-mcp, gateway-mcp)
- Не применимо для tool, требующих кастомной обёртки (например, `knowledge_search` с fallback на anonymous retry при 401 — оставить hardcoded как hybrid)

**Полномочия:**

- Клиент может вызывать только tool, доступные для его tier (T0-T4)
- Tier-фильтрация — на стороне клиента (defense in depth поверх server-side check)

**Свидетельства (наблюдаемость):**

- OTel span `mcp.tools.list` на каждый refresh — duration, tool_count, source_mcp
- Метрика `mcp_tools_cache_hit_rate` (Langfuse / Prometheus)
- Лог `phase: "mcp_discovery_fallback"` при использовании stale-кэша

## Сценарии использования

### Сценарий 1: Бот на старте (bootstrap)

**Кто:** @aist_pilot_me / @aist_me_bot при запуске процесса
**Когда:** один раз в начале жизни процесса
**Что делает:**
1. Вызывает `gateway_mcp.list_tools()` → внутри `tools/list` на Aisystant MCP + personal-knowledge-mcp
2. Заполняет `tools_cache` с timestamp
3. Готов отвечать на сообщения с актуальным списком tool

**Что делает с результатом:** При входящем сообщении передаёт `tools=tools_cache.get_for_tier(user.tier)` в Claude API.

### Сценарий 2: Lazy refresh после TTL

**Кто:** тот же бот, в момент входящего сообщения
**Когда:** `tools_cache.timestamp + 15min < now()`
**Что делает:**
1. Background refresh (fire-and-forget): загружает новый список с MCP
2. Возвращает текущий cached список для текущего сообщения (не блокирует)
3. Следующее сообщение получит обновлённый список

### Сценарий 3: Развёртывание нового tool

**Кто:** разработчик Aisystant MCP добавил новый tool `knowledge_concept_dependencies`
**Когда:** после `wrangler deploy` knowledge-mcp
**Что происходит:**
1. Через ≤15 мин (TTL) бот автоматически подхватывает новый tool
2. LLM в боте видит его в `tools=[...]` при следующем вопросе пользователя
3. Если вопрос подходит под описание tool — LLM вызывает его без отдельной правки промптов

**Тест приёмки:** Развернуть тестовый tool `_smoke_test_tool` с описанием «возвращает строку 'hello'» → ≤15 мин любой пилот, спросивший бота `вызови smoke test tool`, получает ответ через tool-вызов.

## Связи с другими SC

- **DP.SC.025 (capture-bus):** все fail-load события `mcp_discovery_fallback` пишутся через capture-bus в incident-log
- **DP.SC.128 (club-ingest):** для будущей публикации новых tool из club-ingest сервиса — тот же discovery механизм
- **DP.ARCH.001 (платформенная эволюционируемость):** generic discovery — конкретная реализация принципа «новая фича на сервере распространяется на всех клиентов»

## Антипаттерны

- ❌ **Static fallback в коде клиента:** «если MCP вернул пустой список — используй этот hardcoded минимум». Минимум устаревает.
- ❌ **Тier через server-side filter без клиентского guard:** server-side фильтрация — UI hint, не security boundary; клиент обязан проверять.
- ❌ **Eager refresh на каждое сообщение:** убивает p99 латентность бота (4-5s overhead).
- ❌ **Без TTL:** stale-tool, удалённый с сервера, продолжает использоваться LLM.

## Открытые вопросы (на ArchGate)

~~Q1~~, ~~Q2~~, ~~Q3~~ — закрыты, см. [DP.ROLE.038](../02-domain-entities/DP.ROLE.038-mcp-tool-consumer.md) §9.

## ArchGate (2026-07-07, peer-сессия с Kimi, WP-5)

**Вердикт:** полный профиль ЭМОГССБ (7 характеристик, NBR, DRR) избыточен для этого решения. Единственная блокирующая ось — Безопасность (новый риск, которого не было при hardcoded списке: tool-descriptor приходит из сети и становится частью системного промпта без код-ревью — потенциальный вектор prompt-injection). Обучаемость/Наблюдаемость/Интероперабельность материально затронуты, но закрываются точечными критериями приёмки, не отдельными архитектурными осями.

**Security Gate §Б — блокирующая ось, обязательна перед Ф4-Ф7:**
- **Б.x Tool-descriptor validation:** ответ `tools/list` валидируется по JSON Schema; поле `description` санитизируется и ограничивается по длине; blocklist опасных маркеров; источник — только доверенный MCP endpoint из allowlist.
- **Б.y Defense-in-depth для tier-filter:** server-side tier check остаётся первичным барьером; клиентская фильтрация (naming convention, см. DP.ROLE.038 §7) — только UX-оптимизация, не единственная граница доступа.

**Информационные критерии приёмки Ф6 (не блокер, но обязательны к проверке):**
- **L2.7 Интероперабельность:** клиент tolerant-обрабатывает отсутствие optional-полей (например `tags`) в ответе одного из MCP-серверов и graceful-деградирует для этого сервера, не роняя весь список инструментов.
- **L2.2 Наблюдаемость:** discovery убирает естественный сигнал регресса (раньше — деплой бота с diff'ом, теперь новый инструмент появляется без единого деплоя бота). Митигация — tool-call лог включает user query + снапшот доступных tools на момент вызова (`tools_snapshot_id`/timestamp кэша) + выбранный tool + результат, ретеншн 7-30 дней (переиспользует существующую лог-инфраструктуру бота, не новая система). Acceptance: можно воспроизвести решение LLM после истечения TTL кэша.

**Источник:** `sessions/2026-07/2026-07-07-09-archgate-mcp-tool-discovery/report.md`, `decisions/decision-log-2026-07.md`.
