---
id: DP.M.522
name: "Приватный доступ по Tailscale: ослаблять rp_filter точечно только на tailscale-интерфейсе и открывать порт явным правилом, не через глобальный trustedInterfaces"
name_ru: "Приватный доступ по Tailscale: ослаблять rp_filter точечно только на tailscale-интерфейсе и открывать порт явным правилом, не через глобальный trustedInterfaces"
name_en: "Private Tailscale access: loosen rp_filter only on the tailscale interface and open the port with an explicit rule, not via global trustedInterfaces"
type: method
pack: PACK-digital-platform
domain: digital-platform / infra-networking
trust: medium
epistemic_stage: forming
status: draft
created: "2026-10-12"
valid_from: "2026-10-11"
source: "git commit d4eab52 в iwe-server-config; feed:git-diff 2026-10-11"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:2589"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-12-inbox-check.md"
source_candidate: 2
related:
  see_also: []
tags: [tailscale, rp_filter, firewall, zero-trust, scoped-trust]
schema_version: 1
summary: "Для приватного доступа к табло с телефона подключён Tailscale. rp_filter ослаблен (loose) только на интерфейсе tailscale0, не глобально — глобальное ослабление снизило бы защиту от спуфинга и на публичном eth0. Firewall открывает конкретный порт явным правилом именно на tailscale0, а не через trustedInterfaces, который доверил бы интерфейсу вообще всё."
---

# DP.M.522 — Точечное доверие интерфейсу Tailscale, не глобальное

## Проблема

Нужен приватный доступ к сервису (табло) с телефона через Tailscale. Два стандартных упрощения дают избыточное доверие: (1) глобально ослабить `rp_filter` ради одного оверлейного интерфейса — ослабляет защиту от IP-спуфинга и на публичном `eth0`; (2) добавить интерфейс в `trustedInterfaces` firewall — доверяет интерфейсу вообще ВСЁ (включая случайные сервисы на `0.0.0.0`), не только нужный порт.

## IPO-паттерн

| Элемент | Описание |
|---|---|
| Входы | Новый оверлейный интерфейс (Tailscale) для приватного доступа; существующий публичный интерфейс (`eth0`), который не должен терять защиту |
| Обработка | `rp_filter` → `loose` точечно только на `tailscale0` (не глобальный sysctl); firewall → явное правило на конкретный порт именно на `tailscale0`, не включение интерфейса в `trustedInterfaces` |
| Выходы | Доступ к сервису через Tailscale работает; анти-спуфинг на `eth0` не тронут; на `tailscale0` открыт ровно нужный порт, а не всё |

## Когда применять

Любое подключение оверлейной сети (Tailscale, WireGuard, VPN-интерфейс) для приватного доступа к сервису на машине, у которой уже есть публичный сетевой интерфейс с действующей защитой (rp_filter, firewall zones).

## Антипаттерн

- Глобально ослаблять `rp_filter` ради одного интерфейса — снижает защиту всех интерфейсов, не только целевого.
- Доверять интерфейсу через `trustedInterfaces`/эквивалент — открывает ВСЕ сервисы на интерфейсе, не только тот, что нужен.

## Прецедент

Для доступа к табло с телефона подключён модуль Tailscale (WP-389). `rp_filter` ослаблен только на `tailscale0`; firewall открывает порт 443 точечным правилом на `tailscale0`.

## Связи

- WP-389
