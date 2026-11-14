---
id: DP.M.617
name: Cloudflare: один Worker на N custom domains (alias) и Worker как прозрачный proxy — критерии разделения
type: method
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_cf_custom_domain_alias.md (WP-305 A-lite 12.05, WP-319 Ф7 16.05; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [DP.FM.762, PACK-digital-platform]
---

# DP.M.617: CF custom domain alias — один Worker, N доменов

## Паттерн alias
В `wrangler.toml` несколько `routes` с `custom_domain = true` обслуживаются ОДНИМ Worker: логическое разделение endpoints (oauth.*, api.*) без отдельного deploy.

## Что alias НЕ даёт
- Отдельных secrets/env (все домены делят конфигурацию).
- Изоляции attack surface (RCE в одном endpoint затрагивает все).
- Независимого deploy cadence.
- Разной авторизации на уровне CF (разные tier-policies — только в коде).

## Когда переходить на отдельный Worker
1. >100 rps/day постоянно 2+ недель → capacity isolation.
2. Security incident → изоляция secrets/attack surface.
3. Multi-tenant (второй tenant со своим Ory) → tenant isolation.
4. LOC > 5000 → maintainability.

## Паттерн proxy (когда нет DNS write credentials)
`routes` без `custom_domain` перехватывают wildcard. Для WebSocket-апстрима (Streamlit `/_stcore/stream`): `redirect: "manual"` + явный `Host` header — без этого CF ломает WebSocket handshake. Streamlit за CF Worker обязан иметь `STREAMLIT_SERVER_ENABLE_CORS=false` (иначе «Rejecting WebSocket connection from disallowed origin»).
