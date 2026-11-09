---
id: DP.M.177
name: Управление состояниями bug-report в inbox
name_ru: Lifecycle bugs в inbox
name_en: Bug Inbox Lifecycle Management
type: method
status: active
summary: "Метод управляет состояниями bug-report файлов в inbox/bugs/ через frontmatter-статус (open|resolved|invalid) и триггер Week Close: автоматический review открытых багов старше 14 дней с архивацией разрешённых."
created: 2026-05-25
trust:
  F: 4
  G: domain
  R: 0.85
epistemic_stage: evidence
related:
  uses: [DP.M.010]
  references: []
tags: [bugs, inbox, lifecycle, governance, week-close, iwe]
wp: WP-247
---

# Lifecycle bugs в inbox (DP.M.177)

## 1. Проблема

`inbox/bugs/` накапливает открытые bug-файлы без lifecycle: через месяц 40+ файлов без архивации, нет видимого состояния.

## Forces

_Какие конкурирующие давления удерживает метод._

| Force | Tension |
|-------|---------|
| Нулевая инфраструктура (frontmatter + git mv вместо внешнего трекера) ↔ дисциплина регулярного review | Метод отказывается от Linear/GitHub Issues ради трёхзначного статуса в YAML, но цена — обязательный Week Close sweep: 14-дневный триггер и инвариант 28 дней заставляют тратить время недельного закрытия на каждый `open`-баг, иначе система деградирует обратно в 40+ файлов без состояния |
| Простота трёх статусов (open/resolved/invalid) ↔ выразительность полноценного lifecycle | Трёхзначная схема читается sweep-скриптом без парсинга и покрывает вердикты, но не различает «в работе», «ждёт подтверждения», «дубликат» — недостающая гранулярность выносится в WeekPlan-запись как явное решение, а не в расширение статусной модели |

## 2. Метод

### 2.1. Frontmatter bug-файла

Каждый файл `inbox/bugs/bug-YYYY-MM-DD-<тема>.md` получает frontmatter:

```yaml
---
status: open          # open | resolved | invalid
created: YYYY-MM-DD
resolved: ~           # заполняется при закрытии
---
```

**Статусы:**
| Статус | Значение |
|--------|---------|
| `open` | Баг активен, требует внимания |
| `resolved` | Исправлен, можно архивировать |
| `invalid` | Не воспроизводится или не является багом |

### 2.2. Week Close trigger

При Week Close: extension `week-close.before.bugs-sweep.md` выполняет:

1. `find inbox/bugs/ -name "*.md"` → читает frontmatter
2. Фильтрует `status: open` + `created` старше 14 дней
3. Для каждого — предлагает вердикт: resolved / invalid / перенести в WeekPlan
4. Resolved/invalid → `git mv inbox/bugs/<file> archive/bugs/YYYY-MM/<file>`

### 2.3. Инвариант

> Ни один `status: open` bug-файл не живёт в `inbox/bugs/` дольше 28 дней без явного решения (WeekPlan-запись или вердикт).

## 3. Применимость

Метод применим к любому `inbox/<domain>/` с открытыми дефектами, не имеющими внешней системы трекинга (Linear, GitHub Issues). Обобщение: заменить `bugs` на нужный тип артефакта, сохранив `open|resolved|invalid` трёхзначный статус и 14-дневный триггер.

## Bias-Annotation

_Куда систематически съезжает внимание практикующего._

| Bias | Direction of distortion |
|------|--------------------------|
| Статус в frontmatter читается как факт о баге | Практик видит `status: open` и считает баг живым, не проверяя воспроизводимость; вердикт `invalid` выставляется реже, чем следует, потому что требует повторной проверки, а не чтения метки — внимание на файле, а не на дефекте |
| Свежие баги затмевают стареющий хвост | Новые bug-файлы обрабатываются по горячим следам, а файлы возрастом 14–28 дней психологически «уже старые, значит отложенные»; именно на этот невидимый хвост нацелены 14-дневный триггер и инвариант 28 дней, и без Week Close sweep он систематически выпадает из внимания |

---

> 2026-08-01 — миграция на обогащённый формат карточки (Forces + Bias-Annotation), WP-448 Ф12 Батч 3 (суб-батч 5). Эталон формата: `SPF/pack-template/03-methods/_method-card-template.md`.
