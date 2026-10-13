---
id: DP.FM.577
type: failure-mode
status: draft
created: "2026-10-09"
valid_from: "2026-10-09"
name_ru: "`--isolate` пишет в `info/exclude`, не создавая каталог `info/` — падает на свежем git-дереве без шаблона, блокировка доставки маскируется дедупом эскалации"
name_en: "`--isolate` writes to `info/exclude` without creating the `info/` directory first — fails on a fresh git tree without a template; delivery block masked by escalation dedup"
summary: "`session-guard.sh --isolate` писал в `$GIT_DIR/info/exclude`, предполагая, что каталог `info/` уже существует. На свежем git-дереве без шаблона (plain `git init`) это не так — запись падает с «No such file or directory» и молча блокирует всю операцию `--isolate`. Баг маскировался дедупом эскалации: минимум 14 тиков синхронизации подряд без видимого алерта пилоту (с 07.10 12:00), пока не найден и подтверждён независимо Kimi, Codex и холодным ревью Fable."
pack: PACK-digital-platform
domain: digital-platform / git-infrastructure
schema_version: 1
trust: observed
epistemic_stage: forming
related:
  see_also: [DP.METHOD.259]
source: "git commit dde15c8 в iwe-local-config"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:2007"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-09-inbox-check-4.md"
source_candidate: 4
tags: [session-guard, isolate, git-worktree, info-exclude, escalation-dedup, silent-failure]
---

# DP.FM.577 — `--isolate` падает на `info/exclude` на свежем git-дереве без каталога `info/`

## Тезис и механизм ошибки

`session-guard.sh --isolate` пишет в `$GIT_DIR/info/exclude`, не проверяя и не создавая каталог `info/` заранее. На git-дереве, созданном простым `git init` без шаблона, каталог `info/` отсутствует — запись падает («No such file or directory») и прерывает всю операцию `--isolate`, а не только шаг записи exclude-файла.

Отказ не дошёл до пилота как явный алерт: дедуп эскалации поглощал повторяющийся сбой синхронизации (`sync-extensions-auto`) минимум 14 тиков подряд с 07.10 12:00, трактуя повторы одного и того же отказа как уже-известный шум, а не как хронический блокер доставки.

## Диагностический принцип

Запись в файл внутри подкаталога git-метаданных (`info/exclude`, и аналогично любой `$GIT_DIR/<sub>/<file>`) не должна предполагать существование родительского каталога — создание git-дерева не гарантирует полный набор поддиректорий `.git/info/` на всех путях создания (plain `init` vs шаблонный `init` vs `clone`). Фикс — `mkdir -p` перед записью.

Отдельно: дедуп повторяющихся алертов эскалации должен иметь верхнюю границу по числу тиков/времени, после которой повтор того же сигнала эскалируется как хронический, а не продолжает подавляться бесконечно.

## Проверка

«Код пишет файл внутри поддиректории `.git/` (или аналогичного служебного пути), не создав эту поддиректорию явно перед записью?» Да → риск падения на любом пути создания дерева, который не гарантирует эту поддиректорию (plain `git init` — главный кандидат).

## Связи

- **DP.METHOD.259** (info/exclude на конкретном worktree разводит конфликтующие ожидания git-tracking) — тот же файл (`info/exclude`) и тот же код-путь (`session-guard.sh --isolate` / `git worktree add`), но другая, независимая конкретная проблема: там — конфликт двух инвариантов tracking при наличии каталога, здесь — отсутствие самого каталога `info/`. Не дубликат.
- Смежная, пока не применённая находка того же кода (R15 — сверить при apply): «git worktree add падает на info/exclude во вложенных temp-каталогах на macOS» (кандидат #2 отчёта `2026-10-08-inbox-check-3.md`, source: commit a6092842 в DS-my-strategy). Другой конкретный триггер (вложенные temp-каталоги в тестовых фикстурах, намеренно не фиксился — «реальную боевую работу не задевает») и другое следствие (блокирует только тестовые прогоны, не продуктовую доставку). Эта карточка (DP.FM.577), напротив, описывает боевой impact на доставку (14 тиков `sync-extensions-auto`). Разные root cause одного кода — не слияние, но при совместном apply сверить итоговую версию `session-guard.sh`, чтобы один фикс не маскировал необходимость другого.

## Происхождение

git commit `dde15c8` в iwe-local-config. WP-484, WP-7 Ф209.
