---
id: DP.FM.490
type: failure-mode
status: active
created: "2026-09-22"
valid_from: "2026-09-22"
name: "Построчный merge=union молча перемешивает строки соседних многострочных записей append-only журнала"
name_ru: "Построчный merge=union молча перемешивает строки соседних многострочных записей append-only журнала"
name_en: "Line-based merge=union silently interleaves neighboring multi-line append-only records"
summary: "Построчный merge=union возвращает успешное слияние, но разрушает границы многострочных YAML-событий при параллельной записи или cherry-pick разошедшейся истории."
pack: PACK-digital-platform
domain: digital-platform / multi-agent-git-coordination
schema_version: 1
trust: medium
epistemic_stage: observed
source: "git commits b50f2e069, 619185d97 и f1bfed92b в DS-my-strategy"
source_capture: "DS-my-strategy/inbox/captures/2026-09.md:2891,2982"
related:
  see_also: [DP.FM.409, DP.FM.186, DP.FM.233]
tags: [git, merge-driver, append-only, ledger, multi-agent-coordination]
---

# DP.FM.490 — merge=union рвёт многострочные записи журнала

## Механизм ошибки

`merge=union` объединяет строки, а не логические записи. Когда два писателя дописывают многострочные YAML-события или commit переносится поверх параллельно добавленных событий, одинаковые ключи и отступы становятся якорями слияния. Git возвращает успех без конфликта, но строки соседних событий перемешиваются. Механизм воспроизведён в трёх реальных инцидентах.

## Диагностический принцип

Построчное union-слияние безопасно только там, где одна логическая запись занимает одну строку. Оно устраняет не только конфликт, но и сигнал о повреждении многострочной записи.

## Границы

File-lock одного хоста не защищает от слияния историй разных хостов. Безопасные варианты: однострочный формат записи или merge-driver, понимающий границы записей. Название формата само по себе не гарантия: многострочный JSON имеет ту же проблему, а JSONL безопасен только при одной записи на строку.

## Проверка

«Есть ли `merge=union` на append-only файле с многострочными записями?» Да — параллельная история может слиться без конфликта и с повреждением данных.

## Происхождение

Источники: WP-170 follow-up и WP-484 Ф157.
