---
id: DP.SOTA.028
name: "Claude CLI headless hook inheritance — хуки из settings.json наследуются при `claude -p`"
type: sota
status: draft
summary: "Lifecycle-хуки Claude Code (PostToolUse, Stop из .claude/settings.json) срабатывают при `claude -p` идентично интерактивному режиму. Headless-агент автоматически получает весь hook-слой (WakaTime, agent-trace-recorder, rule-engine) без дополнительного кода, при условии что CLAUDE_CONFIG_DIR / CLAUDE_PROJECT_DIR указаны."
created: 2026-05-22
valid_from: 2026-05-22
updated: 2026-11-18
trust:
  F: 3
  G: observed
  R: 0.85
related:
  informs: [DP.IWE.011]
  uses: []
  see_also: [DP.SOTA.021, DP.SOTA.043]
sources:
  - git diff PACK-digital-platform commit d9f4d3c (feat DP.IWE.011 headless adapter v0.1)
  - session-close 2026-05-21
---

# DP.SOTA.028 — Claude CLI Headless Hook Inheritance

> Хуки Claude Code (PostToolUse, Stop из `.claude/settings.json`) срабатывают при запуске `claude -p` точно так же, как в интерактивном режиме. Headless-агент наследует весь hook-слой проекта без дополнительного кода.

## Наблюдение

При проектировании headless-адаптера (DP.IWE.011) обнаружено: lifecycle-хуки Claude Code из `.claude/settings.json` (UserPromptSubmit, PostToolUse, Stop) срабатывают при запуске `claude -p` — без каких-либо изменений относительно интерактивного использования.

**Следствие:** headless-агент автоматически получает:
- WakaTime-tracking
- agent-trace-recorder
- rule-engine (диспетчер правил)
- любой другой PostToolUse/Stop хук проекта

Дополнительный код для имитации не нужен.

## Условие применимости

Хуки наследуются, если при запуске `claude -p` переменные окружения указывают на директорию проекта с `.claude/settings.json`:
- `CLAUDE_CONFIG_DIR` — глобальный конфиг
- `CLAUDE_PROJECT_DIR` — проектный конфиг (`.claude/settings.json` данного репо)

## Проверка

```bash
# Убедиться, что .claude/hooks/*.sh вызываются через PostToolUse при headless-запуске:
claude -p "echo test" 2>&1 | grep -i hook
```

## Применимость

Паттерн применим ко всем headless-сценариям на базе Claude CLI:
- Dispatcher'ы и overnight агенты (cron/launchd)
- Scheduled skill runs (extractor.sh inbox-check и т.п.)
- CI/CD pipeline шаги с `claude -p` (в свежей копии — см. оговорку о доверии к каталогу ниже)

## Различения

- **Headless без хуков (ошибочное допущение)** ≠ **headless с полным hook-слоем (реальность).** До этого наблюдения существовало предположение, что `claude -p` работает в «голом» режиме. Это не так.
- **Необходимое условие:** CLAUDE_PROJECT_DIR или CLAUDE_CONFIG_DIR должны быть правильно выставлены. Без этого хуки из `.claude/settings.json` не применяются.

## Оговорка: доверие к рабочему каталогу (дополнение 2026-11-18, РП-170)

Наблюдение выше сделано без учёта окна доверия к папке. Наследование слоя настроек проекта в недоверенном рабочем каталоге (свежая копия, которую фоновый Claude открывает впервые) не проверялось. В приёмочном прогоне 09.11.2026 автор прогона наблюдал, что в таком каталоге `permissions.allow` из `.claude/settings.json` не применялись (DP.SOTA.043, без изолирующего опыта). Срабатывают ли там хуки, не проверено. Пока это не выяснено, вывод «headless-агент наследует весь слой настроек проекта» распространять только на доверенные каталоги.
