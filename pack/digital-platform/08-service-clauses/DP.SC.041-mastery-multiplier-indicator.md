---
id: DP.SC.041
name: Индикатор мультипликатора IWE в характеристике мастерства
name_ru: Индикатор мультипликатора IWE в характеристике мастерства
name_en: IWE Multiplier Indicator in Mastery Characteristic
type: sc
status: active
layer: L4-Personal
summary: "Потребители (Аттестатор, Навигатор, Metabase) получают в digital_twins.data['3_derived']['3_2_mastery'] четыре числа: multiplier_auto, multiplier_manual, multiplier_drift, multiplier_7d_avg. Расхождение — сигнал, не ошибка."
consumer: Диагност (DP.ROLE.042), Навигатор (MIM.R.007), R24 Аттестатор, Metabase dashboards
created: 2026-05-17
updated: 2026-05-17
related:
  uses: [DP.SC.020]
  see_also: [PD.FORM.104, DP.FM.036]
wp: WP-299
---

# [DP.SC.041] Индикатор мультипликатора IWE в характеристике мастерства

## Правило (инвариант)

> Что ВСЕГДА должно выполняться. Нарушение = провал SC.

- `digital_twins.data['3_derived']['3_2_mastery']` содержит ВСЕ четыре поля: `multiplier_auto`, `multiplier_manual`, `multiplier_drift`, `multiplier_7d_avg`.
- Поле может быть `null` (нет данных), но ключ присутствует ВСЕГДА.
- `multiplier_auto` вычисляется по [PD.FORM.104](../../../../../PACK-personal/pack/personal-development/02-domain-entities/formalizations/PD.FORM.104-iwe-multiplier.md) §1 — формальная формула.
- `multiplier_manual` берётся из последнего `day_close.payload.multiplier` за текущий день; `null` если события нет.
- `multiplier_drift = (manual - auto) / max(auto, 0.01)` если оба не null; иначе `null`.
- `multiplier_7d_avg` — среднее дневных `multiplier_auto` за 7 дней.

## Обещание

**Кому:**
- **Диагност** (DP.ROLE.042) — использует `multiplier_7d_avg` как proxy AI-leverage пилота для рекомендаций ступени.
- **Навигатор (MIM.R.007)** — обсуждает с пилотом расхождение `multiplier_drift` (что не видит автомат? что пилот переоценивает?).
- **R24 Аттестатор** (DP.ROLE.041) — учитывает мультипликатор в оценке прогресса (но не как единственный сигнал).
- **Metabase** — отображает оба индикатора рядом с подсветкой расхождения.

**Зачем:** одно число (только автоматический или только ручной) даёт ложную картину. Автоматический видит только формальные РП и WakaTime. Ручной видит работу пилота, но субъективен. Расхождение между ними — самая ценная информация: что система не учитывает.

**Что получит:** 4 поля в `3_2_mastery` после каждого запуска `recalculate_derived.py`. Все 4 либо рассчитаны, либо явно `null` с понятной причиной (см. PD.FORM.104 §4 «Граничные случаи»).

**Триггер:** Запуск профайлера `recalculate_derived.py` (по расписанию `iwe-profiler.timer` или вручную).

**Время отклика:** ≤1 минуты на пользователя.

**Режим отказа:**
- `learning` БД недоступна → все 4 поля = `null`, ключи присутствуют.
- WakaTime данных нет за период → `multiplier_auto = null`, `multiplier_manual` независим.
- `day_close` события нет → `multiplier_manual = null`, `multiplier_auto` независим.
- Оба null → `multiplier_drift = null` (а не 0).

## Свидетельства (критерий приёмки)

**Данные** (что фактически существует):

| Критерий | Как проверить |
|----------|--------------|
| 4 ключа всегда присутствуют | `psql learning -c "SELECT data->'3_derived'->'3_2_mastery' FROM digital_twins WHERE user_id=...;"` — JSON содержит multiplier_auto, multiplier_manual, multiplier_drift, multiplier_7d_avg |
| `multiplier_drift` корректно вычислен | manual=2.5, auto=2.0 → drift=0.25; manual=null OR auto=null → drift=null |
| `multiplier_manual` берёт последнее day_close дня | `SELECT payload->>'multiplier' FROM domain_event WHERE event_type='day_close' AND date=today ORDER BY occurred_at DESC LIMIT 1;` совпадает с записью в digital_twins |

**Контекст** (при каких условиях обещание действует):

| Условие | Проверка |
|---------|---------|
| Хук `iwe-orz-tracker.sh` эмитит `day_close` | grep `day_close` в логах event-gateway за день |
| `recalculate_derived.py` запускается | `systemctl status iwe-profiler.timer` |
| WakaTime sync работает | `iwe-activity-hub-sync.timer` active |

## Сценарии использования

1. **Аттестатор оценивает ступень.** Читает `3_2_mastery.multiplier_7d_avg`. Сравнивает с ожидаемым диапазоном для ступени. Если ниже нормы И bh.inv в норме — bottleneck не в инвестиции, а в leverage (мало используешь ИИ).

2. **Навигатор обсуждает прогресс с пилотом.** Видит `multiplier_drift = +0.5` (manual 3.0, auto 2.0). Спрашивает: «Что ты сделал из того, что не оформлено как РП? Стоит ли это формализовать?» Расхождение → разговор про невидимую работу.

3. **Metabase dashboard «AI-leverage».** Две линии на одном графике: `multiplier_auto` (синяя) и `multiplier_manual` (зелёная). Расхождение визуально — пилот видит свою картину vs картину системы за прошедшие недели.

## Связанные документы

- [PD.FORM.104](../../../../../PACK-personal/pack/personal-development/02-domain-entities/formalizations/PD.FORM.104-iwe-multiplier.md) — определение мультипликатора (что меряем)
- [DP.FM.036](../05-failure-modes/DP.FM.036-wakatime-coding-time-bias.md) — почему WakaTime подходит для учётного времени (применимость уточнена)
- [DP.SC.020](./DP.SC.044-event-ingest.md) — приём событий `coding_time`, `wp_completed`, `day_close`
- [WP-299](../../../../../DS-my-strategy/inbox/WP-299-time-accounting-system.md) — родительский РП
