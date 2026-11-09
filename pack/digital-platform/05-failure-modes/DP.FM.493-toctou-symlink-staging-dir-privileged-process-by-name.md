---
id: DP.FM.493
type: failure-mode
status: active
created: "2026-09-22"
valid_from: "2026-09-22"
name: "TOCTOU через символьную ссылку или именованный канал в записываемой staging-папке перед привилегированным процессом"
name_ru: "TOCTOU через символьную ссылку или именованный канал в записываемой staging-папке перед привилегированным процессом"
name_en: "TOCTOU through a symlink or FIFO in writable staging before a privileged process"
summary: "Менее доверенный писатель подменяет тип записи в staging; root-процесс позже следует имени и получает произвольную запись, выполнение или зависание."
pack: PACK-digital-platform
domain: digital-platform / privilege-escalation-installers
schema_version: 1
trust: medium
epistemic_stage: observed
source: "git commit ff5874445 в DS-my-strategy (WP-544)"
source_capture: "DS-my-strategy/inbox/captures/2026-09.md:2959"
related:
  see_also: [DP.M.467, DP.M.240]
tags: [security, toctou, symlink, privilege-escalation, installer, root]
---

# DP.FM.493 — TOCTOU через симлинк или FIFO в staging

## Механизм ошибки

Менее привилегированный процесс готовит дерево, root его копирует и затем действует по именам файлов. Подложенный symlink или FIFO при следовании привилегированным инструментом даёт запись или выполнение от root либо вечное ожидание. Проверка контрольной суммы содержимого не обнаруживает подмену типа файловой записи.

## Диагностический принцип

Перед повышением привилегий нужно проверить не только байты, но и тип каждой записи: запретить symlink, FIFO и device. Последующие операции по имени должны выполняться уже в закрытой root-owned копии, недоступной прежнему писателю.

## Проверка

«Проверяется ли тип каждой записи до эскалации привилегий?» Нет — staging остаётся каналом TOCTOU.

## Границы и связи

Применимо к установщикам и копировщикам с `sudo`. `DP.M.467` защищает уже установленную цепочку запуска; этот отказ относится к стадии подготовки и установки.

## Происхождение

Источник: три независимых холодных ревью WP-544, git commit `ff5874445`.
