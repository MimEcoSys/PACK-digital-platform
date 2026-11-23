---
id: DP.SC.135
name: Agent Inbox — конвейер агентных задач IWE
type: sc
status: draft
layer: L2-Platform
summary: "Создатель IWE ставит задачу агенту в единое место и получает результат в декларированной точке не позднее чем через 1 час после due"
consumer: DP.ROLE.001  # IWE Creator
created: 2026-05-17
updated: 2026-05-17
wp: WP-324
related:
  realizes: []
  uses:
    - DP.ROLE.045   # Dispatcher
    - DP.ROLE.044   # Почтальон (для уведомлений о failed P0)
    - DP.ROLE.039   # Peer Agent (sibling-постановщик task'ов)
  extends: []
---

# DP.SC.135 — Agent Inbox

## Правило (инвариант)

- [ ] Каждая task в финальном статусе (completed / failed / blocked) имеет соответствующий result-файл в `inbox/agent/results/`.
- [ ] Task'и в статусе `assigned` старше 2 часов автоматически возвращаются Scout sweeper'ом в `pending` (или помечаются failed).
- [ ] `result_location` task'а — единственная точка истины: агенту запрещено создавать результат в другом месте через fallback. Несоответствие = `status: failed`.
- [ ] Промпт task'а исполняется только через предусмотренный template (никакого произвольного bash).

## Обещание

**Кому:** DP.ROLE.001 Создатель IWE (пилот платформы).

**Зачем:** Делегировать асинхронные/отложенные задачи (анализ материала, разведка медленных источников, soak-verify, weekly evolution) без удержания их в работающей сессии. Видеть в одном месте, что висит на агенте и что уже сделано.

**Что получит:**
1. Задача из `inbox/agent/tasks/*.md` со `status: pending` будет запущена через подходящий канал (CCR / systemd / local) не позднее 1 часа после `due`.
2. Результат окажется ровно в `result_location` (repo + branch + path).
3. Аудит-трейл в `inbox/agent/results/RESULT-<task-id>.md`: время старта, модель, стоимость, ссылка на артефакт, ошибки.

**Триггер:**
- Появление в git нового `tasks/*.md` со `status: pending` и наступление `due`.
- Periodic dispatcher cycle (часовой).

**Время отклика:** ≤1 час после `due`.

**Режим отказа:**
- Dispatcher CCR недоступна → задачи накапливаются в `pending`, следующий запуск подхватит. Через 24h без запуска dispatcher → уведомление пилоту через DP.ROLE.044 (Почтальон).
- `result_location` недоступен → `status: failed` с причиной; артефакт встроен в result-файл как fallback (не теряется).
- RemoteTrigger create вернул ошибку → retry 3× через час; после 3 неудач → `status: failed` с причиной.
- Task >5 одновременно pending → запускаются top-N по `priority` (P0 → P1 → P2 → P3), остальные ждут следующего цикла.

## Свидетельства (критерий приёмки)

**Данные:**

| Критерий | Как проверить |
|----------|--------------|
| `inbox/agent/` структура существует с подкаталогами tasks/results/scout/templates/archive | `test -d <repo>/inbox/agent/tasks && test -d ...` |
| Dispatcher CCR-рутина зарегистрирована и `enabled: true` | `RemoteTrigger list \| jq '.data[] \| select(.name == "WP-324 Agent Inbox Dispatcher")'` |
| Для каждой task в `completed/failed/blocked` существует result-файл | `for f in tasks/*.md; do id=$(yq .id $f); test -f results/RESULT-$id.md \|\| echo MISSING; done` |
| Артефакт в `result_location` совпадает с задекларированным path | acceptance-check внутри dispatcher (часть алгоритма) |

**Контекст:**

| Условие | Проверка |
|---------|---------|
| Пилот имеет git-доступ к governance-репо | `git push DS-my-strategy` от имени пилота работает |
| RemoteTrigger API доступна | `RemoteTrigger list` HTTP 200 |
| Шаблон task.template существует в templates/ | `test -f inbox/agent/templates/<template>.md` |

**Полномочия:**

| Роль | Что подтверждает |
|------|-----------------|
| DP.ROLE.045 Dispatcher | Что task запущена / завершена / зафиксирован статус |
| DP.ROLE.001 IWE Creator | Что промпт корректно сформулирован и acceptance применим |
| Git commit history | Что лента событий (создание → status changes → archive) сохранена |

**Свидетельства:**

| Свидетельство | Источник |
|--------------|---------|
| RESULT-файл с completed_at | `inbox/agent/results/RESULT-*.md` |
| Артефакт в декларированном repo+branch+path | внешний репозиторий (например, DS-principles-curriculum) |
| Audit-trail в archive/YYYY/ | `inbox/agent/archive/YYYY/{tasks,results}/` после move |

## Реализующие сервисы (MAP.002)

| Сервис | Роль | Триггер |
|--------|------|---------|
| S?? Dispatcher CCR (WP-324) | DP.ROLE.045 | ⏰ cron 0 * * * * |
| S?? Scout CCR + sweeper (WP-324) | DP.ROLE.045 | ⏰ cron 0 4 * * * |
| `inbox/agent/` (governance-репо) | артефакт-хранилище | 👤 пилот / dispatcher |

## Пользовательский путь

| # | Шаг | Кто | Сервис |
|---|-----|-----|--------|
| 1 | Создать task-файл из шаблона | DP.ROLE.001 (пилот) | git Write + push |
| 2 | Зафиксировать в git | DP.ROLE.001 | git commit |
| 3 | Подхватить task'и `pending+due` | DP.ROLE.045 (Dispatcher) | Dispatcher CCR cycle |
| 4 | Запустить агента через канал | DP.ROLE.045 | RemoteTrigger / SSH / launchd |
| 5 | Записать `trigger_id`, `status: assigned` | DP.ROLE.045 | git commit |
| 6 | Дождаться `run_once_fired` | агент | внешний канал |
| 7 | Проверить acceptance | DP.ROLE.045 | acceptance-check |
| 8 | Записать result-файл, `status: completed/failed` | DP.ROLE.045 | git commit |
| 9 | При P0-failed — уведомить пилота | DP.ROLE.045 → DP.ROLE.044 | Telegram |
| 10 | Архивировать через 7 дней | DP.ROLE.045 (Scout sweeper) | mv в archive/YYYY/ |

## Связь с другими обещаниями

- Потребляет: **DP.SC.134** (Доставка отправления адресату — для уведомлений о P0-failed)
- Используется в: **DP.SC.020** (Онбординг через бот — будущая интеграция: бот может ставить task для пользователя), **DP.SC.116** (Уведомления и nudges — overlap по транспорту)
- Sibling: **DP.SC.131** (Бэкап-процесс — другой паттерн scheduled-агента, переиспользует systemd, не Agent Inbox)
