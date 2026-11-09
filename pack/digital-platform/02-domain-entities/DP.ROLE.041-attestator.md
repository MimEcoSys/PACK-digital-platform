---
id: DP.ROLE.041
name: Аттестатор
type: role-description
status: draft
valid_from: 2026-05-14
summary: "Роль автоматического вычислителя ступени Ученика: читает события из Activity Hub, считает 7 bh-характеристик (bh.sys/inv/met/awr/agn/scl/stb) по двум осям (Мастерство × Мировоззрение), сравнивает с нормативной матрицей и записывает bh-сигнал в learning.stage_transitions. Итоговую ступень фиксирует двойной gate: bh-сигнал Аттестатора + cp-подтверждение Диагноста (MIM.R.009). Болид-онтология: Аттестатор измеряет Пилота, не всего Созидателя."
related:
  specializes: [U.RoleAssignment]
  component_of: [DP.ROLE.001]
  realizes: [DP.SC.020]
  uses:
    - PD.FORM.089   # RCS-модель v4: 7 bh-характеристик, 13 cp-срезов, двойной gate, матрица минимумов
    - PD.FORM.080   # Нарратив ступеней + двойной gate Д→П
    - DP.ROLE.032   # Event Ingester — поставляет события в domain_event
    - DP.ROLE.034   # Rewards Projector — downstream-параллель по баллам
  downstream_consumers:
    - Портной (re-render personal-guide при смене ступени)
    - Bot notification (пилот получает сообщение о новой ступени)
    - digital_twins.stage_id (единый профиль пользователя)
created: 2026-05-14
updated: 2026-05-14
wp: WP-310
---

# Аттестатор (DP.ROLE.041)

> **Kind:** Platform Evaluation Role (платформенная роль вычисления ступени).
> **Owner Role:** Платформа (aisystant) — исполнитель `stage_evaluator.py` (Railway/tsekh-1 cron).
> **Текущий исполнитель:** `stage_evaluator.py` в `DS-IT-systems/activity-hub/activity_hub/workers/` — запускается cron 04:35 МСК ежедневно (после profiler).

## 1. Миссия

Автоматически и воспроизводимо определять **текущую ступень Ученика** (1 Случайный → 5 Проактивный) по объективным поведенческим данным из Activity Hub. Устранять произвол ручной диагностики: два запуска на одних данных дают одинаковый результат.

Фиксировать **момент перехода** (stage_transitions) и запускать downstream-эффекты: уведомление пилоту, перегенерацию руководства, обновление профиля.

**Граница:** только инкрементальные переходы (ступень растёт, не падает) в MVP. Понижение ступени — отдельная задача (не реализована). Также не заменяет живую диагностику Диагноста (DP.ROLE.042) — дополняет как baseline-proxy для новых пользователей.

---

## 2. Полный процесс: от действия пользователя до смены ступени

### 2.1 Источники событий (откуда приходят данные)

Пользователь действует в разных местах — каждое место эмитирует события в `learning.domain_event` (Activity Hub, Neon):

| Место действия | Что делает пользователь | Событие | Статус |
|---|---|---|---|
| **IWE (VS Code / claude.ai)** | Открывает день (Day Open) | `day_open`, `day_plan_opened` | ✅ ORZ hook |
| **IWE (VS Code / claude.ai)** | Закрывает день (Day Close) | `day_close`, `day_plan_closed` | ✅ ORZ hook |
| **IWE (VS Code / claude.ai)** | Закрывает неделю (Week Close) | `week_plan_closed` | ✅ ORZ hook |
| **IWE (VS Code / claude.ai)** | Закрывает месяц (Month Close) | `month_plan_closed` | ✅ ORZ hook |
| **IWE (VS Code / claude.ai)** | Проводит стратегическую сессию | `strategy_session_completed` | ✅ ORZ hook |
| **IWE (VS Code / claude.ai)** | Извлекает знание (/ke) | `knowledge_extracted` | ✅ ORZ hook |
| **IWE (VS Code / claude.ai)** | Обновляет Pack | `pack_updated` | ✅ git hook |
| **IWE (VS Code / claude.ai)** | Любая IWE-сессия | `iwe_session` | ✅ ORZ hook |
| **Бот (@aist_me_bot)** | Логирует слот (/slot) | `slot_logged` | ✅ бот |
| **Бот (@aist_me_bot)** | Закрывает РП | `wp_closed`, `wp_completed` | ✅ бот |
| **Бот (@aist_me_bot)** | Завершает стратегическую сессию | `strategy_session_completed` | ✅ бот (дубль с IWE) |
| **LMS (aisystant.com)** | Проходит урок | `lesson_completed` | ✅ bridge-2 |
| **LMS (aisystant.com)** | Получает квалификацию | `qualification_granted` | ⚠️ не реализовано (Gap-В, не блокер) |
| **WakaTime** | Кодирует в IDE/VS Code | `coding_time` | ✅ WakaTime adapter (iwe.py) |
| **Клуб (systemsworld.club)** | Публикует пост | `club_post_created` | 🔴 WP-296 ждёт ORY-SSO |
| **GitHub** | Коммитит в Pack | `pack_updated` | ✅ git hook (дубль с IWE) |

> **WakaTime и GitHub** — не «места» в UI-смысле, но реальные источники данных. WakaTime даёт Инвестированное время, GitHub-коммиты в Pack дают Методичность.

### 2.2 Характеристики: из каких событий и к каким осям относятся

Аттестатор группирует события по **7 bh-характеристикам** (bh. = behaviour), разбитым по двум осям: Мастерство и Мировоззрение. Источник определения: `PD.FORM.089 v4 §12`.

**Болид-онтология (FORM.089 §1):** Созидатель = Пилот (Человек) + Машина (IWE). Аттестатор измеряет **Пилота** — его поведенческие метрики из событий Activity Hub. Машина (Pack, DS, Агенты) измеряется отдельно.

**Двойной gate (FORM.089 §5.1):** Аттестатор вычисляет bh-сигнал (recommended_stage) → Диагност (MIM.R.009) проводит диалог по 13 cp-срезам → итоговая ступень = min(bh-сигнал, cp-подтверждение). bh-характеристики фиксируют частоту и объём поведения; cp-срезы оценивают потенциал и глубину понимания.

**Ось: Мастерство** — операциональный уровень, как человек организован и сколько вкладывает.

| Код | Характеристика | Показатель | Откуда события | Тип |
|---|---|---|---|---|
| **bh.sys** | Систематичность | `self_dev_days_per_week` | `SELF_DEV_EVENT_TYPES`: lesson_completed, knowledge_extracted, pack_updated, iwe_session, day_open/close, week/month_plan_closed, strategy_session_completed | обязательная — ноль блокирует ступень |
| **bh.inv** | Инвестированное время | `avg_hours_per_week` | `slot_logged.hours` (4 source: active, self_report_backfill, self_report_daily, self_report_weekly) + `lesson_completed.duration_minutes/60` | обязательная — ноль блокирует ступень |
| **bh.met** | Методичность мышления | `methodical_events_per_month` | lesson_completed, knowledge_extracted, pack_updated, qualification_granted | компенсаторная |
| **bh.scl** | Масштабность | `scale_score` | wp_completed × actual_hours (фиксированный вес в MVP) | информационная |
| **bh.stb** | Устойчивость | `max_gap_days` | максимальный разрыв без SELF_DEV-события за учётный период | gate |

> **К4 fix (FORM.089 §12.2):** `coding_time` (WakaTime) исключён из bh.inv — он включает все репозитории, в том числе рабочие. Используются только чистые учебные события: `slot_logged` + `lesson_completed`. Нормативы установлены с учётом этого занижения.

**Ось: Мировоззрение** — рефлексивный уровень, как человек видит себя и систему.

| Код | Характеристика | Показатель | Откуда события | Тип |
|---|---|---|---|---|
| **bh.awr** | Осведомлённость (worldview) | `worldview_score` | week_plan_closed, month_plan_closed, strategy_session_completed, knowledge_extracted, pack_updated | основная |
| **bh.agn** | Агентность | `agency_score` | wp_created, wp_closed, wp_completed, strategy_session_completed | основная |

> **Почему две оси, а не одна?** Мастерство и Мировоззрение — **ортогональные** линии развития (FORM.080 §3). Можно быть очень систематичным (высокое bh.sys) и при этом не видеть себя как деятеля в системе (низкое bh.awr). Ступень = узкое место обеих осей. Это характеристики **Пилота как системы** — два независимых измерения одного объекта.

**Накопленные часы (hard gate):** `total_hours_cumulative` — кумулятив slot_logged + lesson_completed за всё время. Нельзя получить ступень без минимального опыта. ✅ реализован в stage_evaluator.py.

**AWR_WINDOW_DAYS = 30** — явно зафиксировано в конфиге (З4, WP-310).

### 2.3 Нормативная матрица (пороги по характеристикам)

Аттестатор сравнивает вычисленные индексы (0–5) с матрицей минимумов (FORM.089 v4 §12.3):

| Характеристика | Ст.1 | Ст.2 | Ст.3 | Ст.4 | Ст.5 |
|---|:---:|:---:|:---:|:---:|:---:|
| **bh.sys** Систематичность (дн/нед) | — | ≥2 | ≥3 | ≥4 | ≥5 |
| **bh.inv** Инвестированное время (ч/нед) | — | ≥2 | ≥3 | ≥4 | ≥5 |
| Накоп. часы (hard gate) | — | ≥20ч | ≥48ч | ≥96ч | ≥161ч |
| **bh.met** Методичность мышления | — | — | ≥1 | ≥2 | ≥4 |
| **bh.awr** Системность мировоззрения | — | — | ≥2 | ≥3 | ≥4 |
| **bh.agn** Агентность | — | — | ≥1 | ≥2 | ≥4 |
| **bh.stb** Устойчивость (gate) | — | ≥1 | ≥2 | ≥3 | ≥4 |

> **bh.met ≥ 4 для ст.5** (исправлено WP-310 Ф9: было ≥ 3 — слишком низкий порог для Проактивного).
> **bh.stb gate:** максимальный разрыв без SELF_DEV-активности. STB_GATE: ст.2 ≥ 1, ст.3 ≥ 2, ст.4 ≥ 3, ст.5 ≥ 4 (bh.stb=5 → разрыв ≤1 дня; bh.stb=1 → разрыв 15–30 дней).

**Окно расчёта растёт со ступенью** (`accounting_period` — ключевой параметр):

| Ступень | Окно | Смысл |
|---|---|---|
| Случайный (1) | 1 нед | Начинающий оценивается за последнюю неделю |
| Практикующий (2) | 4 нед | Нужна месячная устойчивость |
| Систематический (3) | 8 нед | Два месяца стабильной практики |
| Дисциплинированный (4) | 12 нед | Квартал |
| Проактивный (5) | 24 нед | Полгода — доказанная устойчивость |

**Управление нормативами.** Сейчас нормативы захардкожены в `stage_evaluator.py` и `compute_stage_mvp()` в FORM.089 §12. Целевой состав управляющих параметров (`i.accounting_period`, `i.min_hours_for_qualification`, пороги характеристик по ступеням, веса событий) — выводить в конфиг Pack (`iwe-actions-catalog.md §7`), чтобы агент-Аттестатор мог перечитывать нормативы без пересборки кода. Это задача Ф5+ (конфиг-driven).

### 2.4 Downstream: что происходит после перехода ступени

```
stage_transitions INSERT (Аттестатор)
    │
    ├─→ digital_twins.stage_id UPDATE      — профиль пользователя обновлён
    ├─→ Уведомление пилоту в бот           — «Вы перешли на ступень N»
    ├─→ Триггер Портному                   — re-render personal-guide под новую ступень
    └─→ Обновление целевого ритма          — норма часов/нед в weekly-plan.md
```

> **Статус Ф2-Ф3 (май 2026):** downstream не реализован. Аттестатор пишет в stage_transitions, но дальше ничего не происходит. Реализация — WP-310 Ф2-Ф3.

---

## 3. Обязанности

| Обязанность | Метод | Триггер |
|-------------|-------|---------|
| Загрузить список opt-in пользователей | `SELECT account_id FROM learning.tracking_consent WHERE opt_in=TRUE` | Каждый запуск |
| Прочитать события по каждому пользователю | SQL по `learning.domain_event` + `learning.w_reflections` | По каждому account_id |
| Вычислить индексы характеристик | `calc_rcs_indices(metrics)` → {bh.sys, bh.inv, bh.met, bh.awr, bh.agn, bh.scl, bh.stb} 0..5 | По каждому account_id |
| Вычислить ступень | `compute_stage(indices)` — FORM.089 §5 | По каждому account_id |
| Сравнить с текущей ступенью | `MAX(to_stage) FROM stage_transitions WHERE account_id=$1` | По каждому account_id |
| Записать переход | INSERT в `learning.stage_transitions` (from, to, triggered_by, evidence JSONB) | Только если computed > cur |
| Запустить downstream | listener/hook → digital_twins + бот + Портной + ритм | После каждого INSERT (Ф2-Ф3) |
| Логировать метрики | stage_transitions_inserted, users_processed, errors | Каждый запуск |

---

## 4. Полномочия

- **Читает** `learning.domain_event` (только WHERE account_id = $1 — L2-PRIVACY).
- **Читает** `learning.w_reflections`.
- **Читает** `learning.tracking_consent` (проверка opt-in).
- **Пишет** в `learning.stage_transitions` (INSERT, не UPDATE).
- **НЕ понижает** ступень (только инкремент в MVP).
- **НЕ читает** raw-текст пользователя — только числа и event_type.

---

## 5. Границы роли

| Делает | НЕ делает |
|--------|-----------|
| Считает ступень автоматически | Не ведёт диалог с пользователем (это Диагност, DP.ROLE.042) |
| Фиксирует переход с evidence | Не объясняет пользователю почему (это Навигатор, MIM.R.007) |
| Запускает downstream-эффекты | Не создаёт контент руководства (это Портной) |
| Работает по расписанию | Не является on-demand API (в MVP) |
| Пишет только вперёд (рост) | Не понижает ступень при деградации (будущая задача) |

---

## 6. Инварианты (что гарантируется)

1. **Idempotency:** повторный запуск на тех же данных не создаёт дублей. UNIQUE(account_id, to_stage) на `stage_transitions`.
2. **Privacy:** только числа/индексы в evidence JSONB — никакого raw-text, имён, email.
3. **Consent gate:** пользователь без opt-in пропускается (skipped_consent += 1).
4. **Монотонность:** `to_stage > from_stage` — DB CHECK constraint (миграция 114+).
5. **Воспроизводимость:** один и тот же алгоритм + данные → одна и та же ступень.

---

## 7. Режим отказа

| Отказ | Симптом | Реакция |
|---|---|---|
| DSN недоступен | `asyncpg.ConnectionError` | Завершить с exit(1), не писать |
| Метрики читаются, но вычисление упало | Exception в `evaluate_one` | errors += 1, пропустить пользователя, продолжить |
| INSERT отклонён (дубль) | ON CONFLICT DO NOTHING | Нормально — idempotent |
| Downstream не отвечает (Ф2+) | Timeout listener | Логировать, не блокировать следующий цикл |
| stage_evaluator не запускался N дней | — | Alert Ф6 (не реализован) |

---

## 8. Известные ограничения MVP

1. **bh.agn (Агентность) без поля initiator.** MVP: все wp_created = самоинициированные. Реализация с `initiator`-полем — WP-214 Ф10.5.
2. **Gap-Д:** bh.sys (Систематичность) использует широкий фильтр `activity_domain IN ('practice', 'learning')` вместо `SELF_DEV_EVENT_TYPES`. Завышает Систематичность. Фикс — Ф4 WP-310.
3. **Gap-А:** поле `quality` в `week_plan_closed` payload не заполняется → весовой бонус ×4 для bh.awr не работает. Фикс — Gap-А WP-310.
4. **Клуб не подключён:** `club_post_created` добавит вес в bh.awr — ждёт WP-296 (ORY-SSO).
5. **Нормативы захардкожены:** пороги и веса в коде, не в конфиге. Управление → конфиг-driven Ф5+.
6. **Downstream не реализован:** после записи stage_transitions ничего не происходит — Ф2-Ф3 WP-310 (✅ реализовано 14 мая, Ф2-Ф3).
7. **bh.scl без actual_hours.** Поле реального времени по wp_completed отсутствует — используется фиксированный вес. Тикет: WP-214 Ф11. (WP-310 Ф11, добавлено 2026-05-15)
8. **bh.stb gate не реализован в rcs-collector.** Нет запроса max_gap в stage_evaluator.py. Добавить в Ф10+ WP-310. (WP-310 Ф10, добавлено 2026-05-15)
9. **Self-report без верификации (Ф13).** В MVP пилот заявляет учебное время сам — нет проверки на завышение. Защитный фактор: симулятор Ф12 показывает bottleneck, не «достижение». Будущее: модель доверия (`confidence: measured | estimated`) с весом.

---

## 9. Ссылки

| Документ | Где |
|---|---|
| Алгоритм вычисления ступени | `PD.FORM.089-learner-rcs.md` §5, §12 |
| Веса событий и конфигурация | `DS-ecosystem-development/.../Data-Governance/iwe-actions-catalog.md §7` |
| Код исполнителя | `DS-IT-systems/activity-hub/activity_hub/workers/stage_evaluator.py` |
| DB-схема stage_transitions | `DS-IT-systems/neon-migrations` (миграции 109-114) |
| Нарративы ступеней | `PD.FORM.080-stage-direction-normative-matrix.md` |
| РП реализации | `DS-my-strategy/inbox/WP-310-attestator.md` |
