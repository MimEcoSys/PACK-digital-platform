---
id: DP.IWE.011-adapter-headless
name: Headless Adapter for IWE Host Contract
name_ru: Headless-адаптер (Agent Inbox как runtime)
type: adapter
parent: DP.IWE.011
contract_version: v0.1
status: active
created: 2026-05-21
entry_point: headless-runner.sh
---

# Headless-адаптер — реализация контракта DP.IWE.011 через Agent Inbox

> Документирует, как Agent Inbox (WP-324) + `iwe-agent-dispatcher.py` реализуют Host Contract v0.1.
> Хост: `IWE_RUNTIME=headless` — нет открытого Claude Code окна, нет интерактивного UI.
> Точка входа: `headless-runner.sh` — принимает протокол + задачу, устанавливает env, запускает `claude -p`.

---

## A. Tool API — маппинг инструментов

| Контракт (абстрактный) | Headless-реализация | Примечание |
|------------------------|---------------------|------------|
| `task_tracker.create(tasks[])` | N файлов `inbox/agent/tasks/TASK-<run>-NN.md` (один на шаг алгоритма, не один на весь прогон) + `status: pending` в frontmatter | Создаётся до запуска runner'а или внутри `claude -p` через `Write` |
| `task_tracker.update(id, status)` | Mid-session (агент отмечает свой шаг) — сам агент через нативный `Edit` правит frontmatter `TASK-<id>.md`. Внешний апдейт (не от текущей сессии) — `update_task_frontmatter()` в dispatcher | UUID = имя файла (TASK-<id>.md); single-writer-инвариант ниже |
| `task_tracker.list()` | `find_pending_tasks()` — сканирует `tasks/*.md` по `status: pending` | Используется dispatcher'ом перед вызовом claude |
| `scheduler.schedule_at(ts, msg)` | cron / systemd-timer (`*/30 * * * *` → `iwe-agent-dispatcher.py`) + `due:` поле в task frontmatter | `schedule_at` = записать task с `due: <timestamp>`, dispatcher возьмёт по расписанию |
| `fs.read(path)` | `Read` (нативный инструмент `claude -p`) | Без изменений |
| `fs.write(path, content)` | `Write` (нативный инструмент `claude -p`) | Без изменений |
| `fs.edit(path, old, new)` | `Edit` (нативный инструмент `claude -p`) | Без изменений |
| `shell.exec(cmd)` | `Bash` (нативный инструмент `claude -p`) | Без изменений |
| `agent.delegate(model, prompt)` | `Agent` (нативный инструмент `claude -p`) | В `claude -p` поддерживается |
| `skill.invoke(skill_id, args)` | `Skill` (нативный инструмент `claude -p`) | SKILL.md доступны если `$CLAUDE_CONFIG_DIR` указан |

**Ключевое отличие от CC-адаптера:**
- `task_tracker.*` — не эфемерный TodoWrite (в памяти процесса), а файловая система. Задачи персистентны между сессиями.
- `scheduler.schedule_at` — не `ScheduleWakeup` (не будит процесс), а `due:` поле + cron-цикл dispatcher'а.

**Single-writer-инвариант (пир-сессия WP-564, 11.09.2026, Claude+Codex).** Пока идёт headless-сессия (между `SESSION_START` и `SESSION_END` для данного `AGENT_SESSION_ID`), её TASK-файлы правит ТОЛЬКО сам агент (через `Edit`) — dispatcher не патчит их параллельно, а откладывает любой внешний апдейт (например, отмену задачи оператором) до `SESSION_END`. Без этого правила параллельная запись агента и dispatcher'а в один frontmatter теряет статус без блокировки/CAS (найдено при разборе, не проверено — CAS/lock сознательно не вводится в v0.1, это более дешёвый вариант той же гарантии).

**Commit-контракт «кто публикует файлы» (пир-сессия WP-564, 12.09.2026, Claude+Kimi+Codex).** Живой прогон Ф2 показал: агент реально способен создать N файлов (per строку `task_tracker.create` выше), но `iwe-agent-dispatcher.py` после `invoke_claude()` делает `git reset --hard origin/<branch>`, а финальный commit стейджит только `[task_path, result_path]` — всё, что агент создал сам и не закоммитил, оставалось untracked и терялось.

| Фаза | Кто публикует | Что коммитится | Инварианты |
|---|---|---|---|
| Reflex-переходы (`pending→assigned`, `reflex-skip`, `reflex bad exec-kind`, `reflex handler missing`, `reflex done`) | Dispatcher | Только `task_path` (+ `result_path`, если уже создан) | Никаких агентских артефактов не ожидается; расширенный staging здесь не нужен |
| LLM-выполнение — сторона агента | Агент (сам, внутри `claude -p`) | Все артефакты, которые он создаёт/меняет под `inbox/agent/tasks/` | Штатные шаблоны (`protocol-open.md`, `protocol-close.md`, `protocol-work.md`) УЖЕ содержат явный шаг `git add && git commit && git push` — это не новое требование для них |
| LLM-выполнение — safety-net dispatcher'а | Dispatcher | Только `.md` в `inbox/agent/tasks/` (кроме `task_path`/`result_path` и удалений) — **осознанно НЕ подхватывает не-`.md` артефакты** (например, лог-файл, который агент завёл в живом прогоне Ф2) | `_collect_extra_task_files()` (WP-564 Ф3) — directory-scope, БЕЗ фильтра по `id`/`task_id` (у внешней задачи и у файлов-шагов разные поля, фильтр по значению не работает); `git status --porcelain -z` (не обычный `--porcelain` — тот квотирует пути с пробелами/кириллицей в кавычки/octal-escape, построчный парсинг такие файлы молча терял бы, найдено ревью этой же пир-сессии). Опирается на строго последовательный `main()` (for-loop + `acquire_lock()`) — параллельная запись в эту директорию архитектурно исключена. Остаточный риск: untracked `.md` от прерванного предыдущего прогона в той же `tasks_dir` тоже будет подхвачен — это мусор в рабочей директории, не гонка |
| API-mode (`repo_dir=None`) | — | — | Агент физически не имеет доступа к репо; safety-net неприменим |

**Для НЕСТАНДАРТНЫХ `--task` (не через штатные шаблоны выше)** — если задание не наследует явный шаг git commit из шаблона, safety-net dispatcher'а остаётся единственной подстраховкой; тем не менее промпт такой задачи должен явно требовать от агента `git add/commit/push` своих файлов — safety-net не заменяет это требование, а покрывает случай, когда агент забыл его выполнить.

---

## B. Lifecycle Events — как headless генерирует события

В CC этапы работы агента = хуки (`PostToolUse`, `Stop`, `UserPromptSubmit`).
В headless те же хуки **работают** при `claude -p` — это ключевое свойство Claude CLI.

| Контракт (событие) | Headless-механизм | Хук | Payload |
|--------------------|-------------------|-----|---------|
| `SESSION_START` | `claude -p` вызывает `UserPromptSubmit` hook | `wakatime-heartbeat.sh` | session_id из `AGENT_SESSION_ID` (env) |
| `SESSION_END` | `claude -p` завершается → `Stop` hook | `wakatime-heartbeat.sh` + `agent-trace-recorder.sh` | duration, exit code |
| `TOOL_EXECUTED` | Каждый инструмент → `PostToolUse` hook | `agent-trace-recorder.sh` | tool_name, result (first 500 chars) |

**Важно:** хуки `.claude/hooks/*.sh` срабатывают при `claude -p` **так же**, как при интерактивном использовании. Это не нужно имитировать — оно работает из коробки.

---

## C. Environment Variables — headless-runner.sh устанавливает

`headless-runner.sh` устанавливает env перед вызовом `iwe-agent-dispatcher.py`:

| Переменная (контракт) | Headless-источник | Значение |
|----------------------|-------------------|---------|
| `IWE_RUNTIME` | Статически в `headless-runner.sh` | `"headless"` |
| `AGENT_SESSION_ID` | `date +%s%N \| md5 \| cut -c1-16` в runner'е | Генерируется при каждом вызове |
| `AGENT_TASK_ID` | Из `--task` аргумента runner'а (или auto из pending) | Имя файла TASK-*.md без расширения |
| `AGENT_MODEL_ID` | `--model` аргумент runner'а (дефолт: `sonnet`) | `claude-sonnet-4-6` |
| `IWE_STATE_DIR` | Из env или дефолт: `~/.iwe/state/` | Создаётся автоматически |
| `CLAUDE_TASK_ID` | Alias = `AGENT_TASK_ID` для CC-совместимости | Нужен для `agent-trace-recorder.sh` |

**Запись session env:** runner записывает `~/.iwe/state/current-session.env` (тот же формат, что CC-адаптер) — для совместимости с хуками.

---

## D. Конфигурация скиллов в headless

Скиллы доступны при `claude -p` если:
1. `CLAUDE_CONFIG_DIR` указывает на директорию с `.claude/skills/` (дефолт: `~/.claude`)
2. Агент вызывает `Skill` инструмент по имени

Для IWE-протоколов через headless:
- `open` → задача с шаблоном `protocol-open` из `inbox/agent/templates/protocol-open.md`
- `close` → задача с шаблоном `protocol-close`
- произвольный скилл → `skill.invoke(id)` внутри `claude -p` сессии

---

## E. Покрытие HIGH-зависимостей из Ж-Ф1

| # | Зависимость CC | Headless-эквивалент | Статус |
|---|---------------|---------------------|--------|
| 1 | `TodoWrite` | `tasks/TASK-*.md` файловая система | ✅ Покрыто |
| 2 | `ScheduleWakeup` | `due:` в frontmatter + cron dispatcher | ✅ Покрыто |
| 3 | `Read/Edit/Write` | Нативные инструменты `claude -p` | ✅ Без изменений |
| 4 | `Bash` | Нативный инструмент `claude -p` | ✅ Без изменений |
| 5 | `PostToolUse/Stop` хуки | Те же хуки срабатывают при `claude -p` | ✅ Без изменений |
| 6 | `Agent/Skill` инструменты | Нативные в `claude -p` | ✅ Без изменений |

**Вывод:** все 6 HIGH-зависимостей покрыты без изменения хуков или протоколов.

---

## Известные отклонения от контракта

| Компонент | Контракт требует | Headless реализует | Статус |
|-----------|-----------------|-------------------|--------|
| `task_tracker.list()` realtime | Список задач в текущем контексте агента | Файловый скан до запуска claude | ⚠️ Pre-session только |
| `task_tracker.update()` из агента | Агент обновляет task mid-session | Агент сам правит frontmatter через `Edit`/`Write` (single-writer-инвариант выше) | ✅ Подтверждено живым прогоном (WP-564 Ф2, 12.09) — агент реально создал 4 файла-шага; ✅ фикс потери файлов перед коммитом (WP-564 Ф3, см. «Commit-контракт» выше) |
| Interactive clarification | Агент может задать вопрос пользователю | Нет UI — вопросы без ответа | ⚠️ Задачи должны быть самодостаточны |
| Real-time output | Пользователь видит вывод в интерфейсе | Всё в RESULT-*.md post-factum | ⚠️ Асинхронный результат |

Отклонения приемлемы для автономных задач (Agent Inbox design intent).
