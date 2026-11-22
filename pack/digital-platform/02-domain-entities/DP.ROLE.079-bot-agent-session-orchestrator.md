---
id: DP.ROLE.079
name: Распорядитель агентных сессий
name_ru: Распорядитель агентных сессий
name_en: Bot Agent Session Orchestrator
aliases:
  - Bot Agent Session Orchestrator
type: role-description
status: active           # WP-428 Ф5 live-smoke принят (single-tenant пилот)
scope: single-tenant (пилот)  # multi-tenant enforcement → спин-офф WP-4XX
valid_from: 2026-06-20
summary: "Оркестратор live-агентной сессии IWE через Telegram: выбирает исполнителя (Claude/Kimi/Hermes) через factory, ведёт lifecycle сессии (start→run→pause→resume→close), принуждает audit + domain-scope, возвращает артефакты в Telegram. Не путать с Диспетчером очереди задач (DP.ROLE.045)."
related:
  specializes: [U.RoleAssignment]
  component_of: [DP.ROLE.001]
  realizes: [DP.SC.186]
  uses:
    - adr-unified-bot-router-v2   # executor-selection + Executor interface
    - DP.ROLE.045                 # Диспетчер — sibling (граница: очередь задач ≠ live-сессия)
    - DP.ROLE.013                 # переключатель доступа по тирам (кто допущен к агенту)
    - external_session.py         # FSM сессии (WP-358)
  downstream_consumers:
    - DP.ROLE.001 IWE Creator — пилот запускает агента из Telegram, получает артефакты
    - DP.ROLE.072 Разработчик-исполнитель (T3-scoped, WP-431) — scoped-агент с approve-before-commit
created: 2026-06-20
updated: 2026-11-22
wp: WP-428
---

# Распорядитель агентных сессий — DP.ROLE.079

> **Прежнее имя** — «Bot Agent Session Orchestrator»; переименовано решением пилота 22.11.2026 (DP.ROLE.001 §3.6, РП-616 Ф4).

## Kind и Owner Role

- **Kind:** оркестрационная роль. LLM-stateless по in-memory (сама не «думает»), file/FSM-stateful по состоянию сессии (`external_session` FSM в PostgresStorage).
- **Owner Role:** DP.ROLE.001 (IWE Creator) — пилот владеет своими агентными сессиями.

## Зачем (обещание, которое реализует)

Реализует DP.SC.186 «Агентная сессия IWE через бота». Даёт пользователю полноценного агента IWE (скиллы, MCP, файлы, commit) через Telegram, с выбором исполнителя и работой на его подписках.

## Обязанности

1. **Выбор исполнителя.** По параметру `executor` (или дефолту пользователя) выбрать реализацию `Executor` через factory: `ClaudeCodeExecutor` | `KimiCliExecutor` | `HermesAgentExecutor`. Не знать рантайм-специфики — звать `executor.execute(session_id, skill_id, context)`.
2. **Lifecycle сессии.** Вести `start → run → pause → resume → close` поверх FSM `external_session`: создать `session_id`, добавлять ходы, heartbeat-прогресс, idle-timeout (30 мин), финализация `/close` → отчёт.
3. **Принуждение безопасности.** Audit-trail каждого действия агента (ОБЯЗАТЕЛЕН); approve-before-commit для T3-scoped; domain-scope (срез доступа по тиру); Telegram только транспорт.
4. **Возврат артефактов.** Коммиты/файлы в целевой репо, ссылка + отчёт в Telegram.

## Полномочия

- Запускать/останавливать рантайм-сессию на раннере пользователя.
- Писать audit-журнал действий.
- **НЕ имеет** права читать домены вне scope сессии (архитектурная гарантия [[Парламент-модель ≠ Президент-модель]], не промпт).
- **НЕ хранит** подписочные credentials — они на раннере пользователя (BYO).

## Входы / Выходы (артефакты)

- **Вход:** агентный запрос из Telegram `{telegram_id, executor, text, attachment?}` (через UnifiedBotRouter).
- **Выход:** артефакты в целевом репо (commit), audit-журнал, отчёт сессии в Telegram.

## Границы с соседними ролями

| Сравнение | DP.ROLE.045 Диспетчер | DP.ROLE.079 Оркестратор сессии |
|-----------|------------------------|--------------------------------|
| Объект | очередь задач `inbox/agent/tasks/` (отложенные, batch) | live-интерактивная сессия из Telegram |
| Режим | one-shot задача с SLA ≤1ч | многоходовая сессия (минуты-часы) |
| Выбор рантайма | фиксированный `claude -p` | executor-selection (3 рантайма) |

- **Router (ADR):** маршрутизирует `request_type` (llm_dialog/day_open/agent_session) — Оркестратор обрабатывает `agent_session`.
- **DP.ROLE.013 (переключатель доступа):** решает, допущен ли тир к агенту; Оркестратор — что делать с допущенным.
- **Исполнители (Executor):** универсальные агенты (Claude Code, Kimi, Hermes), играющие роль IWE-агента; Оркестратор их выбирает, но не является ими ([[Агент ≠ Роль]]).

## Формат / SLA

См. DP.SC.186 (async, heartbeat, idle-timeout). Личность IWE — из источника (MCP), одинакова для всех исполнителей.
