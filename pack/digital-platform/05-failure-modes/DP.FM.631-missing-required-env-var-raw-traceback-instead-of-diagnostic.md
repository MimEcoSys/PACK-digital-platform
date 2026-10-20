---
id: DP.FM.631
type: failure-mode
status: draft
created: "2026-10-16"
valid_from: "2026-10-16"
name: "Отсутствующая обязательная переменная окружения роняет git-хук необработанным traceback вместо диагностики"
name_ru: "Отсутствующая обязательная переменная окружения роняет git-хук необработанным traceback вместо диагностики"
name_en: "Missing required environment variable crashes a git hook with a raw traceback instead of a diagnostic message"
summary: "pre-commit хук (session-guard.sh pre-commit-check) при пустом IWE_AGENT в окружении уходит в fallback автоопределения агента по хосту и угаданной метке, строит путь к семафору по этой догадке и читает файл без проверки существования — вместо честного «агент не задан» коммит падает сырым FileNotFoundError без читаемого сообщения пилоту."
pack: PACK-digital-platform
domain: digital-platform / process-runner
schema_version: 1
trust: observed
epistemic_stage: forming
source: "git commit 2e859f2096 в DS-my-strategy"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:4040"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-16-inbox-check-4.md"
source_candidate: 4
note: "Капча предложила PACK-verification/05-failure-modes. VR manifest исключает тестирование программного кода, а bounded-context PACK-digital-platform маршрутизирует механику охраны сессий сюда. Перенаправлено на DP.FM; номер 631 назначен после кандидатов 2026-10-16-inbox-check-2.md #1 и #2 (номера 629 и 630)."
related:
  see_also: [DP.FM.508, DP.FM.353]
tags: [env-var, pre-commit-hook, session-guard, fallback-autodetect, raw-traceback, diagnostics]
---

# DP.FM.631 — Отсутствующий IWE_AGENT роняет pre-commit хук необработанным traceback

## Тезис и механизм ошибки

pre-commit хук (`session-guard.sh pre-commit-check`) при пустом `IWE_AGENT` в окружении не останавливается с читаемой диагностикой, а уходит в fallback-ветку автоопределения «агента» по хосту и угаданной метке. Этот fallback строит путь к файлу семафора по догадке и сразу читает его, не проверив существование файла. Коммит падает сырым `FileNotFoundError` (необработанный traceback) вместо понятного пилоту сообщения вида «установи IWE_AGENT перед commit».

## Диагностический принцип

Fallback-автоопределение идентичности/окружения безопасно только для чтения уже гарантированно существующих ресурсов. Если путь строится по догадке (не по явно заданному значению), чтение по этому пути обязано сначала проверить существование файла — иначе отсутствие обязательной переменной окружения превращается в необработанное исключение вместо диагностики.

## Проверка

«Если обязательная переменная окружения не задана, fallback-ветка читает ресурс по угаданному пути без проверки его существования?» Да → риск DP.FM.631.

## Фикс (воркераунд; починка хука отложена)

Явно передавать `IWE_AGENT` перед commit. Починка самого хука (явная ошибка при пустом `IWE_AGENT` до входа в fallback, либо проверка существования файла перед чтением) отложена отдельным bug-файлом.

## Границы

Применимо к любому git-хуку или скрипту, где отсутствие обязательной переменной окружения маскируется автоопределением вместо явного отказа. Не ограничивается `session-guard.sh` или `IWE_AGENT`.

## Связи

Источник: правка карточки WP-595 (побочная находка, не специальный аудит); `inbox/bugs/bug-2026-10-15-pre-commit-check-crashes-without-iwe-agent.md`.
