---
id: DP.SC.148
name: Pack Graph Freshness
type: sc
status: draft
layer: L2-Platform
summary: "Pack-граф (concept_graph_nodes + edges) обновляется автоматически при push в Pack-репо и проверяется daily heartbeat + drift detector"
consumer: R21 Publisher (бот), Навигатор (MIM.R.007), любой MCP-клиент с knowledge_pack_traverse
uses:
  - DP.SC.034    # Gateway MCP (webhook channel)
  - DP.SC.005    # Content publishing (pack update trigger)
extends: []
created: 2026-05-19
updated: 2026-05-19
---

# [DP.SC.148] Pack Graph Freshness

<!--
  WP-339. Решает: при push в Pack-репо webhook обновляет только knowledge_chunk,
  но не concept_graph. Граф устаревает, и knowledge_pack_traverse отвечает по
  устаревшему срезу. Три защитных слоя: webhook (L1), heartbeat cron (L2),
  drift detector (observability).
-->

## Правило (инвариант)

- [ ] **Единый pipeline**: один и тот же код обновляет chunks (knowledge_chunk) и edges (concept_graph) для одного файла. Не два независимых pipeline.
- [ ] **Content-hash skip**: если хеш файла не изменился — skip (zero-cost повторная обработка). Хеш хранится в concept_graph.concepts.content_hash (миграция 014).
- [ ] **Idempotency**: двойной webhook не создаёт дубли (UPSERT на уникальном ключе code для concepts, ON CONFLICT DO UPDATE для edges).
- [ ] **Атомарность per file**: `BEGIN` → удалить старые edges для файла → upsert concepts/artifacts → insert новые edges → `COMMIT`.
- [ ] **Removed handling**: для `action=removed` — удалить все nodes и edges, ассоциированные с файлом.

## Обещание

**Кому:** Пользователи IWE (пилоты), LLM-агенты (Kimi, Claude), MCP-клиенты через `knowledge_pack_traverse`.

**Зачем:** Запросы к графу понятий (`knowledge_pack_traverse`, `analyze_verbalization`) отвечают по актуальному состоянию Pack-репозиториев без ручного `npx tsx scripts/ingest-concepts.ts`.

**Что получит:**
- **Push → граф обновлён за ≤60 сек** — webhook вызывает `reindexConceptsForFiles(changed_files)`.
- **Silent-fail защита** — daily heartbeat (00:30 UTC) перестраивает граф для всех файлов со skip по content_hash.
- **Drift visibility** — метрика `drift_artifacts = count(.md in Pack repos) - count(artifact nodes)` с алертом при diff > 5.
- **Ручной ingest deprecated** — `scripts/ingest-concepts.ts` помечен как «cold-start only», не требуется в regular operations.

**Триггер:**
- (L1) GitHub push webhook → Gateway → `/reindex` knowledge-mcp
- (L2) Daily cron 00:30 UTC → `/reindex` с полным списком файлов
- (L3) Manual MCP tool `reindex_pack_graph` (fallback)

**Время отклика (δ):**
- Webhook path: ≤60 сек от push до `knowledge_pack_traverse` видит новый edge.
- Heartbeat path: ≤24 ч (периодичность cron).

**Режим отказа:**
- Webhook fail / Gateway down → heartbeat ловит за 24 ч.
- Heartbeat fail → drift detector алертит при diff > 5.
- Drift detector fail → manual MCP tool `reindex_pack_graph` как fallback.
- OpenAI embeddings API fail → skip файла, записать error в health.graph_usage_events, retry на следующем heartbeat.

## Свидетельства (критерий приёмки)

**Данные:**

| Критерий | Как проверить |
|----------|--------------|
| Push в PACK-systems-art → новый edge виден за <60с | E2E: добавить `[SA.D.005]` в `pack/SA.D.001.md` → push → `knowledge_pack_traverse(seed=SA.D.001)` возвращает edge за <60с |
| Content-hash skip работает | Повторный webhook с теми же файлами → processed=0, skipped=N, latency <1с |
| Removed обрабатывается | Удалить `pack/test.md` → push → `SELECT count(*) FROM concept_graph.concepts WHERE code LIKE '%/test.md'` = 0 |
| Drift detector видит расхождение | Удалить файл из репо без push → drift metric diff ≥ 1 за <24ч |
| Heartbeat обновляет протухший граф | Остановить webhook на 48ч → cron восстанавливает freshness |

**Полномочия:**

- Gateway webhook имеет право вызывать `/reindex` с shared secret (REINDEX_SECRET).
- Heartbeat cron имеет право вызывать `/reindex` с тем же secret.
- MCP tool `reindex_pack_graph` доступен только пилоту с правом записи в Pack-репо (owner).

**Свидетельства (наблюдаемость):**

- Метрика `latency_webhook_to_graph_update_ms` — записывается в `health.graph_usage_events`.
- Метрика `drift_artifacts` — diff между файлами в репо и artifact nodes.
- Метрика `heartbeat_skip_rate` — % файлов, пропущенных по content_hash на heartbeat.
- Лог `phase: graph_reindex` с полями `source, files_count, processed, skipped, errors`.

## Сценарии использования

### Сценарий 1: Пилот редактирует Pack и сразу запрашивает граф

**Кто:** Пилот в VS Code / Claude.ai
**Когда:** push в PACK-personal
**Что происходит:**
1. GitHub webhook → Gateway → `/reindex` (knowledge-mcp)
2. `reindexFiles` обновляет chunks
3. `reindexConceptsForFiles` обновляет graph nodes + edges для changed files
4. Пилот спрашивает «покажи связи моего нового метода» — `knowledge_pack_traverse` видит свежий edge

**Тест приёмки:** E2E сценарий Ф7 WP-339.

### Сценарий 2: Kimi работает batch и через 30 мин ожидает свежий граф

**Кто:** Kimi в peer-agent сессии
**Когда:** после серии правок в Pack
**Что происходит:**
1. Webhook обрабатывает каждый push инкрементально
2. Если push не пришёл (rate limit, GitHub delay) — heartbeat через ≤24ч восстановит
3. Kimi вызывает `knowledge_pack_traverse` — граф не старше 24ч

### Сценарий 3: Внешний MCP-клиент в claude.ai обращается через час после публикации

**Кто:** Пилот через cloud Gateway
**Когда:** через 1 ч после push
**Что происходит:**
1. Webhook уже обработал push за <60с
2. Граф свежий — клиент получает актуальный ответ
3. Если webhook не дошёл — heartbeat зафиксирует через ≤24ч

## Связи с другими SC

- **DP.SC.034 (Gateway MCP):** webhook channel — тот же канал расширяется на graph edges
- **DP.SC.005 (Content publishing):** push в Pack = триггер для обоих pipeline (chunks + graph)
- **DP.SC.009 (Analytics):** drift metric и latency metric пишутся в health-дашборд

## Антипаттерны

- ❌ **Два независимых pipeline**: chunks обновляется через webhook, graph — вручную. Дрейф неизбежен.
- ❌ **Полный rebuild на каждый push**: без content_hash skip — API rate limit и latency >60с.
- ❌ **No removed handling**: удаление файла из репо не удаляет orphan nodes/edges — граф загрязняется.
- ❌ **Heartbeat без skip**: daily cron перестраивает всё заново — бессмысленная нагрузка.

## Открытые вопросы

- Q1: Heartbeat деплоить через systemd timer (tsekh-1) или GitHub Actions cron? → решить в Ф5 WP-339.
- Q2: Drift detector — отдельный cron или part of heartbeat? → part of heartbeat (один запрос).
- Q3: content_hash для concept_graph — добавить колонку в concepts или отдельная таблица? → колонка в concepts (миграция 014).
