---
id: DP.FM.604
type: failure-mode
status: draft
created: "2026-10-12"
valid_from: "2026-10-11"
name: "`git commit -- path` в `--only`-режиме берёт содержимое ВСЕХ изменённых tracked-файлов под путём независимо от стейджа — периодический канал публикации требует явного exclude подпути"
name_ru: "«git commit -- path» в «--only»-режиме берёт содержимое ВСЕХ изменённых tracked-файлов под путём независимо от стейджа — периодический канал публикации требует явного exclude подпути"
name_en: "`git commit -- path` in `--only` mode takes the working-tree content of every modified tracked file under the path, staged or not — a periodic publish channel needs an explicit exclude"
summary: "Периодический путь публикации журнала предполагал, что публикует только то, что сам поставил в стейдж. `git commit -- <path>` в режиме `--only` подхватывает содержимое любого модифицированного tracked-файла под этим путём независимо от того, кто и когда его застейджил — непубликуемые изменения `plan/` утекали в коммит. Фикс — явный `:(exclude)` в pathspec плюс громкая остановка при обнаружении непубликованного коммита с файлом плана."
pack: PACK-digital-platform
domain: digital-platform / git-tooling
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit 24386d2cb в DS-my-strategy; feed:git-diff 2026-10-11"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:2580"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-12-inbox-check.md"
source_candidate: 1
related:
  see_also: ["DP.FM.539", "DP.D.319"]
tags: [git, pathspec, commit-only, partial-publish, path-exclude]
---

# DP.FM.604 — `git commit --only -- path` коммитит весь working tree под путём, не только застейдженное

## Симптом

Периодический путь публикации журнала (`machine/ledger`) предполагал, что коммитит только то, что сам поставил в стейдж через `stage_ledger_paths`. На деле `git commit -- <path>` в режиме `--only` подхватывает working-tree содержимое ЛЮБОГО модифицированного tracked-файла под этим путём независимо от того, кто и когда его застейджил — из-за этого непубликуемые изменения `plan/` утекали в коммит вместе с журналом.

## Причина

`--only` ограничивает коммит путями из pathspec, но не ограничивает его СОДЕРЖИМОЕ стейджем: для каждого файла, попавшего под pathspec, в коммит уходит текущее working-tree содержимое, а не то, что явно застейджено. Код, предполагавший «коммичу только то, что сам застейджил», не учёл это и пропускал любые параллельно модифицированные файлы под тем же путём.

## Исправление

Явный `:(exclude)` для `plan/` в pathspec периодического пути публикации, плюс громкая остановка (не silent skip), если обнаружен непубликованный коммит с файлом плана — чтобы утечка такого рода не прошла незаметно повторно.

## Тест обнаружения

«Код вызывает `git commit --only -- <path>`, предполагая, что публикует только явно застейдженное через отдельный шаг стейджинга?» Да → проверить, не делит ли кто-то ещё рабочее дерево под тем же путём параллельно — если да, воспроизведена эта FM без exclude-pathspec.

## Связанные документы

- `DP.FM.539` (`git status --porcelain` toplevel-relative ≠ pathspec cwd-relative) — смежная тема «pathspec», другой аспект: там рассогласование систем отсчёта путей, здесь — рассогласование «что в pathspec» и «что реально стейджено».
- `DP.D.319` (pathspec scope и patch-id — не доказательство происхождения) — тоже про границы pathspec, но в контексте доказательства происхождения коммита, не публикационной утечки.

## Источник

git commit `24386d2cb` в DS-my-strategy. Связь: WP-561 Ф33.
