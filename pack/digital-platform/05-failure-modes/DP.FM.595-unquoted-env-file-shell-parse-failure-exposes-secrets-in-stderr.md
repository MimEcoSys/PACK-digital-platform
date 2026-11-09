---
id: DP.FM.595
type: failure-mode
status: draft
created: "2026-10-11"
valid_from: "2026-10-11"
name: "Синтаксическая ошибка в env-файле без кавычек: bash падает с ошибкой разбора, строки после точки отказа попадают в stderr как открытый текст — секреты оказываются в логе задачи"
name_ru: "Синтаксическая ошибка в env-файле без кавычек: секреты оказываются в логе задачи через stderr"
name_en: "Unquoted value in env-file causes bash parse failure; lines after the failure point land in stderr as plaintext — secrets end up in the task error log"
summary: "Значение переменной в env-файле содержало символ «*» без кавычек. Bash упал с ошибкой разбора на этой строке; строки после точки отказа не были обработаны как присваивания, а попали в stderr процесса. launchd записал stderr в обычный лог задачи: 6 строк открытого текста, включая пароль Grafana и строку подключения к БД с паролем в URL. Четвёртый инцидент того же класса за полтора месяца. Механизм: ошибка разбора в shell env-файле не просто останавливает чтение — необработанные строки после точки отказа оказываются в stderr и могут попасть в любой лог, захватывающий stderr задачи."
pack: PACK-digital-platform
domain: digital-platform / secrets-management
trust: high
epistemic_stage: confirmed
source: "git commit 43542fb8b в DS-my-strategy (WP-544 Ф19)"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:2333"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-11-inbox-check.md"
source_candidate: 4
related:
  see_also: ["DP.FM.570", "DP.FM.026"]
tags: [env-file, shell-parse-error, secrets, stderr, launchd, log-exposure, bash-syntax, unquoted]
schema_version: 1
---

# DP.FM.595 — Синтаксическая ошибка в env-файле без кавычек: секреты в stderr

## Тезис и механизм

Значение переменной в shell env-файле содержало специальный символ (`*`) без кавычек. Bash упал с ошибкой разбора на этой строке. **Строки после точки отказа не были обработаны как присваивания** — вместо этого они попали в stderr процесса как неструктурированный текст.

launchd записал stderr в стандартный лог ошибок задачи (`sync-server-extensions-err.log`) с обычными правами доступа. В результате 6 строк открытого текста оказались в файле, доступном любому пользователю с правами чтения логов:
- пароль Grafana
- строка подключения к БД с паролем в URL

## Инцидентная статистика

Четвёртый инцидент того же класса за полтора месяца в той же инфраструктуре.

## Инвариант

Ошибка разбора в shell env-файле не просто останавливает чтение — она меняет семантику: строки после точки отказа становятся произвольным выводом, а не присваиваниями. Любой захватчик stderr (launchd, systemd, nohup, tee) сохранит эти строки.

## Профилактика

1. Кавычки для всех значений в env-файлах (`VAR="value with * and spaces"`)
2. Валидация env-файла на синтаксис перед загрузкой (`bash -n` или shellcheck)
3. Перехват stderr задачи и ротация логов с ограниченными правами
4. Пайплайн secrets: пароли в env-файлах только через secret manager или шифрование
