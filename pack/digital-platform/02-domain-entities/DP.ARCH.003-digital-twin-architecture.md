---
id: DP.ARCH.003
version: v1.0
name: Архитектура Digital Twin — единая точка расчёта и чтения
type: domain-entity
status: active
valid_from: 2026-04-30
summary: "8 принципов разделения Calculator / Reader. Единственный калькулятор — Профилировщик (DP.ROLE.116). Интерфейсы — stateless витрины. Каждая цифра трассируется к IND-коду метамодели."
related:
  uses: [DP.ARCH.004, DP.ROLE.028]
  enables: [DP.SC.125]
  source_wp: WP-218
---

# DP.ARCH.003 — Архитектура Digital Twin

## Контекст

До WP-218 (апр 2026) расчётная логика `calculate_derived` существовала в нескольких местах одновременно: в боте (`db/queries/dt_calc.py`), в `digital-twin-mcp` (`src/profile-calculator.js`). Это порождало расхождения показателей: один и тот же пользователь видел 47/100 в боте и 79.9/100 в браузере. Корневая причина — отсутствие единственного калькулятора и единого пути чтения.

## Решение — 8 принципов

### Принцип 1: Единственный калькулятор

Все расчётные показатели вычисляются в одном месте — **Профилировщик (DP.ROLE.116)** (`DS-ai-systems/profiler/scripts/dt_calc.py`). Ни один интерфейс (бот, MCP, CLI) не выполняет расчёт самостоятельно.

Реализация: `DS-ai-systems/profiler/scripts/recalculate_derived.py` — standalone runtime, подключается к Neon напрямую через psycopg2, итерирует все `digital_twins`, читает `data['2_collected']`, вычисляет и пишет только в `data['3_derived']`.

### Принцип 2: Метамодель = реестр индикаторов (source of truth)

`digital-twin-mcp/metamodel/3_derived/*.md` — единственный реестр IND-кодов и их спецификаций (имя, единица измерения, входы из `2_collected`, пороги ступени). Добавление нового индикатора = обновление метамодели + `dt_calc.py` в одном коммите. Других мест нет.

### Принцип 3: Метамодельная трассируемость

Каждое число, которое интерфейс показывает пользователю, связано в коде с IND-кодом из метамодели. Комментарий над обращением к `3_derived`:

```python
# IND.3.10.1 Интегральный индекс агентности
# Писатель: profiler/scripts/dt_calc.py:calc_integral_agency_index
agency = derived.get("3_10_integral") or {}
```

Проверка: grep по handler'ам должен показывать только известные IND-коды над каждым чтением из `3_derived`.

### Принцип 4: Stateless-интерфейсы

Бот `/twin`, `digital-twin-mcp read_digital_twin`, CLI — все делают один SELECT из `digital_twins.data['3_derived']` через Gateway MCP → Ory JWT → ory_id → правильная запись. Никаких локальных вычислений. В UI отображается `calculated_at` — метка когда profiler последний раз пересчитывал данные.

### Принцип 5: Single writer в `3_derived`

Только Профилировщик (DP.ROLE.116) пишет в `3_derived`. Все триггеры (cron 04:30 MSK, on-demand) вызывают один и тот же `recalculate_derived.py`. Бот — pure collector: пишет только в `2_collected`.

### Принцип 6: Event-driven пересчёт как целевой режим

Cron 04:30 MSK остаётся safety net. Целевой триггер — событие Activity Hub (WP-73 Ф3): при поступлении `coding_time`, `git_commit`, `wp_completed`, `learning_step` profiler пересчитывает `3_derived` для соответствующего пользователя.

On-demand пересчёт из MCP интерфейса **не нужен** — добавляет второй путь расчёта, нарушает Принцип 1.

### Принцип 7: Мёртвого кода не оставлять

Ветки эволюции, которые больше не соответствуют архитектуре, архивируются полностью (не «deprecated», не комментарии). Пример: `digital-twin-mcp/src/profile-calculator.js` + `mapping.js` + tool `get_profile_by_areas` → `_archive/pre-4type-projection/` (WP-218 Ф4). Ясность важнее обратной совместимости в dev-инфраструктуре.

### Принцип 8: Расчётные индикаторы расширяются парно с источниками

Каждая новая группа в `2_collected` (например `2_10_*`) влечёт парную работу: (а) обновление метамодели `3_derived/*/*.md` + (б) новая функция `calc_IND_X_Y_ZZ_name` в `dt_calc.py`. Добавить коллектор без формулы = мёртвые данные. Добавить формулу без коллектора = нет входа.

## Последствия

**Выгоды:**
- Одна цифра — один источник: расхождения 47 vs 79.9 невозможны архитектурно.
- Трассируемость: любая цифра в UI связана с IND-кодом → понятно как отладить.
- Масштабируемость: новый IND = метамодель + одна функция, интерфейсы не трогаются.

**Ограничения:**
- On-demand пересчёт требует отдельного механизма вызова (WP-73 Ф3).
- При недоступности profiler (cron не запустился) данные устаревают до следующего цикла.

## Связи

| Артефакт | Роль |
|----------|------|
| `DS-ai-systems/profiler/scripts/dt_calc.py` | Canonical calculator — Профилировщик, DP.ROLE.116 |
| `DS-ai-systems/profiler/scripts/recalculate_derived.py` | Standalone runtime для пересчёта |
| `digital-twin-mcp/metamodel/3_derived/` | Реестр IND-кодов (source of truth) |
| `aist_bot_newarchitecture/db/queries/dt_sync.py` | Pure collector — пишет только `2_collected` |
| `aist_bot_newarchitecture/handlers/twin.py` | Pure reader — SELECT `3_derived` через Gateway |
| `digital-twin-mcp/src/index.js` | MCP interface — `read_digital_twin`, `write_digital_twin`, `describe_by_path` |
| `digital-twin-mcp/_archive/pre-4type-projection/` | Архив legacy projection-слоя (pre-4type-schema) |
| DP.ARCH.004 | Размещение `digital_twins` в Neon БД `indicators` (#5) |
| WP-218 | РП-источник этих принципов |
| WP-73 Ф3 | Event Bus — event-driven триггер (blocked) |
