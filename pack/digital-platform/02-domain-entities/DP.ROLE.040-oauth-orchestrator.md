---
id: DP.ROLE.040
name: OAuth Orchestrator (единая точка OAuth-flows для всех каналов IWE)
type: role-description
status: draft
valid_from: 2026-05-12
summary: "Сервис-роль: принимает OAuth setup/callback запросы от web/vscode/bot каналов, разрешает identity (Ory > telegram > github), управляет state-token lifecycle, координирует token exchange с провайдерами (GitHub App, Linear, Twin, Google Cal, WakaTime, Ory), хранит токены encrypted-at-rest в Neon. Не зависит от bot process."
related:
  specializes: [U.RoleAssignment]
  realizes: [DP.SC.130]
  uses:
    - DP.SC.025   # capture-bus (failure logging)
    - DP.SC.130   # OAuth Gateway SC
created: 2026-05-12
updated: 2026-11-14
wp: WP-305 Ф1
---

# OAuth Orchestrator (DP.ROLE.040)

<!-- see DP.SC.130, WP-305 Ф1 -->

> **Kind:** Service role (роль сервиса в L2 платформенном слое, реализуется модулем в CF Worker `gateway-mcp`).
> **Owner Role:** Platform Architect (Дмитрий Церенцеренов) — на этапе bootstrap; в будущем — DP.ROLE.012 Стратег + DevOps.

## 1. Миссия

Быть **единой точкой OAuth-flows** для всех каналов IWE (web-лендинг, VS Code/Claude Code, Telegram-бот). Принимать identity из трёх источников (Ory session, telegram_user_id, github_username), управлять state-token lifecycle (issue → verify → consume), координировать token exchange с внешними провайдерами, хранить access/refresh tokens encrypted-at-rest.

**Граница:**
- НЕ хранит бизнес-логику конкретного провайдера (например, не разбирает GitHub Issues — это другой сервис).
- НЕ обрабатывает webhook от провайдеров (это `gateway-mcp` или `aist_bot.oauth_server.py:/webhook/github/workbook`).
- НЕ создаёт identity (это Ory Hydra) — только разрешает её.
- НЕ зависит от процесса бота; модуль развёртывается вместе с CF Worker `gateway-mcp`.

## 2. Обязанности

| Обязанность | Метод | Триггер |
|-------------|-------|---------|
| Issue state-token | HMAC-SHA256(payload, server_secret) + nonce + TTL 10min | `GET /auth/{provider}/setup` |
| Verify state-token | Check signature + nonce uniqueness in Neon | `GET /auth/{provider}/callback` |
| Identity resolution | Ory JWT verify (JWKS) > dt_tokens.chat_id lookup > github_username lookup | На каждом setup/callback |
| Token exchange | POST к token endpoint провайдера (по OAuth 2.0 RFC 6749) | После успешного callback |
| Token storage | INSERT/UPDATE в `oauth_gateway.tokens` (Fernet encrypted) | После token exchange |
| Token refresh | Periodic refresh per provider TTL (cron) | До истечения access_token |
| Identity-mapping records | UPSERT `knowledge.github_connections` для GitHub App / аналогичные таблицы для других providers | После install/connect |
| Bot-channel proxy | Принимать state-token с `chat_id` от бота, обрабатывать как legacy flow | `GET /auth/github_app/setup?state=<bot-signed>` |
| Failure logging | Через DP.SC.025 capture-bus | На каждый fail (Ory unavailable, GitHub 5xx, state replay) |

## 3. Полномочия

- **Читает** Ory JWKS для local JWT verification (без call к Hydra на каждом запросе).
- **Читает** `knowledge.github_installations`, `dt_tokens` (Railway-local through MCP) для identity resolution.
- **Пишет** в `oauth_gateway.tokens` (own schema) — Fernet ciphertext.
- **Пишет** в `oauth_gateway.state_tokens` — issued nonces для replay-detection.
- **Пишет** в `knowledge.github_connections` — для GitHub App flow.
- **Вызывает** GitHub App / Linear / Twin / Google Cal / WakaTime / Ory token endpoints (server-to-server).
- **Не вызывает** bot process API (loose coupling). Bot обращается к gateway, не наоборот.
- **Не пишет** в `users` / `digital_twins` (это bot's domain — gateway возвращает callback-redirect, дальше отвечает bot).

## 4. Границы роли

| Делает | НЕ делает |
|--------|-----------|
| OAuth 2.0 flow orchestration | Не парсит контент провайдеров (Issues, repos, calendar events) |
| Identity resolution из трёх источников | Не создаёт identity (Ory это делает) |
| State-token lifecycle | Не хранит длительные session cookies (это Ory) |
| Token storage + refresh | Не использует токены для бизнес-операций (это сервисы потребители) |
| Bot-channel proxy (legacy) | Не дублирует bot's user_events / engagement logic |
| Capture-bus error reporting | Не отправляет TG-уведомления (это bot's responsibility) |

## 5. Артефакты

**Входы:**
- HTTP запросы от web-лендинга / VS Code skill / бота
- Ory JWT в session cookie ИЛИ bot-signed state-token
- Provider OAuth callbacks с `code` + `state`
- JWKS от Ory (cached)

**Выходы:**
- HTTP 302 redirects к провайдерам (setup phase)
- HTTP 302 redirects к callback URI потребителя (success phase)
- Rows в `oauth_gateway.tokens` (encrypted)
- Rows в `oauth_gateway.state_tokens` (для replay detection)
- Rows в `knowledge.github_connections` (для GitHub App)
- Capture-bus events для failures

## 6. Носители (carriers)

**Инстанс роли (на 2026-05-12, после ADR-IWE-016 revision):**

| Инстанс | Стэк | Deployment | Owner |
|---------|------|------------|-------|
| **`gateway-mcp/src/oauth/`** модуль | TypeScript, в составе CF Worker `gateway-mcp` | `oauth.aisystant.com` (custom domain alias на gateway-mcp Worker) | Platform Architect |

**История решения:**
- 12 мая Ф1 ArchGate (ADR-IWE-015): принят Вариант B (отдельный репо `DS-oauth-gateway`)
- 12 мая через ~2h independent review (Opus subagent): обнаружено premature decomposition
- 12 мая ADR-IWE-016 supersedes 15: carrier пересмотрен на A-lite (модуль в gateway-mcp)

**Прецеденты переиспользования (внутри gateway-mcp):**
- `handleOAuthAuthorize` / `handleOAuthCallback` — Ory authorization code flow с JWKS verify
- `handleGitHubInstall` / `handleGitHubCreateRepo` / `handleGitHubRepoCallback` — существующий GitHub App pattern
- `encryptCode` / `decryptCode` — code encryption (для state-token аналогичный механизм)
- Hydra token hook (`/hydra-hook/token`) — для subscription gate

**Триггеры extraction в отдельный CF Worker (ADR-IWE-016 §3):**
1. >100 OAuth setup/день в течение 2+ недель
2. Security incident: компрометация gateway-mcp Worker
3. Второй tenant OAuth (корпоративные клиенты с своим Ory)
4. `gateway-mcp/src/index.ts` > 5000 LOC

## 7. Метрики

- `oauth_orchestrator_setup_total{provider, source, identity_type}` — incoming requests
- `oauth_orchestrator_callback_total{provider, status}` — `status` ∈ {success, state_invalid, state_replay, token_exchange_fail}
- `oauth_orchestrator_token_refresh_total{provider, status}` — periodic refreshes
- `oauth_orchestrator_identity_resolution_latency_ms{type}` — `type` ∈ {ory_jwks, dt_tokens, github_username}
- `oauth_orchestrator_state_token_age_seconds{status}` — distribution до consume
- `oauth_orchestrator_active_tokens{provider}` — gauge live токенов в БД

## 8. Связи

- **Реализует:** [DP.SC.130](../08-service-clauses/DP.SC.130-oauth-gateway.md)
- **Использует:** [DP.SC.025](../08-service-clauses/DP.SC.025-capture-bus.md) (capture-bus)
- **Координируется с:** DP.ROLE.038 MCP Tool Consumer (через VS Code skill `/connect-guide`)
- **Координируется с:** R21 Publisher (бот) — proxy-flow для legacy Telegram пилотов
- **Не подчиняется:** ни одной роли (L2 сервисная роль; её исполняет модуль `gateway-mcp`)
- **WP:** WP-305 Ф1

## 9. Различение vs другие роли

| Роль | Отличие от OAuth Orchestrator |
|------|--------------------------------|
| **gateway-mcp** (DS-MCP) | Общий CF Worker предоставляет MCP-маршрутизацию и контроль доступа к знаниям. Модуль `gateway-mcp/src/oauth/` исполняет роль OAuth Orchestrator в том же Worker; отдельный Worker возможен лишь при триггерах выделения из §6. |
| **DP.ROLE.038 MCP Tool Consumer** | MCP Tool Consumer работает с tools на стороне LLM-клиента. OAuth Orchestrator — сервис, к которому обращается клиент за идентичностью. |
| **R21 Publisher (бот)** | Publisher отправляет user-facing сообщения через TG. OAuth Orchestrator работает на уровне HTTP redirects, не TG-каналом. После Ф4 бот вызывает gateway, не наоборот. |
| **Ory Hydra (внешний)** | Hydra = Authorization Server (issues identity + session). Orchestrator = Resource Coordinator (consumes identity для bridging внешних OAuth-провайдеров). |

## 10. Открытые вопросы (для реализации)

1. **Storage schema name:** `oauth_gateway` отдельный schema в Neon ИЛИ переиспользуем `knowledge` (где github_connections)? Рекомендация: отдельный, для clean RLS scope.
2. **Token refresh frequency:** poll-based cron (раз в час, обновляет тех, у кого TTL < 30 мин) ИЛИ on-demand (refresh при первом 401 от провайдера)? Гибрид: on-demand + safety net cron раз в день.
3. **Bot's state-token HMAC secret:** общий с gateway (shared CF env) ИЛИ separate signing key с verify-by-gateway? Рекомендация: shared (KISS), при компрометации — rotate обе стороны.
4. **Migration strategy для 5 остальных OAuth (Ф5):** все сразу или по одному провайдеру? Рекомендация: GitHub App в Ф2-Ф4, остальные — по мере того как бот сужается до Marathon-only (отдельный РП).
5. **Identity-collision handling (Сценарий 4 SC.130):** UPDATE/INSERT logic — где live? В сервисе (атомарно через WHERE clause) или в DB constraint? Constraint лучше.
6. **Bot proxy degradation:** если OAuth-модуль `gateway-mcp` недоступен → бот возвращает «service temporarily unavailable» (текущее) или fallback на legacy oauth_server.py (если ещё не удалён)? Рекомендация: fallback в течение migration window (Ф4-Ф5), потом удалить.
