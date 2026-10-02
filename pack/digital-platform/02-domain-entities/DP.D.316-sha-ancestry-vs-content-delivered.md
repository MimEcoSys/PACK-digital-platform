---
id: DP.D.316
name: "«Коммит доставлен в origin» ≠ «содержимое доставлено в origin» — проверка по родству SHA даёт ложное «не запушено», когда публикатор переписывает коммиты"
name_ru: "«Коммит доставлен в origin» ≠ «содержимое доставлено в origin»"
name_en: "Commit reached origin ≠ content reached origin — SHA-ancestry check false-negatives under a rewriting publisher"
summary: "merge-base --is-ancestor проверяет родство SHA и даёт «не запушено», если публикующий конвейер пересоздаёт коммит (изолированный worktree — DP.M.414/DP.FM.446). Тот же контент уже может быть в origin под другим SHA. Единица доставки в многосессионном чекауте с переписывающим публикатором — содержимое (blob/tree), не коммит; проверять доставку сравнением object-id файлов (hash-object / rev-parse), не родством SHA."
type: distinction
pack: PACK-digital-platform
domain: digital-platform
schema_version: 1
trust: observed
epistemic_stage: forming
source: "session-transcript 2026-09-12 (23:42-23:44, второй Quick Close сессии РП385)"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-09-15-inbox-check-5.md"
source_candidate: 3
source_capture: "DS-my-strategy/inbox/captures/2026-09.md:1650"
related:
  see_also: ["DP.FM.446", "DP.M.414", "DP.M.439"]
---

# DP.D.316 «Коммит доставлен в origin» ≠ «содержимое доставлено в origin»

## Критерий разграничения

«Проверяю ли я родство SHA (`merge-base --is-ancestor`, `git log`) или итоговое содержимое (`hash-object`, `rev-parse <ref>:<путь>`)?» — если публикующий конвейер когда-либо пересоздаёт коммиты (изолированный worktree, squash, rebase-публикация), родство SHA отвечает на другой вопрос, чем «долетел ли контент».

## Механизм ложного отрицания

`merge-base --is-ancestor <local-sha> origin/main` проверяет, является ли ЛОКАЛЬНЫЙ коммит предком origin. Если публикация прошла через изолированный worktree (DP.M.414 / DP.FM.446), origin получает коммит с тем же содержимым, но новым SHA — локальный коммит никогда не станет предком origin, хотя контент уже там. Наивная проверка по SHA-родству в этой ситуации навсегда отвечает «не запушено».

## Правильная проверка

Сравнение по object-id содержимого: `git hash-object <локальный файл>` = `git rev-parse origin/main:<путь>` для каждого файла. Совпадение → контент доставлен, независимо от расхождения SHA коммитов.

## Применимость

Любой многосессионный (multi-agent) чекаут, где публикующий конвейер переписывает коммиты (worktree-based publish, squash-merge, force-push-with-lease). Родство SHA годится только для линейной истории без переписывания.

Применение к удалению ветки: `git branch -d` проверяет слитость по предковости и не видит ветку, опубликованную через cherry-pick под новым SHA. Ветки изолированных запусков (`extractor/<режим>-<id>`) копились после каждого прогона: содержимое уже в origin, но коммиты имеют другие SHA, и `-d` отказывает. Лечение: при отказе `-d` сверять `git cherry <upstream> <ветка>`. Если нет строк с `+` (все патчи уже есть в upstream), ветку удалять; если есть `+` (неопубликованный коммит), ветку сохранить с предупреждением. Тест написан на настоящей функции, включая ветку с неопубликованным коммитом. Источник: git commit `2a14ef3` в FMT-exocortex-template (#976, WP-530 Ф72); кандидат 10/01.2#1 (`2026-10-01-inbox-check-2.md`).
## Связи

- DP.FM.446 (Смешанная публикация сессии даёт два SHA одного коммита) — механизм-причина этого различения
- DP.M.414 (fetch+cherry-pick+retry через общий шлюз) — публикующий конвейер, чьё поведение делает SHA-родство ненадёжным индикатором
- Источник: session-transcript 2026-09-12, РП385 Quick Close #2


