---
id: DP.SC.139
name: Контролёр развития (Daily Marker Scan)
previously_named: "IWE Stage Controller (до 2026-05-20)"
type: sc
status: draft
layer: L2-Platform
summary: "Опт-инный пилот ежедневно получает корректирующий нудж (TG, render-задача Портному, или сигнал Навигатору/Проводнику/Диагносту) по выбранному профилю контроля (по умолчанию — ступени Ученика и маркеры cp.iwe × cp.cre, FORM.089 §6.3). Профиль контроля расширяемо: степени квалификации, стиль, домены."
consumer: Опт-инный пилот (получатель нуджа), Портной (получатель render-задач), Навигатор / Проводник / Диагност (по типу разрыва)
created: 2026-05-17
updated: 2026-05-20
related:
  realizes: [DP.ROLE.046]
  uses: [DP.SC.134, DP.SC.106]
  extends: []
wp: WP-326
---

# [DP.SC.139] Контролёр развития (бывш. IWE Stage Controller)

> # see DP.SC.139, DP.ROLE.046

<!--
  Разделение зон ответственности с соседними SC:
  - DP.SC.116 (Notifications & Nudges) — общий контракт платформенных нуджей.
    DP.SC.139 — частный случай: нуджи по двумерной стадии мастерства IWE.
  - DP.SC.134 (Notification Dispatcher) — транспорт TG.
    DP.SC.139 uses DP.SC.134 для доставки.
  - DP.SC.106 (Personal Guide render) — Портной собирает руководство.
    DP.SC.139 uses DP.SC.106 для сложного материала через enqueue в guide_render_queue.
-->

## Правило (инвариант)

**Подтверждённый пол ступени (дополнение 14.11, РП-7 Ф309 пачка 2, урок WP-319 16.05):** `confirmed_stage = max(cp_assessments.stage, stage_transitions.to_stage)`. Декларированная/диагностированная ступень — это пол: машина (Аттестатор/evaluator) может только поднять ступень выше, но не опустить ниже заявленного пола, пока данных платформы недостаточно. Иначе пользователь с 6+ годами опыта, у которого у машины нет истории, получает ступень 1 — оскорбительно и неверно. Машинное понижение — только отдельным правилом про долгую неактивность (не реализовано).

- Каждый опт-инный пилот обрабатывается **ровно один раз в сутки** (idempotency на дату + account_id).
- Контролёр **не отправляет повторный нудж по той же оси и тому же gap** в течение **3 дней** (cool-down в `learning.nudge_journal`).
- Контролёр **не блокирует** ступень Ученика — он только инициирует рекомендации (cp.iwe и cp.cre — рекомендательные оси, FORM.089 §5.4).
- Выбор канала детерминирован: **простой шаг** (одно действие пилота, ≤2 мин) → TG через DP.SC.134; **сложный материал** (нужно объяснение, дни на освоение) → enqueue в `guide_render_queue` (mode=weekly).
- Контролёр **запускается из единственного места** (systemd timer на tsekh-1, 05:30 МСК) — `pg_try_advisory_lock` гарантирует single-runner на shared БД.
- При отсутствии `cp_assessments` для пилота — нудж «пройди диагностику» один раз; повторно — не чаще раза в 7 дней.

## Обещание

**Кому:** Опт-инный пилот (`learning.tracking_consent.opt_in = TRUE`) — получает корректирующий нудж по стадии мастерства IWE. Портной — получает enqueue render-задачи.

**Зачем:** Без контролёра пилоты «застревают» на одной стадии без сигнала о следующем шаге. Имена стадий мастерства IWE (Пользователь 1-3 / Разработчик 0-3) и маркеры связи со ступенью Ученика (FORM.089 §6.3) задают рекомендательную траекторию — но кто-то должен ежедневно проверять каждого пилота и инициировать движение. Это контролёр-диспетчер.

**Что получит:**

| Потребитель | Канал | Что получает |
|-------------|-------|-------------|
| Опт-инный пилот | Telegram через DP.SC.134 | Краткий нудж: «Ты на ст.3, но cp.iwe=2. Один шаг к Пользователь-3: сделай Day Close сегодня вечером.» |
| Опт-инный пилот | Персональное руководство (через Портного) | Расширенный раздел в weekly profile.md с объяснением метода (если требуется содержательное освоение) |
| Портной | `guide_render_queue` (mode=weekly) | Trigger render с темой «осваивать cp.cre для перехода Пользователь-3 → Разработчик-1» |

**Триггер:** Ежедневный systemd timer 05:30 МСК на tsekh-1.

**Время отклика:** Обработка всех опт-инов завершается к 06:00 МСК (≤30 мин). Нудж в TG доставляется не позже 06:05 МСК. Окно 05:30 выбрано, чтобы видеть свежие `stage_transitions` от Аттестатора (04:35) и не пересекаться с render-pilot-guides (06:00 вт-вс и 05:00 Пн).

**Режим отказа:**
- systemd timer fail → grafana alert + утреннее уведомление в TG канал tsekh-1 dashboards. Пилоты не получают нудж в этот день; следующий запуск подхватит.
- Neon недоступен → retry 3×, потом fail → лог в systemd journal, нет нуджа в этот день.
- Notification Dispatcher (DP.SC.134) недоступен → TG-нудж не доставлен; запись `pending` в nudge_journal; следующий день: попытка повторно (idempotency по `content_hash` не дублирует).

## Что НЕ делает контролёр

- **Не блокирует ступень Ученика** — cp.iwe и cp.cre informational (FORM.089 §5.4).
- **Не оценивает cp.iwe и cp.cre сам** — читает из `learning.cp_assessments` (источник: Диагност, DP.ROLE.042).
- **Не пишет в `stage_transitions`** — только читает; ступень определяет Аттестатор (DP.ROLE.041).
- **Не интерпретирует содержимое cp-профиля** свободно — следует детерминированной таблице маркеров (FORM.089 §6.3).
- **Не отправляет email/push** — только TG (через DP.SC.134) или enqueue render.
- **Не отправляет нуджи non-opt-in пилотам** — фильтр по `tracking_consent.opt_in = TRUE`.

## Свидетельства (критерий приёмки)

**Данные:**

| Критерий | Как проверить |
|----------|--------------|
| Каждый opt-in пилот обработан в сутки | `SELECT account_id FROM learning.nudge_journal WHERE occurred_at::date = CURRENT_DATE GROUP BY 1` совпадает с opt-in списком |
| Cool-down 3 дня: одинаковый content_hash не повторяется | `SELECT account_id, content_hash, COUNT(*) FROM learning.nudge_journal WHERE occurred_at > NOW() - INTERVAL '3 days' GROUP BY 1,2 HAVING COUNT(*) > 1` → пусто |
| TG-нудж зафиксирован в `domain_event` | `SELECT * FROM domain_event WHERE event_type = 'iwe_stage_nudge_sent' AND payload->>'account_id' = '...'` |
| Render enqueued (для сложных шагов) | `SELECT * FROM learning.guide_render_queue WHERE account_id = '...' AND trigger_kind = 'iwe_stage_controller'` |

**Контекст:**

| Условие | Проверка |
|---------|---------|
| Пилот opt-in | `SELECT opt_in FROM learning.tracking_consent WHERE account_id = '...'` = TRUE |
| Есть cp_assessment (или нет — fallback нудж «пройди диагностику») | `SELECT id FROM learning.cp_assessments WHERE account_id = '...' AND valid_until > NOW()` |
| Текущая ступень из stage_transitions | `SELECT to_stage FROM learning.stage_transitions WHERE account_id = '...' ORDER BY occurred_at DESC LIMIT 1` |

**Полномочия:**

| Роль | Что подтверждает |
|------|-----------------|
| DP.ROLE.046 Контролёр развития | Факт принятия решения (нудж/render/skip) и записи в nudge_journal |
| DP.ROLE.044 Notification Dispatcher | Факт доставки TG-нуджа |
| DP.ROLE.041 Аттестатор | Источник `learning.stage_transitions` (ступень) |
| DP.ROLE.042 Диагност | Источник `learning.cp_assessments` (cp-профиль) |

**Свидетельства:**

| Свидетельство | Источник |
|--------------|---------|
| TG-сообщение получено пилотом | Telegram delivery status (через DP.SC.134) |
| Запись в `learning.nudge_journal` | Neon |
| Запись в `learning.domain_event` (event_type=`iwe_stage_nudge_sent` или `iwe_stage_render_enqueued`) | Neon |

## Реализующие сервисы (MAP.002)

| Сервис | Роль | Триггер |
|--------|------|---------|
| `iwe-stage-controller.py` (tsekh-1, systemd timer) | DP.ROLE.046 | ⏰ Ежедневно 05:30 МСК |
| `iwe-stage-controller.service` (NixOS systemd unit) | DP.ROLE.046 | через timer |

## Сценарий A: новый пилот без cp_assessment

| # | Шаг | Кто | Действие |
|---|-----|-----|----------|
| 1 | Timer запускает контролёр | systemd | tsekh-1 05:30 МСК |
| 2 | Читает opt-in список | DP.ROLE.046 | `SELECT account_id FROM tracking_consent WHERE opt_in = TRUE` |
| 3 | Для пилота X: cp_assessment отсутствует | DP.ROLE.046 | Проверка `cp_assessments` (valid) |
| 4 | Проверка cool-down (нудж «диагностика» за 7 дней) | DP.ROLE.046 | `SELECT FROM nudge_journal WHERE state = 'no_cp_assessment'` |
| 5 | Нудж: «Пройди диагностику /diagnose-iwe (5 мин) — узнай свою стадию мастерства IWE» | DP.ROLE.046 → DP.SC.134 | TG via Notification Dispatcher |
| 6 | Запись в `nudge_journal` | DP.ROLE.046 | INSERT с content_hash |

## Сценарий B: gap по простой оси (cp.iwe ниже маркера)

| # | Шаг | Кто | Действие |
|---|-----|-----|----------|
| 1-2 | Same as Сценарий A | | |
| 3 | Пилот Y: ст.3 (Систематический), cp.iwe=2, cp.cre=0. Маркер ст.3 = (3, 1) → имя стадии «Пользователь-3 + Разработчик-1». Gap по обеим осям. | DP.ROLE.046 | Сравнение с `_IWE_MARKER_BY_STAGE` (FORM.089 §6.3) и `iwe_master_stage_label(stage)` |
| 4 | Cool-down: за 3 дня уже был нудж по этому gap? | DP.ROLE.046 | `SELECT FROM nudge_journal WHERE content_hash = sha256(account_id\|cp.iwe\|2→3)` |
| 5 | Нет → нудж: «Стадия мастерства IWE на твоей ступени: Пользователь-3 + Разработчик-1. Сейчас факт cp.iwe=2, ожидание 3. Сегодня — один шаг: сделай Day Close вечером.» | DP.ROLE.046 → DP.SC.134 | TG |
| 6 | Запись `nudge_journal` (state=`gap_iwe`, content_hash=`sha256(account_id+ось+gap)`) | DP.ROLE.046 | INSERT |

## Сценарий C: gap по сложной оси (cp.cre = 0, нужен контент)

| # | Шаг | Кто | Действие |
|---|-----|-----|----------|
| 1-2 | Same as Сценарий A | | |
| 3 | Пилот Z: ст.3, cp.iwe=3, cp.cre=0. Маркер ст.3: (3, 1) → gap по cp.cre (новая ось, нужен материал) | DP.ROLE.046 | |
| 4 | Cool-down по `start_creation_axis` за 3 дня | DP.ROLE.046 | |
| 5 | Нет → enqueue render: `guide_render_queue` с mode=weekly, trigger_kind=`iwe_stage_controller`, payload={target_axis: 'cp.cre', target_stage: 'Разработчик-1'} | DP.ROLE.046 | INSERT в guide_render_queue |
| 6 | Запись `nudge_journal` (state=`render_enqueued`, content_hash=`sha256(account_id+axis+marker)`) | DP.ROLE.046 | INSERT |
| 7 | Параллельно: preview TG-нудж: «Стадия мастерства IWE сегодня обновляется: {имя стадии}. Портной соберёт раздел про освоение оси создания…» | DP.ROLE.046 → DP.SC.134 | TG (best-effort, не блокирует enqueue) |

## Различение «простой шаг» vs «сложный материал»

| Категория | Канал | Признаки | Пример |
|-----------|-------|----------|--------|
| **Простой шаг** | TG | Одно действие пилота, ≤2 мин, известная команда или паттерн | «Сделай Day Close»; «Запиши слот saw в /slot»; «Проверь WP в WeekPlan» |
| **Сложный материал** | guide_render | Нужно понимание метода, многошаговое освоение, дни до результата | «Начни осваивать создание Pack-доменов»; «Освой паттерн Day Close (зачем, как, что делать на срыве)»; «Пройди методологию маршрутизации знаний» |

**Тест разделения:** «Может ли пилот выполнить нудж за 2 минуты прямо сейчас?» Да → TG. Нет → render.

## Связь со ступенью Ученика и маркерами

Маркер `_IWE_MARKER_BY_STAGE` (FORM.089 §6.3) определяет рекомендуемый профиль (cp.iwe, cp.cre) для каждой ступени:

| Ступень | Маркер | Gap-логика |
|---------|--------|------------|
| 1 Случайный | (1, 0) | Любой профиль ≥ маркера — OK; иначе нудж «начни управлять средой» |
| 2 Практикующий | (2, 0) | cp.iwe < 2 → нудж; иначе OK |
| 3 Систематический | (3, 1) | Двумерный gap-анализ |
| 4 Дисциплинированный | (3, 2) | cp.cre < 2 → render «осваивай Разработчика-2» |
| 5 Проактивный | (3, 3) | cp.cre < 3 → render «продвинутая разработка» |

## Метрики наблюдаемости (Grafana)

| Метрика | Описание |
|---------|----------|
| `iwe_stage_controller.runs_total` | Кол-во запусков timer (должно быть ровно 1/день) |
| `iwe_stage_controller.pilots_processed` | Кол-во opt-in обработано в запуск |
| `iwe_stage_controller.nudges_sent` | Кол-во TG-нуджей отправлено |
| `iwe_stage_controller.renders_enqueued` | Кол-во render-задач в очередь |
| `iwe_stage_controller.skipped_cooldown` | Кол-во пропусков (cool-down 3 дня) |
| `iwe_stage_controller.errors_total` | Ошибки (Neon недоступен, TG fail, etc.) |

## История изменений

| Версия | Дата | Изменение | WP |
|--------|------|-----------|-----|
| 0.1 | 2026-05-17 | Первичная фиксация контракта | WP-326 |
| 0.2 | 2026-05-17 | Триггер 06:00 → 05:30 МСК (выровнено с systemd timer; обоснование: координация с Аттестатором 04:35 и render-pilot-guides 06:00) | WP-326 |
| 0.3 | 2026-05-17 | SQL-приёмочные запросы: `sent_at` → `occurred_at` (выравнивание с миграцией 219 — колонка называется `occurred_at`, не `sent_at`) | WP-326 |
