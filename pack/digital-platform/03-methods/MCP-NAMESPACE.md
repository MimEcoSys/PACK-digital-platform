# MCP Namespace — соглашение IWE

> **Источник:** WP-189 Ф2 (1 апр 2026)
> **Статус:** active
> **Связи:** WP-187 (knowledge-mcp изоляция), WP-184 (knowledge_feedback), WP-73 ADR-018, WP-222 (закрытие отдельного tailor-mcp; функцию покрывает digital-twin-mcp как backend Памяти.Derived)
> **Обновлено (2026-10-02, РП-170):** добавлен раздел «Поддомены» (решение пилота 26.09.2026).
> **Обновлено:** 2026-05-06 (WP-222 Ф6) — удалены упоминания `tailor-mcp` как отдельного сервиса; уточнено имя `digital-twin-mcp` как machine identity (см. HD «MCP display identity ≠ machine identity»); функционально это backend **Памяти.Derived** (HD #27).

## Namespace соглашение

| Префикс | Категория | Кто управляет | Примеры |
|---------|-----------|--------------|---------|
| без префикса | Платформенные (наши) | Платформа (обновляем через update.sh) | `knowledge-mcp`, `digital-twin-mcp` |
| `ext-*` | Вендорские | Вендоры (OAuth-токены пользователя) | `ext-google-calendar`, `ext-linear`, `ext-slack` |
| `<username>-*` | Пользовательские | Пользователь (его данные, его ответственность) | `tseren-notes`, `tseren-obsidian` |

**Правило:** платформенные — без префикса (их имена зарезервированы). Вендорские — `ext-*`. Пользовательские — свой префикс (username или любой уникальный).

## Поддомены: `mcp.<домен>` и `open.<домен>`

Решение пилота 26.09.2026. Префикс поддомена сервиса — часть публичного контракта, а не случайное имя, и действует одинаково на обоих брендах платформы (system-school.ru и aisystant.com):

| Поддомен | Что означает |
|----------|--------------|
| `mcp.<домен>` | вход с аккаунтом МИМ |
| `open.<домен>` | доступ без входа |

**Тест выбора:** функция сервиса требует входа с аккаунтом МИМ? Да → `mcp.<домен>`. Нет → `open.<домен>`.

**Применено:** сервис без авторизации переименован из `mcp.system-school.ru` в `open.system-school.ru`. Имя `mcp.system-school.ru` зарезервировано под будущий авторизованный коннектор и этим сервисом задним числом не занято. Переименование готовит имя под будущий `open.aisystant.com` (второй бренд или регион на том же коде).

Источник: git commit `5c33103` в open.system-school.ru; захват DS-my-strategy/inbox/captures/2026-09.md:4676; extraction-report `2026-09-28-inbox-check-3.md`, кандидат #5. Связь: WP-581.

## Симметричная схема трёх платформенных MCP

```
Пользователь работает в: claude.ai / Cursor / Telegram
         ↓ (один Gateway URL, OAuth через Ory)
┌──────────────────────────────────────────────────┐
│  MCP Gateway (наш, Ory auth)                     │
│                                                  │
│  knowledge-mcp        ← общее знание платформы  │
│  (L2 shared + L4 per-user) ZP/FPF/SPF/Pack + личные репо │
│                                                  │
│  digital-twin-mcp     ← Память.Derived          │
│  (per-user RLS)         (machine name = legacy;  │
│                         function = derived       │
│                         memory backend)          │
│                                                  │
│  personal-knowledge-mcp  ← его репо             │
│  (per-user RLS)           эмбеддинги на нашей   │
│                           инфре                 │
└──────────────────────────────────────────────────┘
```

Все три — **наши сервисы**. Изоляция через RLS по `user_id`, не отдельные инстансы.

## Ownership данных

| MCP | Читает | Пишет | Владелец расчёта |
|-----|--------|-------|-----------------|
| `knowledge-mcp` | ZP, FPF, SPF, Pack платформы | — | Платформа |
| `digital-twin-mcp` | Память.Derived (`indicators.calculated_profile`, `indicators.digital_twins`) | `1_declarative`, `2_collected` через bot-side writers | **projection-worker (WP-253)** + R28 Профилировщик = writers Памяти.Derived. Machine name = legacy alias (HD «display ≠ machine»). |
| `personal-knowledge-mcp` | Репо пользователя (выбранные) + Qdrant | GitHub коммит (async) | Пользователь |

> **⚠️ digital-twin-mcp = read-only потребитель Памяти.Derived.** projection-worker (WP-253) + R28 Профилировщик = writers. On-demand recalc → вызов через projection-worker / R28, не внутри digital-twin-mcp.
>
> **Имя сервиса:** `digital-twin-mcp` (machine name) — historical artefact из эпохи когда «digital twin» был основным концептом. После переименования в **Память.Derived** (HD #27, WP-257) machine identity сохранена для обратной совместимости (бот, gateway-mcp upstream registry, OAuth registrations). В Pack документации, tool descriptions, OAuth consent screens — используется **Память.Derived**. Переименование machine identity отложено до Q3+ (по принципу осторожности; см. WP-222 Ф2 АрхГейт).

## Выбор репо для индексации (personal-knowledge-mcp)

Пользователь явно указывает какие репо индексировать — платформа не индексирует всё автоматически.

**Где указывается:** настройки Gateway (UI) или `.exocortex.env`:
```
PERSONAL_KNOWLEDGE_REPOS=TserenTserenov/PACK-my-domain,TserenTserenov/DS-my-notes
```

**Как работает:**
1. Пользователь добавляет репо в список
2. Платформа индексирует → эмбеддинги в Neon/Qdrant с его `user_id`
3. При push в репо → webhook → переиндексация изменённых файлов
4. `personal-knowledge-mcp` возвращает только его данные (RLS)

## Контракты MCP (спецификации для downstream РП)

### knowledge-mcp → WP-187

```
Tool: search(query: str, source?: str, source_type?: str, limit: int = 5) → SearchResult[]
  Изоляция:
    - Авторизованный пользователь автоматически видит платформенные + свои личные документы
    - user_id передаётся прозрачно через HTTP-заголовок X-User-Id (Gateway из Ory JWT)
    - НЕ через аргументы tool (защита от подмены user_id)
    - platform namespace (user_id IS NULL): ZP, FPF, SPF, Pack платформы — доступно всем
    - user namespace (user_id = UUID): Pack пользователя — только владельцу
    - прямой доступ минуя Gateway: только platform namespace

Tool: knowledge_feedback(document_id: str, query: str, helpfulness: bool, user_id: str) → void
  Сохраняет в retrieval_feedback(user_id, document_id, query_hash, helpfulness, created_at)
  Реализация: WP-184 Ф3
```

### digital-twin-mcp → WP-175 (исторически), WP-253 (актуально)

> **Эволюция контракта:**
> - **WP-175 (30 мар 2026):** Был Python stdio-сервис `tailor-mcp` с tool `get_tailor_context`. Архивирован 2026-05-06 (WP-222 Ф1) — нет production-потребителей.
> - **WP-253 (актуально):** `digital-twin-mcp` = Cloudflare Worker на `https://twin.aisystant.com/mcp`, читает `indicators.digital_twins` + `indicators.calculated_profile` (Память.Derived) с RLS.

**Текущие tools digital-twin-mcp:**

```
Tool: dt_read_digital_twin(path: str) → DigitalTwinNode
  Возвращает: фрагмент Памяти.Derived (профиль, индикаторы, цели) по пути.
  RLS: изолировано по user_id из X-User-Id (Gateway из Ory JWT).
  Доступ: через Gateway (https://mcp.aisystant.com/) или прямой (https://twin.aisystant.com/mcp).

Tool: dt_write_digital_twin(path: str, data: any) → void
  Пишет в `indicators.digital_twins` (для legacy bot-writer'ов).
  Будущее: отказ от прямой записи в пользу events через event-gateway (WP-253 Ф9.x).
```

**Контракт `tailor_context`** (что Портной читает) теперь — формат-объект (PD.SPEC.001 §2). Способ получения:
- **Текущий носитель Портного** (render-pilot-guides.py): прямой psycopg2 → `indicators` schema, **не** через MCP
- **Будущий носитель Портного** (ИИ-агент после WP-150 Ф6): через `dt_read_digital_twin` + `personal_search` + `knowledge_search` от MCP Gateway

### personal-knowledge-mcp → WP-187

```
Tool: search(query: str, user_id: str, limit: int = 5) → SearchResult[]
  Ищет только в репо пользователя (его user_id)

Tool: propose_capture(content: str, suggested_location: str, user_id: str) → CaptureProposal
  Поведение: зависит от capture_autonomy в params.yaml
    propose (default): возвращает предложение, ждёт подтверждения
    auto: сразу пишет в GitHub

Tool: write(path: str, content: str, user_id: str) → WriteResult
  Auth: GitHub App Installation Token (repo-scoped)
  Async: write → queue → background commit (~5 сек)
  Side effect: ingest_event() в Activity Hub (ADR-009)
```

## Temporal метаданные (единый формат с WP-180 Ф10.1)

Все эмбеддинги в Qdrant:
```json
{
  "document_id": "PACK-my-domain/concept.md",
  "content": "...",
  "valid_from": "2026-01-15",
  "superseded_by": null,
  "user_id": "TserenTserenov"
}
```

Единый формат с MEMORY.md frontmatter (WP-180 Ф10.1):
```yaml
---
valid_from: 2026-01-15
superseded_by: null
---
```

При поиске: `superseded_by != null` → пониженный score.

## ADR-018 (WP-73 §3.8) — обновить

Добавить namespace соглашение: платформенные (без префикса) / вендорские (`ext-*`) / пользовательские (`<username>-*`).
