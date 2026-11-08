---
id: DP.D.376
name: "Агрегатор ≠ нейтральный посредник: он входит в бюджет потока наравне с источниками"
name_ru: "Агрегатор ≠ нейтральный посредник: он входит в бюджет потока наравне с источниками"
name_en: "An aggregator is not a neutral intermediary: it counts toward the stream budget like any source"
type: distinction
status: draft
pack: PACK-digital-platform
domain: digital-platform / notifications
schema_version: 1
trust: medium
epistemic_stage: forming
created: "2026-11-07"
valid_from: "2026-11-03"
source: "captures/2026-11.md, РП-568 (сессия 2026-11-03)"
source_capture: "DS-my-strategy/inbox/captures/2026-11.md"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-11-07-inbox-check-4.md"
source_candidate: 1
---

# DP.D.376: Агрегатор ≠ нейтральный посредник

**Различение.** Сводка (агрегатор) уведомлений сама является источником сообщений. Цель по суточному потоку (0–2 сообщения) нельзя достичь, если число слотов агрегатора больше цели.

**Пример.** Сводка шла каждые 3 часа (шесть слотов) и давала 7 из 16 сообщений в сутки. Перенос остальных источников в сводку сокращал поток, но нижняя граница задавалась числом слотов самой сводки. Пилот перевёл её на 07/14/21.

**Правило применения.** Частота агрегатора — рычаг того же рода, что подключение источников. Бюджет потока считать как сумму источников и слотов агрегатора; цель ниже числа слотов недостижима.
