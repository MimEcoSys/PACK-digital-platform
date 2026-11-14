---
id: DP.FM.760
name: Ротация PEM-ключа в CF Worker без пробы записи — 18ч silent breakage (PKCS#1 vs PKCS#8, потерянные заголовки при upload)
type: failure-mode
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_cf_worker_jwt_pkcs8.md (WP-7 Ф-MCP-JWT-PKCS, 21-22.05; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [AR.205, PACK-digital-platform]
---

# DP.FM.760: JWT-ключ в CF Worker после ротации

## Симптом
18ч: `personal_write` падает с opaque `Backend error: Invalid PKCS8 input`, чтение работает. Деплои зелёные.

## Двойной root cause
1. **Latent code:** createGitHubAppJWT поддерживал regex только PKCS#1 PEM-заголовков, но передавал DER в `importKey("pkcs8", …)` — работало только из-за либеральности BoringSSL; рантайм CF ужесточился.
2. **Operational:** после `wrangler secret put` секрет оказался БЕЗ PEM-заголовков (pipe-echo без `-e` или JSON-encoded copy ломает переводы строк). Первая гипотеза «PKCS#8 vs PKCS#1» оказалась неверной — GitHub отдаёт PKCS#1, потерялись заголовки.

## Паттерн
Ротация credential внешнего сервиса → **выкладка → smoke-проба записи** обязательна (rotate → deploy → probe), не только проверка чтения. Чтение может не трогать затронутый код-путь.

## Тест обнаружения
Прямая проба: после ротации — один реальный write-вызов против API, сверка отсутствия 4xx/5xx. См. AR.205 (probe 4 слоя).
