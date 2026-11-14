---
id: DP.FM.757
name: "grep -c . || echo 0 на пустом вводе даёт двойной вывод \"0\\n0\"; stat различается на macOS/Linux"
type: failure-mode
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_bash_grep_count_empty_input.md (ke-queue-stats, 14-16.06; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [DP.FM.759, DP.FM.767, PACK-digital-platform]
---

# DP.FM.757: grep -c пустого ввода и кроссплатформенный stat

## Симптом 1
`COUNT=$(echo "$VAR" | grep -c . || echo 0)`: на пустой строке grep печатает `0`, выходит с кодом 1 → `|| echo 0` дописывает второй `0` → `COUNT="0\n0"` → `[ "$COUNT" -eq 0 ]` падает «integer expression expected».

## Паттерн
```bash
if [ -z "$VAR" ]; then COUNT=0; else COUNT=$(echo "$VAR" | grep -c .); fi
```
`[ -z ]` ДО grep, не `|| echo 0`.

## Симптом 2 (тот же файл)
`stat -f "%m"` (BSD/macOS) vs `stat -c "%Y"` (Linux) — dispatch по `uname -s` обязателен.

## Тест обнаружения
Пустой ввод в любой счётчик с fallback'ом; запуск скрипта на обеих платформах.
