---
id: DP.FM.583
type: failure-mode
status: draft
created: "2026-10-10"
valid_from: "2026-10-10"
name: "Проверка платформенной возможности после захвата ресурса — путь ошибки оставляет ресурс висящим"
name_ru: "Проверка платформенной возможности после захвата ресурса — путь ошибки оставляет ресурс висящим"
name_en: "Capability check performed after resource acquisition leaks the resource on the error path"
summary: "POSIX-специфичные атрибуты (SIGHUP, killpg) читались после Popen; на платформе без них AttributeError выбрасывался, когда дочерний процесс уже запущен, и никто его не освобождал."
pack: PACK-digital-platform
domain: digital-platform / process-management
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit a35b5db в iwe-local-config (WP-529 Ф19, issue #1005б)"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-10-inbox-check-5.md"
source_candidate: 1
tags: [resource-leak, fail-fast, platform-check, subprocess, error-path]
---

# DP.FM.583 — Проверка возможности платформы после захвата ресурса

## Тезис и механизм ошибки

Код обращался к POSIX-специфичным атрибутам (`SIGHUP`, `os.killpg`) только после того, как дочерний процесс был запущен через `Popen`. На платформе без этих атрибутов `AttributeError` возникал, когда ресурс (процесс) уже захвачен, и ни один обработчик его не освобождал — процесс утекал.

## Признаки

- В одной функции сначала захватывается ресурс (процесс, файл, соединение, блокировка), затем читаются атрибуты платформы/библиотеки, отсутствующие не везде.
- Путь ошибки между захватом и освобождением не покрыт `try/finally`.

## Митигация

Проверку платформенной/библиотечной возможности выполнять ДО захвата ресурса (fail-fast); если порядок поменять нельзя — освобождение ресурса в `finally`.

## Тест обнаружения

«Есть ли в функции обращение к необязательной возможности платформы после того, как ресурс уже захвачен?» Да → проверка стоит не на месте.
