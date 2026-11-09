---
id: DP.ECON.001
name: Points Engine — движок начисления баллов
type: domain-entity
status: draft
summary: "Доменная модель системы баллов: сущности, инварианты, формула, потоки. Source-of-truth для Points Engine (WP-121, WP-311). Текущая реализация: база rewards (Neon)."
created: 2026-04-13
updated: 2026-05-17
related:
  realizes: [DP.SC.105, DP.SC.122]
  uses: [DP.ARCH.004, DP.ARCH.006, DP.SYS.001]
  source: "WP-121 Ф0 калибровка 9 апр 2026, Ф1 миграции 13 апр, Ф2 v2 PL/pgSQL 8 мая; WP-311 Ф0b обновление 17 мая (current v2 model)"
tags: [points, contribution-economy, gamification, billing]
---

# [DP.ECON.001] Points Engine — движок начисления баллов

> **Обещания потребителям:** [DP.SC.105 Экономика вклада](../08-service-clauses/DP.SC.105-reputation-economy.md) (бизнес-смысл), [DP.SC.122 Rewards Projection](../08-service-clauses/DP.SC.122-rewards-projection.md) (техническое обещание потребителям balance).
> **Текущая реализация (v2):** Neon БД `rewards`, PG-функция `rewards.compute_effective_amount()` (миграция [`205-rewards-compute-effective-amount.sql`](../../../../DS-IT-systems/neon-migrations/mvp/205-rewards-compute-effective-amount.sql), WP-121 Ф2 v2, 8 мая 2026). Roll-out: SC.122 закрыт по latency 24 апр; backfill завершён 17 мая (WP-121 Ф-Close).
> **Калибровка v1:** WP-121 Ф0, 9 апр 2026 — 66 934 events, 102 users, целевой payout 20.4%.

---

## 0. Версионирование модели

| Версия | Что | Когда | Где |
|--------|-----|-------|-----|
| **v1** | `Base × ActionType × Streak × Qualification × daily_cap`. БД `platform` схема `points`. Категории `time/wp/quality/platform/condition/none`. 8 квалификаций. | 13 апр 2026 (WP-121 Ф1) — **архивирована, не deployed** | §§2-12 ниже (исторический baseline калибровки) |
| **v2 (текущая)** | `base × dom × qual × streak`, capped by `min(dom_cap, qual_cap) − today_total`. БД `rewards` (Neon). Активити-домены `learning/practice/work`. Для уровня 4 (Ученик) множитель = stage 1-5; для уровней 5-11 — qualification_multipliers. Streak: COUNT(DISTINCT DATE day_plan_closed) за 7 дней / 7 × 0.5 + 1.0, capped 1.5. | 8 мая 2026 (WP-121 Ф2 v2) — production | §1.5 ниже |

**Расхождения v1 → v2 (что переехало):**
- `point_rules` → `reward_rules` (Neon, schema `reference`)
- `point_transactions` → `applied_events` (Neon, schema `rewards`)
- `point_balances` остаётся, но в схеме `rewards`
- `ActionType` (×1/×2/×3/×5 через category) → `dom` (×1/×3/×5 через `activity_domain_multipliers`)
- Квалификация: 8 степеней МИМ остаются, но теперь дополнены student_stage 1-5 для уровня 4 (Ученик) — единая шкала уч.прогресса
- Идемпотентность: `UNIQUE(event_id)` в `point_transactions` → `PK applied_events.event_id`
- Проекция: монолитная `calculate_points()` → split на `compute_effective_amount()` (расчёт) + `multi-domain-projection-worker` (доставка из `learning.domain_event`)

---

## 1.5. Формула v2 (current production)

```
effective = LEAST(base × dom_mult × qual_mult × streak_mult, daily_cap_remaining)
where:
  base               = reward_rules.amount (lookup by trigger_event + match_condition <@ payload)
  dom_mult           = activity_domain_multipliers.multiplier
                       domain ∈ {learning, practice, work}
                       resolve: _event_type_to_domain(event_type) OR repo_domain_map[payload.repo]
  qual_mult          = student_stage_multipliers.multiplier (если level=4)
                       OR qualification_multipliers.multiplier (level 5-11)
                       fallback: 0.5 + 0.2 × level (для level 1-3)
  streak_mult        = LEAST(1.0 + days/7 × 0.5, 1.5), GREATEST(_, 1.0)
                       days = COUNT(DISTINCT DATE day_plan_closed events за 7д до ingested_at)
                       только если reward_rules.streak_eligible
  daily_cap          = LEAST(dom_cap, qual_cap)  -- более жёсткий
  daily_cap_remaining = GREATEST(0, daily_cap − SUM(applied_events.effective WHERE DATE = today))

  cap_truncated = (effective < raw)  -- audit-флаг
```

**Источник правды:** [`205-rewards-compute-effective-amount.sql`](../../../../DS-IT-systems/neon-migrations/mvp/205-rewards-compute-effective-amount.sql) (PL/pgSQL, lines 174-325).

**Текущее состояние данных (state 16 мая, последний probe):**
- `reference.reward_rules`: 40 enabled triggers (35 типов событий за 7 дней)
- `rewards.point_balances`: 3889 accounts, 4.18M points total
- `rewards.applied_events`: журнал начислений с разложением (audit: base/dom/qual/streak/cap_truncated)
- Cursor (multi-domain): `learning.processed_events.rewards-projection.last_event_id` = 646043 (lag ~18 events)
- Cursor (legacy backfill): `rewards.processed_events.point_balances` = 631679 (97.6%) — decommission'd 17 мая

**Что осталось:** 20 мая final smoke wave-1 (WP-188 Ф4.5 + WP-311 Ф5).

---

## v4.4 (дизайн, ожидает deploy)

> **Источник:** WP-327 v4.4 (18–22 мая 2026). Реализация не задеплоена. V2 продолжает работать в production.

### Формула v4.4

```
баллы = вес × коэф_Квалификации × коэф_серии
где:
  вес                = фактор_усилия × коэф_редкости × коэф_группы
  коэф_Квалификации  = lookup по 12 ступеням (таблица ниже)
  коэф_серии         = streak_multiplier (4 уровня)
  daily_K            = управляющий параметр панели (default: 8)
  daily_cap          = base_multiplier × daily_K × max(коэф_группы)
```

### Панель управления (7 ручек)

| Ручка | Default | Описание |
|-------|---------|----------|
| `rate` | авто | EMA-ставка (0.01–0.20) |
| `budget_pct` | — | % выручки на выплаты |
| `referral_pct` | — | % пула на рефералы |
| `base_multiplier` | 25 | Базовый множитель баллов |
| `daily_K` | 8 | Дневной cap в единицах base_multiplier |
| `streak_max` | ×2.2 | Максимальный streak-коэффициент |
| `welcome_bonus` | 100 | Стартовые баллы при регистрации |

### 12 ступеней квалификации

| Ступень | Название | коэф_Квалификации |
|---------|----------|-------------------|
| 1 | Случайный | ×0 |
| 2 | Практикующий | ×0.4 |
| 3 | Систематический | ×0.7 |
| 4 | Дисциплинированный | ×1.0 |
| 5 | Проактивный | ×1.3 |
| 6 | Интеллектуал | ×1.6 |
| 7 | Профессионал | ×2.0 |
| 8 | Исследователь | ×2.5 |
| 9 | Просветитель | ×3.0 |
| 10 | Лидер сообщества | ×3.5 |
| 11 | Архитектор экосистем | ×4.0 |
| 12 | Общественный деятель | ×5.0 |

### 4 группы активности

| Группа | Название | коэф_группы |
|--------|----------|-------------|
| G1 | Личное развитие | ×1 |
| G2 | Продукт и ИИ | ×2 |
| G3 | Знания | ×3 |
| G4 | Сообщество | ×4 |

### Серия (streak) — 4 уровня

| Дней подряд | коэф_серии |
|-------------|------------|
| 0–6 | ×1.0 |
| 7–13 | ×1.3 |
| 14–27 | ×1.7 |
| 28+ | ×2.2 |

### EMA-ставка

```
new_rate = old_rate × (1 - α) + raw_rate × α
где α = 0.3, clamp(0.01, 0.20)
```

---

## 1. Ключевое различение

> ⚠️ **Секции 1-12 ниже = v1 (исторический baseline калибровки).** Текущая production-формула — §1.5 выше. Cекции v1 сохранены: (а) для калибровочных коэффициентов (payout 20.4%, B-сценарий со streak); (б) как baseline для будущих ревизий. Имена таблиц `point_rules`/`point_transactions` в v1-тексте = НЕ актуальные имена БД (они в v2 → `reward_rules`/`applied_events`, schema `rewards` в Neon).

### 1.1. Три системы учёта одной активности

| Система | Что считает | Убывает? | Ограничение | Кто пишет |
|---------|------------|----------|-------------|-----------|
| **Баллы** | earned_total — сумма всех начислений за всё время | Никогда | — | DP.ROLE.034 |
| **Бонусы** | доступный лимит скидки = `min(points, Σ(active_days_at_qual_i × daily_cap_i))` | Да (при оплате) | история × дневной cap квалификации | DP.ROLE.051 |
| **Ступень** | cp-профиль FORM.089 (13 срезов + 7 bh) | Нет | — | Профилировщик (DP.ROLE.116) |

**Баллы** — геймификация, лидерборд, история. Никогда не уменьшаются (только earned_total растёт).

**Бонусы** — лояльность, скидка при оплате. Формула с учётом смены квалификации:

```
бонусы = min(
  point_balances.points,                     -- баллы (earned − spent)
  Σ(active_days_at_qualification_i × daily_cap_i)  -- исторический cap
)
```

Где `Σ` — сумма произведений «дней на текущей квалификации × daily_cap той квалификации». Вычисляется из `rewards.applied_events.qualification_snapshot` (уже содержит снимок квалификации на момент каждого события). Защита: бонусов не может быть больше, чем пилот реально «заработал» с учётом своей квалификации в каждый из активных дней.

**Архит. TODO (~2h):** добавить `earned_total` в `point_balances` (сейчас `points` = earned − spent). Тогда `points` → текущий баланс (убывает при оплате); `earned_total` → никогда не убывает = настоящие Баллы для лидерборда. Завести как отдельный WP после Этапа 4 WP-327.

**Ступень** (cp-профиль) определяет `daily_cap` — тем самым влияет на максимальный размер бонусов.

---

**Баллы = вычисляемая проекция**, а не хранимое состояние.

```
user_events (факты, append-only)
  │
  ▼
Readiness Gate (WP-109 Ф4)
  │ все источники synced + checksum OK?
  ▼
calculate_points()
  │ event + point_rules → effective_points
  ▼
points.point_transactions (начисления, append-only)
  │
  ▼
points.point_balances (агрегат-кэш)
  │
  ▼
Бот: /points (пользователь видит)
```

Пересчёт = replay всех events по текущим rules. Один event → максимум одна транзакция.

---

## 2. Формула начисления

```
effective_points = min(Base × ActionType × Streak × Qualification, daily_cap)
```

| Множитель | Источник | Диапазон |
|-----------|---------|---------|
| **Base** | `points.point_rules.points` | 2–69 pts/event |
| **ActionType** | `points.point_rules.category` | ×1 / ×2 / ×3 / ×5 |
| **Streak** | `points.point_balances.streak_multiplier` | ×1.0 – ×1.5 |
| **Qualification** | `points.qualification_multipliers.multiplier` | ×1.0 – ×5.0 |
| **daily_cap** | `points.qualification_multipliers.daily_cap` | 100 – 1000 |

---

## 3. Сущности

### 3.1. point_rules — правила начисления

Какой `event_type` → сколько базовых баллов, лимит в день.

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | SERIAL PK | — |
| `event_type` | TEXT | Тип события (topic_created, wp_completed, …) |
| `source` | TEXT | lms / bot / iwe / club / NULL=любой |
| `category` | TEXT | time / wp / quality / platform / condition / none |
| `points` | INTEGER | Базовые баллы (0 для none/condition) |
| `max_per_day` | INTEGER | Лимит событий типа за день (anti-abuse) |
| `active` | BOOLEAN | Версионирование: false = деактивировано |
| `valid_from/until` | TIMESTAMPTZ | Для replay по историческим правилам |

**Категории действий (ActionType):**

| Категория | Множитель | Примеры |
|-----------|-----------|---------|
| `time` | ×1 | text_submitted, commit_created, ai_chat |
| `wp` | ×2 | wp_completed, content_published |
| `quality` | ×3 | knowledge_extracted, distinction_added |
| `platform` | ×5 | fmt_commit_merged |
| `condition` | — | day_open, day_close (условие, не баллы) |
| `none` | — | session_start, reminder_delivered |

> Примечание: base points в таблице уже отражают категорийный множитель (откалиброваны ×2.3 от единицы для достижения payout 20%). `ActionType` в формуле = 1 при category=time, т.е. реализован через разницу в `points`.

### 3.2. qualification_multipliers — 8 степеней квалификации МИМ

Источник: [system-school.ru/qualification](https://system-school.ru/qualification).

| Квалификация | Множитель | Daily cap | Описание |
|---|---|---|---|
| Ученик | ×1.0 | 100 | Ежедневный слот, 10+ ч/нед |
| Работник | ×1.3 | 140 | Рациональная работа, причинно-следственный анализ |
| Стратег | ×1.6 | 200 | Выбор метода в неопределённости |
| Специалист | ×2.0 | 280 | Инженерный процесс, широкая эрудиция |
| Практик | ×2.5 | 360 | Применяет на практике, организует до 10 человек |
| Мастер | ×3.0 | 500 | Проекты оргразвития в масштабе компании |
| Реформатор | ×4.0 | 700 | Масштаб отрасли и сообщества |
| Общественный деятель | ×5.0 | 1000 | Цивилизационный масштаб |

**Квалификация ≠ тир подписки (DP.D.047).** Тир = уровень доступа (оплата). Квалификация = степень мастерства (поведение + экзамен МИМ, 3 года).

Квалификация читается из ЦД (`digital_twins.data.3_derived`). Points Engine **не вычисляет** квалификацию — только читает.

### 3.3. point_transactions — журнал начислений (append-only)

| Поле | Тип | Описание |
|------|-----|---------|
| `id` | BIGSERIAL PK | — |
| `user_id` | TEXT | Ory UUID (T1+) или telegram_id::text (T0) |
| `event_id` | BIGINT UNIQUE | → development.user_events.id (1:1, NULL для spent/manual) |
| `rule_id` | INTEGER | → point_rules.id |
| `points` | INTEGER | Effective points (уже с множителями, может быть отрицательным) |
| `type` | TEXT | earned / spent / correction / expired / manual |
| `qualification` | TEXT | Снимок квалификации на момент начисления |
| `source_region` | TEXT | world / ru (для аудита по юрисдикциям) |
| `reference_id` | BIGINT | Для correction → оригинальная транзакция |
| `action_type_mult` | NUMERIC | Множитель категории (аудит + SBT) |
| `streak_mult` | NUMERIC | Множитель streak (аудит) |
| `qual_mult` | NUMERIC | Множитель квалификации (аудит) |
| `action_hash` | TEXT | SHA-256(event_id, rule_id, user_id, points) — для SBT |
| `verified_by` | TEXT | Верификатор (будущее: peer-review) |
| `milestone_eligible` | BOOLEAN | TRUE = засчитывается в milestone для SBT |

**Типы транзакций:**
- `earned` — начисление по правилу (calculate_points)
- `spent` — списание при оплате баллами (Billing Service, WP-183)
- `correction` — ручная корректировка (±, reference → оригинал)
- `expired` — истечение срока (политика expiry, будущее)
- `manual` — ручное начисление администратором

### 3.4. point_balances — агрегированный баланс (кэш)

| Поле | Описание |
|------|---------|
| `user_id` | TEXT PK — Ory UUID или telegram_id::text |
| `total_earned` | Сумма всех earned транзакций |
| `total_spent` | Сумма всех spent транзакций |
| `total_corrections` | Сумма всех correction транзакций |
| `balance` | total_earned − total_spent + total_corrections |
| `streak_days` | Текущий streak (дней подряд) |
| `streak_multiplier` | Текущий множитель ×1.0–×1.5 |
| `last_active_date` | Дата последней активности (для расчёта streak) |

**Это кэш, не source-of-truth.** Source-of-truth = `point_transactions`. При replay: TRUNCATE point_balances → пересчёт из транзакций.

---

## 4. Инварианты

| # | Инвариант | Механизм |
|---|-----------|----------|
| I1 | Один event → максимум одно начисление | UNIQUE(event_id) в point_transactions |
| I2 | Events неизменяемы | Append-only user_events, нет UPDATE/DELETE |
| I3 | Транзакции неизменяемы | Append-only. Ошибка → INSERT correction |
| I4 | Баланс = сумма транзакций | point_balances = materialized SUM (кэш) |
| I5 | Начисление только при Readiness Gate OK | calculate_points() проверяет sync_log |
| I6 | Idempotent replay | Тот же event + тот же rule = тот же результат |

---

## 5. Streak

| День | Множитель |
|------|-----------|
| 1 | ×1.0 |
| 2 | ×1.07 |
| 3 | ×1.14 |
| … | … |
| 7+ | ×1.5 (максимум, удерживается) |
| Пропуск | сброс → ×1.0 |

«День» = Day Open + хотя бы 1 event из любого источника.

Штраф за отсутствие Day Open (×0.5) **отложен** до >30% активных дней содержат Day Open (сейчас 0.7%). Включать через `active=false` в соответствующем правиле.

---

## 6. Конвертация: бонусы → скидки

> **Конвертируются бонусы, не баллы.** Бонусы = `min(points, Σ(active_days_at_qual_i × daily_cap_i))` — ограниченная сумма, учитывающая историю квалификации пилота. Баллы (earned_total) в конвертацию напрямую не идут.

- Текущий курс: **1 бонус = 0,10 ₽**. Источник истины — активная запись `reference.loyalty_pool_config.rate`; бот использует то же значение как fallback.
- Применяется к: практикумам, семинарам, резидентурам, менторским сессиям, приоритетной ИИ-поддержке
- Скидка оформляется в юрлице покупки (РФ или мир, WP-215)
- Скидка может покрывать 100% стоимости (допустимо: вклад заслуживает бесплатного доступа)

**TODO:** уточнить механизм курса (источник: курс ЦБ на момент списания? фиксированный? кто writer?) — отдельный Pack-update РП.

---

## 7. Потоки данных

### 7.1. Начисление (earned)

```
user_events.INSERT (Activity Hub, WP-109)
  → Readiness Gate: все источники synced + checksum?
  → calculate_points(event, rules)
  → INSERT point_transactions (type='earned')
  → UPSERT point_balances
```

### 7.2. Списание (spent)

```
Участник → /buy_with_points → Billing Service (WP-183)
  → SELECT balance FROM point_balances
  → balance >= price?
  → INSERT point_transactions (type='spent', points=-N)
  → UPDATE point_balances
  → Выдать доступ
```

### 7.3. Replay (пересчёт)

```
Триггер: новые правила / исправление / аудит
  → TRUNCATE point_transactions (или archive)
  → FOR EACH event IN user_events ORDER BY created_at:
      calculate_points(event, rules_at(event.created_at))
  → Пересчёт point_balances
```

---

## 8. Readiness Gate (WP-109 Ф4)

Перед каждым вызовом `calculate_points()`:
1. Каждый source: последний sync = success, не старше 48h
2. Checksum: count в API источника == count в Neon (расхождение ≤3%)
3. Все проверки OK → начисление. Хоть одна ❌ → СТОП + алерт

Без Gate баллы начислялись бы по неполным данным → неточные балансы → потеря доверия.

---

## 9. Антизлоупотребления

| Механизм | Как работает |
|----------|-------------|
| `max_per_day` в point_rules | Лимит событий одного типа за день |
| `daily_cap` в qualification_multipliers | Потолок баллов за день по квалификации |
| Readiness Gate | Начисление только по подтверждённым данным |
| UNIQUE(event_id) | Дедупликация: один event = одна транзакция |
| Append-only | Нельзя задним числом изменить транзакцию |

---

## 10. Будущее: SBT (Soulbound Tokens)

**Триггер:** 500+ активных участников.

Поля подготовлены в `point_transactions`:
- `action_hash` — SHA-256 fingerprint транзакции
- `verified_by` — верификатор (peer-review, admin)
- `milestone_eligible` — засчитывается в milestone для mint

Стек: ERC-5192 (non-transferable), Base L2, Coinbase Smart Wallet.
Оценка: 60–110h, gas ~$5–50/мес.

---

## 11. Результаты калибровки (Ф0, 9 апр 2026)

> Данные: 66 934 events, 102 users (67 с >0 баллами), период 2020–2026.

| Сценарий | Payout% | Возврат/год |
|----------|---------|------------|
| A: без streak, без штрафа | 20.4% | $2 047 |
| B: + streak (рекомендуется) | 24.0% | $2 408 |
| C: + streak + штраф ×0.5 | 13.8% | $1 384 |

**Рекомендуемый сценарий B** (streak без штрафа). Включить штраф при >30% активных дней с Day Open.

---

## 12. Связи

| Сущность | Связь |
|----------|-------|
| DP.SC.105 | Реализует обещание «Экономика вклада» |
| DP.ARCH.006 | Память.Derived предоставляет квалификацию для множителя |
| DP.SYS.001 | Activity Hub поставляет user_events |
| WP-109 | Readiness Gate + Activity Hub |
| WP-183 | Billing Service вызывает spent-транзакции |
| WP-121 | РП реализации (Ф0–Ф5) |
| WP-215 | Региональное разделение (юрлицо конвертации) |

---

*Создано: 2026-04-13. WP: 121 Ф1 Pack. Калибровка: Ф0, 9 апр 2026.*
