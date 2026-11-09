---
id: DP.FM.633
type: failure-mode
status: draft
created: "2026-10-16"
valid_from: "2026-10-16"
name: "skopeo copy без --multi-arch all тихо сужает multi-manifest источник до одной платформы"
name_ru: "skopeo copy без --multi-arch all тихо сужает multi-manifest источник до одной платформы"
name_en: "skopeo copy without --multi-arch all silently narrows a multi-manifest source to one platform"
summary: "Второй живой прогон CI (сразу после фикса provenance-валидатора, DP.FM.632) нашёл, что сверка публикации сравнивала digest верхнеуровневого index.json, посчитанный verify-шагом, с digest результата обычного skopeo copy — а обычный copy без --multi-arch тихо пересериализует только текущую платформу и пересчитывает иной digest. Оба digest расходились по разным, независимым причинам."
pack: PACK-digital-platform
domain: digital-platform / release-engineering
schema_version: 1
trust: observed
epistemic_stage: forming
source: "git commit 24e98d5b в aist_bot_newarchitecture (WP-562 Ф9), peer-session 2026-10-15-35-wp562-publish-image-artifact"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:4076"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-16-inbox-check-5.md"
source_candidate: 3
related:
  see_also: ["DP.FM.632"]
tags: [oci, skopeo, multi-arch, manifest-list, digest-mismatch, image-publish]
---

# DP.FM.633 — skopeo copy без --multi-arch тихо сужает manifest list

## Симптом

Второй живой прогон CI (сразу после фикса provenance-валидатора, см. `DP.FM.632`) нашёл второе расхождение: сверка публикации сравнивала digest верхнеуровневого `index.json`, посчитанный verify-шагом, с digest, полученным обычным `skopeo copy` без флага `--multi-arch`. По умолчанию при отсутствии `--multi-arch` `skopeo copy` тихо сужает multi-manifest источник до текущей (локальной/override) платформы и пересериализует результат — сравнение шло не «тот же index с двух сторон», а «оригинальный multi-platform index против урезанного до одной платформы и пересобранного». Оба digest были «неверны» по-разному — обе стороны сравнения независимо пересчитывали digest с нуля.

## Причина

Команда `skopeo copy` без `--multi-arch all` рассчитана на одноплатформенный сценарий по умолчанию; при multi-manifest источнике она молча выбирает текущую платформу вместо явной ошибки о несовместимости режима с типом источника.

## Антипаттерн → Паттерн

- **Антипаттерн:** копирование multi-platform образа инструментом, который по умолчанию принимает одну платформу, без явного расширяющего флага; плюс пересчёт digest результата copy с нуля вместо переиспользования уже посчитанного значения верификации.
- **Паттерн:** `skopeo copy --multi-arch all --preserve-digests` — копирует весь manifest list байт-идентично, без пересериализации; сверка публикации использует уже посчитанный verify-шагом `index_digest`, не пересчитывает его повторно — одним независимым пересчётом меньше, с которым можно было бы разойтись.

## Тест обнаружения

«Источник — multi-manifest (manifest list / OCI index)? Явно передан флаг, расширяющий copy с одной платформы на весь список? Сравнение digest использует одно и то же посчитанное значение с обеих сторон, или пересчитывает его дважды независимо?» Нет флага ИЛИ двойной независимый пересчёт → риск расхождения, маскирующего настоящую причину.

## Связанные документы

- Источник: git commit `24e98d5b` в aist_bot_newarchitecture (WP-562 Ф9), peer-session `2026-10-15-35-wp562-publish-image-artifact`.
- `DP.FM.632` — предыдущая находка того же первого живого прогона публикации образа (provenance-валидатор); эта карточка — следующий шаг того же процесса, другой механизм.
