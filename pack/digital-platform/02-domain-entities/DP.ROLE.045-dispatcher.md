---
id: DP.ROLE.045
name: Agent Task Dispatcher
type: role-description
status: draft
valid_from: 2026-05-17
summary: "Координатор очереди агентных задач IWE: читает inbox/agent/tasks/, запускает через подходящий канал (CCR / systemd / local), фиксирует lifecycle и audit-trail."
related:
  specializes: [U.RoleAssignment]
  component_of: [DP.ROLE.001]
  realizes: [DP.SC.135]
  uses:
    - DP.ROLE.039        # Peer Agent — sibling (peer может писать task для другого peer)
    - DP.ROLE.044        # Notification Dispatcher — уведомление пилота о P0-failed
    - DP.ROLE.072        # Разработчик-исполнитель — потребитель задач конвейера
    - DP.ROLE.071        # Ведущий разработчик — контроль WIP и приоритетов очереди
    - RemoteTrigger API  # claude.ai CCR-канал
    - inbox/agent/       # task/result хранилище
  downstream_consumers:
    - DP.ROLE.001 IWE Creator — пилот видит status pending tasks и забирает results
    - DP.ROLE.039 Peer Agent — peer ставит task для другого peer через тот же канал
    - DP.ROLE.072 Разработчик-исполнитель — получает задачи конвейера из очереди
    - Scout CCR — пишет findings + auto-promotes в tasks/ для P0
created: 2026-05-17
updated: 2026-06-09
wp: WP-324
---

# Agent Task Dispatcher — DP.ROLE.045

> # see DP.SC.135, DP.ROLE.045
>
> **Kind:** Coordinator Role — управляет очередью, не выполняет содержательную работу.
> **Owner Role:** IWE Platform — исполнитель: dispatcher CCR-рутина (claude.ai) + Scout sweeper.

---

## 1. Миссия

Гарантировать, что задача, поставленная агенту в `inbox/agent/tasks/`, запускается вовремя через подходящий канал, и что её результат фиксируется однозначно — в декларированной точке (`result_location`).

Аналогия: диспетчер таксопарка. Не везёт пассажиров, не выбирает маршрут — только сводит заказ с водителем, отслеживает выполнение, фиксирует факт доставки.

**Граница:** Dispatcher не разбирает содержание промпта, не выбирает branch для коммита, не интерпретирует acceptance. Все эти решения уже сделаны в task-файле (пилотом или предыдущим агентом).

---

## 2. Обязанности

| Обязанность | Как выполняется |
|-------------|----------------|
| Читать pending task'и | `git clone <governance-repo> --depth 50 && find inbox/agent/tasks -name '*.md'` |
| Парсить frontmatter | yq / python yaml parser |
| Фильтровать: `status: pending` AND `due ≤ now()` | python list comprehension |
| Сортировать по `priority` | P0 → P1 → P2 → P3 |
| Подставлять параметры в template | jinja2-like substitution `{{var}}` |
| Запускать через канал | `agent: ccr-opus` → `RemoteTrigger create`; `tsekh-systemd` → `ssh + systemd-run`; `local-launchd` → osascript |
| Записывать `trigger_id` + `status: assigned` | git Edit + commit + push |
| Проверять acceptance | acceptance-check скрипт (часть dispatcher impl) |
| Создавать result-файл | Write `RESULT-<task-id>.md` + git commit |
| При P0-failed — нотифицировать | `send_telegram_message` через DP.ROLE.044 |
| Архивировать >7 дней | Scout sweeper: `mv tasks/X.md archive/2026/` + соответствующий result |
| Cleanup stale assigned (>2h) | Scout sweeper: `status: assigned → pending` или `failed` |
| Распознать задачу конвейера | `wp: WP-4xx` OR `tags: [conveyor]` OR `tier_required: T4+` — парсинг frontmatter |
| Поставить в очередь команды | `status: pending → status: queued-for-team` — запись в task-файл |
| Уведомить команду | Ping в peer-status или Telegram через DP.ROLE.044 |

---

## 3. Входы / Выходы

**Входы (от потребителей):**
- `inbox/agent/tasks/TASK-*.md` — поставленные task'и (от пилота или peer-агента).

**Выходы:**
- `inbox/agent/tasks/TASK-*.md` — обновлённые frontmatter (status, trigger_id, completed_at).
- `inbox/agent/results/RESULT-*.md` — артефакты + audit-trail.
- `inbox/agent/archive/YYYY/` — закрытые task'и через 7 дней.
- `inbox/agent/scout/YYYY-MM-DD.md` — Scout findings (написаны Scout-агентом, dispatcher только координирует).
- Telegram сообщения пилоту (через DP.ROLE.044) при P0-failed.

**Артефакты в git:**

| Файл / папка | Что пишет |
|--------------|-----------|
| `inbox/agent/tasks/*.md` | Frontmatter updates (status, trigger_id) |
| `inbox/agent/results/RESULT-*.md` | Создание новых result-файлов |
| `inbox/agent/archive/YYYY/` | Move старых tasks+results |
| `inbox/agent/.dispatcher.lock` | Lock-файл (50 min TTL) |
| `inbox/agent/.dispatcher.log` | Краткий журнал циклов (ротация ежемесячно) |

---

## 4. Архитектура (слои)

```
Постановщики task'ов
├── DP.ROLE.001 IWE Creator (пилот)    ← Write tasks/TASK-*.md + git push
├── DP.ROLE.039 Peer Agent             ← через тот же канал (sibling)
└── Scout CCR (auto-promote P0)        ← Write tasks/TASK-*.md внутри своего цикла
        │
        ▼
DP.ROLE.045 Dispatcher
├── Reader        → git clone + parse frontmatter
├── Filter        → status==pending AND due<=now
├── Sorter        → by priority P0..P3
├── Template      → substitute {{vars}} from task body
├── Launcher      → switch by agent: → channel-specific call
│     ├── RemoteTrigger create (CCR)
│     ├── ssh + systemd-run (tsekh-1)
│     └── osascript + launchctl (local mac)
├── Watcher       → RemoteTrigger get for status
├── Acceptance    → проверить result_location
└── Archiver      → 7d → archive/YYYY/

Каналы выполнения
├── claude.ai CCR (RemoteTrigger)
├── tsekh-1 systemd (existing 13 timers)
└── local-launchd (1 plist)

Уведомления
└── DP.ROLE.044 Notification Dispatcher → Telegram (только P0-failed)
```

---

## 5. Ограничения (инварианты роли)

1. **Single source of truth — task-файл.** Dispatcher не хранит state отдельно. Один pull DS-my-strategy → полный recovery после рестарта.
2. **No fallback в выборе места.** `result_location` задан → агент пишет ровно туда, dispatcher проверяет ровно там. Если недоступно — failed, не silent push в другое место (root cause Ф1).
3. **Lock-based concurrency.** Два параллельных dispatcher не запускаются. Lock-файл с TTL 50 мин; при истечении — следующий dispatcher cleanup'ает и работает.
4. **No bash injection.** Dispatcher не выполняет произвольный bash из task body — только через template substitution + предусмотренный канал.
5. **Idempotency на task_id.** Повторный запуск dispatcher для уже `assigned` task — no-op (только проверяет trigger_id status, не создаёт новый).
6. **Push-to-queue, not assign.** Диспетчер ставит задачу конвейера в очередь команды (`queued-for-team`), не назначает конкретному разработчику. Конкретный разработчик берёт задачу сам (pull) или получает от Ведущего (DP.ROLE.071).
6. **Audit-trail обязателен.** Каждое изменение статуса = git commit с осмысленным message (`dispatch(WP-324): TASK-X pending→assigned via trig_NNNN`).

---

## 6. Связи с другими ролями

| Роль | Отношение |
|------|-----------|
| DP.ROLE.001 IWE Creator | Главный постановщик task'ов |
| DP.ROLE.039 Peer Agent | Sibling: peer-агент может писать task для другого peer через тот же канал; lock защищает от race |
| DP.ROLE.044 Notification Dispatcher | Потребитель Dispatcher'а: при P0-failed → send_telegram_message |
| DP.ROLE.053 Декомпозитор | Источник task'ов: при появлении новой РП open-loop ≥3h может предложить разбиение через template `task: artifactor-stages` |
| Навигатор (MIM.R.007) | Источник task'ов: может ставить «retro по неделе» через template `retro` |
| DP.ROLE.072 Разработчик-исполнитель | Потребитель задач конвейера — получает из очереди |
| DP.ROLE.071 Ведущий разработчик | Контроль WIP и приоритетов очереди команды |

---

## 7. Точки входа (интерфейсы)

### Постановка task'а (для постановщика)

```bash
# 1. Скопировать шаблон
cp inbox/agent/templates/analyze-section.md \
   inbox/agent/tasks/TASK-2026-05-17-analyze-section-11.md

# 2. Заполнить frontmatter и параметры

# 3. git push
git add inbox/agent/tasks/
git commit -m "task(WP-321): analyze section 11"
git push
```

### Dispatcher cycle (для dispatcher CCR)

```python
# Псевдокод
def dispatcher_cycle():
    if lock_held_within_50min(): return
    acquire_lock()
    try:
        repo = git_clone(governance_repo, depth=50)
        tasks = parse_tasks(repo / "inbox/agent/tasks/")

        # Этап 1: запустить pending+due
        for task in sorted(filter(is_pending_and_due, tasks), key=lambda t: t.priority):
            template = load_template(task.template)
            prompt = substitute(template, task.params)
            trigger_id = remote_trigger_create(prompt, agent=task.agent)
            task.trigger_id = trigger_id
            task.status = "assigned"
            git_commit_one_task(task)

        # Этап 2: проверить assigned
        for task in filter(is_assigned, tasks):
            trigger = remote_trigger_get(task.trigger_id)
            if trigger.ended_reason == "run_once_fired":
                ok = check_acceptance(task)
                task.status = "completed" if ok else "failed"
                write_result_file(task, trigger)
                if task.priority == "P0" and not ok:
                    notify_pilot_via_dp_role_044(task)
                git_commit_one_task(task)

        git_push()
    finally:
        release_lock()
```

### Watcher / Sweeper (Scout daily)

```python
# Запускается раз в день в составе Scout CCR
def sweep_stale_assigned(repo_path):
    for task in find_assigned(repo_path):
        if hours_since(task.assigned_at) > 2:
            # Trigger всё ещё в работе? Или CCR упала?
            trigger = remote_trigger_get(task.trigger_id)
            if trigger.ended_reason == "":  # ещё идёт
                continue
            elif trigger.ended_reason == "run_once_fired":
                # успешно отработал, но dispatcher не успел подобрать
                ok = check_acceptance(task)
                task.status = "completed" if ok else "failed"
            else:
                task.status = "pending"  # вернуть в очередь
```

---

## 8. Метрики

| Метрика | Норма | Где брать |
|---------|-------|-----------|
| Median lag (due → run start) | ≤30 мин | git log + RemoteTrigger metadata |
| % failed из общего | ≤10% | scan results/ |
| Pending count > 5 одновременно | редко (раз в неделю) | live count в результате dispatcher cycle |
| Stale assigned (>2h) | 0 после Scout sweeper | результат sweeper |
| Cost (USD/неделя) | < $30 для пилотной нагрузки | RemoteTrigger metadata aggregate |

---

## 9. Открытые вопросы (для пересмотра после первой недели)

1. **Throttle по cost.** При cost > N$/день — приоритет только P0. Где порог?
2. **Auto-archive >7d.** Достаточно ли 7 дней? Может, 14?
3. **Template versioning.** Если template меняется — старые task'и используют старый или новый? Сейчас — новый (substitute at dispatcher time). Возможен conflict.
4. **Peer-coordination.** Если два peer-агента одновременно пишут task на одну тему — нужна dedup-логика. Сейчас полагаемся на git merge.
