---
id: DP.FM.530
type: failure-mode
status: draft
created: "2026-10-02"
valid_from: "2026-09-28"
name: "Пустой коммит-маркер в публикуемом диапазоне останавливает cherry-pick: результат цикла остаётся на хосте, журнал пишет «degraded»"
name_ru: "Пустой коммит-маркер в публикуемом диапазоне останавливает cherry-pick: результат цикла остаётся на хосте, журнал пишет «degraded»"
name_en: "An empty marker commit inside the published range stops cherry-pick: the cycle result stays on the host and the ledger records \"degraded\""
summary: "Оркестратор такта делает ровно два своих коммита: пустой маркер начала (`*-close-start`, STEP 0) и коммит результата. `ds-publish --from-commit` в реализации DS-my-strategy (`publish_commit` в `scripts/lib/publish-gate.sh`) переносит диапазон `origin/main..<sha>`; `git cherry-pick` останавливается на пустом маркере («The previous cherry-pick is now empty»), результат остаётся на хосте, ledger фиксирует цикл как degraded («local commit not confirmed on origin/main»). Живые падения: 28.09 (W39) и 02.10 00:02 (месячный такт на tsekh-1). Исправление: публиковать ровно коммит результата (`--exact-commit`)."
pack: PACK-digital-platform
domain: digital-platform / publication
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit 92c62e05e в DS-my-strategy (WP-561 Ф31); живые падения 28.09 (W39) и 02.10 00:02"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:184"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-02-inbox-check-3.md"
source_candidate: 3
related:
  see_also: ["DP.FM.441", "DP.M.414", "DP.FM.507"]
tags: [git, cherry-pick, range-transplant, empty-commit, marker-commit, publish, degraded]
---

# DP.FM.530 — Пустой коммит-маркер в публикуемом диапазоне останавливает cherry-pick

## Симптом

Недельный и месячный оркестраторы такта (изолированные запуски) делают в своей копии два коммита: пустой маркер начала `*-close-start` (STEP 0) и коммит результата. Публикация `ds-publish --from-commit <sha>` в реализации DS-my-strategy (`publish_commit` в `scripts/lib/publish-gate.sh`) переносит диапазон `origin/main..<sha>`; в `ds-publish.sh` шаблона FMT-exocortex-template контракт иной (один коммит за вызов, см. `DP.FM.441`, триггер 3). `git cherry-pick` останавливается на пустом маркере («The previous cherry-pick is now empty»), публикация обрывается, результат цикла остаётся на хосте, а ledger пишет цикл как `degraded` («local commit not confirmed on origin/main»). Живые падения: 28.09 (W39) и 02.10 00:02 (месячный такт на tsekh-1).

## Причина

Диапазонный перенос предполагает, что каждый коммит диапазона несёт патч. Маркер патча не имеет, и `cherry-pick` диапазона без `--allow-empty` или `--keep-redundant-commits` на нём останавливается. Публикатор не знает, какие коммиты вызывающего относятся к результату: «от коммита» означает «всё от origin/main до sha», хотя вызывающий хотел доставить один коммит.

## Исправление

1. Вызывающий называет ровно коммит результата: `--exact-commit` рядом с `--from-commit` (пару понимает `publish_commit` в `publish-gate.sh`).
2. Изолированные обёртки стартуют из свежего worktree `origin/main`, поэтому точная публикация роняет только маркер, чужого в диапазоне нет.
3. Проверка сценарием с реальным публикатором и bare origin: без флага exit 20; с флагом результат доставлен, маркер не доставлен, чужой коммит origin цел.

## Тест обнаружения

«Есть ли в `origin/main..HEAD` коммиты без патча (`git show --stat <sha>` пуст), и публикатор переносит диапазон?» Да и да → перенос остановится на маркере. Признак: падение повторяется ровно в тактах, где STEP 0 ставит маркер.

## Связанные документы

- DP.FM.441 (публикующая обёртка при частичном результате сообщает успех): там вершину цепочки молча усекали до одного коммита, здесь один коммит молча расширен до диапазона; обе ошибки в арности на границе вызывающий и публикатор.
- DP.M.414 (шлюз fetch + cherry-pick + retry): эта карточка описывает его отказ при диапазоне со служебными коммитами. DP.FM.507: другой механизм потери результата на изолированном пути.
- Источник: WP-561 Ф31, коммит 92c62e05e в DS-my-strategy.
