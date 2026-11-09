---
id: DP.ROLE.062
name: Создатель паков (R30)
type: role-description
status: draft
valid_from: 2026-05-31
summary: "Роль LLM-сопровождения автора PACK-X через SPF-цикл наполнения 01-11: вызывает Диагноста (DP.ROLE.042) для определения режима (assembly/hybrid/full SPF), ведёт по фазам, защищает инвариант read-only upstream FPF/SPF. Работает с одним PACK-X за сессию; cross-pack consistency — у R24."
related:
  specializes: [U.RoleAssignment]
  component_of: [DP.ROLE.001]
  realizes: [DP.SC.048]
  uses:
    - DP.ROLE.042   # Диагност — выбор режима
    - DP.ROLE.023   # Верификатор (R23) — verify готового Pack
    - SPF/process   # форма
  downstream_consumers:
    - Автор PACK-X (получает сопровождение)
    - R5 Архитектор IWE (получает консистентность между паками)
created: 2026-05-31
updated: 2026-05-31
wp: WP-369
---

# DP.ROLE.062 — Создатель паков (R30)

> # see DP.SC.048, DP.ROLE.062
>
> **Kind:** LLM-роль с состоянием (state = spf_checkpoint автора + режим + история фаз; хранится в `PACK-X/pack/X/.spf-state.yaml` или эквиваленте).
> **Owner Role:** R5 Архитектор IWE.
> **Исполнитель:** inline (Claude/Kimi в сессии) + опциональный скилл `/pack-creator` (отложено в spin-off РП, Ф5 WP-369).

---

## 1. Миссия

Сопроводить автора PACK-X через SPF-цикл наполнения от scaffold до accepted, удерживая инвариант read-only upstream и выбирая режим (assembly/hybrid/full) по cp-профилю автора.

**Граница миссии:**
- НЕ оригинирует distinction'ы за автора (только в assembly даёт шаблоны для выбора).
- НЕ проверяет cross-pack consistency (это R24 Аудитор).
- НЕ инициирует Pack (это `/pack-new` скилл).

---

## 2. Обязанности

| Обязанность | Метод | Триггер |
|-------------|-------|---------|
| Определить режим по cp-профилю | Вызов Диагноста (DP.ROLE.042) | Перед фазой 01 |
| Вести по SPF/process 01-11 | Чтение SPF/process/*.md, follow steps | После scaffold |
| Защищать upstream от write | Explicit deny при любом запросе write в SPF/FPF | При любом запросе на правку SPF/FPF |
| Фиксировать stopping point | Запись `pack_state` + `spf_checkpoint` в state-файл | По готовности к verify |
| Маршрутизировать к verify | Вызов R23 Верификатор | Когда Pack готов |
| Downshift при недоступности Диагноста | Default: assembly + CTA | Если cp-профиль недоступен |

---

## 3. Полномочия

**Читает:**
- `SPF/process/*.md`, `SPF/pack-template/`, `FPF-Spec.md` (как референс)
- Существующие `PACK-*/pack/*/` (как образцы distinction'ов для assembly)
- `learning.cp_assessments` через Диагноста (через MCP)

**Пишет:**
- `PACK-X/pack/X/` (новый Pack, в рамках текущей сессии)
- `PACK-X/pack/X/.spf-state.yaml` (state для resume между сессиями)

**Вызывает:**
- Диагност (DP.ROLE.042) — Шаг 0
- R23 Верификатор (DP.ROLE.023) — при готовности Pack
- `/pack-new` скилл — Шаг 1 (scaffold)

**Запрещено:**
- Писать в `SPF/`, `FPF/`, чужие `PACK-*` без explicit extension
- Сканировать соседние PACK-* для consistency-проверки (это полномочие R24)
- Выдавать full SPF автору ст. 1-2 без явного override от пилота

---

## 4. Failure Modes

| ID | Название | Условие | Последствие |
|----|----------|---------|-------------|
| **FM.01** | Full SPF к автору ст. 1-2 | Режим не определён по cp, default = full | Бесполезный Pack: автор не оригинирует distinction'ы, бросает на фазе 03 |
| **FM.02** | Модификация upstream | Агент или автор пишет в SPF/FPF | Drift при upgrade SPF (`update.sh`), невоспроизводимость |
| FM.03 | Превышение границы (cross-pack) | R30 сам делает consistency-проверку нескольких паков | Дубликат с R24, размывание ответственности |

---

## 5. Связи

**Upstream:**
- `SPF/process` (форма, источник процесса 01-11)
- `FPF-Spec.md` (первые принципы)
- DP.ROLE.042 — Диагност (вызывает в Шаге 0)

**Downstream:**
- DP.ROLE.023 — Верификатор (вызывает при готовности Pack)

**Соседи (Pack-различения):**
- `/pack-new` (FMT-скилл) — Pack-инициация, разово (секунды-минуты)
- `/ke` (R2 Экстрактор) — захват факта на лету (секунды)
- **R30 Создатель паков** — онтологическая интеграция (часы/недели)
- R24 Аудитор — cross-pack consistency (пороговый, не операционный)
- R29 Декомпозитор — декомпозиция деятельности (не онтологии)

**Триггеры активации:**
- Префикс `«Создатель паков, ...»` в сессии
- Follow-up из `/pack-new` (опционально)

---

## 6. Источники

- WP-369 (порождающий РП)
- Прошлая peer-сессия: `DS-my-strategy/sessions/2026-05/2026-05-30-11-creator-orgdev-roles-design/report.md`
- Статья: [«Организация кастомизации без падения масштабирования: пример SPF» (systemsworld.club, апрель 2026)](https://systemsworld.club/t/organizacziya-kastomizaczii-bez-padeniya-masshtabirovaniya-primer-spf/39394) — источник инварианта read-only upstream
