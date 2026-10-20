---
id: DP.FM.630
type: failure-mode
status: draft
created: "2026-10-16"
valid_from: "2026-10-15"
name: "«Компонент целиком не установлен» и «компонент установлен, но его файл повреждён» — разные failure modes, требующие разного ответа (тихий unresolved vs fail-closed)"
name_ru: "«Компонент целиком не установлен» и «компонент установлен, но его файл повреждён» — разные failure modes, требующие разного ответа (тихий unresolved vs fail-closed)"
name_en: "'Component entirely absent' and 'component installed but its file is corrupted' are different failure modes requiring different responses (silent unresolved vs fail-closed)"
summary: "artifactor.py путал опциональный компонент, которого штатно нет в данной установке (напр. author-only Pack, не поставляемый с шаблоном), с компонентом, который установлен, но чей registry-файл повреждён/нечитаем — оба случая одинаково падали в exit 3/CONFIG_ERROR. Разделены: компонент отсутствует целиком → тихий result_kind_resolution=unresolved; компонент присутствует, но реестр повреждён → fail-closed, как раньше."
pack: PACK-digital-platform
domain: digital-platform / pack-registry-resolution
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit 97a65121 в FMT-exocortex-template (scripts/artifactor.py); WP-7 Ф230, issue #1231"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:3927"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-16-inbox-check-2.md"
source_candidate: 2
related:
  see_also: [DP.FM.562, DP.SC.205, DP.FM.508]
tags: [fail-closed, fail-open, optional-component, registry-corruption, config-error, artifactor]
---

# DP.FM.630 — artifactor.py путал «компонента нет» с «компонент повреждён»

## Тезис и механизм ошибки

`scripts/artifactor.py` разрешает `result_kind` через реестр Pack'ов (`result-kinds-registry.yaml`). До фикса он одинаково реагировал на два разных по смыслу случая: (1) опциональный Pack целиком отсутствует в данной установке (например, author-only `PACK-digital-platform`, никогда не поставляемый с шаблоном — штатная ситуация) и (2) Pack установлен, но его registry-файл повреждён или нечитаем (порча конфигурации — ненормальная ситуация). Оба случая одинаково приводили к `exit 3`/`CONFIG_ERROR`.

## Границы

Применимо к любому резолверу/классификатору, читающему реестр опциональных компонентов: «компонента нет вообще» (ожидаемо для многих инсталляций) — не то же самое, что «компонент заявлен, но его описание нечитаемо» (повреждение данных). Смешение обоих в одну ветку обработки либо маскирует реальную порчу конфигурации под штатное отсутствие, либо превращает штатное отсутствие в громкую ошибку.

## Тест обнаружения

«Резолвер/верификатор при отсутствующем опциональном компоненте и при повреждённом файле этого же компонента возвращает один и тот же код ответа?» Да → риск воспроизведения DP.FM.630: нет разделения между «нормально, просто не установлено» и «установлено, но сломано».

## Противодействие

Разделить ветки обработки явно: компонент отсутствует целиком → тихий `unresolved`/degraded-результат без ошибки; компонент присутствует, но его данные не читаются/не парсятся → fail-closed с диагностируемым кодом ошибки, как раньше.

## Связи

- `DP.FM.562` — другая failure mode того же `scripts/artifactor.py` (классификатор ключевых слов путает изобретённую форму слова с реальным склонением), другой механизм, тот же инструмент.
- `DP.SC.205` — независимо созданный в тот же день verifier с принципом «fail-closed на любую неуверенность: отсутствующий реестр, повреждённый реестр... — разные внутренние причины, один и тот же внешний отказ»; эта карточка документирует более ранний, зеркальный баг (до того, как такое разделение стало осознанным принципом), где отсутствие и повреждение ошибочно давали один и тот же ответ без различения причины.
- `DP.FM.508` — смежная по словарю (fail-open/fail-closed), другой субстрат (session identity gate, не pack-реестр).

## Происхождение

git commit `97a65121` в FMT-exocortex-template, `scripts/artifactor.py`. WP-7 Ф230, issue #1231.
