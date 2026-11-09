---
id: DP.ARCH.006
version: v1.0
name: Память (Observed события + Derived агрегаты)
type: domain-entity
status: active
summary: "Память — операционный слой модели пользователя. Писатель = платформа runtime, владелец = Neon. Два под-слоя: Observed (append-only события) + Derived (вычисляемые агрегаты, бывший узкий ЦД). Event Sourcing + CQRS. BKT, HLR, engagement, misconceptions, qualifications. Замещает основную часть монолита DP.ARCH.003."
created: 2026-04-22
updated: 2026-04-24
valid_from: 2026-04-22
derived_from: DP.ARCH.004@v2.6
trust:
  F: 4
  G: domain
  R: 0.6
epistemic_stage: emerging
related:
  specializes: [U.System]
  uses: [DP.ARCH.001, DP.ARCH.002, DP.ARCH.004, DP.CONCEPT.001, DP.SOTA.009, DP.D.052]
  used_by: [DP.AISYS.014, DP.CONCEPT.003, DP.ARCH.007, DP.SC.104]
  replaces_part_of: [DP.ARCH.003]
tags: [memory, event-sourcing, cqrs, learner-model, knowledge-tracing, observed, derived]
name_ru: "Память (Observed события + Derived агрегаты)"
---

# Память (Observed события + Derived агрегаты)

> **Implementation Note.** Event Sourcing паттерн (Observed → Derived → Projection), типы событий, проекции (BKT, HLR, engagement) — домен. Конкретные схемы Neon, RLS, pgbouncer, Python snapshot code — текущая реализация. Детали: [C2.IT-Platform / Data-Stores](../../../DS-ecosystem-development/C.IT-Platform/C2.IT-Platform/C2.2.Architecture/Data-Stores/).

> **Расщепление ЦД (WP-257 Ф5).** Монолит DP.ARCH.003 расщеплён на три сущности по writer+owner:
> - [DP.ARCH.005 Persona](DP.ARCH.005-persona-entity.md) — writer=user, owner=Git
> - **Память** (этот файл) — writer=платформа, owner=Neon
> - [DP.ARCH.007 Projection](DP.ARCH.007-projection.md) — writer=agent runtime, owner=ephemeral

## 1. Назначение

Память — **операционный слой модели пользователя**, куда платформа автоматически записывает **наблюдения** (что пользователь делал) и **вычисления** (что из этого следует).

**Ключевой принцип: ни одно действие пользователя не проходит мимо.** Каждое взаимодействие (ответ на тест, чат с ИИ, выполнение ДЗ, рефлексия, марафон, онбординг) записывается как **Observed-событие** и влияет на **Derived-проекции**.

**Writer + owner контракт:**
- **Writer:** платформа runtime (aist-bot, LMS, Claude Code, MCP, Стратег) через единый Activity Hub API
- **Owner:** Neon PostgreSQL (`digital-twin` DB #5, `activity-hub` DB #3 — см. WP-228 Ф25 для финального именования)
- **Reader:** MCP `dt_*`, Портной, Оценщик, Nudge Engine, Open Learner Model

**Память ≠ Персона:** Персона = «что пользователь говорит о себе» (writer=user, owner=Git). Память = «что платформа наблюдает и вычисляет» (writer=platform, owner=Neon). См. [DP.D.052](../01-domain-contract/DP.D.052-persona-memory-context.md).

> **Память как инфраструктура адаптивной персонализации:** Память — основа механизма Персонализации (механизм 1 из 3 в [DP.CONCEPT.003](DP.CONCEPT.003-adaptive-personalization.md)). Данные Памяти.Derived → Портной → персонализированный контент. Механизм Адаптивности (BKT/HLR) обновляет Derived по обратной связи.

---

## 2. Два под-слоя: Observed и Derived

> **Наследует 3-слойную архитектуру Events → State → Views из старого DP.ARCH.003, но переопределяет по writer+owner:**
> - **Observed = Events** (факты от платформы, append-only)
> - **Derived = State** (вычисления из Observed, snapshot)
> - **Views вышли в [DP.ARCH.007 Projection](DP.ARCH.007-projection.md)** — потому что их writer — агент в runtime, а не платформа-observer

### 2.1 Observed (неизменяемый лог наблюдений)

Каждое действие пользователя = событие. Append-only. Никогда не удаляется, не изменяется.
Источники: Бот, LMS, Claude Code, MCP, Стратег.

### 2.2 Derived (вычисляемые проекции = текущий профиль)

N независимых проекций из одного потока Observed:
- `skill_mastery` (BKT → P(known) по навыкам)
- `memory_decay` (HLR → полураспад, spaced repetition)
- `engagement` (агрегаты → streak, regularity)
- `misconceptions` (паттерн-матчинг + LLM extraction)
- `qualifications` (threshold rules → стадия, индексы)
- `baseline` / `potential` (PD.FORM.088/089 — двухслойные значения характеристик)

Каждая проекция пересчитывается из Observed событий. Можно построить N вариантов для одного пользователя.

### 2.3 Почему Observed+Derived, а не 4 слоя

Предыдущая метамодель делила данные на 4 слоя по **источнику** (кто пишет): declarative, collected, derived, generated. Это создавало ложные архитектурные границы:

- «Declarative» и «Collected» — оба являются **Observed-событиями**, различаясь лишь атрибутом `confidence`
- «Derived» и «Generated» — разные по writer+owner: Derived = платформа пишет в хранилище; Generated = агент формирует в runtime (переехало в [DP.ARCH.007 Projection](DP.ARCH.007-projection.md))

**Текущая модель делит по writer+owner:**

| Слой | Природа | Writer | Owner | Хранится? |
|------|---------|--------|-------|-----------|
| Observed | Неизменяемые факты наблюдения | Платформа runtime | Neon | Да, навсегда |
| Derived | Вычисляемый снимок | Платформа (batch/stream) | Neon | Да (snapshot) |
| Projection ([DP.ARCH.007](DP.ARCH.007-projection.md)) | Генерируемый ответ | Агент в runtime | Ephemeral | Нет |

**Примечание о Persona:** декларативные данные пользователя (goal_set, self_assessed) **также** попадают в Observed-события — но это событие *«пользователь сообщил X о себе»*, не сам факт X. Source-of-truth декларации — Персона (Git). Memory.Observed фиксирует факт сообщения во времени (для replay, audit, confidence calibration).

---

## 3. Observed: структура и типы событий

### 3.1 Схема события

Каждое событие содержит:

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | BIGSERIAL | Уникальный ID (монотонно растущий) |
| `user_id` | BIGINT | Пользователь |
| `event_type` | TEXT | Тип события (см. каталог ниже) |
| `source` | TEXT | Система-источник: `bot`, `lms`, `claude_code`, `strategist` |
| `payload` | JSONB | Специфичные данные события |
| `confidence` | FLOAT | Доверие к сигналу: 0.0–1.0 |
| `skill_ids` | TEXT[] | Затронутые навыки (если применимо) |
| `created_at` | TIMESTAMPTZ | Время события |

### 3.2 Каталог типов событий

#### Прямые действия (confidence = high)

| event_type | source | payload (ключевые поля) | Что даёт |
|------------|--------|------------------------|----------|
| `test_answered` | bot, lms | `questionId, skillId, depth, correct, responseMs` | Skill mastery (BKT) |
| `homework_submitted` | lms | `homeworkId, skillIds[], score, timeSpentMs` | Mastery + engagement |
| `marathon_step` | bot | `lessonId, stepId, completed, timeSpentMs` | Progress, time-on-task |
| `feed_answered` | bot | `questionId, answer, correct` | Knowledge signals |
| `session_start` | bot | `platform, timestamp` | Streak, regularity |
| `session_end` | bot | `durationMs` | Session length |

#### Декларации пользователя (confidence = lower, субъективные)

> **Важно:** декларативные события фиксируют **факт сообщения** в Memory.Observed, но source-of-truth декларации — Персона (Git). При расхождении Git-версия преобладает. Декларативные события полезны для timeline, calibration confidence, audit.

| event_type | source | payload | Что даёт |
|------------|--------|---------|----------|
| `goal_set` | bot | `goal, targetSkill, targetDepth` | Цели для gap-анализа |
| `self_assessed` | bot | `skillId, selfRating` | Субъективная оценка (калибровка с объективной) |
| `profile_updated` | bot | `field, oldValue, newValue` | Контекст |
| `reflection` | bot | `text, extractedInsights[]` | Metacognition |
| `note_created` | bot | `text, tags[]` | Рефлексивность |

#### Системные (confidence = high, автоматические)

| event_type | source | payload | Что даёт |
|------------|--------|---------|----------|
| `ai_chat` | bot | `sessionId, userMessage, extractedSkills[], comprehension` | Misconceptions, interests |
| `strategy_session` | strategist | `weekPlan, rpCount` | Инициативность |
| `knowledge_extracted` | extractor | `entities[], packId` | Вклад в знания |

#### Операционные (confidence = 1.0, WP-151 Ф3)

| event_type | source | payload (ключевые поля) | Что даёт |
|------------|--------|------------------------|----------|
| `onboarding_completed` | bot | `lang, path, duration, schedule_time, start_date` | Воронка: конверсия регистрации |
| `onboarding_step` | bot | `step` (language/name/duration/schedule/date/confirm) | Микро-воронка: где отваливаются |
| `mode_changed` | bot | `from_mode, to_mode, trigger` | Когда и почему меняют режим |
| `settings_changed` | bot | `field, old_value, new_value` | Паттерн изменения настроек |
| `reminder_delivered` | bot | `reminder_type, marathon_day` | Факт отправки напоминания |
| `reminder_opened` | bot | `source` | Конверсия: напоминание → действие |
| `error_shown` | bot | `error_key, handler` | UX-проблемы |
| `help_viewed` | bot | `source` (command/callback) | Индикатор «потерянности» |
| `progress_viewed` | bot | `view_type` (short/full) | Интерес к прогрессу |
| `marathon_completed` | bot | `total_topics, completed_topics, path` | Ключевая milestone-метрика |

### 3.3 Confidence как атрибут, не слой

Бывшее деление «declarative vs collected» заменяется **атрибутом confidence**:

| Тип сигнала | confidence | Пример |
|-------------|-----------|--------|
| Прямой тест / ДЗ | 0.9–1.0 | Правильный/неправильный ответ |
| Поведенческий | 0.7–0.9 | Session duration, streak |
| LLM-извлечённый | 0.4–0.7 | Misconception из чата |
| Самооценка | 0.3–0.5 | «Я знаю ZP.1 на 4 из 5» |

При Bayesian update: `confidence` используется как вес — тестовый ответ двигает P(known) сильнее, чем косвенный сигнал из чата.

### 3.4 Событие = факт, независимый от канала (Channel-Agnostic Events)

**Принцип:** Событие описывает **что произошло с пользователем**, а не где это произошло. `session_start` из бота и `session_start` из VS Code — одно и то же событие с разным `source`. Канал доставки — атрибут, не тип.

**Следствия:**

1. **Единый event store** для всех каналов. Бот, экзокортекс (Claude Code), LMS, Web App — все пишут в `development.user_events` через один API (Activity Hub).
2. **source как атрибут.** Поле `source` (`bot`, `exocortex`, `lms`, `web_app`) — единственное отличие между каналами. Проекции (Derived) агрегируют по `user_id`, не по `source`.
3. **Канало-независимые типы** — события, которые возникают в нескольких каналах:

| event_type | Каналы | Примечание |
|---|---|---|
| `session_start` | bot, exocortex | Сессия работы |
| `ai_chat` | bot, exocortex | Вопрос ИИ-консультанту |
| `settings_changed` | bot, exocortex | Изменение настроек |
| `progress_viewed` | bot, exocortex | Просмотр Памяти.Derived (/twin, /me) |
| `note_created` | bot, exocortex | Заметка (fleeting note) |
| `knowledge_extracted` | bot, exocortex | Capture знания в Pack |
| `goal_set` | bot, exocortex | Установка цели |
| `self_assessed` | bot, exocortex | Самооценка |

4. **Канало-специфичные типы** — привязаны к конкретному каналу:

| event_type | Канал | Почему специфичен |
|---|---|---|
| `onboarding_*` | bot | TG-интерфейс регистрации |
| `reminder_*` | bot | Push-уведомления TG |
| `marathon_*`, `feed_*` | bot | Учебные модули бота |
| `error_shown` | bot | TG UI ошибок |
| `commit_pushed` | exocortex | Git workflow |
| `wp_completed` | exocortex | Закрытие РП |

**Антипаттерн:** писать в Derived (snapshot) минуя Observed. Экзокортекс, пишущий напрямую в `digital_twins.data` вместо event store — нарушает Event Sourcing: нет лога, нет replay, нет ретроспективных запросов. Временно допустимо (dt-collect.sh для 2_6/2_7), но при появлении Activity Hub — мигрировать на events.

---

## 4. Derived: проекции и методы вычисления

### 4.1 Проекция: Skill Mastery

**Вопрос:** «Насколько пользователь владеет каждым навыком?»

**Метод: Bayesian Knowledge Tracing (BKT)**

Для каждой пары (user, skill) поддерживаем P(known) — вероятность владения навыком.

```
Параметры BKT (на навык):
  P(L₀)  = начальное знание (prior)                    ≈ 0.1
  P(T)   = вероятность выучить за 1 попытку             ≈ 0.3
  P(G)   = вероятность угадать правильный ответ         ≈ 0.25
  P(S)   = вероятность ошибиться по невнимательности    ≈ 0.1

При правильном ответе:
  P(L|correct) = P(L)×(1−P(S)) / [P(L)×(1−P(S)) + (1−P(L))×P(G)]

При неправильном ответе:
  P(L|wrong)   = P(L)×P(S) / [P(L)×P(S) + (1−P(L))×(1−P(G))]

После обновления — шанс обучения:
  P(L_new) = P(L_updated) + (1 − P(L_updated)) × P(T)
```

**Входные события:** `test_answered`, `homework_submitted`, `feed_answered`

**Выход:** `{user_id, skill_id, p_known, bloom_depth, attempts, last_event}`

**Маппинг Bloom depth:** P(known) → Bloom через пороги:

| P(known) | Bloom depth | Интерпретация |
|----------|-------------|---------------|
| 0.0–0.2 | 0 (не знает) | Нет владения |
| 0.2–0.4 | 1 (запоминание) | Может вспомнить |
| 0.4–0.6 | 2 (понимание) | Может объяснить |
| 0.6–0.75 | 3 (применение) | Может применить |
| 0.75–0.9 | 4 (анализ/оценка) | Может проанализировать |
| 0.9–1.0 | 5 (создание) | Может создать новое |

**SOTA эволюция:** BKT (v1, сейчас) → BKTransformer (v2, при >100K событий) → Deep KT + Cognitive Load (v3).

### 4.2 Проекция: Memory Decay

**Вопрос:** «Когда навык "протухнет" без повторения?»

**Метод: Half-Life Regression (HLR, Duolingo)**

```
P(recall, t) = 2^(−Δt / h)

h = 2^(θ · x)

где x = [кол-во повторений, кол-во правильных, кол-во ошибок,
         текущий P(known), время с последнего повторения]
```

**Что даёт:**
- Для каждого навыка: `next_review_date` — когда P(recall) упадёт ниже 0.5
- Spaced repetition: бот знает, когда напомнить пользователю повторить навык
- Предиктивная Память: «через 2 недели без практики ZP.3 деградирует»

**Входные события:** те же, что для Skill Mastery

**Выход:** `{user_id, skill_id, half_life, p_recall_now, next_review_date}`

### 4.3 Проекция: Engagement Profile

**Вопрос:** «Насколько регулярно и интенсивно пользователь занимается?»

**Метод: скользящие агрегаты**

| Метрика | Формула |
|---------|---------|
| `streak_days` | Longest consecutive days with ≥1 event |
| `active_days_7d` | `COUNT(DISTINCT date) WHERE last 7 days` |
| `active_days_30d` | `COUNT(DISTINCT date) WHERE last 30 days` |
| `regularity` | `active_days_7d / 7` |
| `avg_session_min` | `AVG(session_duration) WHERE last 30 days` |
| `preferred_hour` | `MODE(EXTRACT(hour FROM created_at))` |
| `events_per_active_day` | `COUNT(events) / active_days_30d` |

**Входные события:** все типы (по факту наличия)

**Выход:** `{user_id, streak, regularity, avg_session_min, preferred_hour, events_per_active_day}`

### 4.4 Проекция: Misconception Map

**Вопрос:** «Какие конкретные заблуждения у пользователя?»

**Метод: паттерн-матчинг + LLM extraction (async)**

Для тестов:
- Неправильный ответ → маппинг на `common_errors` из ячеек curriculum (MIM.MAP.001)
- Каждая ячейка содержит типичные ошибки → автоматический матчинг

Для чатов:
- Async LLM (Haiku) анализирует сообщения пользователя
- Экстрагирует misconceptions с confidence score

**Входные события:** `test_answered` (неправильные), `ai_chat`

**Выход:** `{user_id, skill_id, misconception_type, evidence_count, confidence, first_seen, last_seen}`

### 4.5 Проекция: Qualifications (стадия и квалификация)

**Вопрос:** «На какой стадии развития находится пользователь?»

**Метод: threshold rules — пороговые правила поверх других проекций**

Это единственная проекция, которая читает другие проекции, а не сырые события:

```
                   Skill Mastery ──┐
                   Engagement    ──┼──→ Qualifications (threshold rules)
                   Misconceptions──┘
```

Пороги определяются для каждой стадии (Random → Practicing → Systematic → Disciplined → Proactive) через комбинацию: min(P(known)) по ZP-навыкам, active_days, misconception_count.

**Выход:** `{user_id, stage, agency_index, mastery_index, worldview_level}`

### 4.6 Проекция: Baseline + Potential (двухслойные значения)

**Вопрос:** «Устойчивый уровень характеристики (не моментальный) и потолок, до которого можно поднять?»

**Метод: сглаживание Observed + анализ исторической динамики** (PD.FORM.088/089).

Для характеристик пользователя (собранность, регулярность, скорость обучения):
- **baseline** = сглаженное значение показателя (скользящее среднее, устойчивый уровень) — двигается методами M1/M2 за недели-месяцы
- **potential** = оценка потолка шкалы — расширяется фундаментальным развитием (M4) за годы

Различение: значение-сейчас (моментальное, зашумлённое) ≠ baseline (устойчивый). Программа ЛР целится в baseline и potential, не в значение-сейчас.

**Входные события:** все события активности пользователя (slots, sessions, completions) за длинное окно.

**Выход:** `{user_id, characteristic_id, value_now, baseline, potential, last_updated}`

---

## 5. Три типа характеристик по вычислимости

Не все характеристики созидателя одинаково вычислимы из Observed-событий.

| Тип | Описание | Confidence | Примеры |
|-----|----------|-----------|---------|
| **A. Прямо вычислимые** | Считаются из событий по формуле | Высокий | Streak, часы в неделю, P(known), recovery speed |
| **B. Косвенно выводимые** | Proxy-сигналы через поведение или LLM | Средний | Эмоциональная устойчивость (через variance активности), misconceptions (через LLM) |
| **C. Только декларация** | Пользователь сообщает сам, объективно не проверить | Низкий | Мемы, калибр личности, контроль инфопотока → живут в Персоне, копия в Observed |

### Пример типа A: «Устойчивость к сбоям»

```yaml
characteristic: "Устойчивость к сбоям"
computation_type: A (прямо из событий)
input_events: [session_start]
method: |
  1. Найти все gaps > 3 дней (нет событий)
  2. Для каждого gap: дней до первого дня с ≥ 2 событиями
  3. recovery_speed = median(recovery_days)
thresholds:
  good: < 2 дней
  medium: 2–5 дней
  poor: > 5 дней
confidence: high
```

### Пример типа B: «Эмоциональная стабильность» (proxy)

```yaml
characteristic: "Эмоциональная стабильность (proxy)"
computation_type: B (косвенно)
input_signals:
  - regularity_variance (дисперсия active_days за 30 дней) — тип A
  - recovery_speed (дней до восстановления streak) — тип A
  - session_time_variance (стабильность длины сессий) — тип A
  - sentiment_trend (тренд тональности в чатах) — тип B, LLM
  - self_reported_state (самооценка состояния) — тип C
method: |
  stability_proxy = w1 × (1 − norm(regularity_variance))
                  + w2 × (1 − norm(recovery_speed))
                  + w3 × (1 − norm(session_time_variance))
                  + w4 × sentiment_score
                  + w5 × self_reported_state
  где w1-w5 — веса (начальные: 0.25, 0.25, 0.2, 0.15, 0.15)
confidence: medium
caveat: "Proxy ≠ клиническая оценка. Показывать пользователю с пометкой."
```

**Правило:** для каждой характеристики метамодели Памяти нужна такая карточка метода. Характеристики без карточки — не вычислимы.

---

## 6. Как Derived используется платформой (поверх — Проекция)

> **Примечание:** всё, что ниже (бот-сценарии, агентные промпты, Open Learner Model, Nudge Engine) — это **писатели Projection**, не Памяти. Они **читают** Derived. Описание проекций см. [DP.ARCH.007](DP.ARCH.007-projection.md).

### 6.1 Читатели Derived

| Читатель | Проекции | Где описан |
|----------|---------|-----------|
| Бот (DP.AISYS.014) — консультация, марафон, лента, /mydata, адаптивный тест | skill_mastery, memory_decay, misconceptions, engagement | [DP.ARCH.007 §Projection: User Views](DP.ARCH.007-projection.md) |
| ИИ-агенты (Стратег, Портной, Консультант, Диагност MIM.R.009) | qualifications, skill_mastery, misconceptions, engagement | [DP.ARCH.007 §Projection: LLM Context](DP.ARCH.007-projection.md) |
| Open Learner Model (пользователь видит свой профиль) | все проекции | [DP.ARCH.007 §User Views](DP.ARCH.007-projection.md) |
| Nudge Engine | skill_mastery, memory_decay, engagement, misconceptions, qualifications | [DP.ARCH.007 §Nudge Engine](DP.ARCH.007-projection.md) |

### 6.2 Замыкание цикла: Observed → Derived → Projection → новые Observed

```
Пользователь отвечает на вопрос
        ↓
Observed: test_answered {skill: ZP.3, correct: false}
        ↓
Derived update: P(known ZP.3) = 0.23 → 0.19
        ↓
Projection: Диагност (агент) видит bottleneck, собирает контекст
        ↓
Бот предлагает материал по ZP.3 (ячейка из curriculum)
        ↓
Пользователь изучает и отвечает на новый вопрос
        ↓
Observed: test_answered {skill: ZP.3, correct: true}
        ↓
Derived update: P(known ZP.3) = 0.19 → 0.35
        ↓
... цикл продолжается
```

Это реализация **Intervention Loop** (DP.M.007): действие → измерение → обновление модели.

---

## 7. Хранилище: схемы данных

> **Implementation Note.** Конкретная реализация в Neon PostgreSQL: schemas, таблицы, потоки данных, именование БД (целевая карта 12 БД утверждена в [DP.ARCH.004](DP.ARCH.004-neon-data-architecture.md) §1 v2.3 через WP-228 Ф25 DONE 22 апр) → [C2.IT-Platform / Data-Stores](../../../DS-ecosystem-development/C.IT-Platform/C2.IT-Platform/C2.2.Architecture/Data-Stores/).

**Доменные принципы:**
- **Память = несколько БД Neon** (не одна schema, не одна БД):
  - Observed события → `activity-hub` (#3)
  - Derived агрегаты → `digital-twin` (#5, имя под пересмотр в WP-228 Ф25)
  - Платёжные события → `payment-registry` (#4)
  - Метрики здоровья платформы → `health` (#8)
  - Подписки-контракты → `platform` (#1)
- 5 доменов: идентичность, развитие, финансы, подключения, служебное
- Критерии разделения: один домен, независимое создание и развитие, независимый доступ, тест канала
- Activity Hub — единая точка записи Observed-событий из всех источников

---

## 8. Безопасность

> **Implementation Note.** RLS-политики, 5 ролей PostgreSQL (bot_service, mcp_user, web_app, analyst, financier), pgcrypto шифрование → [C2.IT-Platform / Data-Stores](../../../DS-ecosystem-development/C.IT-Platform/C2.IT-Platform/C2.2.Architecture/Data-Stores/).

**Доменные принципы:**
- RLS на всех таблицах с `user_id` — пользователь видит только свои данные
- Ролевая модель: сервисы, пользователи, аналитики, финансисты — разный доступ
- Секреты зашифрованы at rest
- **PII-класс (DP.ARCH.004 §2 П6.1):** Observed-события с email/telegram_id — PII, логирование запрещено. Payment events — строже PII (payment_credentials class).

---

## 9. Масштабирование и retention

> **Implementation Note.** Метрики масштабирования, Neon pricing tiers, retention policy, snapshot оптимизация → [C2.IT-Platform / Data-Stores](../../../DS-ecosystem-development/C.IT-Platform/C2.IT-Platform/C2.2.Architecture/Data-Stores/).

**Доменные принципы:**
- Observed < 2 лет → горячее хранилище, > 2 лет → архив
- Derived всегда актуальные (пересчёт из Observed)
- Snapshotting при rebuild > 1 сек

---

## 10. Эволюция Derived → CHR-Space

Начальные 5 проекций покрывают базовые потребности. Модель характеристик созидателя описывает **30+ измерений** (CHR-Space). Подобно тому как характеристики автомобиля (скорость, экономичность, безопасность) описывают его профиль, характеристики человека (агентность, обучаемость, стрессоустойчивость, калибр) описывают профиль созидателя.

### 10.1 Примеры будущих проекций

| Проекция | Из каких событий | Метод |
|----------|-----------------|-------|
| `agency` (агентность) | goal_set, self_assessed, task_completed | Composite score |
| `stress_resilience` (стрессоустойчивость) | engagement при нагрузке, recovery patterns | Time-series analysis |
| `techno_integration` (техноинтеграция) | WakaTime, экзокортекс usage, tool adoption | Aggregate + decay |
| `social_impact` (социальное влияние) | comment_created, question_answered, referral | Network analysis |
| `creativity` (креативность) | guide_published, methodology_contributed | Output + novelty score |
| `learning_velocity` (скорость обучения) | test_answered (accuracy over time per skill) | Regression slope |

Каждая новая проекция = новая таблица + replay Observed-событий. Архитектура Event Sourcing это позволяет: лог неизменяем, проекции создаются ретроспективно.

### 10.2 Исследовательская лаборатория (Фаза 4+)

«Лаборатория характеристик» — среда для работы с накопленными событиями:

1. **Экспериментировать** с новыми проекциями (replay на копии данных)
2. **Выявлять корреляции** между характеристиками (матрица корреляций)
3. **Обнаруживать синергии** (агентность + интеллект + калибр → лидерский потенциал)
4. **Строить персональную траекторию** (gap-анализ: Target(role) − Current(state))
5. **Валидировать методы** вычисления характеристик (A/B-тестирование формул)

**Триггер:** >1K пользователей с >6 мес историей событий.

---

## 11. Маппинг: Память ↔ DT MCP метамодель (WP-151 Ф6, legacy IND-нумерация)

> **Контекст:** Два представления одних данных. Этот документ описывает **архитектурные слои** (Observed → Derived). Метамодель DT MCP (`DS-MCP/digital-twin-mcp/metamodel/`) описывает **типы индикаторов** (IND.1-4). Этот маппинг связывает их. IND-нумерация — legacy терминология до WP-257; логически эквивалентна новой Memory-модели.

### 11.1 Слои ↔ типы индикаторов

| Слой Памяти | IND-тип метамодели | Кол-во | Confidence | Примеры IND-кодов |
|---|---|---|---|---|
| **Observed** | IND.1 (declarative) | 20 | 0.3-0.5 | IND.1.1 (профиль), IND.1.2 (цели), IND.1.5 (стиль подачи) |
| **Observed** | IND.2 (collected) | 30+ | 0.7-1.0 | IND.2.1 (сессии), IND.2.6 (кодирование), IND.2.10 (история) |
| **Derived** | IND.3 (derived) | 37 | вычисляемый | IND.3.1 (агентность), IND.3.2 (мастерство), IND.3.4 (квалификация) |
| **Projection** ([ARCH.007](DP.ARCH.007-projection.md)) | IND.4 (generated) | 3 | on-demand | IND.4.3 (прогнозы), IND.4.4 (отчёты) |

**Принцип соответствия:** IND.1 и IND.2 = Observed-события с разным `confidence` (§3.3). IND.3 = Derived (проекции). IND.4 = Projection (генерируемые агентом, не хранятся — [DP.ARCH.007](DP.ARCH.007-projection.md)). Четвёрка IND.1-4 — историческое деление по источнику; архитектурно значим только слой (Observed/Derived/Projection).

### 11.2 Derived-проекции → IND.3 группы метамодели

| Проекция (§4) | Метод | IND.3 группа | Конкретные индикаторы | Реализация |
|---|---|---|---|---|
| **skill_mastery** | BKT | IND.3.2 (mastery) | IND.3.2.01 (практика), IND.3.2.04 (мировоззрение) | BKT v0.8 (`dt_calc.py`): P(mastery) по 72 мемам (PD.CAT.001) |
| **memory_decay** | HLR | — | — | Не реализована. Требует >100K событий |
| **engagement** | Агрегаты | IND.3.1 (agency), IND.3.10 (integral) | IND.3.1.02 (slot_regularity), IND.3.10.1 (agency_index) | `engagement` VIEW + `dt_sync` + `dt_calc.py` v0.7 |
| **misconceptions** | LLM + pattern | IND.3.3.04 (мемы), IND.3.11.02 (заблуждения) | IND.3.3.04 (текущие мемы по BKT) | BKT по мемам (Ф5). LLM extraction — не реализована |
| **qualifications** | Threshold rules | IND.3.4, IND.3.11.01 | IND.3.4.01 (ступень ученика), IND.3.11.01 (диагн. состояние) | `student_stage` в `dt_calc.py` (learner + builder path) |

### 11.3 Вторая ось: 5 областей развития (PD.FORM.080)

Помимо проекций (горизонтальный срез по методу), метамодель содержит группировку по **областям развития** — вертикальный срез по предмету:

| Область (FORM.080) | IND.3 индикаторы (мировоззрение) | IND.3 индикаторы (мастерство) |
|---|---|---|
| knowledge | IND.3.2.04, IND.3.3.04 | IND.3.2.01, IND.3.2.05 |
| tools | IND.3.9.1 | IND.3.2.02, IND.3.2.03, IND.3.9.2 |
| constraints | IND.3.3.03 | IND.3.1.04, IND.3.6.04 |
| environment | IND.3.3.05, IND.3.3.02 | IND.3.7.1, IND.3.7.2 |
| organism | IND.3.6.01 | IND.3.6.02, IND.3.6.03, IND.3.6.05 |

Реализация: `mapping.js` (DT MCP, `AREA_MAPPING`). Source-of-truth: PD.FORM.080 §9, PD.FORM.081.

### 11.4 Известные разрывы

| # | Разрыв | Влияние | Где закрывается |
|---|---|---|---|
| 1 | memory_decay (HLR) не реализована | Нет spaced repetition, нет `next_review_date` | WP-151 Ф8+ (при >100K событий) |
| 2 | misconceptions: LLM extraction не реализована | Только BKT по мемам, нет анализа чатов | WP-151 Ф7 (Лаборатория) |
| 3 | ~10 индикаторов IND.3 без вычисления | IND.3.3.05 (калибр), IND.3.5 (роли), IND.3.9 (AI usage) | WP-175 (маппинг метамодели) |
| 4 | Области Worldview и Exocortex: недостаточно индикаторов | 2 инд. для мировоззрения, 0 для экзокортекса | WP-175 (GAP-лист) |
| 5 | dt_calc.py пороги ступеней не совпадают с нормами метамодели | Proxy (events/sessions) вместо duration-of-stability | WP-175 (калибровка) |

### 11.5 Потоки данных (текущее состояние, апрель 2026)

```
Бот (log_event)  ──→ development.user_events ──→ engagement VIEW ──→ dt_sync ──→ digital_twins
     20 event_types          Neon (#3)              15 метрик          04:30 MSK      JSONB (#5)
                                                                         │
                                                                         ▼
                                                                    calculate_derived()
                                                                    dt_calc.py v0.8
                                                                         │
                                                                         ▼
                                                              3_derived (3 проекции):
                                                              - slot_regularity (IND.3.1.02)
                                                              - student_stage (IND.3.4.01)
                                                              - integral_agency_index (IND.3.10.1)
                                                              - mastery_by_area (BKT, IND.3.2.04)
                                                              - worldview_gaps (BKT, IND.3.3.04)
```

> **Связь с WP-175:** WP-175 формализует полный маппинг таблица индикатор → область → норма в PD.FORM.080 §10. Этот раздел описывает архитектурное соответствие слоёв.

---

## 12. SOTA-основа

| Технология / подход | Источник | Как используем |
|---------------------|----------|----------------|
| **Event Sourcing + CQRS** | Microsoft Azure Patterns, production-proven | Архитектура слоёв Observed → Derived |
| **xAPI (Actor-Verb-Object)** | IEEE Standard (Oct 2023) | Формат событий, совместимость |
| **Bayesian Knowledge Tracing** | Corbett & Anderson 1995, тысячи публикаций | Skill mastery P(known) |
| **Half-Life Regression** | Duolingo (Settles 2016), production 1B+ exercises/day | Memory decay, spaced repetition |
| **BKTransformer** | JEDM 2025 | Эволюция BKT → hybrid (v2) |
| **Open Learner Model** | IEEE TLT 2020 | Видимый профиль для пользователя |
| **Personal AI Memory (Letta/Mem0/LangMem)** | 2025-2026 | Различение Persona/Memory/Context ([DP.D.052](../01-domain-contract/DP.D.052-persona-memory-context.md)) |
| **Overlay + Perturbation Model** | PMC 2022 | Skill mastery + misconception map |
| **Duolingo Birdbrain** | Duolingo Engineering Blog | ELO-подобная система ability+difficulty |
| **Khan Academy Mastery** | EDM 2022 | 4-уровневый state machine per skill |

---

## 13. Связанные документы

- [DP.ARCH.001](DP.ARCH.001-platform-architecture.md) — 3-слойная архитектура платформы
- [DP.ARCH.002](DP.ARCH.002-service-tiers.md) — Тиры обслуживания
- [DP.ARCH.004](DP.ARCH.004-neon-data-architecture.md) — Архитектура Neon (12 БД v2.3)
- [DP.ARCH.005](DP.ARCH.005-persona-entity.md) — Персона (writer=user, owner=Git)
- [DP.ARCH.007](DP.ARCH.007-projection.md) — Проекция (writer=agent runtime)
- [DP.D.052](../01-domain-contract/DP.D.052-persona-memory-context.md) — Персона ≠ Память ≠ Контекст
- [DP.CONCEPT.001](DP.CONCEPT.001-platform-concept.md) — Концепция платформы
- [DP.CONCEPT.003](DP.CONCEPT.003-adaptive-personalization.md) — Адаптивная персонализация
- [DP.SOTA.009](../06-sota/DP.SOTA.009-knowledge-digital-twins.md) — Knowledge-Based Digital Twins
- [DP.M.007](../03-methods/DP.M.007-intervention-loop.md) — Intervention Loop
- [MIM.FORM.006](../../../PACK-MIM/pack/mim/02-domain-entities/formalizations/MIM.FORM.006-thinking-profile-model.md) — Модель профиля мышления
- [MIM.R.009](../../../PACK-MIM/pack/mim/02-domain-entities/MIM.R.009-diagnostician.md) — Диагност узких мест
- [MIM.MAP.001](../../../PACK-MIM/pack/mim/07-map/MIM.MAP.001-competency-depth-cell-template.md) — Шаблон ячеек

---

*Статус: active. Выделено из DP.ARCH.003 в WP-257 Ф5 (расщепление по writer+owner).*
*Создано: 2026-04-22. Наследует содержимое §3-§5, §13-§15, §18 старого DP.ARCH.003.*
