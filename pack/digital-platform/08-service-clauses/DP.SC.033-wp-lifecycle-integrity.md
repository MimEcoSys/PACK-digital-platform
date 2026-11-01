---
id: DP.SC.033
name: Целостность состояний РП
name_ru: Целостность состояний РП
name_en: Work Product Lifecycle Integrity
type: sc
status: active
layer: L4-Personal
summary: "Стратег получает гарантию: статус любого РП одинаков во всех 5 хранилищах IWE в течение ≤5 минут после любого изменения. Нарушение = drift, обнаруживается автоматически."
consumer: R1 Стратег (DP.ROLE.012)
created: 2026-05-08
updated: 2026-05-08
related:
  realizes: [DP.M.010]
  uses: [DP.SC.013]
  role: DP.ROLE.037
wp: WP-297
---

# [DP.SC.033] Целостность состояний РП

## Правило (инвариант)

> Что ВСЕГДА должно выполняться. Нарушение = провал SC.

- Статус РП в inbox/frontmatter и WP-REGISTRY.md ВСЕГДА одинаков.
- done-РП НЕ остаётся в `inbox/` дольше одного Day Close.
- MEMORY.md содержит ТОЛЬКО `in_progress` / `pending` РП.
- Новый РП создаётся одновременно во всех 5 местах (атомарно или с немедленным ремонтом).
- drift type A (zombie WP) обнаруживается каждый Day Open через `active-wp-sweep.sh`.
- При архивации РП context-файл получает `status: archived` + `archived_at: YYYY-MM-DD`. Если в frontmatter нет поля `results_in` (ссылки на Pack/DS куда ушли результаты) — добавляется `results_not_captured: true` (TTL 7 дней, решается пилотом при Week Close).

### Инвариант inbox-lifecycle (DP.M.008 элемент #12 ТО)

Inbox — **транзитная зона**. Документы в `inbox/WP-N(/)` — временные handoff-материалы для исполнения РП. Финальные результаты РП (знания, решения, код) уходят в Pack или DS в процессе работы (через KE / apply-captures). После закрытия РП:
1. Context-файл → `archive/wp-contexts/WP-N(/)` через `git mv`
2. Pack/DS уже содержат результаты — проверяется по полю `results_in`
3. Если `results_in` нет → флаг `results_not_captured: true`, рассматривается при Week Close

Это правило формализует элемент **#12 ТО** (Техническое обслуживание) из DP.M.008.

## Обещание

**Кому:** R1 Стратег — при формировании DayPlan, при открытии сессии по РП.

**Зачем:** Стратег принимает решения на основе состояния РП. Если DayPlan показывает закрытые РП как активные — решения неверны. Drift разрушает планирование.

**Что получит:** DayPlan содержит только реально активные РП. MEMORY.md не содержит zombie. При любом изменении статуса все 5 хранилищ обновлены.

**Триггер:** Смена статуса РП (создание / переход in_progress→done / архивация).

**Время отклика:** ≤5 минут (Quick Close) или ≤следующего Day Close (максимум).

**Режим отказа:** drift обнаруживается `active-wp-sweep.sh` → секция `⚠️ Drift` в DayPlan → ручная архивация через `archive-done-wp.sh {N}`.

## Свидетельства (критерий приёмки)

**Данные** (что фактически существует):

| Критерий | Как проверить |
|----------|--------------|
| Нет zombie WPs в inbox/ | `bash active-wp-sweep.sh` — раздел `⚠️ Drift` пуст |
| MEMORY.md не содержит done-РП | `grep -c "done\|✅" MEMORY.md` → 0 в секции «Активные РП» |
| REGISTRY обновлён | `grep "~~${N}~~" WP-REGISTRY.md` — done-строки зачёркнуты |
| done-РП заархивированы | `ls inbox/WP-*.md` → нет файлов со `status: done` в frontmatter |

**Контекст** (при каких условиях обещание действует):

| Условие | Проверка |
|---------|---------|
| Day Close выполнен | `git log --oneline -1` в DS-my-strategy — коммит дня есть |
| Quick Close выполнен после сессии | open-sessions.log — строка закрыта |

**Полномочия** (кто уполномочен подтвердить):

| Роль | Что подтверждает |
|------|-----------------|
| R1 Стратег | Корректность решений об архивации |
| Регистратор РП (DP.ROLE.037) | Техническую консистентность хранилищ |
| R23 Верификатор (Haiku) | Формальное соответствие чеклисту Day Close |

**Свидетельства** (как узнать, что обещание выполнено):

| Свидетельство | Источник |
|--------------|---------|
| Вывод `active-wp-sweep.sh` без раздела `⚠️ Drift` | scripts/active-wp-sweep.sh |
| DayPlan содержит только in_progress РП | current/DayPlan YYYY-MM-DD.md |
| Коммит Day Close в DS-my-strategy | git log DS-my-strategy |

## Реализующие сервисы

| Сервис | Роль | Триггер |
|--------|------|---------|
| `active-wp-sweep.sh` | Детектор drift type A | 🤖 Day Open scaffold |
| `archive-done-wp.sh` | Ремонт drift type A | 👤 Стратег / 🤖 Day Close |
| `wp-new` skill | Атомарное создание | 👤 WP Gate Ритуал |
| `protocol-close.md §2` | Обновление frontmatter | 👤 Quick Close |

## Пользовательский путь (happy path)

| # | Шаг | Кто | Инструмент |
|---|-----|-----|-----------|
| 1 | Создаёт РП через WP Gate Ритуал | Стратег + Агент | wp-new skill |
| 2 | Работает по РП, закрывает сессию | Агент | Quick Close → frontmatter status |
| 3 | Day Close: обновляет REGISTRY + архивирует done | Агент | archive-done-wp.sh |
| 4 | Day Open: sweep проверяет drift | Агент | active-wp-sweep.sh |
| 5 | DayPlan содержит только реальные активные РП | Стратег | — |

## Связь с другими обещаниями

- Потребляет: **DP.SC.013** (work-session — протокол сессии)
- Реализует: **DP.M.010** (методика управления lifecycle)
- Используется в: **DP.SC.001** (daily-planning — DayPlan использует sweep)
