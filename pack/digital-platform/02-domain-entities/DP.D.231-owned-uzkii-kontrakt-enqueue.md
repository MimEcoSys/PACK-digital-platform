---
id: DP.D.231
name: "Owned узкий контракт enqueue (producer → API/RPC) ≠ raw cross-service SQL write"
type: distinction
pack: PACK-digital-platform
domain: digital-platform
trust: confirmed
epistemic_stage: observed
status: active
valid_from: 2026-07-11
created: 2026-07-19
source: "миграция из 01B-distinctions.md (РП170 Ф2, 2026-07-19)"
see_also: []
schema_version: 1
---

# DP.D.231: Owned узкий контракт enqueue (producer → API/RPC) ≠ raw cross-service SQL write

Производитель публикует НАМЕРЕНИЕ через owned-контракт получателя (`enqueue` — узкий API/RPC, зеркало канало-агностичного `send()`). Он НЕ пишет сырой SQL в БД сервиса-получателя напрямую. Разделение ответственности:
- **Producer (Nudge Engine):** решает ЧТО доставить и КОГДА по смыслу (контент, уместность). `scheduled_at` НЕ входит — это будущая data-driven политика получателя.
- **Consumer (Приёмщик и Распорядитель доставки, DP.ROLE.123, 075):** решает ПРОПУСТИТЬ ли (потолок/дедуп/opt-out) и КОГДА физически.

**Тест:** «Производитель пишет в БД получателя напрямую (INSERT/UPDATE)?» Да → нарушение границы. Должен идти через `enqueue` (API/RPC).

**Связано с:** «Источник доставки ≠ Политика-на-место ≠ Физический транспорт» (уточняет ось «owned-контракт vs raw cross-service write»), «Gateway с одной ответственностью ≠ Gateway с прикладной логикой» (тот про gateway; этот про любую producer-consumer границу).

**Источник:** WP-117 Ф-integration peer-session 2026-06-21 (DP.SC.116 «Контракт enqueue», «Связь с DP.SC.177»).
