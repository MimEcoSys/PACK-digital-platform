---
id: DP.M.476
type: method
status: active
created: "2026-09-30"
name: "Пропуск обязательного действия по условию оформляется заведённым обращением, а не молчанием"
summary: "Автоматика пропустила релиз при пустом [Unreleased], хотя после тега было 10 коммитов. Правило: пропуск по условию = заведённое обращение (release-skipped при пустом [Unreleased] и ≥5 коммитах после тега) плюс мягкий гейт «PR в main добавляет строку в CHANGELOG со своим номером»."
pack: PACK-digital-platform
domain: digital-platform
trust: medium
epistemic_stage: forming
source: "git commit 3040a94 в FMT-exocortex-template (WP-529)"
source_capture: "DS-my-strategy/inbox/captures/2026-09.md"
related:
  see_also: ["DP.M.039", "DP.FM.497"]
---

# DP.M.476 — Видимый пропуск релиза

**Вход:** автоматика пропускает действие по условию.
**Процесс:** при пропуске, если признаки «нужно было» (порог по умолчанию ≥5 коммитов после последнего тега — настраиваемый параметр, не фиксированная константа), завести обращение; мягкий гейт на CHANGELOG в PR.
**Выход:** пропуск виден и разбираем.
