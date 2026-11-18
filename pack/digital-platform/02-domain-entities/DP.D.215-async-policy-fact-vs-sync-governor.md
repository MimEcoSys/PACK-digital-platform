---
id: DP.D.215
name: "Асинхронный policy-fact на следующий батч ≠ Синхронный governor (для capped-класса доставки)"
type: distinction
domain: digital-platform
pack: PACK-digital-platform
status: active
valid_from: 2026-06-21
schema_version: 1
source: "WP-117 Ф-integration, peer-session 2026-06-21, report.md §3, §4"
related: [DP.D.213, DP.D.214]
---

# DP.D.215 — Асинхронный policy-fact ≠ Синхронный governor

| Async policy-fact (батч) | Sync governor |
|--------------------------|---------------|
| Флаг на следующий drain-цикл | Перехватывает выход движка до Приёмщика (DP.ROLE.123) |
| Нет синхронной зависимости engine → governor | Синхронная связь: engine зовёт governor |
| Достаточен для low-priority / capped | Нужен при контекстных правилах или high-priority |
| «Срочно прямо сейчас» — источник сам шлёт через Вестник | Governor нужен, если движок обязан остановиться |

**Инвариант:** Выбор между async policy-fact и sync governor определяется приоритетом и частотой класса доставки. Для batched capped-класса (низкий приоритет, дренируется раз в сутки) синхронный governor избыточен — async флага на следующий drain-цикл достаточно.

**Trigger для Governor:** если сигнал становится контекстным правилом (DP.D.213), а не категориальным флагом — async модели не хватает.

**Тест:** «Нужен ли синхронный перехват выхода движка или хватает async policy-fact на следующий батч?» Ответ определяется приоритетом/частотой класса.

**Источник:** WP-117 Ф-integration, peer-session 2026-06-21, report.md §3, §4.
