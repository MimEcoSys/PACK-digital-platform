---
id: DP.FM.525
type: failure-mode
status: draft
created: "2026-10-02"
valid_from: "2026-09-27"
name: "Имя env-переменной override занято платформой под другой смысл (`IWE_RUNTIME` = имя хоста, не путь): состояние пишется не туда, защита слепнет, тест маскирует"
name_ru: "Имя env-переменной override занято платформой под другой смысл (`IWE_RUNTIME` = имя хоста, не путь): состояние пишется не туда, защита слепнет, тест маскирует"
name_en: "A script's override env var name is already claimed by the platform with another meaning (`IWE_RUNTIME` = host name, not a path): state goes to the wrong place, a guard goes blind, a test masks it"
summary: "Скрипты брали `$IWE_RUNTIME` как опциональный путь к каталогу рантайма, а `.claude/settings.json` задаёт ту же переменную как имя хоста (`claude-code`, DP.IWE.011 раздел C). Под Claude Code путь резолвился относительно строки `claude-code`: журнал и файлы состояния уходили в `claude-code/...` рядом с репозиторием, а защита `canon-reconcile-published.sh` искала живых писателей не там и ни разу не отказала по живому писателю за 230 запусков. Смоук-наборы экспортировали собственный override того же имени и дефекта не видели. Исправление: отдельное имя `IWE_RUNTIME_DIR`, имя хоста остаётся в `IWE_RUNTIME`; новые тесты падают на старом коде."
pack: PACK-digital-platform
domain: digital-platform / env-configuration
schema_version: 1
trust: empirical
epistemic_stage: pattern
source: "git commit 93698d3 в IWE (wp-reopen-gate.sh, refs-sync-broker.sh); bug-файл 2026-09-30 по canon-reconcile-published.sh (DS-my-strategy d06435f2e); iwe-local-config c099b2b и 9102ca9 (WP-530 F75); PR #977 в шаблон"
source_capture: "DS-my-strategy/inbox/captures/2026-09.md:4695"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-09-28-inbox-check-4.md"
source_candidate: 2
related:
  see_also: ["DP.IWE.011", "DP.FM.249", "AR.273", "DP.FM.516"]
tags: [env-var, name-collision, override, state-directory, smoke-test-masking, silent-failure]
---

# DP.FM.525 — Имя env-переменной override занято платформой: состояние пишется не туда

## Симптом

1. `wp-reopen-gate.sh` и его каталог состояния брали `$IWE_RUNTIME` как опциональный override пути. `.claude/settings.json` уже задаёт эту переменную глобально как идентификатор рантайма агента (`claude-code`). Каждый реальный запуск под Claude Code молча писал состояние аренды в ложный относительный путь вместо документированного `.iwe-runtime`. Нашёл дефект живой запуск задеплоенного скрипта; смоук-набор в песочнице экспортировал собственный override того же имени и коллизию скрыл.
2. Тот же класс в `canon-reconcile-published.sh` (bug-файл 30.09): каталог рантайма брался как `${IWE_RUNTIME:-...}/.iwe-runtime`. Скрипт после `cd "$REPO"` искал семафоры живых писателей в `claude-code/sessions/*.open` внутри репозитория, их там нет, поэтому защита «нет живого писателя в каноне» слепа. Журнал скрипта: 230 строк, все «refused», ни одного отказа из-за живого писателя; сам журнал писался в репозиторий как неотслеживаемая папка `claude-code/`. Смоук `canon-reconcile-published-smoke.sh` экспортирует песочный путь, поэтому дефекта не видел. Тот же файл содержит шаблонный PR #977; шаблонный `settings.json` переменную не задаёт.
3. Позже остальные читатели корня (`wp-archive-closed-phases.py`, четыре скилла) строили путь из `IWE_RUNTIME` так же: замок и журнал восстановления попадали в `claude-code/` под рабочим каталогом.

## Причина

Имя переменной для внутреннего override выбрано из локального словаря скрипта (`IWE_RUNTIME` звучит как путь), без сверки с именами, уже занятыми платформой (settings агента). Проверка «переменная задана → использовать как путь» срабатывает всегда, а ошибки нет: путь просто другой. Смоук-тест, экспортирующий ту же переменную, проверяет собственную подстановку, а не поведение под платформенным значением.

## Исправление

Коммит c099b2b (iwe-local-config, WP-530 F75, шаг 1): `IWE_RUNTIME` остаётся именем хоста, каталог задаётся отдельной `IWE_RUNTIME_DIR`; старое абсолютное значение `IWE_RUNTIME`, если это существующий каталог, принимается как устаревшее. Охват: `iwe-env-bootstrap.sh`, `protocol-stop-gate.sh`, `canon-reconcile-published.sh`. Новый тест `runtime-env-split-smoke.sh` (20 сценариев, 39 проверок): 29 проверок падают на прежнем коде. Коммит 9102ca9 (шаг 2): остальные читатели корня; новый тест на 14 проверок, 9 падают на базе шага 1.

## Тест обнаружения

«Имя переменной под override сверено grep-ом с платформенными конфигами (settings агента, plist и unit планировщиков, CI)?» Нет → возможна коллизия. «Смоук-тест экспортирует ту же переменную, которую код читает как override?» Да → тест не обнаружит коллизию; нужен кейс с платформенным значением (`IWE_RUNTIME=claude-code`) и новый тест, который падает на старом коде.

## Связанные документы

- DP.IWE.011 (раздел C: `IWE_RUNTIME` — имя хоста), AR.273 (конфликт переменных окружения чинится в settings, не в скилле), DP.FM.249 (устаревший дефолт переменной: другой механизм, не коллизия имени).
- Источник: WP-530 F75, WP-561; bug-файл 2026-09-30.
