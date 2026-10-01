---
id: DP.M.075
name: No-op heartbeat для детекции silent-fail в scheduled workflow
kind: Method
status: active
created: 2026-05-17
sources:
  - WP-322 «Pack-drift-watcher» Ф1.3 H2+H3 (DS-principles-curriculum/890b15b — pack-drift-watcher.yml)
  - session-transcript 2026-05-17
related:
  complements: [DP.M.028]  # Stateless Worker Cursor Pattern — там negative signal (exit 1 на errors>0), здесь positive signal на no-op
  applies_to: [scheduled GH Actions, cron, drift-watcher, security-scan, low-rate watcher, daily reindex внешнего корпуса (FPF/SPF) в knowledge-mcp]
---

# DP.M.075: No-op heartbeat для детекции silent-fail в scheduled workflow

## Определение

Метод обнаружения silent-fail в scheduled CI/cron pipeline'ах с low event rate: при «no-op» исходе (drift=0, нет событий, нечего делать) workflow эмитит **positive heartbeat** — структурированную запись в лог + step-summary с метаданными последнего запуска. Отсутствие heartbeat за > expected interval = детектор silent failure.

## Проблема

Scheduled workflow (cron, drift-watcher, scheduled audit) при штатном «нечего делать» проходит без notification — на radar'е не отличается от «workflow не запускался вовсе» (cron broken, schedule disabled, branch protection ругается). Класс ошибок симметричен «errors>0 → exit 1 в systemd» — там детект через negative-signal, здесь через positive.

## Forces

_Какие конкурирующие давления удерживает метод._

| Force | Tension |
|-------|---------|
| Экономия сигнала (лог только когда реально что-то найдено) ↔ наблюдаемость «процесс жив» | Обычный лог минимизирует шум для non-events, но именно это делает «нечего делать» неотличимым от «cron сломан/schedule disabled»; heartbeat намеренно добавляет шум в null-результат ради этого различения |
| Простота сигнала (одна строка) ↔ полнота метаданных (timestamp, source_hash, trigger, run_url, result) | Каждое дополнительное поле облегчает диагностику «на каком состоянии проверяли», но каждое поле — это то, что должно синхронно обновляться с реальностью источника, иначе heartbeat формально есть, а диагностической ценности не несёт |

## Триггер применимости

> «Есть ли scheduled job, у которого "всё нормально" выглядит как "не запускался"?»

- **Да** → добавить heartbeat в no-op ветку.
- **Нет** (workflow реагирует на events и любой запуск что-то меняет) → не нужен.

- **Пример (2026-09, WP-532 Ф9):** ежесуточная переиндексация FPF в поиске год работала в проде без heartbeat — «жива ли» никто не проверял, и по той же причине для второго источника (SPF) такая же задача не была заведена вовсе. Отсутствие наблюдателя скрывает не только отказ задачи, но и отсутствие задачи для соседнего источника.

## Компоненты heartbeat-сигнала

При no-op исходе:

1. **Лог-маркер** — `::notice::` (GitHub Actions) или structured log line, парсимый watcher'ом.
2. **Step Summary** — строка в `GITHUB_STEP_SUMMARY` с метаданными:
   - `timestamp` (когда сработал)
   - `source_hash` / `pack_commit` (на каком состоянии)
   - `trigger` (schedule / manual / push)
   - `run_url` (ссылка на запуск)
   - `result: no-op` (явный маркер)

## Различение

**Heartbeat ≠ positive-result logging.** Heartbeat нужен именно в «no-op» ветке, не вместо normal output. Если есть события — обычный лог. Если событий 0 — heartbeat.

## Bias-Annotation

_Куда систематически съезжает внимание практикующего._

| Bias | Direction of distortion |
|------|--------------------------|
| Логирование тянется к normal-path, не к no-op ветке | Внимание естественно идёт туда, где «видно результат» (события найдены, drift обнаружен), и недооценивает именно null-путь (`result: no-op`) — ветку добавляют в последнюю очередь или забывают, потому что «там же ничего не произошло» |
| Создание сигнала подменяет реакцию на его отсутствие | После того как heartbeat реализован, внимание смещается на следующую задачу и не доходит до настройки alert'а «heartbeat отсутствует > expected interval» — сам факт наличия строки в логе ошибочно воспринимается как решённая проблема детекции silent-fail |

## Применимость

- Scheduled GH Actions, GitLab CI cron jobs.
- Cron-jobs без external monitoring (uptime watcher не помогает).
- Watcher-воркеры с low event rate (drift, security scan, dependency audit, license audit).
- ETL-pipeline'ы, которые «штатно ничего не нашли».

## Связи

- **Дополняет:** feedback_silent_projection_fail.md (silent UPSERT fail в projection-worker).
- **Дополняет:** feedback_alerter_writer_sampling_drift.md (idle ≠ stuck без backlog-проверки).
- **Дополняет:** DP.M.028 (cursor pattern) — там exit-code на errors>0; здесь positive signal на drift=0.

---

> 2026-07-27 — миграция на обогащённый формат карточки (Forces + Bias-Annotation), WP-448 Ф12 Батч 3 (суб-батч 3). Эталон формата: `SPF/pack-template/03-methods/_method-card-template.md`.
