---
id: DP.SC.034
name: Local MCP Gateway для multi-agent VS Code
name_ru: Local MCP Gateway для multi-agent VS Code
name_en: Local MCP Gateway for multi-agent VS Code
type: sc
status: draft
layer: L4-Personal
summary: "Peer-агент (Claude Code, Kimikode и т.п.) в одной VS Code сессии получает гарантию: tool-вызовы маршрутизируются через единую точку, конфликт записи в один файл предотвращается pessimistic-lock'ом, новый агент подключается без правки кода других агентов."
consumer: DP.ROLE.039 Peer Agent (Claude Code, Kimikode и др.)
created: 2026-05-11
updated: 2026-05-11
related:
  realizes: [DP.IWE.005]
  uses: [DP.SC.023, DP.SC.129]
  distinct_from: [DP.IWE.003]
  role: DP.ROLE.039
wp: WP-150 Ф6
---

# [DP.SC.034] Local MCP Gateway для multi-agent VS Code

> **Различение:** этот Gateway — **локальный, in-process, single-user, multi-agent** слой внутри VS Code. Не путать с DP.IWE.003 / Aisystant MCP — облачным multi-tenant Gateway на `mcp.aisystant.com` для внешних AI-клиентов. См. `~/IWE/.claude/rules/distinctions.md` → «Local Gateway (DP.IWE.005) ≠ Cloud Gateway (DP.IWE.003 / Aisystant MCP)».

## Правило (инвариант)

> Что ВСЕГДА должно выполняться. Нарушение = провал SC.

- В одной VS Code сессии **никогда** два peer-агента одновременно не пишут в один файл (pessimistic lock at file level).
- Tool-вызов от любого peer-агента проходит через Gateway — нет прямого доступа к платформенным tool'ам в обход.
- Добавление нового peer-агента не требует правки кода других агентов (только конфигурация tool-allowlist в Gateway).
- При недоступности Gateway peer-агенты получают понятный error, не падают в undefined behavior.
- Tool-allowlist на peer-агента детерминирован (одинаковый allowlist → одинаковый видимый набор tool'ов).

## Обещание

**Кому:** DP.ROLE.039 Peer Agent (Claude Code, Kimikode и др.) при работе в одной VS Code сессии.

**Зачем:** Два peer-агента в одном workspace без координации создают race-condition: одновременная запись в файл, повреждение состояния, дублирование работы. Tool-allowlist без единой точки = расползание прав агента (каждый видит «всё» по умолчанию).

**Что получит:**
- Один URL/endpoint для tool-вызовов (одинаковый для всех peer-агентов в сессии).
- Tool-allowlist, отфильтрованный по identity агента (Claude видит свой набор, Kimikode — свой; пересечение — общие tool'ы вроде `read_file`).
- Lock-acquisition API для exclusive write (acquire → write → release).
- Lock-status API для проверки «кто сейчас держит file»? (для координации до lock collision).
- Conflict event при попытке записи в locked-файл (структурированный error с информацией о держателе lock).

**Триггер:** Peer-агент вызывает tool через MCP-стандарт `tools/call`.

**Время отклика:**
- Tool routing overhead: ≤50ms (in-process / Unix socket, не HTTP).
- Lock acquisition: ≤20ms (in-memory dictionary с TTL).
- Lock collision response: немедленно (один JSON-RPC roundtrip).

**Режим отказа:**
- Gateway недоступен (процесс не запущен) → peer-агент получает MCP `transport_error` с инструкцией «start local gateway».
- Tool отсутствует в allowlist агента → MCP `tool_not_available` (не `internal_error`, чтобы агент не интерпретировал как баг).
- Lock collision → MCP `tool_call_error` с payload `{holder: "kimikode", file: "src/foo.py", acquired_at: "..."}`.
- Сетевой fail к внешним MCP (Aisystant MCP) при routing-through → fallback: peer-агент получает `mcp_upstream_unavailable`, может работать с local-only tool'ами.

**Безопасность (раскрытие для потребителя):**
- Local Gateway = trust boundary **одного пользователя**. Между peer-агентом и Gateway нет аутентификации — доверие на уровне ОС (filesystem perms для сокета / loopback-bind для TCP).
- **MITM при upstream-proxy:** если peer-агент через Gateway вызывает upstream tool (например, `knowledge_search` на Aisystant MCP), Gateway видит credentials (OAuth токены и т.п.) peer-агента в открытом виде. Это **сознательный дизайн** внутри trust boundary одного пользователя; не использовать Local Gateway в окружении, где Gateway-процесс не контролируется владельцем workspace.
- **PII в логах:** Gateway пишет в лог только `tool_name + agent_id + duration`, не содержимое аргументов/ответов.
- **Tier-фильтрация:** не Local Gateway (это про single-user); tier — в upstream (DP.ROLE.038).

## Свидетельства (критерий приёмки)

**Данные** (что фактически существует):

| Критерий | Как проверить |
|----------|--------------|
| Gateway процесс запущен | `lsof -i :PORT` или `ps | grep iwe-local-gateway` показывает один процесс |
| Tool-allowlist детерминирован | Два последовательных `tools/list` от одного peer-агента → одинаковый набор |
| Lock-state видим | `gateway_status` tool возвращает `{locks: [{file, holder, acquired_at}]}` |
| Lock collision → правильный error | Два write в один файл от разных peer → второй получает `tool_call_error` с holder info |
| Новый агент без правок других | Подключение третьего peer-агента к Gateway → существующие Claude/Kimikode не перезапускаются |

**Контекст** (при каких условиях обещание действует):

| Условие | Проверка |
|---------|---------|
| VS Code сессия активна (workspace открыт) | `code` процесс запущен |
| Все peer-агенты подключены к одному Gateway endpoint | у каждого agent.config — один и тот же `gateway_url` |
| Pre-flight `gateway_status` отвечает | первый запрос от агента возвращает 200 |

**Полномочия** (кто уполномочен подтвердить):

| Роль | Что подтверждает |
|------|-----------------|
| DP.ROLE.039 Peer Agent | Корректность tool routing для своего allowlist |
| Платформенная команда (Архитектор) | Архитектурную целостность (in-process / socket, не HTTP) |
| R23 Верификатор (Haiku) | Формальное соответствие чеклисту приёмки |

**Свидетельства** (как узнать, что обещание выполнено):

| Свидетельство | Источник |
|--------------|---------|
| Лог Gateway процесса | `~/.iwe/gateway.log` (структурированный JSONL, append-only) |
| Метрика `gateway_tool_call_count{agent, tool}` | `gateway_metrics` MCP tool (in-process) или `~/.iwe/gateway-metrics.json` (sampling 1s) |
| Метрика `gateway_lock_collision_total{file, holders}` | то же |

## Реализующие сервисы

| Сервис | Роль | Триггер |
|--------|------|---------|
| `iwe-local-gateway` (новый процесс) | Tool routing + lock manager | 👤 запуск из VS Code task / 🤖 auto-start при первом подключении |
| `gateway_status` tool | Видимость состояния (locks, agents, tools) | 👤 peer-агент запрашивает |
| `acquire_file_lock` / `release_file_lock` tool | Pessimistic lock API | 🤖 wrapper в `write_file` peer-агента |
| Aisystant MCP (опционально как upstream) | Routing к облачным tool (knowledge_search, dt_*) | 🤖 если peer-агент запрашивает upstream tool |

## Пользовательский путь (happy path)

| # | Шаг | Кто | Инструмент |
|---|-----|-----|-----------|
| 1 | Открывает VS Code в IWE-workspace | Пилот | VS Code |
| 2 | Gateway auto-start (или запуск из VS Code task) | Пилот / system | `iwe-local-gateway` |
| 3 | Claude Code подключается к Gateway | Claude Code | MCP `initialize` через socket |
| 4 | Kimikode подключается к тому же Gateway | Kimikode | MCP `initialize` через socket |
| 5 | Claude вызывает `acquire_file_lock("src/foo.py")` | Claude Code | MCP `tools/call` |
| 6 | Claude пишет в `src/foo.py` через `write_file` | Claude Code | MCP `tools/call` |
| 7 | Kimikode пробует `write_file("src/foo.py")` → получает `tool_call_error` с holder=claude | Kimikode | MCP `tools/call` |
| 8 | Kimikode ждёт или работает с другим файлом | Kimikode | MCP `tools/call` |
| 9 | Claude вызывает `release_file_lock("src/foo.py")` | Claude Code | MCP `tools/call` |
| 10 | Kimikode успешно пишет в `src/foo.py` | Kimikode | MCP `tools/call` |

## Сценарии использования (минимум 3)

### Сценарий 1: Parallel work на разных файлах

Claude рефакторит `src/auth.py`, Kimikode пишет тесты в `tests/test_auth.py`. Каждый держит lock на свой файл. Конфликта нет. Sync через git sequential commits (peer-agent choreography, см. DP.SC.035).

### Сценарий 2: Lock collision → graceful retry

Оба агента независимо приняли решение редактировать `src/index.ts`. Claude приходит первым, получает lock. Kimikode получает `tool_call_error` с holder=claude → реагирует: либо ждёт `release` (polling `gateway_status` с backoff), либо переключается на другой файл из своего todo и повторяет попытку через 2 минуты.

### Сценарий 3: Подключение третьего агента без правок

Пилот хочет добавить Aider (новый peer-агент) в сессию. Действия:
1. Запускает Aider с конфигом `gateway_url=...`
2. Aider вызывает `tools/list` → видит allowlist (configured platform-side в `~/.iwe/gateway-config.yaml`)
3. Claude и Kimikode продолжают работу без перезапуска

## Связь с другими обещаниями

- Реализует: **DP.IWE.005** (Local Gateway Pack-сущность)
- Использует: **DP.SC.023** (mcp-extensibility — расширяемость tool-набора)
- Использует: **DP.SC.129** (generic-mcp-tool-discovery — для allowlist на агента)
- Отличается от: **DP.SC.021** (свои знания через облачный сервер МИМ с подпиской, не локальная маршрутизация)
- Парный SC: **DP.SC.035** (peer-agent-choreography — turn-based протокол поверх Gateway)
- Не пересекается с: **DP.IWE.003 / Aisystant MCP** (другой паттерн, другая аудитория)

## Открытые вопросы (для реализации, не блокируют спецификацию)

1. **Transport:** Unix socket vs TCP localhost vs in-process? — рекомендация Unix socket (нет конфликта портов, права через filesystem).
2. **Auto-start:** VS Code extension hook или systemd-style launchd plist? — позже, после первой ручной интеграции.
3. **Lock granularity:** только файлы, или ещё директории/глобы? — старт только с файлов; директории — расширение.
4. **TTL на lock:** автоматический release через N минут, чтобы зависший агент не блокировал навсегда? — да, default 5 минут с warning лог-событием.
5. **Persistence locks между перезапусками Gateway:** нужна ли? — нет, lock = эфемерное состояние, перезапуск Gateway = «всё свободно».
