---
id: DP.SC.031
title: "Единый Read API над Памятью.Derived для пользовательских поверхностей"
status: draft
layer: L4-Personal
audience: [R1 Стратег, R5 Архитектор, R14 Заказчик]
created: 2026-04-24
updated: 2026-10-02
links: [DP.D.052, DP.ARCH.004, WP-187, WP-227, WP-73, WP-109, WP-117]
related:
  extends: []
  realizes: [dt_* MCP tools в gateway-mcp, /twin MCP endpoint]
  uses: [DP.D.052, DP.ARCH.004]
---

# DP.SC.031 — Единый Read API над Памятью.Derived

> **Контекст:** возник из закрытия WP-135 «Мой ЦД — мультиканальный интерфейс самообслуживания» 24 апр 2026. Пять фаз WP-135 распределены по WP-117 (бот), WP-187 (VS Code через Gateway), WP-212 (экспорт GDPR), WP-73 (Web App). Распределение рискует потерять главную архитектурную ценность WP-135: «один API, много поверхностей». Этот SC фиксирует инвариант, чтобы независимые реализации в разных РП не дублировали SELECT-логику и не обходили тир-гейтинг.

## Обещание

**Кому:** любой канал-потребитель пользовательских данных (бот `/me`, `/progress`, `/twin`; VS Code IWE extension; Web App dashboard; сторонние плагины L3 через Plugin API WP-258) и стоящие за ними роли — R1 Стратег (владелец собственных данных), R14 Заказчик (потребитель своих индикаторов), R5 Архитектор (ответственный за целостность read-модели).

**Зачем:** согласно модели Персона/Память/Контекст (DP.D.052, введена WP-257 22 апр 2026), расчётные индикаторы пользователя (baseline, potential, RCS, streak, active_days, coding_time, IWE-активность) живут в **Память.Derived** (Neon `platform`, бывший `digital-twin` #5). Если каждый канал ходит напрямую в БД своим SELECT'ом, возникают три проблемы:

1. Дублирование логики расчёта/агрегации → расхождение чисел между каналами (бот показывает streak 5, VS Code — 4).
2. Обход tier-gating (T1-T4) и RLS → пользователь одного тира видит через Web App то, что запрещено в боте.
3. Невозможность централизовать audit trail (см. DP.SC.032) — часть обращений не логируется.

**Что получит:**

- **Единственная точка доступа к Памяти.Derived для UI-каналов** — MCP tools `dt_*` в `gateway-mcp` (или `/twin` MCP endpoint, WP-227). Любой канал (бот, VS Code, Web App, L3-плагин) ходит через этот слой, не напрямую в Neon `platform`.
- **Стабильный контракт read-model** — набор именованных выборок (`dt_read_digital_twin`, `dt_describe_by_path`, будущие `dt_activity_week`, `dt_indicators`), с версионированием схемы.
- **Tier-gating на уровне API** — не на уровне канала. T1/T2/T3/T4 проверяется в gateway, каналы получают только разрешённые секции.
- **Единый формат snapshot** для audit trail (DP.SC.032) — структура `{sections, snapshot}` одинакова во всех каналах.

**Критерий приёмки:**

1. Ни один UI-канал (бот, VS Code, Web App, L3-плагин) не содержит прямых SQL-запросов к Neon `platform` для чтения Памяти.Derived. Проверка: `grep -r "platform\." aist_bot_newarchitecture/` на паттернах SELECT не находит read-индикаторы.
2. Добавление нового канала не требует правок схемы БД — только новый адаптер над `dt_*` tools.
3. Tier-gating проверяется в одном месте (gateway или `/twin` handler), не дублируется в каналах.
4. Расхождение метрик между каналами = баг gateway (один источник), не баг канала.
5. L3-плагины (WP-258, Plugin API) подключаются через те же `dt_*` tools, получая те же гарантии tier-gating.

## Инварианты

1. **Read-only.** Этот SC покрывает только чтение. Запись в Память.Derived — отдельный контур (projection-workers, event-gateway, WP-253).
2. **Derived, не Observed.** Через этот API отдаются агрегаты и расчёты (baseline, indicators, streaks). Сырые события (activity-hub #3) — отдельный endpoint, не смешиваются.
3. **Персона — не здесь.** Декларации пользователя о себе (PACK-personal, DS-my-strategy, captures) живут в Git пользователя, владелец — пилот. Gateway может проксировать чтение Персоны (`personal_*` tools), но это другое обещание (DP.SC.022), не смешивается с Памятью.Derived.
4. **Tier-gating — не переопределяется каналом.** Если бот запрашивает секцию `iwe_activity`, а у пользователя тир T2 — gateway возвращает 403 / пустую секцию, бот не может «договориться» о выдаче. Право на копию своих доверенных данных в объявленном составе тиром не ограничивается (ADR-IWE-014 §3.4); секции вне объявленного состава остаются под ограничением по тиру.
5. **Один формат snapshot.** Каналы могут рендерить по-разному (TG-строка vs webview vs rich dashboard), но источник данных — один JSON-контракт.

## Negative guarantees (что НЕ покрывает)

- **НЕ покрывает write-path.** Запись событий → event-gateway (WP-253). Изменение подписок → `/subscribe` в боте. Изменение Персоны → push в Git пользователя.
- **НЕ покрывает Platform-knowledge.** PACK-digital-platform, FPF, ZP — общая онтология команды, читается через `knowledge_*` tools, не `dt_*`.
- **НЕ заменяет Metabase (#7).** Административная отчётность (Методсовет, команда) — отдельный read-путь через Metabase/Directus. Этот SC — только для пользовательских UI-каналов.
- **НЕ гарантирует консистентность на субсекундном интервале.** Projection-workers имеют lag (обычно <10 сек). Канал видит «почти свежий» snapshot, не транзакционно-согласованный с write-потоком.

## Сценарии использования

### SC.029.1 — Чтение дашборда в боте (`/me`, `/progress`)

**Триггер:** пользователь пишет `/me` или `/progress` в @aist_me_bot.

**Потребитель:** R1 Стратег (владелец данных) — видит свой профиль, активность, развитие, IWE.

**Владелец:** gateway-mcp (handler `dt_read_digital_twin`) + bot handler (тонкий адаптер).

**Шаги:**
1. Bot получает update, извлекает `user_id` из `telegram_id`.
2. Bot вызывает `dt_read_digital_twin(user_id, sections=['profile','activity','learning','iwe'])` через Gateway (JWT auth).
3. Gateway проверяет тир (по подписке в БД #1 `platform`), фильтрует запрошенные секции.
4. Gateway читает Память.Derived одним SELECT'ом, возвращает `{sections, snapshot}`.
5. Bot рендерит TG-сообщение из snapshot (≤15 строк, emoji-метрики, кнопки drill-down).

**Время отклика:** ≤500 ms p95.

**Ожидаемый результат:** пользователь видит актуальный профиль + audit-событие `dt_view_requested` (см. DP.SC.032).

### SC.029.2 — Status line + webview в VS Code IWE extension

**Триггер:** пользователь открывает VS Code с IWE extension.

**Потребитель:** R1 Стратег — видит streak + coding_time в status bar, по клику открывается webview с полным дашбордом.

**Владелец:** gateway-mcp + IWE extension (VS Code).

**Шаги:**
1. Extension на старте (и каждые 5 мин) вызывает `dt_read_digital_twin(sections=['profile','coding'])` через OAuth-аутентифицированный Gateway.
2. Status line обновляется: `🔥5 · ⏱5h42m`.
3. По клику — webview запрашивает `sections=['profile','activity','learning','iwe','coding']`, рендерит rich panel.

**Время отклика:** ≤300 ms p95 (status line обновляется неблокирующе).

### SC.029.3 — Web App dashboard (будущий канал)

**Триггер:** пользователь открывает вкладку «Мой ЦД» в Web App Aisystant (WP-73 Ф1.1).

**Потребитель:** R1 Стратег — видит графики, heatmap, фильтры по периодам.

**Владелец:** gateway-mcp + Web App frontend.

**Шаги:**
1. Web App через OAuth получает JWT.
2. Вызывает `dt_read_digital_twin(sections=[...], period='30d')` + `dt_activity_timeseries(period='90d')` (новый endpoint, добавляется при реализации Ф4).
3. Рендерит rich dashboard.

**Симптом нарушения SC:** Web App ходит напрямую в Neon `platform` — критическое нарушение инварианта 1. Gateway обойдён, tier-gating не проверяется, audit trail (SC.030) теряет события.

## Реализующие сервисы (MAP.002)

| Сервис | Роль | Триггер | Путь |
|--------|------|---------|------|
| gateway-mcp (`dt_*` tools) | R29 API-слой | MCP request с JWT | DS-MCP/gateway-mcp |
| /twin MCP endpoint | R29 API-слой | HTTP POST с JWT | /twin (WP-227) |
| projection-worker | R6 Кодировщик | LISTEN/NOTIFY от event-gateway | WP-253 P2 |

## Связь с другими обещаниями

- **Extends:** DP.SC.021 (mcp-knowledge-access) — паттерн «единая точка доступа для MCP tools» повторяется для Памяти.Derived.
- **Feeds:** DP.SC.032 (audit trail view personal data) — каждое обращение через этот API логируется.
- **Related:** WP-187 (Gateway MVP), WP-227 (/twin service), WP-73 (Platform Architecture), WP-258 (Plugin API L2).
- **Potentially-conflicts:** нет. Write-path (WP-253 event-gateway) идёт в другую сторону, не пересекается.

---

**Статус:** draft, 24 апр 2026. Создан при закрытии WP-135 как фиксация архитектурного инварианта перед распределением фаз по WP-117/WP-212/WP-73. Требует: (1) ревью владельцем, (2) включения в DP.ARCH.004 read-path раздел, (3) регистрации `dt_*` tools в MAP.002 как реализующих сервисов.
