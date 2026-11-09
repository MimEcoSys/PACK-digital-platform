---
id: DP.FM.585
type: failure-mode
status: draft
created: "2026-10-10"
valid_from: "2026-10-10"
name: "Append-only автомат без декларации держит дерево грязным и блокирует ff-only синк"
name_ru: "Append-only автомат без декларации держит дерево грязным и блокирует ff-only синк"
name_en: "Undeclared append-only automaton keeps working tree dirty and blocks ff-only sync"
summary: "Автомат, который только дописывает в свои файлы без коммита, постоянно держит рабочее дерево грязным; fail-closed ff-only merge из-за этого никогда не проходит — на всём дереве, каждый цикл."
pack: PACK-digital-platform
domain: digital-platform / multi-agent-git-coordination
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit a9b1658 в iwe-local-config (WP-538, peer-session 2026-10-09-21-wp538-canon-refresh-skip-worktree)"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-10-inbox-check-6.md"
source_candidate: 1
related:
  see_also: [DP.M.515]
tags: [append-only, dirty-worktree, ff-only, sync, canon-refresh, multi-agent]
---

# DP.FM.585 — Append-only автомат без декларации блокирует ff-only синк всего дерева

## Тезис и механизм ошибки

Автомат, чья задача — только дописывать в свои файлы (лог, очередь, счётчик), делает это без коммита. В результате рабочее дерево остаётся грязным на каждом цикле. Скрипт синхронизации `canon-refresh.sh` работает в режиме `--ff-only`; при любом грязном дереве он отказывает. Сбой затрагивает всё дерево, а не только файлы автомата — каждый агент теряет sync до очистки.

Три дня 373 коммита дрейфа — потому что никто явно не задекларировал append-only пути.

## Признаки

- Скрипт синхронизации стабильно падает с «dirty working tree» на каждом цикле.
- `git status` показывает одни и те же файлы грязными при любом запуске — это файлы автоматически обновляемых очередей/логов.
- Автоматы-авторы этих файлов работают корректно и не считают поведение проблемой.

## Митигация

1. Явно задекларировать append-only пути (в конфигурации агента или скрипте синхронизации).
2. Коммитить такие пути только если байты на диске — строгий суперсет committed HEAD (старое содержимое байт в байт, только хвост добавлен). Любое иное изменение не трогать.
3. Скрипт синхронизации должен опционально пропускать задекларированные append-only пути (skip-worktree или явный allowlist) перед проверкой чистоты.

## Тест обнаружения

«Есть ли в системе автоматы, которые пишут в файлы в рабочем дереве и не коммитят?» Да → задекларированы ли их пути явно? Нет → потенциальный блокировщик синка.

## Связи

- `DP.M.515` — метод, явно декларирующий режим писателя (append-only vs транзакционный) в контракте автоматизации; этот FM — конкретное проявление отсутствия такой декларации на синхронизации git-дерева.

## Происхождение

git commit `a9b1658` в iwe-local-config (WP-538, peer-session `2026-10-09-21-wp538-canon-refresh-skip-worktree`). Захват: `DS-my-strategy/inbox/captures/2026-10.md`; extraction report `2026-10-10-inbox-check-6.md`, кандидат #1.
