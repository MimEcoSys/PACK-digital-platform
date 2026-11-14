---
id: DP.CONCEPT.010
name: Карта-derived routing без freeze-at-assignment — temporal fallback в маске централизованной маршрутизации
type: domain-entity
trust: theoretical
epistemic_stage: distinction
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_temporal_fallback_routing.md (WP-324 Ф7, архитектурное ревью 17.05; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [PACK-digital-platform, PACK-digital-platform]
---

# DP.CONCEPT.010: temporal fallback — freeze-at-assignment

## Различение
Тест: «может ли результат оказаться в нескольких местах?»
- Явный path в task — однозначен.
- Карта-derived БЕЗ override, с freeze — однозначен (карта не меняется для in-flight).
- Карта-derived С override или БЕЗ freeze — два возможных места / зависимость от версии карты в момент исполнения = temporal fallback.

## Четыре условия легитимности Карта-derived routing
1. **Нет override** — либо routing_key, либо explicit result_location, не оба.
2. **Derivation тотальная и pure** — детерминированная функция; unknown kind = failed, не дефолт.
3. **Freeze в момент постановки** — dispatcher при assigned материализует result_location и записывает в frontmatter task: карта — генератор первой версии, task — снапшот.
4. **Разделение карты** — исполняемая routing-функция не живёт в справочной карте для людей (отдельный документ).

## Где ещё тот же паттерн
- Путь в конфиг-файле без freeze (значение при написании ≠ при запуске).
- Feature flag с default-value (код идёт по двум путям в зависимости от наличия конфига).
- DNS alias с TTL (запись имени ≠ снапшот IP).

## Экономика
Цена 4 условий + новый документ > выигрыша на малых масштабах (1 пилот, <10 kinds, стабильная структура) — строить не нужно, явные пути корректнее.
