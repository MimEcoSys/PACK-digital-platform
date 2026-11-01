---
id: DP.ROLE.080
name: Владелец выдачи согласия на анализ данных (Consent Grant Authority)
type: role-description
status: draft
valid_from: 2026-07-04
summary: "Единственный компонент, который пишет scope=data_analysis в learning.consent_grant и эмитит consent_granted в public.domain_event. Не отвечает за revoke, не отвечает за text_analysis/typing_tracking (владелец — бот)."
related:
  specializes: [U.RoleAssignment]
  component_of: [DP.ROLE.001]
  uses:
    - DP.ARCH.006   # domain_event / memory record
    - DP.ROLE.032   # Event Ingester — валидирует consent_granted перед записью
  supersedes: []
created: 2026-07-04
updated: 2026-07-04
wp: WP-457
---

# Владелец выдачи согласия на анализ данных — DP.ROLE.080

> **Kind:** Operational Role — пишет `learning.consent_grant` для одного scope. Узкая роль: покрывает только выдачу (grant), не весь процесс согласия целиком.
> **Owner Role:** IWE Platform — носитель: `learning-context-service` (DS-MCP, Cloudflare Worker).

---

## 0. Почему роль называется не «Владелец согласия», а именно «выдача»

Название сознательно не использует слово «lifecycle». Consent-lifecycle = grant + revoke. У этой роли есть только grant. Revoke для `data_analysis` на момент написания паспорта (2026-07-04) не имеет рабочего пути через основной пользовательский интерфейс — см. §6 «Известные разрывы». Называть роль «владельцем всего процесса согласия» значило бы утверждать то, что не соответствует коду.

Паспорт написан после реализации серверной проверки scope (см. §3) — не раньше, чтобы утверждение «пишет только data_analysis» было фактом кода на момент фиксации, а не намерением поверх дыры (peer-сессия с Kimi, эскалация, решение пилота 2026-07-04).

---

## 1. Миссия

Быть единственным писателем `scope=data_analysis` в `learning.consent_grant`: принять запрос на выдачу согласия (из бота через MCP-инструмент `grant_consent`, либо из другого авторизованного клиента шлюза), записать его и оставить неизменяемый след перехода в `public.domain_event` (событие `consent_granted`).

---

## 2. Обязанности

| Обязанность | Как выполняется |
|-------------|----------------|
| Принять запрос на выдачу согласия | MCP-инструмент `grant_consent` (`mcp-handler.ts`), вызывается ботом или другим авторизованным клиентом шлюза |
| Отклонить запрос на scope не своей ответственности | Allow-list `["data_analysis"]` — любой другой scope в списке отклоняет весь запрос с явной ошибкой (не молча игнорирует) |
| Записать согласие | `INSERT ... ON CONFLICT DO UPDATE` в `learning.consent_grant` (`account_id`, `scope='data_analysis'`, `granted=true`) |
| Эмитировать отпечаток перехода | `emitConsentGrantedEvent()` → `public.domain_event`, событие `consent_granted` (после успешного INSERT, per-scope) |

**Запрещено:**
- Принимать/записывать `text_analysis` или `typing_tracking` через `grant_consent` — эти scope пишет бот напрямую (`db/queries/consent.py:set_consent_grant`, `aist_bot_newarchitecture`).
- Молча принимать неизвестный/чужой scope как часть batch-запроса — весь запрос отклоняется явной ошибкой (см. §3).

---

## 3. Полномочия

- **Единственный** writer scope `data_analysis` в `learning.consent_grant`.
- Право на `INSERT`/`UPDATE` в `learning.consent_grant` для этого scope.
- Право на эмиссию события `consent_granted` в `public.domain_event` (через `event-gateway`, валидатор схемы).

**Серверная проверка границы (2026-07-04, реализовано в этой сессии):** `grant_consent` отклоняет любой scope вне `["data_analysis"]` явной ошибкой JSON-RPC (`fail(...)`, `isError: true`), не игнорирует молча. До этой правки граница держалась только на конвенции вызывающей стороны (бот всегда передавал только нужный scope) — это было архитектурной фикцией: сервис технически мог записать любой scope. Инвариант теперь проверяется кодом самого сервиса, не только соглашением снаружи.

**Не имеет права:**
- Писать `revoked_at` для `data_analysis` (revoke не реализован этой ролью — см. §6).
- Читать/писать consent других scope (`text_analysis`, `typing_tracking`, легаси `stage_evaluation`/`club_activity` из `learning.tracking_consent`).

---

## 4. Входы и выходы

**Входы:**
- `grant_consent` MCP tool call: `{agreed: true, scopes?: ["data_analysis"]}` (отсутствие `scopes` трактуется как `["data_analysis"]`).

**Выходы:**
- `learning.consent_grant` row: `{account_id, scope: "data_analysis", granted: true, consent_version, granted_at, interface: "mcp"}`.
- `consent_granted` событие в `public.domain_event`: `{account_id, scope: "data_analysis", granted: true, ...}` (схема — `event-gateway`).
- JSON-RPC ответ: `{success: boolean, scopes_granted: string[]}` при успехе; `{error: string, isError: true}` при отклонении scope или отсутствии `agreed`.

---

## 5. Связи / Владение scope (карта, не `state-axes-registry.yaml`)

> Владение consent-scope — контракт между компонентами (кто пишет что), не таксономия типа состояния. `state-axes-registry.yaml` остаётся SoT для типов состояния («Доверие» и др.), не для этой карты — решение peer-сессии 2026-07-04 (Kimi настоял на разделении).

| Scope | Писатель | Роль/сущность |
|---|---|---|
| `data_analysis` | `learning-context-service` | **эта роль (DP.ROLE.080)** |
| `text_analysis` | бот (`aist_bot_newarchitecture`) | не паспортирована отдельно на 2026-07-04 (см. §7) |
| `typing_tracking` | бот (`aist_bot_newarchitecture`), тот же код-путь что `text_analysis` | не паспортирована отдельно; отдельный ли это scope или производное от `text_analysis` — открытый продуктовый вопрос, вне объёма Ф10 условия 1 |
| `stage_evaluation`, `club_activity` (легаси, `learning.tracking_consent`) | бот, WP-188 механизм | вне области этой роли и вообще вне `learning.consent_grant` |

| Роль | Отношение |
|------|-----------|
| Бот (`aist_bot_newarchitecture`, системная сущность `DP.AISYS.014`) | Со-писатель consent (другие scope), НЕ читает/пишет `data_analysis` |
| `DP.ROLE.032` Event Ingester | Валидирует схему и allow-list источников для `consent_granted` перед записью в `domain_event` |
| Шлюз (`gateway-mcp`) | Транспорт: пробрасывает вызов `grant_consent` от бота/клиента к сервису, не пишет данные сам |

---

## 6. Известные разрывы (зафиксированы честно, не устранены этим паспортом)

| Разрыв | Статус на 2026-07-04 | Что делать |
|---|---|---|
| **Revoke для `data_analysis` не работает через основной UI бота.** Обе кнопки отзыва в `/consent` (`consent_goto_optout`, `consent_revoke_confirm`) пишут в `learning.tracking_consent` (легаси WP-188 таблица), не в `learning.consent_grant`. Пользователь видит «согласие отозвано», реальная запись `data_analysis` остаётся `granted=true`. | Найдено в этой сессии, GDPR-релевантно, НЕ входит в объём этой роли. | Отдельная срочная сессия/задача — зафиксировано в `WP-457.md` «Осталось». Не паспортируется как обязанность этой роли. |
| **Статус деплоя фикса границы (§3) по окружениям.** | `pilot` (канареечная ветка бота) — ✅ фикс write-path применён (сессия `2026-07-04-07`). `new-architecture` (прод-бот) — ⏳ фикс ещё не перенесён (Pilot-First, ожидаемо, не баг). | Cherry-pick в `new-architecture` — отдельный шаг продвижения, не блокирует этот паспорт. |
| **`typing_tracking` как отдельный scope или производное `text_analysis`.** | Открытый продуктовый вопрос, не решён. | Отложено к Ф14 (аудит писателей состояний по типам, WP-457). |

---

## 7. История изменений

| Версия | Дата | Изменение | WP |
|--------|------|-----------|-----|
| 0.1 | 2026-07-04 | Первичная фиксация роли. Попытка утром (`2026-07-04-01-wp457-f10-consent-owner`) не завершилась паспортом — архитектура write-path была не решена (3-4 параллельных писателя, найдено сессией). Write-path зафиксирован сессией `2026-07-04-07`. Серверная проверка scope реализована этой сессией (`2026-07-04-13`) ДО фиксации паспорта — peer-сессия с Kimi, эскалация к пилоту, решение: «чинить сейчас, не документировать разрыв». | WP-457 |
