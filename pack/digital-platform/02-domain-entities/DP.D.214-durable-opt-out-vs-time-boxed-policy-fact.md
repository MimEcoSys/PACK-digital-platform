---
id: DP.D.214
name: "Durable user-opt-out (у Распорядителя доставки) ≠ Time-boxed policy-fact навигатора (в движке)"
type: distinction
domain: digital-platform
pack: PACK-digital-platform
status: active
valid_from: 2026-06-21
schema_version: 1
source: "WP-117 Ф-integration, peer-session 2026-06-21, report.md §2 Т2-Т4, §4"
related: [DP.D.213]
---

# DP.D.214 — Durable user-opt-out ≠ Time-boxed policy-fact навигатора

| Durable user-opt-out | Time-boxed policy-fact |
|---------------------|------------------------|
| Постоянный: явный отказ пользователя | Временной: действует до `until: T` |
| Enforcement у Распорядителя доставки (DP.ROLE.075, нижний слой) | Enforcement в движке до `produce()` |
| Снимается только пользователем | Снимается по `until` источником-навигатором |
| Пробивает всё выше по стеку | Не пробивает пользовательский opt-out другого слоя |

**Инвариант:** Оба шлюза могут разделять один словарь категорий (DP.SC.116), но физически разделены и не взаимозаменяемы. `action: allow` от источника — carve-out только внутри его собственных suppress-записей; не отменяет пользовательский opt-out из другого слоя.

**Failure mode слияния:** временное подавление читается как постоянный отказ пользователя; теряется владелец таймера `until`. → См. DP.FM.232.

**Тест:** «Кто и когда снимает блок — пользователь навсегда у Распорядителя доставки или источник по until:T в движке?» Разные ответы → два шлюза, не одно поле.

**Источник:** WP-117 Ф-integration, peer-session 2026-06-21, report.md §2 Т2-Т4, §4.
