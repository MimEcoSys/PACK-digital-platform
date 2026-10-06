---
id: DP.FM.539
type: failure-mode
status: draft
created: "2026-10-06"
valid_from: "2026-10-05"
name: "`git status --porcelain` отдаёт пути относительно toplevel, а переданные дальше pathspec — относительно cwd: без `cd` на toplevel проверка по пути молча промахивается"
name_ru: "`git status --porcelain` отдаёт пути относительно toplevel, а переданные дальше pathspec — относительно cwd: без `cd` на toplevel проверка по пути молча промахивается"
name_en: "git status --porcelain paths are toplevel-relative while pathspecs are cwd-relative: without cd to toplevel, per-path checks silently miss"
summary: "`git status --porcelain` всегда печатает пути относительно корня репозитория; если скрипт вызван с поддиректорией как `<repo-path>` и передаёт эти же строки дальше как pathspec для `git restore`/`git diff`, пути интерпретируются относительно cwd — несовпадение корней молча проваливает каждую последующую проверку «путь за путём». Фикс: `cd` на `git rev-parse --show-toplevel` сразу после входа в репозиторий, до разбора статуса."
pack: PACK-digital-platform
domain: digital-platform / git-tooling
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit 9482de01313685b9ac3b70b8735efb2306aa3372 в iwe-local-config; feed:git-diff 2026-10-05"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:834"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-06-inbox-check.md"
source_candidate: 1
related:
  see_also: ["DP.D.319", "DP.D.302"]
tags: [git, porcelain, pathspec, toplevel, cwd, path-mismatch]
---

# DP.FM.539 — `git status --porcelain` toplevel-relative ≠ pathspec cwd-relative

## Симптом

Скрипт восстановления per-path зеркал (canon-refresh recovery) вызывался с поддиректорией репозитория как `<repo-path>`. Статус парсился через `git status --porcelain`, пути из вывода передавались дальше как pathspec в `git restore`/`git diff`. `git status --porcelain` всегда печатает пути относительно TOPLEVEL репозитория независимо от cwd вызова; pathspec, переданный `git restore`/`git diff` без указания корня, интерпретируется относительно CWD. Когда cwd — поддиректория, а не toplevel, каждая проверка «путь за путём» молча не находит совпадения — не ошибка, а тихий no-op.

## Причина

Два независимых соглашения git про один и тот же путь: `--porcelain` выход — контракт «от корня репозитория», pathspec-аргумент — контракт «от текущей директории», если не указано иное. Скрипт, который читает одно и передаёт в другое без явного выравнивания базы, работает корректно только пока вызван из toplevel — и расходится тихо, без ошибки, именно когда вызван из поддиректории.

## Исправление

`cd "$(git rev-parse --show-toplevel)"` сразу после входа в репозиторий, до разбора `git status --porcelain` и до использования путей как pathspec.

## Тест обнаружения

«Скрипт парсит `git status --porcelain` и использует эти строки как pathspec ниже по течению (restore/diff/checkout)? Скрипт может быть вызван с поддиректорией репозитория как входным путём?» Да и да → риск воспроизведён, если явного `cd` на toplevel (или префиксации путей) нет.

## Связанные документы

- `DP.D.319` (pathspec scope и patch-id — не доказательство происхождения): смежная тема «pathspec», другой аспект — там pathspec как граница коммита, здесь — рассогласование систем отсчёта путей между porcelain-выводом и pathspec-входом.
- `DP.D.302` (NFC vs NFD path form): другой класс несовпадения представления одного и того же пути (кодировка имени, не база отсчёта), тот же общий урок «путь ≠ путь, если сравнивать побайтово без нормализации к общему контракту».

## Источник

git commit `9482de01313685b9ac3b70b8735efb2306aa3372` в iwe-local-config. Связь: WP-538 Ф5а.
