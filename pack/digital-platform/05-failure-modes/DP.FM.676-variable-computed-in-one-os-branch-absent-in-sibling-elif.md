---
id: DP.FM.676
name: Переменная, вычисленная в одной ветке OS-условия, отсутствует в соседней elif-ветке
type: failure-mode
status: draft
trust: observed
epistemic_stage: forming
pack: PACK-digital-platform
domain: digital-platform
created: 2026-10-24
valid_from: 2026-10-22
source: peer-session WP-7 Ф244 (issue #1303 FMT-exocortex-template, PR #1312)
source_capture: DS-my-strategy/inbox/captures/2026-10.md:6433
extraction_report: DS-my-strategy/inbox/extraction-reports/2026-10-24-inbox-check.md
source_candidate: 4
name_ru: Переменная из одной ветки OS-условия отсутствует в соседней ветке
name_en: Variable computed in one OS branch is absent in the sibling elif branch
schema_version: 1
related:
  see_also:
  - DP.FM.664
summary: 'Переменные IWE_TEMPLATE_DIR и IWE_SCRIPTS вычислялись только в Darwin-ветке; Linux шёл отдельным elif. Копирование их использования в Linux-ветку подставило бы пустые значения.'
---

# DP.FM.676 — Переменная из одной ветки OS-условия отсутствует в соседней ветке

## Исторический отказ

При исправлении issue #1303 (systemd-юнит без Environment=) исходная гипотеза гласила, что пять переменных уже вычислены и доступны обеим веткам. Проверка кода показала: IWE_TEMPLATE_DIR и IWE_SCRIPTS вычисляются только внутри Darwin-ветки, Linux идёт отдельным `elif`, и этих переменных там нет. Простое копирование использования дало бы пустые значения.

## Противодействие

При переносе кода между параллельными ветками условия проверять место вычисления каждой переменной, а не предполагать её доступность. Исправление — продублировать вычисление в обеих ветках. Защита от повторения: регресс-тест, запускающий обе ветки.

## Граница

DP.FM.664 — отсутствие платформо-специфичного инструмента на другой платформе; здесь — область видимости переменной между ветками одного условия.
