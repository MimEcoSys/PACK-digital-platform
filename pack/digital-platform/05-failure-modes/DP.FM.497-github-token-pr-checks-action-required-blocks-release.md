---
id: DP.FM.497
type: failure-mode
status: active
created: "2026-09-30"
name: "PR, открытый через GITHUB_TOKEN, получает проверки в статусе action_required: обязательная проверка не запускается, релиз стоит"
summary: "Проверки PR, открытого встроенным токеном, стартуют как action_required, обязательная проверка релиза не выполняется, PR недельного релиза два дня заблокирован."
pack: PACK-digital-platform
domain: digital-platform
trust: medium
epistemic_stage: forming
source: "git commit 3040a94 в FMT-exocortex-template (WP-529)"
source_capture: "DS-my-strategy/inbox/captures/2026-09.md"
related:
  see_also: ["DP.FM.268"]
---

# DP.FM.497 — Проверки PR от GITHUB_TOKEN в action_required

**Симптом:** PR релиза (#935) два дня заблокирован: required-проверка (release-receipt) не запускалась.

**Лечение:** после открытия PR явно запускать проверку на ветке релиза; ежедневный сторож на устаревшие release-PR.

**Применимость:** любой автоматический релиз через встроенный токен.
