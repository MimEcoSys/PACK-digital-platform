---
id: DP.SC.151
name: Контролёр развития (профиль Onboarding Tick)
type: sc
status: active
layer: L2-Platform
summary: "Опт-инный пилот R2 получает поведенческий нудж (TG или render-задача Портному) по очереди из 11 онбординговых сообщений (WP-343) + независимые upgrade-маркеры T1→T4 (WP-349: B-low/B-high/C/E). Сообщение приходит не по расписанию, а по реальному поведению пилота. Не более 1 нуджа в сутки. Следующее сообщение доставляется в течение 8h после срабатывания триггера."
consumer: "Опт-инный пилот R2 (получатель нуджа), Портной DP.ROLE.030 (render-задачи), Проводник R13 (FSM апдейты)"
created: 2026-05-20
updated: 2026-05-22
related:
  realizes: [DP.ROLE.046]
  extends: [DP.SC.139]
  uses: [DP.SC.134, DP.SC.106]
wp: [WP-346, WP-349]
---

# [DP.SC.151] Контролёр развития — профиль Onboarding Tick

> # see DP.SC.151, DP.ROLE.046 §12

<!--
  Контекст: DP.SC.139 — базовый SC Контролёра (профиль Development, 1×/день).
  DP.SC.151 extends DP.SC.139 для профиля Onboarding:
  - другой источник состояния: learning.onboarding_state (не cp_assessments)
  - другая частота: 3×/день (05:30/12:00/18:00 МСК)
  - другая таблица маркеров: OnboardingMarkers (11 сообщений WP-343)
-->

## Правило (инвариант)

- **Не более 1 нуджа в сутки** одному пилоту (cool-down 24h по `last_nudge_at` в `onboarding_state`).
- **Порядок сообщений строго последовательный:** сообщение N отправляется только если N-1 уже отправлено (или не применимо). Исключение: сообщения 3 и 4 — параллельные (оба после consent).
- **Upgrade-маркеры независимые (WP-349):** B-low/B-high/C/E не зависят от прогресса sequential-маркеров (0-10). Приоритет: sequential → upgrade. Upgrade срабатывает только когда ни один sequential не ожидает отправки.
- **Повторных отправок нет:** если `msg_N_sent_at IS NOT NULL` — это сообщение не отправляется снова.
- **Только opt-in пилоты:** фильтр по `learning.tracking_consent.opt_in = TRUE`.
- **Single-runner:** `pg_try_advisory_lock` на БД — исключает параллельные тики.
- **Сообщения 0 и 1 — ручные:** не автоматизируются контролёром (доставляются вручную при запуске R2).

## Обещание

**Кому:** Опт-инный пилот R2 (`tracking_consent.opt_in = TRUE`) — получает своевременный нудж по онбординговому пути.

**Зачем:** Без контролёра пилот «застревает»: consent есть, но следующего шага нет. 11 сообщений (WP-343) превращают пассивное ожидание в активное сопровождение по реальному поведению.

**Что получит:**

| Потребитель | Канал | Что получает |
|-------------|-------|-------------|
| Пилот | Telegram через DP.SC.134 | Краткий нудж: «Следующий шаг — /connect» или «Записывайте время: /slot» |
| Пилот | Персональная база знаний (через Портного DP.ROLE.030) | Сообщение 7 или 8 — сложный материал через render-queue |
| Проводник R13 | FSM-апдейт | После msg_5 — показать /connect; после msg_9 — показать «Установить приложение» |

**Триггер:** systemd timer на tsekh-1, `OnCalendar=*-*-* 02:30,09:00,15:00 UTC` (= 05:30/12:00/18:00 МСК).

**Время отклика:** Нудж доставляется не позже чем через 8h после срабатывания поведенческого триггера (в худшем случае — пропустили один из трёх тиков, ждём следующего).

**Режим отказа:**
- systemd timer fail → grafana alert в tsekh-1 dashboards. Пилот не получает нудж в этот тик; следующий тик через 6-7h.
- Neon недоступен → retry 3×, потом fail → лог в journal, нет нуджа в этот тик.
- Notification Dispatcher недоступен → TG-нудж не доставлен; `onboarding_state` не обновляется → следующий тик повторит решение (idempotent).

## Что НЕ делает контролёр (профиль Onboarding)

- **Не редактирует тексты сообщений 0-10** — они в WP-343 (Pack source-of-truth, утверждены).
- **Не принимает контентные решения** — только проверяет таблицу `OnboardingMarkers`.
- **Не общается с пилотом интерактивно** — это Навигатор (MIM.R.007) при 3+ днях тишины.
- **Не оценивает ступень мастерства** — это Диагност (DP.ROLE.042) и Аттестатор (DP.ROLE.041).
- **Не создаёт персональное руководство** — только enqueue задачу Портному (DP.ROLE.030).

## Свидетельства (критерий приёмки)

| Критерий | Как проверить |
|----------|--------------|
| Пилот получил msg_5 ровно один раз | `SELECT msg_5_sent_at FROM learning.onboarding_state WHERE account_id = '...'` — одна timestamp, не NULL |
| Между нуджами прошло ≥24h | `last_nudge_at` — разрыв с предыдущим `msg_N_sent_at` ≥24h |
| Event записан в domain_event | `SELECT * FROM domain_event WHERE event_type='onboarding_msg_sent' AND account_id='...'` — есть запись |
| Cool-down не позволил повтор | `SELECT count(*) FROM domain_event WHERE event_type='onboarding_msg_sent' AND payload->>'msg_num'='5' AND account_id='...'` = 1 |
| Tick выполнялся 3× в день | systemd journal: `journalctl -u iwe-onboarding-controller -n 20` — 3 запуска за сутки |

## Поведенческие триггеры сообщений

| # | Сообщение | Триггер (условие) |
|---|-----------|-------------------|
| 0 | Анонс старта | Ручная рассылка (контролёр не автоматизирует) |
| 1 | Согласие и первый шаг | Ручная рассылка при первом входе |
| 2 | Узнать свою ступень | consent_at ≥3 дня назад AND msg_2 не отправлено |
| 3 | Подтянуть историю | first_use_consent AND NOT first_use_points |
| 4 | Записывать время | first_use_consent AND NOT first_use_slot |
| 5 | Собеседник в браузере | msg_4 отправлено AND (slot_count≥2 OR activity_days≥3) |
| 6 | Помощники и подписка | msg_5 отправлено AND (браузер подключён OR activity_days≥7) |
| 7 | Личная база знаний | msg_6 отправлено AND has_subscription AND activity_days≥7 |
| 8 | Что внутри базы | msg_7 отправлено AND first_use_guide_render AND ≥1 день после msg_7 |
| 9 | Полное окружение | msg_8 отправлено AND first_use_guide_render AND activity_days≥14 |
| 10 | Проверка системы | msg_9 отправлено AND ≥3 недели с consent_at |

## Поведенческие триггеры upgrade-маркеров (WP-349)

Запускаются после того, как ни один sequential-маркер (0-10) не ожидает отправки.

| Ключ | Название | Триггер (условие) | Cooldown |
|------|----------|-------------------|---------|
| B-low | Пост-диагност ступень 1 | has_diagnosis AND cp_stage = 1 AND msg_b_low не отправлено | 24h (общий last_nudge_at) |
| B-high | Пост-диагност ступень ≥2 | has_diagnosis AND cp_stage ≥ 2 AND msg_b_high не отправлено | 24h |
| C | Активный пилот на T1 | activity_days ≥ 7 AND NOT has_subscription AND msg_c не отправлено | 24h |
| E | Ступень ≥2 без подписки | cp_stage ≥ 2 AND NOT has_subscription AND msg_e не отправлено | 24h |

**Источник cp_stage:** `learning.cp_assessments` (таблица Диагноста DP.ROLE.042). Синхронизируется через `sync_counters_from_events()` в начале каждого тика.

**Известное ограничение (WP-349 backlog):** задержка cp_stage до 20h при диагнозе вечером (cron тика 05:30 МСК). Фикс — mini-sync на событии `diagnosis_completed` — запланирован на следующую итерацию.

## Метрики наблюдаемости

| Метрика | Где | Цель |
|---------|-----|------|
| `onboarding_controller.runs_total` | tsekh-1 journal | ≥3/день (3 тика) |
| `onboarding_msg_sent_total{msg_num}` | Neon domain_event | мониторинг по фазам R2 |
| `onboarding_users_stuck_at_level{level}` | Metabase | воронка онбординга WP-343 Ф4 |
| `onboarding_cooldown_blocked_total` | tsekh-1 journal | ожидаемо >0 (защита работает) |

## Реализующие сервисы (MAP.002)

| Сервис | Роль | Триггер |
|--------|------|---------|
| `onboarding_controller.py` (tsekh-1) | DP.ROLE.046 профиль Onboarding | ⏰ 3×/день |
| `iwe-onboarding-controller.service` (NixOS) | systemd unit | через timer |
| `iwe-onboarding-controller.timer` (NixOS) | systemd timer | OnCalendar |

## Managed-канал (T3a, WP-309 Ф8)

msg_7 запускает **двухтрековую доставку** персонального руководства:

| Трек | Условие | Что происходит |
|------|---------|---------------|
| **T3a Managed** | Нет `user_sources` (sovereign-репо) И нет `pilot_repo_map` | `create_managed_repo()` → репо `aisystant/pg-{uuid8}` создаётся автоматически → нудж содержит ссылку `GUIDE_WEB_URL/guide/{uuid}?auto=1` |
| **T3b Sovereign** | Есть `user_sources` (GitHub App установлен) | Нудж содержит `/personal-guide-start` |
| **T3a уже создан** | Есть `pilot_repo_map` (managed) | Нудж содержит прямую ссылку `GUIDE_WEB_URL/guide/{uuid}` |

**URL web-ридера:** `GUIDE_WEB_URL` env var на tsekh-1. Дефолт: `https://guide.system-school.ru`. Fallback (пока DNS не настроен): `https://web-production-1812d.up.railway.app`.

**Инвариант:** managed-репо никогда не видно в GitHub пилота — хранится в org `aisystant`. Пилот читает через web-ридер. Миграция managed→sovereign при достижении ступени 3 — WP-309 Ф10+.

## История изменений

| Версия | Дата | Изменение | WP |
|--------|------|-----------|-----|
| 0.1 | 2026-05-20 | Первичная фиксация контракта Onboarding Tick | WP-346 |
| 0.2 | 2026-05-22 | UPGRADE_MARKERS B-low/B-high/C/E: независимые триггеры T1→T4; cp_stage из cp_assessments; приоритет sequential→upgrade | WP-349 |
| 0.3 | 2026-05-22 | Managed-канал T3a: двухтрековая доставка msg_7 (create_managed_repo + web-reader URL); status → active | WP-309 Ф8 |
