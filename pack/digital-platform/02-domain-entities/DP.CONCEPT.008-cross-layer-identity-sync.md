---
id: DP.CONCEPT.008
name: Identity-операция обязана обновлять ВСЕ слои идентичности, не только legacy — иначе read-path упирается в NULL
type: domain-entity
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_cross_layer_identity_sync.md (WP-188 Ф17, 12.05; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [PACK-digital-platform, PACK-digital-platform]
---

# DP.CONCEPT.008: cross-layer identity sync

## Симптом
Пользователь делает /link → «найден и привязан» → /consent → «аккаунт не привязан». Два сообщения подряд противоречат друг другу.

## Причина
Identity-слои создавались инкрементально, каждый со своей семантикой. Write-функции остались привязаны к legacy-таблице (`users.aisystant_id`), а новый read-path (`resolve_ory_id_from_chat`) читает другой слой (`persona.ory_identity.telegram_id`), который writer не обновлял.

## Правило
Любая identity-операция (link/unlink/merge) обновляет ВСЕ слои:
- [ ] `users.*` (Railway-local, legacy)
- [ ] `persona.ory_identity.*` (Neon, новый слой)
- [ ] `development.identity_map` (Activity Hub, если применимо)
- [ ] event-gateway POST (асинхронные потребители, если применимо)
- [ ] сброс negative-кэшей (`_ory_cache.pop(chat_id, None)`)

## Как ловить
1. Тест-сценарий: /link → проверка через ВСЕ read-path за один вызов.
2. Перед коммитом: `grep -rn "telegram_id|aisystant_id|ory_id" handlers/ db/queries/` — все read-path функции проверены при смене write-path.
3. Долгосрочно: каждая identity-таблица — один write-владелец (OwnerIntegrity); пока слоёв несколько — атомарные write-функции, обновляющие все.
