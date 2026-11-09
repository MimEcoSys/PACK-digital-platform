---
id: DP.SC.048
name: Создатель паков
name_ru: Создатель паков
name_en: Pack Creator
type: sc
status: draft
layer: L4-Personal
summary: "Автор PACK-X получает: LLM-сопровождение через весь SPF-цикл наполнения собственного Pack 01-11, с режимом по cp-профилю (assembly/hybrid/full SPF) и защитой инварианта read-only upstream FPF/SPF."
consumer: Автор PACK-X (cp ст. 1-5), R5 Архитектор IWE
created: 2026-05-31
updated: 2026-05-31
related:
  specializes: []
  realizes:
    - DP.ARCH.001               # Экзокортекс — надсистема
  uses:
    - DP.ROLE.062               # Создатель паков (R30) — носитель роли
    - DP.ROLE.042               # Диагност — выбор режима по cp-профилю
    - DP.ROLE.023               # Верификатор (R23) — verify готового Pack
    - DP.ROLE.024               # Аудитор (R24) — cross-pack consistency (за границей роли)
  see_also:
    - DP.SC.014                 # Pack formalization
    - DP.SC.036                 # Routing Gate
wp: WP-369
---

# [DP.SC.048] Создатель паков

## 1. Правило (инвариант)

> Нарушение любого = провал SC.

- **Read-only upstream.** SPF/FPF не модифицируются. Любой запрос на изменение upstream → STOP + перенаправление в `PACK-X/pack/X/` через explicit extend/override.
- **Три режима, не один.** Режим определяется cp-профилем автора (Диагност, DP.ROLE.042): assembly (ст. 1-2) / hybrid (ст. 3) / full SPF (ст. 4-5). Нет режима «всегда full SPF».
- **Обязательная диагностика.** Перед фазой 01 SPF/process — вызов Диагноста. cp-профиль недоступен → downshift в assembly с явным предупреждением.
- **Кастомизация через extension.** Все локальные добавления — в `PACK-X/pack/X/`, никогда в `SPF/` или `FPF/`.
- **Один Pack за сессию.** Создатель паков работает с **одним** PACK-X за сессию. Cross-pack consistency (скан соседних паков на ID-коллизии, онтологические конфликты, drift) — это полномочие R24 Аудитор, не R30. R30 читает соседние PACK-* только как reference-шаблоны для distinction'ов, не как authority для правок.

---

## 2. Обещание

**Кому:**
- **Автор PACK-X (cp ст. 1-5)** — «LLM-сопровождение через весь SPF-цикл 01-11 с защитой от антипаттерна "локальные кастомизации ломают upgrade SPF" ([systemsworld.club, апрель 2026](https://systemsworld.club/t/organizacziya-kastomizaczii-bez-padeniya-masshtabirovaniya-primer-spf/39394))»
- **R5 Архитектор IWE** — «консистентность между паками, upstream FPF/SPF не разрушен»

**Зачем:**
- `/pack-new` даёт scaffold за 5 мин (разово), `/ke` — захват факта за секунды, но ни один не ведёт через **онтологическую интеграцию** (часы/недели по SPF/process 01-11)
- Авторы ст. 1-2, получившие full SPF без режима, производят бесполезный Pack: не оригинируют distinction'ы (FM.01)
- Без явной защиты инварианта — автор модифицирует SPF локально, при `update.sh` теряет правки или ломает upgrade

**Что получит:**

```
{
  "mode": "assembly | hybrid | full_spf",
  "spf_checkpoint": "01 | 02 | ... | 11 | stopped",
  "pack_state": "scaffold | ontology-draft | reviewed | accepted",
  "upstream_touch": "none | read-only | BLOCKED_WRITE_ATTEMPT",
  "next_action": "конкретный шаг для следующей сессии"
}
```

---

## 3. Время отклика

- Определение режима по cp-профилю — < 1 с (кэш Диагноста в `learning.cp_assessments`).
- Одна фаза SPF с LLM-сопровождением — 10-30 мин (зависит от фазы).
- Полный цикл 01-11 — 2-6 недель (не монолитно, по фазам, между сессиями).

---

## 4. Основной flow

```
Автор инициирует («Создатель паков, ...» или follow-up из /pack-new)
  │
  ├─ Шаг 0: вызов Диагноста → cp-профиль
  │   ├─ ст. 1-2 → assembly-режим
  │   ├─ ст. 3   → hybrid-режим
  │   └─ ст. 4-5 → full SPF-режим
  │   └─ cp недоступен → default: assembly + CTA «пройдите диагностику для точной калибровки»
  │
  ├─ Шаг 1: scaffold (/pack-new) — для всех режимов
  │
  ├─ Шаг 2: фазы 02-11 по SPF/process, глубина зависит от режима
  │   ├─ assembly: агент предлагает готовые distinction-шаблоны из соседних паков (read-only), автор выбирает
  │   ├─ hybrid:   агент предлагает + автор модифицирует под домен
  │   └─ full SPF: автор оригинирует distinction'ы, агент консультирует по форме
  │
  ├─ Шаг 3: при любом запросе write в SPF/FPF → BLOCKED_WRITE_ATTEMPT + объяснение extension-механизма
  │
  └─ Stopping point: Pack проходит /verify по SPF.SPEC.001
```

**Метрика:** `spf-depth-distribution.tsv` — режим × фаза × результат (для калибровки assembly-шаблонов).

---

## 5. Сценарии использования

**Сценарий 1: Автор ст. 2 хочет Pack «системный менеджмент в строительстве» — assembly-режим**
- Потребитель: автор домена, cp.iwe=2.
- Диагност → ст. 2 → assembly. Агент выдаёт scaffold + шаблоны distinction'ов из PACK-systems-art и PACK-MIM (read-only, как образцы) → автор заполняет чек-листы.
- Результат: Pack проходит `/verify`, без оригинальных distinction'ов (OK для assembly-режима).

**Сценарий 2: Автор ст. 4 делает Pack «цифровой двойник образования» — full SPF**
- Потребитель: автор домена, cp.iwe=4.
- Диагност → ст. 4 → full SPF. Агент консультирует по форме, но distinction'ы оригинирует автор.
- Результат: Pack с оригинальной онтологией, принят R23 Верификатор.

**Сценарий 3: Запрос на правку `SPF/process/05-methods.md`**
- Потребитель: автор, не понимает границу.
- Агент: STOP + объяснение «это upstream; ваши изменения — в `PACK-X/pack/X/03-methods/`» + ссылка на extension-механизм.
- Результат: инвариант защищён, автор переадресован, `upstream_touch: BLOCKED_WRITE_ATTEMPT` в логе.

---

## 6. Режимы отказа

| ID | Сценарий | Поведение |
|----|----------|-----------|
| **FM.01** | Full SPF к автору ст. 1-2 | Режим не определён по cp → downshift в assembly + объяснение «на вашей ступени оригинировать distinction'ы ещё рано, начнём с готовых шаблонов» |
| **FM.02** | Запрос на write в SPF/FPF | BLOCKED_WRITE_ATTEMPT → лог + объяснение extension-механизма + ссылка на `PACK-X/pack/X/` |
| FM.03 | Диагност недоступен (нет cp-профиля) | Default: assembly + CTA «пройдите диагностику для точной калибровки» |
| FM.04 | Pack не проходит verify после 3 итераций | Эскалация R5 Архитектор + R24 Аудитор (cross-pack drift-check) |
| FM.05 | Автор бросает процесс на фазе N | Состояние сохраняется (`spf_checkpoint: N`), возможен resume в новой сессии |

---

## 7. Метаданные

- **Owner Role:** R5 Архитектор IWE.
- **Реализация:** inline (Claude/Kimi в сессии) + опциональный скилл `/pack-creator` (отложено в spin-off РП).
- **Триггер активации:** префикс `«Создатель паков, ...»` (см. `.claude/rules/role-prefixes.md`).

**Связи:**
- DP.ROLE.062 — носитель роли R30.
- DP.ROLE.042 — Диагност (Шаг 0).
- DP.ROLE.023 — Верификатор (verify готового Pack).
- DP.ROLE.024 — Аудитор (cross-pack consistency, **за границей** R30).
- SPF/process 01-11 — источник процесса.
- WP-369 — порождающий РП.

**Связанные документы:**
- Инвариант read-only upstream формализован в `SPF/process/00-process-overview.md#extension-mechanism` (WP-377 Ф2.2).

**Открытые задачи (spin-off, post-WP-369):**
- Файловый guard в скилле `/pack-creator` (запрет write в SPF/FPF на уровне файловой системы) — отдельный РП (Ф5 WP-369 отложен).
