---
id: DP.FM.632
type: failure-mode
status: draft
created: "2026-10-16"
valid_from: "2026-10-16"
name: "Валидатор образа отвергал валидные provenance-манифесты buildx с инлайн data-дескриптором конфига"
name_ru: "Валидатор образа отвергал валидные provenance-манифесты buildx с инлайн data-дескриптором конфига"
name_en: "Image validator rejected valid buildx provenance manifests with an inline config descriptor `data` field"
summary: "Первый живой прогон CI с buildx `provenance: mode=min` впервые передал provenance-attestation манифест, чей config — OCI «empty»-descriptor, инлайнящий содержимое через собственное поле `data` вместо отдельного blob. Проверяющий скрипт безусловно отвергал любой descriptor с полем `data`, поэтому шаг падал на каждом вызове с provenance; локальная разработка никогда не передавала --provenance и не вскрыла пробел."
pack: PACK-digital-platform
domain: digital-platform / release-engineering
schema_version: 1
trust: observed
epistemic_stage: forming
source: "git commit d0610faa в aist_bot_newarchitecture (WP-562 Ф9), peer-session 2026-10-15-35-wp562-publish-image-artifact"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:4067"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-16-inbox-check-5.md"
source_candidate: 2
related:
  see_also: ["DP.FM.633"]
tags: [oci, buildx, provenance, attestation, descriptor, image-validation]
---

# DP.FM.632 — Валидатор образа отвергал валидные provenance-манифесты buildx

## Симптом

Первый живой прогон в GitHub Actions (не локальная разработка) впервые передал buildx `provenance: mode=min`. Проверяющий скрипт безусловно отвергал любой descriptor с полем `data` как невалидный — хотя это стандартный способ OCI инлайнить пустой config аттестации вместо отдельного blob-файла. Каждая сборка с включённым provenance добавляет attestation-манифест, чей config — именно такой инлайн-дескриптор; шаг валидации падал на каждом вызове с момента написания. Локальная сборка при разработке никогда не передавала `--provenance`, поэтому пробел не вскрывался до первого живого прогона CI.

## Причина

`Descriptor.parse` был написан с неявным предположением, что валидный descriptor всегда указывает на отдельный blob, и отвергал любой descriptor, несущий содержимое инлайн через `data`. OCI provenance-attestation — легитимный случай именно такого инлайн-дескриптора; валидатор не учитывал эту форму вовсе.

## Антипаттерн → Паттерн

- **Антипаттерн:** валидатор дескрипторов безусловно отвергает любой `data`-инлайн как невалидный, не проверяя, легитимна ли эта форма для данного типа манифеста.
- **Паттерн:** инлайн `data` принимается как валидный, только если его хеш сверен с заявленным digest самого дескриптора — тем же способом, которым уже проверялись обычные blob-файлы. Поле `urls` при этом остаётся отвергнутым. Фикс не ослабляет проверку, а добавляет к ней ещё один легитимный путь с тем же уровнем доказательности.

## Тест обнаружения

«Если тип манифеста допускает несколько легитимных форм хранения содержимого дескриптора (blob-ссылка, инлайн `data`, внешний `urls`) — проверяет ли валидатор каждую форму по отдельности на соответствие заявленному digest, или отвергает/принимает по одному общему правилу, не рассчитанному на все легитимные формы?» Общее правило без разбора форм → риск ложного отказа (как здесь) или ложного принятия.

## Связанные документы

Источник: git commit `d0610faa` в aist_bot_newarchitecture (WP-562 Ф9), peer-session `2026-10-15-35-wp562-publish-image-artifact`. Первая живая публикация образа в реестр для этой системы.
