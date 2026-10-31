---
id: DP.IWE.003
name: Gateway-архитектура IWE
type: domain-entity
status: active
created: 2026-03-31
updated: 2026-04-01
trust:
  F: 3
  G: domain
  R: 0.7
epistemic_stage: evidence
related:
  specializes: [U.System]
  uses: [DP.ARCH.001, DP.EXOCORTEX.001, DP.IWE.001, DP.IWE.002]
  enables: [DP.D.036]
---

# Gateway-архитектура IWE

## 1. Определение

Gateway-архитектура — паттерн развёртывания IWE, при котором пользователь подключается к платформе через единый MCP Gateway URL из любого AI-клиента, без обязательного использования VS Code или Claude Code CLI.

IWE при этом остаётся слоем: **git-репо пользователя + MCP Gateway + протоколы**. Клиент — сменная деталь.

> **Инстанс паттерна — Aisystant MCP (`mcp.aisystant.com`).** «Gateway» — архитектурный паттерн; конкретная реализация на домене — **Aisystant MCP**. Паттерн может быть реализован и другими инстансами; текущая реализация — Aisystant MCP.

## 2. Два режима подключения

| Режим | Аудитория | Точка входа | Что нужно пользователю |
|---|---|---|---|
| **Gateway** | Массовая (нетехническая) | Один URL + OAuth | Зарегистрироваться, подключить connector |
| **Direct MCP** | Технари | VS Code + Claude Code CLI | Настроить `.mcp.json` вручную |

Оба режима существуют параллельно. Gateway не вытесняет CLI — он расширяет аудиторию.

## 3. Три MCP в Gateway

| MCP | Слой | Данные | Изоляция |
|---|---|---|---|
| **knowledge-mcp** (платформенный) | L2 | ZP, FPF, SPF, Pack платформы, курсы + CLAUDE.md пользователя | Публичный + user-space через user_id |
| **digital-twin-mcp** (авторизованный) | L2 | ЦД пользователя (SurrealDB) | RLS по user_id, Ory OAuth |
| **personal-knowledge-mcp** (личный) | L4 | GitHub-репо пользователя + эмбеддинги на платформе | GitHub App token (repo-scoped) |

Весь Gateway — под Ory-авторизацией. Открытые (публичные) MCP подключаются напрямую, минуя Gateway.

## 4. Доставка CLAUDE.md (system prompt)

CLAUDE.md пользователя хранится в его git-репо. knowledge-mcp доставляет его как system prompt через MCP `prompts`/`resources` endpoint. Это обеспечивает работу протоколов ОРЗ и скиллов в любом клиенте — не только в Claude Code.

Механизм защиты: version pinning (git commit hash). Alert при изменении hash без явного деплоя.

## 5. Personal Knowledge MCP — архитектура данных

```
Git-репо пользователя (GitHub)
  └── Pack, CLAUDE.md, протоколы, заметки (Markdown)
         ↓ при write через MCP
personal-knowledge-mcp:
  1. GitHub API commit (данные остаются у пользователя)
  2. ingest_event() → Activity Hub (Event Bus, ADR-009)
  3. Vectorize → эмбеддинги на платформе (Neon pgvector → Qdrant)
         ↓
  MCP search(query, user_id) → RLS изолирует данные
```

**Принцип разделения:** данные (репо) у пользователя, эмбеддинги (производные) на платформе.

## 6. Онбординг

При регистрации платформа форкает шаблон IWE (FMT-exocortex-template) в GitHub-пространство пользователя через GitHub OAuth. Пользователь получает рабочую среду без ручной настройки.

**Требование:** для подключения personal-knowledge-mcp (личная база знаний) пользователю необходим **GitHub-аккаунт**. Без GitHub-аккаунта Gateway работает в режиме knowledge-mcp + digital-twin-mcp (платформенные знания + ЦД), но без личных знаний.

| Компонент Gateway | Требует GitHub? | Когда нужен |
|---|---|---|
| knowledge-mcp (платформенные знания) | Нет | Всегда доступен |
| digital-twin-mcp (ЦД) | Нет | T3+ (заполнить ЦД) |
| personal-knowledge-mcp (личные знания) | **Да** | T4 или Gateway с личной базой |

## 7. Связь с принципами DP.ARCH.001

| Принцип | Как реализуется |
|---|---|
| #6 Отчуждаемость | Данные в GitHub пользователя — уходит с данными |
| #8 Знания публичны, данные приватны | knowledge-mcp (публичный) ≠ DT-mcp (приватный) |
| #11 Per-user blast radius | GitHub App token repo-scoped, RLS по user_id |
| #13 ИИ-системы UI-agnostic | Gateway работает в любом клиенте |
| #15 Multi-surface | Gateway = новая поверхность наряду с ботом, Web App, CLI |

## 6a. Изоляция данных (multi-tenant)

**Принятое решение (АрхГейт 2026-04-01):** namespace per user в pgvector (фильтр по `user_id`).

| Фаза | Решение | Порог |
|------|---------|-------|
| **Сейчас → ~30к пользователей** | Namespace per user: фильтр `WHERE user_id = $1` + HNSW индекс на всю таблицу | 30к пользователей × ~1к векторов = 30М строк |
| **При росте >30к** | Миграция на Qdrant: collection per user, отдельный HNSW индекс на коллекцию | ADR при достижении порога |

**Обоснование:** pgvector с фильтром по `user_id` эффективен при ~30М строк. При превышении порога деградирует recall (ANN-поиск не партиционирован). Миграция на Qdrant — отдельное архитектурное решение, не требует изменения протокола MCP.

**Безопасность:** `user_id` берётся из JWT-токена (Ory), не из параметра запроса. SQL-инъекция исключена на уровне ORM.

## 6b. Переиндексация embeddings

**Принятое решение:** webhook-триггер при push в Pack-репо пользователя.

```
Push в Pack-репо (GitHub)
  → GitHub webhook → personal-knowledge-mcp
  → Задача в очередь (async)
  → Векторизация изменённых файлов
  → Обновление embeddings в pgvector/Qdrant
```

**Гарантии:**
- Пользователь не управляет индексом вручную
- Задержка переиндексации: целевое ≤5 мин после push
- Частичная переиндексация: только изменённые файлы (diff от предыдущего commit hash)
- При сбое: retry с backoff, alert в логах платформы

## 6c. Gateway latency SLA

| Компонент | Целевое |
|-----------|---------|
| Gateway overhead (auth + routing) | ≤200ms |
| Контекстный кэш (Pack не менялся) | ≤50ms (из кэша) |
| Инвалидация кэша | При push в репо (тот же webhook, §6b) |
| Полный путь вендорского AI → данные → ответ | ≤500ms (без LLM inference) |

**Кэш:** TTL определяется commit hash репо. При совпадении hash — отдаём из кэша без чтения файлов.

## 8. Gateway = полный T4 (принцип паритета)

**Принцип:** Gateway ДОЛЖЕН обеспечивать полный T4 — без CLI, без локальной среды. Пользователь через claude.ai/ChatGPT/Cursor получает тот же функционал, что и через Claude Code.

### 8.1. Разрыв и решение

| Возможность T4 | Direct MCP (CLI) | Gateway (текущий) | Gateway (целевой) |
|---|---|---|---|
| personal CLAUDE.md | ✅ нативно | ✅ knowledge-mcp prompts | ✅ |
| personal memory | ✅ файлы | ✅ knowledge-mcp resources | ✅ |
| ЦД read/write | ✅ MCP | ✅ MCP | ✅ |
| Поиск по знаниям | ✅ MCP | ✅ MCP | ✅ |
| **Агенты** (Стратег, Экстрактор, Синхронизатор) | ✅ Claude Code sub-agents | ❌ | ✅ **серверные агенты** через MCP tools |
| **git commit/push** | ✅ bash | ⚠️ personal-knowledge-mcp write | ✅ через MCP write → GitHub API |
| **WakaTime** | ✅ локально | ❌ | ✅ **серверный трекинг** через MCP tool |
| **Клуб** (publish) | ✅ CLI | ❌ | ✅ **MCP tool** `club_publish` (доступно с T3) |
| **Подключение к LLM-интерфейсам** | ✅ Claude Code нативно | ✅ MCP-коннектор (claude.ai, ChatGPT, Cursor, Gemini) | ✅ |
| **Персональное руководство** | ✅ через агентов | ❌ | ✅ серверно через MCP |

### 8.2. Серверные агенты

Агенты переносятся с локального Claude Code на платформу:

```
Сейчас (Direct MCP):
  Claude Code → skill "Стратег" → локальные файлы → git push

Целевое (Gateway):
  AI-клиент → MCP tool "run_strategist(params)" → 202 + run_id →
    agent-runner запускает агента серверно (Ory JWT) →
    LLM Proxy → tool_use → enforce_scope → GitHub App commit
  AI-клиент → MCP tool "get_run_status(run_id)" → status + result_url
```

**Реализация (WP-201 Ф3.5, 30 мая 2026):** три MCP tools зарегистрированы в Gateway:

| Tool | Семантика | Free? |
|---|---|---|
| `run_strategist(user_prompt, context_artifacts?, idempotency_key?)` | Async kick-off Стратега (R1 / DP.ROLE.012). 202 + run_id. | Требует подписку |
| `run_extractor(user_prompt, context_artifacts?, idempotency_key?)` | Async kick-off Экстрактора (DP.ROLE.027). 202 + run_id. | Требует подписку |
| `get_run_status(run_id)` | Sync GET статуса run + result_url при completed. | **Free** для authenticated (read-only, не тратит LLM) |

**Auto-onboarding (Ф4):** webhook `installation_repositories.added` → gateway-mcp параллельно создаёт `user_sources` (для индексации) и `agent_scopes_mvp` (для агентов) через `POST /v1/admin/scope-provision` agent-runner. Пилоту не нужен manual SQL.

Пользователю не нужен CLI — агенты работают на стороне платформы, результат коммитится в его GitHub-репо, ссылка возвращается в `result_url` через `get_run_status`.

### 8.3. Платформенный LLM как сервис

**Решение:** платформа предоставляет доступ к AI-моделям (LLM) как сервис. Пользователю НЕ нужен личный API-ключ. Платформа проксирует вызовы через свои ключи, выбирая оптимальную модель для задачи.

**Архитектура:**

```
Пользователь (бот / Gateway / Claude Code)
  → Платформенный LLM Proxy (Ory-авторизация, user_id)
    → Роутинг: задача → оптимальная модель (Claude/GPT/другие)
    → Учёт токенов per user_id
    → Ответ пользователю
```

| Режим | LLM доступ | Лимит | Оплата |
|---|---|---|---|
| Trial (30 дней) | ✅ Платформенный | Базовый (достаточно для знакомства) | Платформа покрывает |
| Подписка БР | ✅ Платформенный | Расширенный по тарифу | Включено в подписку |
| Превышение лимита | ✅ Платформенный | Докупить пакет токенов | Доп. оплата |
| Direct MCP (T4) | Платформенный или личный | По выбору | Пользователь выбирает |

**Зачем для Gateway:** пользователь подключает Gateway URL к claude.ai/ChatGPT — но серверные агенты и MCP tools работают через **платформенный ключ**, а не через клиент пользователя. Это позволяет:
- Агентам работать серверно (§8.2) с гарантированным доступом к LLM
- Оптимизировать стоимость через routing (дешёвые модели для простых задач, мощные — для сложных)
- Контролировать качество (одна модель для ЦД, другая для поиска, третья для агентов)

Лимиты токенов — часть Billing Module (DP.SC.112). Мониторинг: usage per user_id, alert при превышении порога.

## 10. Единственная ответственность Gateway (ADR, WP-402)

> **Источник:** ИТ-встреча 07.06.2026 (Андрей Смирнов) + peer-сессия WP-402 (Claude + Kimi, 08.06.2026).
> **Статус:** принято. Защищает паттерн от рецидива — backend-state в gateway.

### 10.1. Тест единственной ответственности

**Тест Андрея (дословно):** посмотри на конфиги gateway — если там только URL бэкендов (три MCP-сервера) → правильный gateway. Если там БД, GitHub-токены, что угодно кроме URL → gateway взял на себя прикладную логику.

**Аналогия:** регулировщик только направляет, не печёт пирожки.

### 10.2. Принцип-арбитр

> **Gateway маршрутизирует ПО правилам, но не ВЛАДЕЕТ состоянием правил.**

Разрешает кажущийся конфликт «маршрутизация — функция gateway, значит таблица маршрутов имеет право жить в gateway»:

- Gateway **делает** fan-out routing по списку backends для конкретного `user_id` — это его роль.
- Gateway **не делает** CRUD состояния «какой backend привязан к какому пользователю» — это прикладные данные.
- Источник истины состояния (таблица) принадлежит **control-plane** (отдельный сервис). Gateway получает готовый список backend-URL по HTTP (`GET /backends/{userId}`) и роутит. В конфиге gateway — `CONTROL_PLANE_URL` (ещё один URL), не `REGISTRY_DB_URL` (Neon-коннект).

Тот же паттерн применяется к subscription (фаза Р4): источник истины (подписка) вне gateway, gateway читает claim из JWT (инжектится Ory token hook через `HYDRA_HOOK_SECRET`) + graceful degradation (expired → 401 → silent refresh), не из `SUBSCRIPTION_DATABASE_URL`. **Выполнено (WP-402 Р4, 2026-06-08):** `SUBSCRIPTION_DATABASE_URL` убран из роутинг-пути gateway; token hook (`/hydra-hook/token`) читает БД как endpoint выдачи claims — легитимный остаток, признанный в WP-402 Р7.**

### 10.3. Граница ответственности

| Остаётся в Gateway (маршрутизация) | Выносится (прикладная логика / БД) |
|---|---|
| Ory JWT auth | `scope.ts` + `provisionBridgeScopes` — bridge write-scope и provisioning (INDICATORS БД) → `bridge-scope-service` (WP-402 Р1, завершено 2026-06-09) |
| Fan-out по backend-URL | `agent-status.ts` — agent registry (БД) → `agent-status-service` (WP-402 Р2) |
| Rate-limit, circuit-breaker | `backend-registry.ts` — BYOB per-user (БД) → control-plane (удалён как dead weight, WP-402 Р3) |
| `knowledge-gate.ts` — HTTP-валидация backend (БД нет) | subscription/tier — переведено на JWT-claim (WP-402 Р4) |
| `agent-tools.ts` — JSON-схемы proxy (БД нет) | GitHub webhook handler — installations БД → `github-integration-service` (WP-402 Р6) |
| `tool-tiers.ts` — tier-policy (pure-function, БД нет) | `get_user_context`, BYOK, consent, cognitive-brief → `user-profile-service` / `learning-context-service` (WP-402 Р8–Р9) |
| Hermes proxy (`HERMES_RUNTIME_URL` — URL, не Neon), IWE system prompt (~700 строк статики) | BYOK-management (`list/grant/revoke_llm_key`) → `user-profile-service` (WP-402 Р11) |

**Выполнено (WP-402, 2026-06-09):** gateway на роутинг-пути не имеет Neon-коннектов. `INDICATORS_DATABASE_URL`, `SUBSCRIPTION_DATABASE_URL` (роутинг), `DATABASE_URL` (роутинг, кроме token hook), `LEARNING_DATABASE_URL` убраны. Остаётся `SUBSCRIPTION_DATABASE_URL` только в token hook endpoint (`/hydra-hook/token`) — endpoint выдачи claims, не роутер, признан легитимным остатком в WP-402 Р7.

**Критерий выноса (однозначный):** модуль открывает соединение с Neon → не gateway. Исключение отсутствует: `knowledge-gate.ts`, `tool-tiers.ts`, Hermes proxy, IWE system prompt работают без Neon (HTTP-валидация / pure-function / URL-proxy / статика) и потому остаются — это подтверждает критерий, а не нарушает его. *Чистка index.ts от объёмной статики — отдельный refactor-РП (не нарушение принципа, поэтому вне scope WP-402).*

### 10.4. BYOB и control-plane (двухтактно)

- **Такт 1 (WP-402):** `backend_registry` сейчас — задел (0 строк в проде, env `REGISTRY_DB_URL` помечен `optional until BYOB is live`, [DP.D.036](../02-domain-entities/DP.D.036-byob-knowledge-architecture.md) status=draft). Удаляется из gateway как dead weight; fan-out остаётся на статических backends из env. Удаление, не миграция — мигрировать нечего.
- **Такт 2 (BYOB в прод, отдельная фаза):** control-plane владеет `backend_registry`; gateway читает `GET /backends/{userId}`. BYOB работает без редеплоя gateway — динамика на стороне control-plane.

### 10.5. Развёртывание без downtime

Blue/green с health-check вместо in-place миграции: gateway v2 поднимается отдельным контейнером; health-check `/health` возвращает 200 только если успешно забиндил backend-URL из env (рантайм-проверка теста §10.1); оркестратор переключает трафик после успешного health-check; rollback мгновенный.

### 10.6. Результат WP-402 Р16: роутинг-путь полностью без DB-fallback

`validateOryToken` — итоговое состояние после WP-402 Р16 (2026-06-09):

| Путь | Тип токена | Логика подписки | Статус |
|------|-----------|-----------------|--------|
| Try0 (JWT) | JWT access token | Claim `ext.has_subscription` из Hydra hook (Variant D), всегда boolean. `?? false` для legacy-токенов. | ✅ завершено |
| Try1 (opaque) | Opaque access token | `hasSubscription` выводится из тира через `user-profile-service /tier`: T2/T3/T4 → true, T1 → false. Один HTTP-вызов вместо DB+HTTP. | ✅ завершено |
| Try2 (Kratos) | Kratos session | Удалён. Подтверждено мёртвым кодом — ни бот, ни браузер, ни другие клиенты не несут Kratos session token в gateway. | ✅ удалён |

**`SUBSCRIPTION_DATABASE_URL` остаётся только в Hydra token hook** (`/hydra-hook/token`) — endpoint выдачи claims, не роутинг-путь. Это легитимный остаток, зафиксированный в §10.4.

## 9. Связанные документы

- **[DP.IWE.013](DP.IWE.013-iwe-architecture.md)** — архитектура IWE: функциональные подсистемы, модули, системы окружения и размещение; сверка с этим документом — там §11.
- [DP.ARCH.001](DP.ARCH.001-platform-architecture.md) — архитектура платформы (принципы ЭМОГССБ)
- [DP.EXOCORTEX.001](DP.EXOCORTEX.001-modular-exocortex.md) — модульный экзокортекс
- [DP.IWE.001](DP.IWE.001-intelligent-working-environment.md) — IWE как концепция
- [DP.IWE.002](DP.IWE.002-iwe-template-and-setup.md) — шаблон и setup
- [DP.D.036](../02-domain-entities/DP.D.036-byob-knowledge-architecture.md) — BYOB Knowledge Architecture
