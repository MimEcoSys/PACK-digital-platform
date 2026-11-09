---
id: DP.ROLE.043
name: Лаборант
type: role-description
status: draft
valid_from: 2026-05-16
summary: "Роль симулятора траектории Созидателя: принимает профиль + паттерн поведения, запускает сценарий (Scenario.run() → DataFrame), возвращает траекторию характеристик и ступени во времени — в pilot-mode без технических кодов."
related:
  specializes: [U.RoleAssignment]
  component_of: [DP.ROLE.001]
  realizes: [DP.SC.133]
  uses:
    - DP.ROLE.041   # Аттестатор — источник bh-профиля через Neon read-only
    - stage_config.py  # SoT нормативов (STAGE_GATE_MATRIX, STB_GATE, CUMULATIVE_HOURS_GATE)
  downstream_consumers:
    - Пилот (Ученик) — видит траекторию и рекомендацию
    - Навигатор (MIM.R.007) — использует для ответа «через сколько перейдёшь»
    - Команда — калибровка норм (S4) и когортная аналитика (S3)
created: 2026-05-16
updated: 2026-05-16
wp: WP-319
---

# Лаборант — DP.ROLE.043

> # see DP.SC.133, DP.ROLE.043
>
> **Kind:** Computation Role (вычислительная роль без побочных эффектов).
> **Owner Role:** Платформа (aisystant) — исполнитель: Railway-сервис `simulator-lab`.
> **Источник нормативов:** `stage_config.py` (единственный SoT — Лаборант не хардкодит пороги).

---

## 1. Миссия

Перевести **паттерн поведения пилота** в **понятную траекторию**: что произойдёт с его характеристиками и ступенью через 4, 8, 12 недель, если он изменит (или сохранит) текущее поведение.

Аналогия: краш-тест автомобиля. Задаёшь нагрузку (паттерн) → измеряешь деформацию (изменение ступени). Лаборант — стенд, не оракул. Он моделирует механику платформы, не предсказывает реальное поведение человека.

**Граница:** Лаборант только читает данные (read-only Neon), только вычисляет, только отдаёт результат. Он не пишет в Neon, не меняет профиль, не отправляет уведомления.

---

## 2. Обязанности

| Обязанность | Как выполняется |
|---|---|
| Загрузить реальный bh-профиль пилота | `load_profile(account_id, conn)` через `stage_simulator_ro` |
| Запустить сценарий | `Scenario.run(profile, params, horizon_weeks=12) → DataFrame` |
| Найти bottleneck | `argmin` по дистанции до следующей ступени |
| Сформировать pilot-mode текст | По эталону DP.SC.133 (без кодов, конкретная рекомендация) |
| Парсить текстовый сценарий | LLM-парсер (Haiku tool_use, confidence gate 0.7) |
| Показать Expert-mode | Plotly multi-line chart, YAML upload, sliders |

---

## 3. Входы / Выходы

**Входы:**
- `account_id` — идентификатор пилота (из Neon `learning.stage_transitions`)
- `scenario_params` — словарь переопределений bh (hours_per_week, days_per_week, …)
- `horizon_weeks` — горизонт симуляции (по умолчанию 12)
- `scenario_id` — s1 / s2 / s3 / … (какой сценарий запускать)

**Выходы:**
- `DataFrame[week × {bh.sys, bh.inv, bh.met, bh.awr, bh.agn, bh.stb, stage, points, bottleneck}]`
- Pilot-mode текст (str, по эталону SC.133)
- Plotly figure (для UI)

---

## 4. Архитектура (слои)

```
Engine (pure Python, stage_config SoT)
  Scenario.run(profile, params, horizon) → DataFrame
       ↑                    ↑
Data layer            Scenario layer
load_profile()        s1_stage_trajectory.py
load_real_events()    s2_rewards_trajectory.py
stage_simulator_ro    s3_cohort_dynamics.py
(Neon read-only)      YAML presets / LLM parser
```

**Принцип эволюции:**
- Новое bh-измерение = колонка в DataFrame + строка в stage_config. UI подхватывает через introspection.
- Новый сценарий = один файл `scenarios/SN.py` (наследник `Scenario`), без правки engine или UI.

---

## 5. Ограничения (инварианты роли)

1. **Read-only.** Роль не имеет прав на INSERT/UPDATE/DELETE в Neon. Реализовано через `stage_simulator_ro` (GRANT SELECT only).
2. **Без кодов в Pilot-mode.** Нарушение контракта → регрессия SC.133.
3. **Нормативы из stage_config.** Лаборант не содержит жёстко прописанных порогов.
4. **Deterministic.** При одинаковом профиле + параметрах → одинаковый результат. LLM-парсер — единственный недетерминированный компонент (с confidence gate).

---

## 6. Связи с другими ролями

| Роль | Отношение |
|---|---|
| DP.ROLE.041 Аттестатор | Источник данных (Аттестатор записывает в Neon, Лаборант читает) |
| Навигатор (MIM.R.007) | Потребитель (Навигатор встраивает ссылку на симулятор в ответы) |
| DP.ROLE.042 Диагност | Смежная роль (Диагност — статичный snapshot, Лаборант — динамическая траектория) |
