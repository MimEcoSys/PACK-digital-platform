---
id: DP.FM.758
name: "cmd | head -1 || echo default не срабатывает на пустом пайплайне — head выходит с 0; fallback только через явную проверку -z"
type: failure-mode
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_bash_pipeline_fallback.md (WP-337-З, 23.05; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [DP.FM.757, PACK-digital-platform]
---

# DP.FM.758: pipeline-fallback через || не стреляет

## Симптом
`$(find ... | sort -n | head -1 || echo 10000)` на пустой выдаче find даёт пустую строку, не 10000 — арифметика ломается.

## Причина
`||` срабатывает только при ненулевом exit code левой части; `head -1` на пустом stdin завершается с 0.

## Антипаттерн → Паттерн
- **Антипаттерн:** fallback через `||` внутри подстановки команды с пайпом.
- **Паттерн:** присвоить результат, затем `[[ -z "$VAR" ]] && VAR=<default>` отдельным оператором.

## Тест обнаружения
Любое pipeline-вычисление числа с fallback: прогон с гарантированно пустой выдачей первой команды.
