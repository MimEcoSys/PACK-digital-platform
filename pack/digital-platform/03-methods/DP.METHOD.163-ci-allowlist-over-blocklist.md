---
id: DP.METHOD.163
type: method
domain: PACK-digital-platform
status: draft
summary: "CI-защита конфигурации через allowlist (явный список разрешённых) надёжнее blocklist (grep по подозрительным именам). Blocklist пропускает нейтрально-именованные нарушения; allowlist блокирует любое имя вне списка."
created: 2026-06-30
valid_from: 2026-06-30
version: v1.0
source: "session-transcript 2026-06-30-05-wp410-mcp-unification; WP-410 decision-log-2026-06.md (решение 3)"
related:
  see_also: [DP.M.090, DP.METHOD.162, DP.M.460]
---

# DP.METHOD.163: CI allowlist вместо blocklist для защиты конфига от дрейфа

## Назначение

Метод CI-защиты, предотвращающей случайное подтягивание приватных/привилегированных env-bindings в публичный режим сервиса.

## Проблема blocklist

Blocklist (grep по паттернам: `PERSONAL_|PRIVATE_|SCOPE_`) имеет фундаментальный изъян:
- Разработчик называет binding нейтрально (`KNOWLEDGE_SEMANTIC_PRIVATE`) → grep не срабатывает.
- Любое новое имя вне паттернов — автоматически пропускается.

Blocklist = ложная безопасность при росте списка bindings.

## Паттерн allowlist

Файл `.ci/public-allowed-bindings.txt` с явным списком разрешённых имён bindings в публичном режиме. CI job: при любом binding'е в конфиге, не находящемся в allowlist → fail.

```
# .ci/public-allowed-bindings.txt
KNOWLEDGE_DB_URL
EMBED_MODEL
MAX_RESULTS
CACHE_TTL
```

## Алгоритм CI-проверки

```bash
# Извлечь все binding-имена из конфига публичного сервиса
bindings=$(grep "^[A-Z_]*=" config/public.env | cut -d= -f1)
# Проверить каждое против allowlist
while IFS= read -r binding; do
  if ! grep -qxF "$binding" .ci/public-allowed-bindings.txt; then
    echo "ERROR: Unauthorized binding '$binding' in public mode config"
    exit 1
  fi
done <<< "$bindings"
```

## Применение в WP-410

WP-410 multi-mode MCP (public/personal режимы): нужна защита чтобы разработчик не добавил PERSONAL_* binding в public конфиг случайно. Принято: `.ci/public-allowed-bindings.txt` + CI fail на любое имя вне списка.

## Паттерн применимости

Любой конфиг с явными режимами (public/private, prod/staging, multi-tenant):
- При добавлении нового allowed binding → обновить allowlist явно.
- При CI fail → осознанное решение: разрешить или убрать binding.

## Другие применения

- Allowlist изоляции исполнения сценариев (`isolated_allowlist`, commit `e7b417f` в FMT-exocortex-template, #972): путь day-plan, evening, day-close, session-prep, week-review нельзя подтвердить безопасным по промптам и коду, поэтому по умолчанию сценарий в allowlist не входит (отказ по умолчанию), а причина не-включения записывается над списком, рядом с ним. Источник: кандидат 10/01.2#4 (`2026-10-01-inbox-check-2.md`).
- Исполняемый default-deny allowlist для публичной MCP-выдачи документов (путь, версия, язык, явное разрешение на выдачу), хранимый в закрытой конфигурации сервиса с историей изменений — не в самом Pack и не в открытом репозитории; отсутствие документа в списке = default-deny, без необходимости отдельного ревью каждого уже разрешённого случая. Источник: WP-590, codex-сессия 01a11197-09cd-7731-b86f-9530aa20614b (2026-10-06/07). Захват: `DS-my-strategy/inbox/captures/2026-10.md:1364`.

## Тест

«Если разработчик добавит новый env-binding с нейтральным именем в публичный конфиг — CI заблокирует?»
- Allowlist: CI fail → правильно.
- Blocklist: CI pass → неправильно.

## Связи

- DP.M.090 — mutation testing для CI guards (как проверить что guard работает)
- DP.METHOD.162 — auth layering (смежный принцип безопасности при слиянии сервисов)
