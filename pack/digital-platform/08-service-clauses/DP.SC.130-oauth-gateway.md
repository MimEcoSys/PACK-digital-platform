---
id: DP.SC.130
name: OAuth Gateway (единая точка OAuth для всех каналов IWE)
type: sc
status: draft
layer: L2-Platform
summary: "Web/VS Code/Bot пилот получает доступ к внешним OAuth-провайдерам (GitHub App, Linear, Twin, Google Calendar, WakaTime, Ory) через единый endpoint с dual identity (telegram_user_id ИЛИ ory-session)"
consumer: R21 Publisher (бот) + R38 MCP Tool Consumer (VS Code/Claude Code) + web-пилот (через лендинг)
created: 2026-05-12
updated: 2026-11-27
related:
  realizes:
    - DP.ARCH.001  # эволюционируемость L2 — единая точка вместо фрагментации
  uses:
    - DP.SC.025    # capture-bus (для логирования OAuth failures)
  extends: []
---

# [DP.SC.130] OAuth Gateway

<!--
  WP-305 Ф1 ArchGate (12 мая 2026):
  - ADR-IWE-015 (изначально): Вариант B — отдельный репо DS-oauth-gateway
  - ADR-IWE-016 (revision, 12 мая после independent review): Вариант A-lite —
    модуль `gateway-mcp/src/oauth/` + CF custom domain `oauth.aisystant.com`
    (alias на тот же gateway-mcp Worker). Carrier пересмотрен; обещание
    остаётся неизменным. Триггеры extraction в отдельный Worker —
    см. ADR-IWE-016 §3.

  Решает: oauth_server.py в боте требует telegram_user_id → web-канал C
  (system-school.ru/iwe) технически не работает без бота. Нужен Ory-direct
  flow с dual identity.
-->

> **Уточнение (инверсия модели, WP-415, 2026-06-14).** Шлюз обслуживает любого клиента платформы (IWE, claude.ai, ChatGPT, кастомные клиенты). Аутентификация не зависит от конкретного клиента-помощника — «каналы IWE» в названии исторические; обещание шире и покрывает любой совместимый клиент.

> **Держатель и носитель (27.11.2026, РП-611 Ф23, заявка И-67).** Держатель обещания — РП-262 (Ф3б, сервис подключений), подтверждено пилотом 20.11.2026. Статус остаётся «черновик» до проверки на работающей системе. Расхождение не снято: выше носитель записан как модуль gateway-mcp `src/oauth/` (ADR-IWE-016, 12.05), а Ф3б по АрхГейту 03.10 строит отдельный сервис подключений; РП-262 сверит при срезе волны 2 и поправит описание носителя.

## Правило (инвариант)

- [ ] Identity-resolution приоритет: **Ory session > telegram_user_id > github_username**. Нижний уровень используется только если верхний отсутствует.
- [ ] `user_uuid` в OAuth state/callback берётся **только из проверенного источника** (Ory JWT / HMAC-signed state-token) — никогда из query body или непроверенного header.
- [ ] State-token подписан HMAC-SHA256 с server secret (CF env). TTL ≤ 10 мин. Replay-защита через nonce в Neon.
- [ ] OAuth access/refresh tokens **никогда не логируются** (даже маскированно). Только tool name + status code.
- [ ] B7.3.1 классификация: токены = `secrets` класс → column-level Fernet encryption обязательно перед хранением в Neon.
- [ ] Bot-канал работает через **proxy** к gateway (без дублирования логики). Bot не имеет своей копии OAuth client secret.

## Обещание

**Кому:**
- Web-пилот (заход с `system-school.ru/iwe`, без Telegram)
- VS Code/Claude Code пилот (R38, через `/connect-guide` skill)
- Бот (R21, как legacy proxy для существующих Telegram-пилотов)

**Зачем:**
После WP-301 OAuth flow физически живёт в `aist_bot_newarchitecture/oauth_server.py` и требует `telegram_user_id`. Web-канал C (WP-304 Ф3) технически не работает — даже если на лендинге Ory-логин даёт `user_uuid`, setup endpoint его не примет. Нужна единая точка с dual identity.

**Что получит:**
HTTP-сервис `oauth.aisystant.com` с endpoints:
- `GET /auth/github_app/setup?source=web|vscode|bot` — старт GitHub App install (Ory session ИЛИ telegram_user_id)
- `GET /auth/github_app/callback` — обработка install → запись `github_connections.user_uuid` (web) или `chat_id` (legacy)
- `GET /auth/{provider}/callback` — callbacks для Linear, Twin, Google Calendar, WakaTime, Ory (постепенная миграция из bot's oauth_server.py)
- `GET /.well-known/oauth-protected-resource` — OAuth metadata

**Триггер:**
- Web: пилот жмёт «Подключить персональное руководство» на лендинге → редирект на gateway с ory_session cookie
- VS Code: skill `/connect-guide` открывает URL gateway → если нет Ory session → редирект на consent → возврат
- Bot: `/connect_guide` команда → бот генерирует state-token с `chat_id` → редирект на gateway

**Время отклика:**
- Setup (issue redirect): ≤500ms p95
- Callback (token exchange + DB write): ≤2s p95
- Web full OAuth UX (click → install → return): ≤10s (включая GitHub UI)

**Режим отказа:**
- Ory недоступен → 503 + HTML с инструкцией «попробуйте через 1 мин». Логируется `phase: "ory_unavailable"`.
- GitHub API недоступен → 502 + retry-after header. State-token остаётся валидным до TTL.
- Neon недоступен → state-token validation fail-open для legacy chat_id flow (есть в bot's Railway), fail-closed для Ory flow.
- Идентичность не разрешается ни по Ory, ни по telegram, ни по github → 401 + JSON `{"error": "identity_required", "redirect": "/auth/ory/login"}`.

## Свидетельства (критерий приёмки)

**Данные:**

| Критерий | Как проверить |
|----------|--------------|
| Endpoint `/auth/github_app/setup` принимает оба режима identity | `curl 'oauth.aisystant.com/auth/github_app/setup?telegram_user_id=X'` → 302 redirect; `curl --cookie 'ory_session=...' 'oauth.aisystant.com/auth/github_app/setup'` → 302 redirect |
| `github_connections.user_uuid` заполнено для web-flow | После web-onboarding: `SELECT user_uuid, chat_id FROM knowledge.github_connections WHERE user_uuid='<ory-uuid>'` → row exists, `chat_id IS NULL` |
| State-token не reuse-able | Второй callback с тем же state → 400 `{"error": "state_already_used"}` |
| `oauth.aisystant.com` обслуживается тем же Worker, что и `mcp.aisystant.com` | `curl https://oauth.aisystant.com/.well-known/oauth-protected-resource` и `curl https://mcp.aisystant.com/.well-known/oauth-protected-resource` отдают идентичный JSON (один Worker, два custom domain) |
| `gateway-mcp/src/oauth/` модуль не размывается по `index.ts` | `grep -r "github_app_setup\|github_app_callback" gateway-mcp/src/` → все matches в `src/oauth/` (кроме одной строки регистрации в index.ts) |

**Контекст:**

| Условие | Проверка |
|---------|---------|
| Применимо только для платформенных OAuth-providers (Ory, GitHub App, Linear, Twin, Google Cal, WakaTime) | Список заморожен в `oauth_gateway/config/providers.ts`; новые провайдеры — через ArchGate |
| Bot-канал (legacy) работает через proxy | `/auth/github_app/setup?telegram_user_id=X` принимается и возвращает тот же flow как до выноса |
| Web-канал работает без Telegram | E2E тест: новый Ory-аккаунт без `chat_id` проходит install App до конца → запись в БД создана |

**Полномочия:**

| Роль | Что подтверждает |
|------|-----------------|
| DP.ROLE.040 OAuth Orchestrator | Подтверждает корректность identity-resolution и state-token подписи |
| DP.ROLE.038 MCP Tool Consumer | Подтверждает, что VS Code skill корректно работает с gateway URL |
| R21 Publisher (бот) | Подтверждает, что proxy-flow не теряет существующих Telegram-пилотов |

**Свидетельства (наблюдаемость):**

| Свидетельство | Источник |
|--------------|---------|
| OTel span `oauth.setup` / `oauth.callback` | duration, source (web/vscode/bot), identity_type (ory/telegram), provider |
| Метрика `oauth_identity_resolution_total{type=ory|telegram|github}` | Langfuse/Prometheus |
| Лог `phase: "identity_fallback"` при использовании nижнего уровня identity | capture-bus → incident-log |
| Лог `phase: "state_token_replay_detected"` | security incident-log |

## Сценарии использования

### Сценарий 1: Web-пилот (никогда не открывал бота)

**Кто:** новый волонтёр с лендинга `system-school.ru/iwe`
**Когда:** после Ory-логина на лендинге
**Что делает:**
1. На лендинге жмёт «Подключить персональное руководство» → редирект на `oauth.aisystant.com/auth/github_app/setup?source=web`
2. Gateway видит `ory_session` cookie, извлекает `user_uuid` через JWKS verify
3. Generate state-token с `{user_uuid, source: "web"}`, redirect на GitHub App install page
4. Пилот ставит App на репо `personal-guide` → GitHub redirect на `/auth/github_app/callback?state=...&installation_id=...`
5. Gateway: verify state → INSERT `github_connections {user_uuid, installation_id, chat_id: NULL}`
6. Redirect на `system-school.ru/iwe/connected` → пилот видит «✅ App подключён»

**Никакого Telegram, никакого `dt_tokens`.**

### Сценарий 2: VS Code/Claude Code пилот

**Кто:** пилот в браузере (claude.ai/code) или VS Code
**Когда:** запускает skill `/connect-guide`
**Что делает:**
1. Skill открывает `oauth.aisystant.com/auth/github_app/setup?source=vscode`
2. Если нет Ory session → редирект на Ory consent (`hydra.aisystant.com/oauth2/auth?...`)
3. После consent → возврат на gateway с ory_session → дальше как Сценарий 1
4. Skill получает callback через webhook на claude.ai (или polling state в boon)

### Сценарий 3: Существующий Telegram-пилот (legacy)

**Кто:** пилот с established `dt_tokens.chat_id`
**Когда:** жмёт inline-кнопку в `/connect_guide` в боте
**Что делает:**
1. Бот генерирует state-token с `{chat_id, source: "bot"}` → подписывает своим HMAC (gateway знает этот secret через CF env)
2. Бот: inline-button URL = `oauth.aisystant.com/auth/github_app/setup?state=...`
3. Gateway: verify state → resolve `user_uuid` через `dt_tokens` (Railway-local, MCP read-through)
4. Дальше как Сценарий 1 (с заполненным `chat_id` в `github_connections`)

**Не ломается ни один существующий пилот.**

### Сценарий 4: Identity-collision (web-пилот → потом подключает Telegram)

**Кто:** пилот, который сначала пришёл через web, затем установил бота
**Что делает:**
1. Web flow создал запись `github_connections {user_uuid, chat_id: NULL}` (Сценарий 1)
2. Позже пилот делает `/start` в боте → OAuth Ory → `dt_tokens {chat_id, dt_user_id, ory_user_uuid}`
3. Бот видит существующий `user_uuid` в `dt_tokens` → UPDATE `github_connections.chat_id` (не INSERT)

**Тест приёмки:** ord users в `github_connections` остаётся стабильным; нет дубликатов по `user_uuid`.

## Связи с другими SC

- **DP.SC.025 (capture-bus):** все OAuth-failures и `state_token_replay_detected` пишутся через capture-bus в incident-log
- **DP.SC.034 (Local MCP Gateway):** местный gateway координирует с oauth-gateway для VS Code сценария 2 (через MCP tools)
- **DP.SC.129 (Generic MCP Tool Discovery):** не связан напрямую, но oauth-gateway publishes `tools/list` для discovery (если будет нужно)
- **DP.ARCH.001:** OAuth Gateway — конкретная реализация принципа «единая точка для эволюционируемости»

## Антипаттерны

- ❌ **identity из query string:** `?user_uuid=X` без proof → identity substitution attack. Всегда из подписанного state ИЛИ Ory session.
- ❌ **state-token без TTL:** замена expired для replay.
- ❌ **Логирование access_token (даже маскированно):** OAuth tokens = secrets, log = persistent storage с другим политиками retention.
- ❌ **Создание github_connections без verification что user_uuid существует в Ory:** orphan records.
- ❌ **Bot's oauth_server.py хранит свою копию GitHub App private key:** двойной источник правды, drift.

## Реализационные находки (batch3 РП170, 2026-07-22)

### Single-flight cache для OAuth refresh-token (гонка конкурентных вызовов)

Конкурентные вызовы, обновляющие один и тот же refresh-token, схлопываются в единый запрос к Ory через Durable Object как сериализатор гонки. Успешный результат кэшируется на 5 секунд (окно гонки) — повторные вызовы в это окно получают закэшированный результат вместо повторного обращения к Ory. Неуспешный результат **не кэшируется** — следующий вызов бьёт Ory заново, а не повторяет ошибку из кэша.

Паттерн воспроизводим для любого конкурентного обновления токена, не только для Ory — применим к другим провайдерам при расширении gateway.

### Захардкоженный `expires_in` в ответе `/token` — риск рассинхрона

`expires_in: 3600` в ответе `/token` захардкожен вместо передачи реального значения, полученного от Ory. Если Ory меняет TTL токена (конфигурация провайдера, ротация политики), клиент продолжает ориентироваться на устаревшее захардкоженное значение → преждевременно считает токен истёкшим или, наоборот, использует просроченный.

**Лечение:** передавать `expires_in` из ответа Ory без модификации, не константой.

## Открытые вопросы

- Q1: где живёт OAuth refresh logic — gateway или MCP client? Gateway — потому что storage и rotation policy там.
- Q2: миграция остальных 5 OAuth (Ф5 WP-305) — постепенно (по мере спроса) или большим этапом?
- Q3: как обрабатывать GitHub App suspended state? Gateway проверяет при каждом запросе или периодически (cron)?
