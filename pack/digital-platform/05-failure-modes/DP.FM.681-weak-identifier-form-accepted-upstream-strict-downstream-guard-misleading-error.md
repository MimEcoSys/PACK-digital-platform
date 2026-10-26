---
id: DP.FM.681
name: "Слабая форма идентификатора проходит входную проверку, а строгий downstream-guard падает с сообщением про другую причину"
name_ru: "Слабая форма идентификатора проходит входную проверку, а строгий downstream-guard падает с сообщением про другую причину"
name_en: "A weak identifier form passes the entry check; a strict downstream guard then fails with a message naming a different cause"
summary: "`isolate-push.sh --exact-commit` проверял только существование коммита и достижимость из ветки (cat-file/merge-base принимают короткий SHA). Guard `ledger-source-snapshot.py` требует полный 40-64-символьный hex и на коротком SHA отвечает сообщением про архивацию периода на origin, а не про формат аргумента. Валидацию и нормализацию нужно делать на входе первого инструмента."
type: failure-mode
status: draft
pack: PACK-digital-platform
domain: digital-platform / tool-chain-validation
trust: empirical
epistemic_stage: pattern
valid_from: "2026-10-22"
created: 2026-10-23
schema_version: 1
related:
  see_also:
  - DP.FM.530
source_capture: DS-my-strategy/inbox/captures/2026-10.md:6353
extraction_report: DS-my-strategy/inbox/extraction-reports/2026-10-23-inbox-check-5.md
source_candidate: 1
---

# DP.FM.681 — Слабая форма идентификатора проходит вход, строгий downstream-guard даёт ложный диагноз

## Симптом

Публикация WP-538 (`--exact-commit 5933310c8`, 9 символов) трижды подряд падала с сообщением, указывающим на «archived on origin», хотя реальная причина — формат аргумента.

## Механизм

1. Первый инструмент проверяет идентификатор слабыми операциями (существование, достижимость), которые принимают сокращённую форму.
2. Вызываемый им downstream-guard требует строгую форму (`re.fullmatch` по полному hex) и бросает `ValueError("invalid commit")`.
3. Сообщение об ошибке на уровне цепочки называет другую проблему и уводит диагностику в сторону.

## Защита

Нормализовать идентификатор сразу после проверки существования (`git rev-parse --verify`), до передачи любому downstream-guard. Не полагаться на то, что downstream либо примет слабую форму, либо назовёт настоящую причину.

## Связи

- WP-484, WP-538; консультация Kimi/Codex.
- Смежный контекст: DP.FM.530 (тот же инструмент `--exact-commit`, другой дефект).
