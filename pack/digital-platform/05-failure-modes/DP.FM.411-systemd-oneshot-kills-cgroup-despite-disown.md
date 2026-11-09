---
id: DP.FM.411
name: "systemd Type=oneshot без KillMode= убивает всю cgroup сразу после ExecStart — disown от этого не защищает"
type: failure-mode
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-09-09
sources:
  - "git commit 4111e1a66 (DS-my-strategy, tsekh1-git-sync.sh, WP-503 Ф24)"
related:
  see_also: [DP.FM.410]
---

# DP.FM.411: systemd Type=oneshot убивает cgroup независимо от disown

## Симптом
Фоновый прогон получал SIGKILL за миллисекунды после выхода `ExecStart`, раньше, чем успевал сделать что-то полезное.

## Причина
`disown` защищает процесс только от сигнала завершения ШЕЛЛА, а не от systemd: юнит `Type=oneshot` без `KillMode=` считает себя завершённым сразу после выхода `ExecStart` и убивает ВСЮ cgroup юнита, включая disowned-потомков.

## Антипаттерн → Паттерн
- **Антипаттерн:** полагаться на `disown`/`&` как на способ пережить завершение родительского юнита `Type=oneshot`.
- **Паттерн:** `systemd-run --user --collect` — создаёт отдельный transient-юнит с своим запуском и остановкой ВНЕ cgroup вызывающего сервиса, так что деактивация родителя потомка не касается. Верифицировано вживую на реальном хосте.

## Тест обнаружения
«Фон запускается изнутри юнита `Type=oneshot` через `disown`/`&`, без `systemd-run`?» Да → под systemd (в отличие от голого shell) это не гарантирует переживание завершения родительского юнита; единственный надёжный способ — отдельный transient-юнит.

## Применимость
Любой фоновый запуск изнутри systemd-юнита `Type=oneshot`, рассчитывающий пережить завершение `ExecStart`.

## Связанные документы
- Источник: WP-503 Ф24, живой прогон на tsekh-1 07.09
