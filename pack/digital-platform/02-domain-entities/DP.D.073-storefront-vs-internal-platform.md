---
id: DP.D.073
name: "Внешняя витрина ≠ Внутренняя часть платформы (по ритму изменений + аудитории, не по технослою)"
type: distinction
status: active
valid_from: 2026-05-18
source: "session-transcript 2026-05-18; DS-my-strategy 4be27130 (WP-336: добавить ось «внешняя витрина / внутренняя часть»); DP.CONCEPT.002 §1"
---

# DP.D.073: Внешняя витрина ≠ Внутренняя часть платформы

> **Не путать с frontend/backend split.** Frontend/backend режет систему по **технологическому слою** (UI vs API vs DB). Витрина/внутренняя часть режет по **ритму изменений + аудитории**.

## Различение

| Аспект | Внешняя витрина | Внутренняя часть |
|--------|------------------|-------------------|
| **Аудитория** | Анонимный посетитель + community-participant | Authenticated learner / agent |
| **Cadence изменений** | Маркетинг-cadence (пара раз в неделю) | Product-cadence (каждый коммит) |
| **Стек-оптимизация** | SEO / статика / incremental adoption | Реактивный / stateful / интеграция с агентами |
| **Содержимое** | Лендинг, public docs, community, status-страница | LMS, табло, IWE, AI-агенты |
| **Acquisition** | Community / SEO / контент | Onboarding после authentication |

## Тест применимости

«Есть ли два разных пользовательских режима с разной cadence изменений и разной аудитории?» Да → оси витрина/внутренняя часть. Нет → достаточно классического frontend/backend.

## Архитектурные развилки, которые порождает различение

1. **Repo-стратегия:** monorepo vs два отдельных фронтенда.
2. **Design-tokens:** общие vs отдельные системы.
3. **Component library:** shared vs дублирование (с разной cadence).
4. **Preservation контекста при auth-переходе:** анонимный → authenticated (как переносить track-record интереса).

## Контр-pattern

«Единое приложение, public-страницы прячутся за authentication» — оптимизирует под product-cadence, но ломает SEO + теряет community-acquisition. Анти-паттерн для B2C-платформ с community-слоем.

## Не путать с

- **public-API ≠ private-API split.** Там критерий «кто может вызвать», здесь — «какой ритм изменений и какой пользовательский режим».
- **frontend ≠ backend (DP.D.030 deployment-topology).** Технослой, не аудитория.
- **authenticated ≠ unauthenticated (DP.D.034 access-control-model).** Это право доступа, а не decomposition платформы.

## Применимость

- B2C-платформы с community-слоем (IWE, Vercel-style dev-platform, GitHub-style developer-tools)
- Edu-tech с public-каталогом и authenticated-LMS
- SaaS с marketing-site + product
- WP-336 (платформенная декомпозиция Aisystant)
