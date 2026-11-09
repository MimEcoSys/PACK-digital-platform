---
id: DP.FM.607
type: failure-mode
status: draft
created: "2026-10-10"
valid_from: "2026-10-10"
name: "Авторизация MCP tools/list асимметрична tools/call: gateway не минтит assertion для list, backend требует — постоянный backend_tools_empty"
name_ru: "Авторизация MCP tools/list асимметрична tools/call: gateway не минтит assertion для list, backend требует — постоянный backend_tools_empty"
name_en: "MCP tools/list auth asymmetric to tools/call: gateway never mints assertion for list, backend always requires it — permanent backend_tools_empty"
summary: "Gateway минтит assertion только для tools/call, но не для tools/list; backend требует authenticate() на обоих. Результат: backend_tools_empty на каждом вызове — детерминированный сбой, выглядящий как транзиентный."
pack: PACK-digital-platform
domain: digital-platform / mcp-gateway
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit c6fb014af в DS-my-strategy (WP-578)"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-10-inbox-check-6.md"
source_candidate: 5
tags: [mcp, tools-list, tools-call, auth-asymmetry, gateway, backend-tools-empty]
---

# DP.FM.607 — Авторизация MCP tools/list асимметрична tools/call

## Тезис и механизм ошибки

Gateway и backend по-разному определяют, какие MCP-методы требуют авторизации:

| Сторона | tools/call | tools/list |
|---------|-----------|-----------|
| Gateway | минтит assertion | **не минтит** |
| Backend | требует authenticate() | **тоже требует** |

Расхождение приводит к тому, что каждый запрос `tools/list` проходит без assertion, backend возвращает ошибку авторизации, клиент получает пустой список инструментов (`backend_tools_empty`). Сбой детерминированный, не транзиентный — но выглядит как «временно не отвечает».

## Признаки

- `backend_tools_empty` появляется системно, не только при перегрузке.
- Логи gateway: нет строки «minting assertion for tools/list».
- Логи backend: `authenticate()` вызван для tools/list → ошибка.
- tools/call при этом работает корректно (assertion минтится).

## Диагностика

Читать логи gateway и backend одновременно. Ключевой вопрос: «Для каких MCP-методов gateway минтит assertion?» Если список не совпадает с тем, что backend требует — найдена причина.

## Митигация

Привести оба контракта к одному списку методов, требующих авторизации. Решение (какую сторону менять) — за владельцем сервиса. Промежуточный вариант: gateway минтит assertion для всех методов, не только tools/call.

## Тест обнаружения

«Совпадает ли список MCP-методов, для которых gateway минтит assertion, с тем, что требует backend?» Нет → потенциальный DP.FM.607.
