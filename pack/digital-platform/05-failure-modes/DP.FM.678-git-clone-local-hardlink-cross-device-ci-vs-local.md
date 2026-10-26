---
id: DP.FM.678
type: failure-mode
status: draft
created: "2026-10-24"
valid_from: "2026-10-23"
name: "Тестовый `git clone --local` в tmp терпит «Invalid cross-device link» на CI-раннерах при иной файловой системе, чем локально"
name_ru: "Тестовый `git clone --local` в tmp терпит «Invalid cross-device link» на CI-раннерах при иной файловой системе, чем локально"
name_en: "A test's `git clone --local` into tmp hits 'Invalid cross-device link' on CI runners when tmp is a different filesystem than the repo"
summary: "Тест клонирует репозиторий в scratch-каталог через `git clone --local`, который по умолчанию пытается делать жёсткие ссылки на объекты. Локально /tmp и репозиторий обычно на одной файловой системе — тест зелёный. На CI-раннерах (GitHub Actions) /tmp часто на другой файловой системе — жёсткая ссылка невозможна, клон падает с «Invalid cross-device link». Нужен флаг `--no-hardlinks`, форсирующий копирование объектов."
pack: PACK-digital-platform
domain: digital-platform / CI testing
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit 284f328c в FMT-exocortex-template (scripts/tests/test_generate_manifest_registers_setup_exclusions.sh)"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:6624"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-24-inbox-check-5.md"
source_candidate: 4
related:
  see_also: ["DP.FM.509"]
tags: [git, ci, test-fixture, cross-device, hardlinks]
---

# DP.FM.678 — `git clone --local` без `--no-hardlinks` падает на CI при другой файловой системе

## Тезис и механизм ошибки

Тест-генератор манифеста клонирует репозиторий в scratch-каталог настоящим клоном (не `git archive`, который стирает `.git` и тихо даёт пустой манифест). `git clone --local` по умолчанию пытается создать объекты как жёсткие ссылки на исходный репозиторий — быстро, но требует одной файловой системы. На раннерах GitHub Actions временный каталог клона и репозиторий оказались на разных файловых системах, жёсткая ссылка через границу невозможна, и клон падает с «Invalid cross-device link». Локально (одна файловая система) тест зелёный — дефект не воспроизводится без CI-среды.

## Диагностический принцип

«Зелёный локально» ≠ «зелёный на CI» для любого теста, выполняющего `git clone --local` в tmp: граница файловой системы между tmp и репозиторием — не локальный инвариант.

## Исправление

Флаг `--no-hardlinks` форсирует копирование объектов вместо жёстких ссылок. Тот же флаг уже стоял в соседнем тесте (`test_issue_1006_yml_author_scan.sh`) — класс дефекта был решён в одном месте и не распространён на остальные тесты с аналогичным клоном.

## Проверка

«Делает ли тест `git clone --local` (прямо или через вызываемый скрипт) в каталог, не гарантированно на той же файловой системе, что репозиторий?» Да и без `--no-hardlinks` → риск DP.FM.678 на CI. При починке одного такого падения — искать тот же вызов по всему набору тестов, не только в упавшем файле.

## Связи

- `DP.FM.509` — смежная тема (git test fixture зависит от окружения хоста), другой механизм: там наследуется default branch/identity хоста, здесь — граница файловой системы при клонировании.
- WP-529 (FMT PR #1317), peer-session 2026-10-23-06-wp529-continue.
