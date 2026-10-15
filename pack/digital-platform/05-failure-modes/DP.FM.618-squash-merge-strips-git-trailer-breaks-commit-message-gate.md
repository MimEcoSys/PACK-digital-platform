---
id: DP.FM.618
type: failure-mode
status: draft
created: "2026-10-13"
valid_from: "2026-10-13"
name: "Squash-слияние стирает git-trailer из тела коммита — гейт, читающий метаданные доставки из сообщения на main, перестаёт срабатывать"
name_ru: "Squash-слияние стирает git-trailer из тела коммита — гейт, читающий метаданные доставки из сообщения на main, перестаёт срабатывать"
name_en: "Squash merge strips the git trailer from the commit body — a gate reading delivery metadata from the main commit message silently stops firing"
summary: "Контракт доставки (категория релиза) хранился в git-trailer тела коммита. GitHub при squash-merge собирает новое сообщение коммита, trailer исчезает, проверка на main краснеет. Сбой каскадный и тихий: красный validate → не стартует зависимый release-workflow → не выходит автобамп релиза — при этом каждый отдельный PR выглядит «слитым»."
pack: PACK-digital-platform
domain: digital-platform / ci-release-pipeline
schema_version: 1
trust: observed
epistemic_stage: forming
source: "git commit 2b2925582 в MC-sessions (report.md/_outcome.md пир-сессии 2026-10-12-02-bot-signal-1183-1185; фикс — PR #1203 FMT-exocortex-template, слит обычным merge commit)"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:3094"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-13-inbox-check-3.md"
source_candidate: 4
related:
  see_also: ["DP.FM.550", "DP.D.316", "DP.D.329"]
tags: [git, squash-merge, trailer, ci-gate, release-pipeline, workflow_run]
---

# DP.FM.618 — Squash стирает git-trailer: гейт на main молчит, релиз не выходит

## Симптом

Релизный конвейер шаблона заблокирован на несколько часов (с 23:34 предыдущего дня): три подряд merge-коммита на `main` (включая собственный черновик) не проходят `check-delivery-route-label.sh`, поэтому `release.yml` (триггер — `workflow_run` успешного `validate`) не запускается. Каждый отдельный PR при этом выглядит «слитым».

## Механизм

1. Контракт доставки хранится в git-trailer тела коммита (`Delivery-Route: <category>`).
2. GitHub при squash-merge собирает НОВОЕ сообщение коммита для `main` — исходный trailer в это сообщение не переносится.
3. Проверка `check-delivery-route-label.sh` на `main` не находит trailer → красный `validate`.
4. `release.yml` триггерится успехом `validate` (`workflow_run`) → не стартует.
5. Недельный автобамп релиза не выходит, пользователи шаблона не получают релиз — при полностью «зелёном на вид» потоке отдельных PR.

Сбой каскадный и тихий: ни один из трёх красных индикаторов не указывает прямо на причину (потерю trailer при squash), обнаружен случайно, по ходу соседнего issue.

## Исправление (разблокировка, не системный фикс)

1. Слить свой PR обычным merge commit с trailer'ом в теле — первый зелёный прогон.
2. Вручную запустить пропущенный weekly-release (`workflow_dispatch`), одобрить GitHub-подтверждения запуска на бот-PR.
3. Пересоздать ветку автобампа (потребовалось трижды — гонка с параллельными сессиями, слившими 6 PR в main за то же время; разрешено прямой договорённостью о паузе merge).

Системный фикс (метка PR вместо trailer, запрет squash для таких PR и другие варианты) **сознательно оставлен пилоту как решение о политике слияния** — не реализован в этой сессии.

## Тест обнаружения

«Гейт/workflow читает метаданные из сообщения коммита (git-trailer), а репозиторий допускает squash-merge по умолчанию?» Да → риск DP.FM.618: метаданные нужно либо хранить там, что squash не переписывает (метка PR, файл в дереве, проверка на уровне PR), либо squash запретить для таких PR.

## Границы

Карточка о метаданных доставки в теле коммита конкретно. Не о потере СОДЕРЖИМОГО при squash стопки PR — это другой механизм (`DP.FM.550`): там терялось содержимое зависимого PR, здесь — метаданные независимого гейта при обычном (не стопочном) squash-merge.

## Связанные документы

- `DP.FM.550` — squash-мердж базового PR осиротил зависимый PR стопки: смежный, но другой механизм (контент vs метаданные), не дубль.
- `DP.D.316`, `DP.D.329` — «коммит доставлен» / «запушено в ветку» ≠ «содержимое доставлено»: та же семья различений «индикатор говорит одно, содержимое/метаданные — другое».
- Источник: WP-7 (issues #1183/#1185 FMT-exocortex-template), PR #1203, PR #1214 (auto-bump), релиз v0.41.8.
