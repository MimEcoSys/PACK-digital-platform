---
id: DP.M.500
type: method
status: draft
created: "2026-10-06"
valid_from: "2026-10-05"
name_ru: "Переиспользовать существующий content-based классификатор для нового класса файлов вместо параллельной git-dirty-state эвристики; никогда не делать abort всего прогона на неоднозначности"
name_en: "Reuse an existing content-based classifier for a new file class instead of a parallel git-dirty-state heuristic; never abort the whole run on ambiguity"
summary: "Пир-сессия (Claude+Kimi+Codex, WP-592) нашла в FMT-exocortex-template, что для нового класса файлов (governance-скрипты update.sh) не нужно строить отдельную git-state-based эвристику — достаточно распространить уже работающий content-based классификатор (classify-workspace-copy.sh + .memory-deployed.tsv), который обслуживает memory/*.md|.yaml|.yml в том же файле. Этот механизм также не прерывает весь прогон на неоднозначности — только помечает каждый файл статусом (uptodate/replaced/kept/unknown)."
pack: PACK-digital-platform
domain: digital-platform / governance-script-policy
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit a35759a1 в FMT-exocortex-template (WP-485 Ф17)"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:1034"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-06-inbox-check-5.md"
source_candidate: 1
related:
  see_also: ["DP.M.481", "DP.M.470"]
tags: [governance-script, content-based-classifier, update.sh, ambiguity, no-abort]
---

# DP.M.500 — Переиспользовать content-based классификатор вместо параллельной git-state эвристики

## Проблема

Новый класс файлов (governance-скрипты `update.sh`) сталкивается с той же задачей «можно ли это безопасно перезаписать», которую уже решает существующий content-based механизм для другого класса файлов (`memory/*.md|.yaml|.yml`) в том же файле. Соблазн — построить вторую, git-dirty-state-based эвристику рядом, специально для нового класса.

## Метод

1. **Проверить, есть ли уже работающий классификатор для той же задачи** («можно ли перезаписать файл X безопасно?») для другого класса файлов в том же скрипте/модуле.
2. **Распространить существующий механизм на новый класс**, а не строить параллельный git-state-aware механизм — content-based классификация (`classify-workspace-copy.sh` + `.memory-deployed.tsv`) переносится на governance-скрипты без изменения своей логики.
3. **Не прерывать весь прогон на одной неоднозначной записи.** `apply_governance_script_policy()` никогда не делает abort — только помечает каждый файл статусом (`uptodate`/`replaced`/`kept`/`unknown`) и продолжает.

## Тест

«Существует ли в кодовой базе уже работающий классификатор для той же задачи («можно ли безопасно перезаписать?») для другого класса файлов?» Да → распространить его, не строить параллельный механизм. И отдельно: «Останавливает ли весь pipeline одна неоднозначная запись?» Да → чрезмерная цена за edge case, нужен per-item статус вместо hard-abort.

## Связи

- WP-485 Ф17, WP-592 (пир-сессия Claude+Kimi+Codex, триаж issues FMT-exocortex-template)
- Источник: git commit `a35759a1` в FMT-exocortex-template; независимый ревью (Fable) предложил удалить параллельную эвристику и распространить существующий механизм.
- `DP.M.481` — смежный: условное самолечение грязной служебной копии (та же область, другая конкретная техника).
