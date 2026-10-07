---
id: DP.M.502
name: "Захват stderr анализатора в приватный per-invocation temp-файл вместо /dev/null — различать причины отказа guard'а"
name_ru: "Захват stderr анализатора в приватный per-invocation temp-файл вместо /dev/null — различать причины отказа guard'а"
name_en: "Capture an analyzer's stderr into a private per-invocation temp file instead of /dev/null — distinguish guard failure causes"
type: method
pack: PACK-digital-platform
domain: digital-platform / guard-engineering
trust: medium
epistemic_stage: forming
status: draft
created: "2026-10-06"
valid_from: "2026-10-06"
source: "git commit a5a67fc в iwe-local-config (secret-leak-block.sh)"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:1174"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-06-inbox-check-8.md"
source_candidate: 5
summary: "secret-leak-block.sh отправлял stderr анализатора в /dev/null, из-за чего любой отказ (неподдерживаемый синтаксис vs сам анализатор сломан) доходил до агента одним и тем же общим сообщением «анализатор не отработал». Фикс — захват stderr в приватный per-invocation temp-файл (не напрямую в общий durable-журнал, чтобы не ловить дозапись от параллельного вызова), surfacing последней строки в сообщении об отказе, best-effort дозапись в журнал постфактум; fallback на /dev/null при отказе mktemp сохраняет прежний risk profile."
tags: [stderr-capture, guard-engineering, error-diagnosis, fail-closed]
schema_version: 1
---

# DP.M.502 — Захват stderr анализатора в temp-файл вместо /dev/null

## Проблема

Любой guard/анализатор, печатающий одно и то же общее сообщение об отказе независимо от настоящей причины, не позволяет отличить «ожидаемый случай не поддерживается» от «сам инструмент сломан». secret-leak-block.sh скрывал реальную причину отказа анализатора за одним и тем же текстом «анализатор не отработал», потому что stderr анализатора уходил прямиком в `/dev/null`.

## Метод

1. Не отправлять stderr анализатора в `/dev/null` безусловно.
2. Захватывать stderr в приватный temp-файл, создаваемый отдельно на каждый вызов (`mktemp` per-invocation) — не писать напрямую в общий durable-журнал, чтобы не перепутать свою дозапись с дозаписью от параллельного вызова того же guard'а.
3. При отказе анализатора — показать в сообщении об отказе последнюю строку из захваченного stderr (surfacing), а не общий текст.
4. Best-effort дозаписать захваченный stderr в общий журнал постфактум (не блокирующе).
5. Если сам `mktemp` недоступен/отказал — fallback на `/dev/null`, сохраняя прежний (известный) risk profile, не превращая деградацию инструмента захвата в новый класс отказа.

## Тест

«Guard печатает одно и то же сообщение об отказе для двух структурно разных причин (ожидаемый неподдерживаемый случай vs внутренняя поломка инструмента)?» Да → применим этот метод: stderr нужно сохранять и показывать по-разному для каждой причины.

## Применимость

Любой guard/анализатор/валидатор, вызывающий внешний инструмент и скрывающий его stderr — особенно там, где одно обезличенное сообщение сейчас маскирует разные root cause.

## Связи

- Источник: bug-2026-10-06-secret-leak-block-guard-fails-closed-on-quick-close-runner-start.md
