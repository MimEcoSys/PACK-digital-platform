---
id: DP.M.515
name: "Append-only автомат в git-дереве: явная декларация mode=append в automation-contract и flush только при байтовом суперсете HEAD"
name_ru: "Append-only автомат в git-дереве: явная декларация mode=append в automation-contract и flush только при байтовом суперсете HEAD"
name_en: "Append-only automation in a git tree: declare mode=append in automation-contract and flush only when disk bytes are a strict byte-superset of HEAD"
type: method
pack: PACK-digital-platform
domain: digital-platform / git-automation
trust: medium
epistemic_stage: forming
status: draft
created: "2026-10-11"
valid_from: "2026-10-11"
source: "git commit a9b1658 в iwe-local-config (WP-538 Ф15); peer-session 2026-10-09-21-wp538-canon-refresh-skip-worktree"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:2342"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-11-inbox-check.md"
source_candidate: 5
related:
  see_also: ["DP.M.481", "DP.FM.585"]
tags: [git, append-only, automation-contract, ff-merge, canon-refresh, launchd]
schema_version: 1
summary: "Append-only писатели в git-дереве создают «вечную грязь» (uncommitted changes на каждом тике), блокирующую ff-only merge canon-refresh.sh для всего дерева. Решение: явная колонка mode='append' в automation-contract.conf; try_flush_append_only() коммитит задекларированный путь только если байты на диске — точный байтовый суперсет HEAD. Любая другая правка остаётся нетронутой."
---

# DP.M.515 — Append-only автомат в git-дереве: декларация и flush-инвариант

## Проблема

Автомат, который дописывает в свой файл на каждом тике, но никогда не коммитит, создаёт постоянную незакоммиченную правку в рабочем дереве. `canon-refresh.sh` с ff-only merge останавливается при любой грязи в дереве. Один незадекларированный append-only автомат блокирует синхронизацию **всего** дерева на каждом цикле.

На tsekh-1: 3 суток блокировки, 373 коммита дрейфа до обнаружения.

## IPO-паттерн

| Элемент | Описание |
|---|---|
| Входы | Автомат, пишущий в свой файл на каждом тике; automation-contract.conf без описания режима; canon-refresh.sh с ff-only merge |
| Обработка | Добавить колонку `mode="append"` в automation-contract.conf для каждого append-only автомата; реализовать `try_flush_append_only()`, которая проверяет байтовый суперсет перед коммитом |
| Выходы | Рабочее дерево чистое после каждого тика; ff-only merge проходит; чужие правки не затронуты |

## Flush-инвариант

`try_flush_append_only()` коммитит задекларированный путь **только если** байты на диске — точный байтовый суперсет HEAD (старые байты сохранены побайтово). Если файл содержит правки, не являющиеся чистым append к HEAD — функция не коммитит, сигнализирует для ручной проверки.

Этот инвариант гарантирует: flush никогда не перезатирает правки другого агента или пользователя.

## Когда применять

Любой автомат в общем git-дереве, который:
- пишет только в один файл
- никогда не читает чужие файлы
- добавляет строки (журнал, лог, счётчик), не редактирует

Такой автомат обязан быть задекларирован с `mode=append` в automation-contract и использовать flush с байтовым суперсетом.

## Связи

- `DP.FM.585` (append-only автомат без декларации блокирует ff-only синк дерева) — тот же прецедент и источник (WP-538, peer-session 2026-10-09-21-wp538-canon-refresh-skip-worktree): там — failure mode (что произошло без декларации), здесь — метод (как задекларировать и безопасно сбрасывать).
