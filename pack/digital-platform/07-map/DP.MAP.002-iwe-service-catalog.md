---
id: DP.MAP.002
name: IWE Service Catalog
type: map
status: draft
summary: "Кросс-системный каталог всех сервисов IWE: сервис → роль → вход → выход → потребитель → исполнитель → триггер"
created: 2026-02-23
updated: 2026-02-23
related:
  uses: [DP.ROLE.001, DP.D.033, DP.ARCH.001]
  extends: [DP.MAP.001]
---

# [DP.MAP.002] IWE Service Catalog
<!-- index-health: skip -->
<!-- Pack service-catalog. Плоская таблица (сервис × 7 атрибутов) — длинные
     строки = ячейки-списки с метаданными. Форма подчинена доменной модели. -->

> **Назначение:** Единая плоская таблица всех описаний методов (MethodDescription) IWE.
> Каждая строка = одно описание метода: интерфейс (вход → выход) + роль + исполнитель + триггер.
> Первичный ключ — имя. Все ссылки ведут на source-of-truth.
>
> **Терминология (FPF A.3.2):**
> Точный термин: **описание метода** (U.MethodDescription) — спецификация «как делать».
> Житейские имена: «процесс», «сервис» — полисемичны (FPF L-PROC, L-SERV):
>
> | Житейское слово | В этой таблице значит | Но может значить и |
> |-----------------|----------------------|--------------------|
> | «процесс» | Описание метода (рецепт/SOP) | Работу (что произошло) или абстрактный Метод |
> | «сервис» | Описание метода (точка входа) | Обещание потребителю или систему-исполнителя |
>
> При чтении этой таблицы «процесс» и «сервис» = описание метода. В других контекстах — уточняй.
>
> **Правило:** Данные описываются ТАМ, ГДЕ рождаются (method card / role description).
> Эта карта — навигация, не source-of-truth данных.

## Условные обозначения

| Символ | Значение |
|--------|----------|
| ⏰ | По расписанию (cron / scheduler) |
| ⚡ | По событию (event-driven) |
| 👤 | По запросу пользователя (on-demand) |

## Ссылки на source-of-truth

| Ресурс | Путь |
|--------|------|
| Каталог ролей | [DP.ROLE.001 §3.2](../02-domain-entities/DP.ROLE.001-platform-roles.md#32-каталог-ролей-платформы) |
| Реестр исполнителей | [DP.ROLE.001 §3.1](../02-domain-entities/DP.ROLE.001-platform-roles.md#31-реестр-исполнителей) |
| PROCESSES: Стратег | [strategist/PROCESSES.md](../../../../DS-IT-systems/DS-ai-systems/strategist/PROCESSES.md) |
| PROCESSES: Экстрактор | [extractor/PROCESSES.md](../../../../DS-IT-systems/DS-ai-systems/extractor/PROCESSES.md) |
| PROCESSES: Синхронизатор | [synchronizer/PROCESSES.md](../../../../DS-IT-systems/DS-ai-systems/synchronizer/PROCESSES.md) |
| PROCESSES: Шаблонизатор | [setup/PROCESSES.md](../../../../DS-IT-systems/DS-ai-systems/setup/PROCESSES.md) |
| PROCESSES: Бот | [aist_bot/PROCESSES.md](../../../../DS-IT-systems/aist_bot_newarchitecture/PROCESSES.md) |
| Сценарии Стратега | [DP.ROLE.012/scenarios/](../02-domain-entities/DP.ROLE.012-strategist/scenarios/) |

---

## Каталог сервисов

| # | Сервис | [Роль](../02-domain-entities/DP.ROLE.001-platform-roles.md#32-каталог-ролей-платформы) | Вход | Выход (РП) | Кому | [Исполнитель](../02-domain-entities/DP.ROLE.001-platform-roles.md#31-реестр-исполнителей) | Триггер | Реализация |
|---|--------|------|------|------------|------|-------------|---------|------------|
| S01 | **Day Plan** | [R1 Стратег](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | WeekPlan, fleeting-notes, вчерашний DayPlan, коммиты | DayPlan | R14 Заказчик, R20 Рецензент | A1 Claude → [strategist.sh](../../../../DS-IT-systems/DS-ai-systems/strategist/scripts/strategist.sh) | ⏰ ежедн 04:00 | [PROCESSES](../../../../DS-IT-systems/DS-ai-systems/strategist/PROCESSES.md) |
| S02 | **Session Prep** | [R1 Стратег](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | WeekPlan (с итогами W{N-1}), inbox, MAPSTRATEGIC всех систем | WeekPlan (draft) | R14 Заказчик | A1 Claude → strategist.sh | ⏰ Пн 04:00 | [PROCESSES](../../../../DS-IT-systems/DS-ai-systems/strategist/PROCESSES.md) |
| S03 | **Week Review** | [R1 Стратег](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | Коммиты за неделю, DayPlans, WeekPlan | Секция «Итоги W{N}» в WeekPlan + пост итогов | R21 Публикатор постов клуба, R14 Заказчик | A1 Claude → strategist.sh | ⏰ Пн 00:00 | [PROCESSES](../../../../DS-IT-systems/DS-ai-systems/strategist/PROCESSES.md) |
| S04 | **Note Review** | [R1 Стратег](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | [fleeting-notes.md](../../../../DS-my-strategy/inbox/fleeting-notes.md), [captures.md](../../../../DS-my-strategy/inbox/captures.md) | Notes-Archive, WP-proposals, captures | R1 (session-prep) | A1 Claude → strategist.sh | ⏰ ежедн 23:00 | [PROCESSES](../../../../DS-IT-systems/DS-ai-systems/strategist/PROCESSES.md) |
| S05 | **Evening Review** | [R1 Стратег](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | DayPlan, коммиты за сегодня | Итог дня, carry-over | R14 Заказчик | A1 Claude (CLI) | 👤 по запросу | [SC.05](../02-domain-entities/DP.ROLE.012-strategist/scenarios/on-demand/) |
| S06 | **Check Plan** | [R1 Стратег](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | Текущая задача, WeekPlan/DayPlan | in-plan / aligned / unplanned | R14 Заказчик | A1 Claude (CLI) | 👤 по запросу | [SC.06](../02-domain-entities/DP.ROLE.012-strategist/scenarios/on-demand/) |
| S07 | **Update Priorities** | [R1 Стратег](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | Изменение приоритетов | Обновлённый Week/DayPlan | R14 Заказчик | A1 Claude (CLI) | 👤 по запросу | [SC.07](../02-domain-entities/DP.ROLE.012-strategist/scenarios/on-demand/) |
| S08 | **Add Workproduct** | [R1 Стратег](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | Описание нового РП | Строка в WeekPlan | R14 Заказчик | A1 Claude (CLI) | 👤 по запросу | [SC.08](../02-domain-entities/DP.ROLE.012-strategist/scenarios/on-demand/) |
| S09 | **Knowledge Extraction** | [R2 Экстрактор](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | captures.md, сессионные артефакты | Pack-сущности (M/D/FM/WP/SOTA) | Pack-репо | A1 Claude → [extractor.sh](../../../../DS-IT-systems/DS-ai-systems/extractor/scripts/extractor.sh) | ⏰ ежедн 04:00 / 👤 close | [PROCESSES](../../../../DS-IT-systems/DS-ai-systems/extractor/PROCESSES.md) |
| S10 | **Inbox Check** | [R2 Экстрактор](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | captures.md, fleeting-notes.md | Классификация + маршрутизация | R1 Стратег, Pack-репо | A1 Claude (CLI) | 👤 по запросу | [PROCESSES](../../../../DS-IT-systems/DS-ai-systems/extractor/PROCESSES.md) |
| S11 | **Ontology Sync** | [R2 Экстрактор](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | Pack entities | Обновлённая онтология (SPF.SPEC.002) | I4 knowledge-mcp | A1 Claude (CLI) | 👤 по запросу | [PROCESSES](../../../../DS-IT-systems/DS-ai-systems/extractor/PROCESSES.md) |
| S12 | **Q&A** | [R3 Консультант](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | Вопрос ученика + knowledge-mcp + DT | Ответ (TG message) | R16 Ученик | A1 Haiku → I1 Bot | ⚡ вопрос ученика | [PROCESSES](../../../../DS-IT-systems/aist_bot_newarchitecture/PROCESSES.md) |
| S13 | **DZ-Check** | [R3 Консультант](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | ДЗ ученика + эталон + DT | Оценка + обратная связь | R16 Ученик | A1 Haiku → I1 Bot | ⚡ ДЗ отправлено | [PROCESSES](../../../../DS-IT-systems/aist_bot_newarchitecture/PROCESSES.md) |
| S14 | **Content Pre-Gen** | [R3 Консультант](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | Расписание + knowledge-mcp | Pre-gen cache | R3 (для доставки) | A1 Haiku → I1 Bot | ⏰ scheduler (за 3ч) | [PROCESSES](../../../../DS-IT-systems/aist_bot_newarchitecture/PROCESSES.md) |
| S15 | **Feed Delivery** | [R3 Консультант](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | Pre-gen cache + user tier | TG сообщение ленты | R16 Ученик | I1 Bot | ⏰ scheduler | [PROCESSES](../../../../DS-IT-systems/aist_bot_newarchitecture/PROCESSES.md) |
| S16 | **Marathon Step** | [R3 Консультант](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | Marathon config + DT | TG сообщение марафона | R16 Ученик | I1 Bot | ⏰ scheduler | [PROCESSES](../../../../DS-IT-systems/aist_bot_newarchitecture/PROCESSES.md) |
| S17 | **Scheduler Dispatch** | [R8 Синхронизатор](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | Текущее время + конфигурация | Запуск агентов | R1/R2/R8/R9/R10/R21 | I5 launchd → [scheduler.sh](../../../../DS-IT-systems/DS-ai-systems/synchronizer/scripts/scheduler.sh) | ⏰ 10x/день | [PROCESSES](../../../../DS-IT-systems/DS-ai-systems/synchronizer/PROCESSES.md) |
| S18 | **Code Scan** | [R8 Синхронизатор](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | git repos (коммиты за 24ч) | TG notification + report | R14 Заказчик | I2 bash → [code-scan.sh](../../../../DS-IT-systems/DS-ai-systems/synchronizer/scripts/code-scan.sh) | ⏰ ежедн 04:00 | [PROCESSES](../../../../DS-IT-systems/DS-ai-systems/synchronizer/PROCESSES.md) |
| S19 | **Pack Projection** | [R8 Синхронизатор](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | Pack frontmatter | CQRS YAML projection | I4 knowledge-mcp | I2 bash → [pack-project.sh](../../../../DS-IT-systems/DS-ai-systems/synchronizer/scripts/pack-project.sh) | ⏰ после S18 | [PROCESSES](../../../../DS-IT-systems/DS-ai-systems/synchronizer/PROCESSES.md) |
| S20 | **Consistency Check** | [R8 Синхронизатор](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | Pack repos, downstream repos | Consistency report | R5 Архитектор | I2 bash / A1 Claude | 👤 по запросу | [PROCESSES](../../../../DS-IT-systems/DS-ai-systems/synchronizer/PROCESSES.md) |
| S21 | **Unsatisfied Report** | [R8 Синхронизатор](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | feedback_triage DB | [feedback-triage/YYYY-MM-DD.md](../../../../DS-agent-workspace/scheduler/feedback-triage/) | R7 Триажёр | I2 bash | ⏰ ежедн | [PROCESSES](../../../../DS-IT-systems/DS-ai-systems/synchronizer/PROCESSES.md) |
| S22 | **Fleeting Notes Sync** | [R8 Синхронизатор](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | TG saved messages (файл) | [fleeting-notes.md](../../../../DS-my-strategy/inbox/fleeting-notes.md) | R1 (note-review) | I5 launchd → fswatch | ⏰ каждые 2 мин | [PROCESSES](../../../../DS-IT-systems/DS-ai-systems/synchronizer/PROCESSES.md) |
| S23 | **Template Sync** | [R9 Шаблонизатор](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | Platform files (CLAUDE.md, prompts, memory/) | [FMT-exocortex-template](../../../../FMT-exocortex-template/) | R14 Заказчик (шаблон) | I3 bash → [template-sync.sh](../../../../DS-IT-systems/DS-ai-systems/setup/scripts/template-sync.sh) | ⏰ ежедн 04:00 | [PROCESSES](../../../../DS-IT-systems/DS-ai-systems/setup/PROCESSES.md) |
| S24 | **Template Validation** | [R9 Шаблонизатор](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | FMT-exocortex-template | Pass/Fail report | R9 Шаблонизатор | I3 bash → [validate-template.sh](../../../../DS-IT-systems/DS-ai-systems/setup/scripts/validate-template.sh) | ⏰ после S23 | [PROCESSES](../../../../DS-IT-systems/DS-ai-systems/setup/PROCESSES.md) |
| S25 | **Daily Scan** | [R21 Публикатор постов клуба](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | [DS-Knowledge-Index/docs/](../../../../DS-Knowledge-Index-Tseren/docs/) (status=ready) | Расписание публикаций | R14 Заказчик | I9 → scheduler | ⏰ ежедн 03:00 | [PROCESSES](../../../../DS-IT-systems/aist_bot_newarchitecture/PROCESSES.md) |
| S26 | **Scheduled Publish** | [R21 Публикатор постов клуба](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | scheduled_publications DB | Discourse topic + frontmatter update | systemsworld.club, R14 | I1 Bot → Discourse API | ⏰ */30 мин | [PROCESSES](../../../../DS-IT-systems/aist_bot_newarchitecture/PROCESSES.md) |
| S27 | **Manual Publish** | [R21 Публикатор постов клуба](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | Команда /club publish | Discourse topic + новый график | R14 Заказчик | I1 Bot | 👤 команда | [PROCESSES](../../../../DS-IT-systems/aist_bot_newarchitecture/PROCESSES.md) |
| S28 | **Comment Check** | [R21 Публикатор постов клуба](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | published_posts DB | TG notification о комментарии | R14 Заказчик | I1 Bot | ⏰ */15 мин | [PROCESSES](../../../../DS-IT-systems/aist_bot_newarchitecture/PROCESSES.md) |
| S29 | **Auto-Triage** | [R7 Триажёр](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | helpful=false / user_comment | feedback_triage DB + TG alert | R14 (alert), R7 (review) | Haiku → I1 Bot | ⚡ unhelpful feedback | [PROCESSES](../../../../DS-IT-systems/aist_bot_newarchitecture/PROCESSES.md) |
| S30 | **Triage Session** | [R7 Триажёр](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | feedback_triage DB + inbox | Приоритизированный backlog | R6 Кодировщик, R14 | A1 Claude (CLI) | 👤 сессия техдолга | [PROCESSES](../../../../DS-IT-systems/aist_bot_newarchitecture/PROCESSES.md) |
| S31 | **L1 Unstick** | [R11 Наладчик бота](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | Зависший пользователь (FSM timeout) | FSM reset | R16 Ученик | I1 Bot | ⚡ timeout event | [PROCESSES](../../../../DS-IT-systems/aist_bot_newarchitecture/PROCESSES.md) |
| S32 | **L2 Auto-Fix** | [R11 Наладчик бота](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | Повторяющаяся ошибка (error_logs) | Автоматический fix | R11 Наладчик бота | I7 → I1 Bot | ⚡ error pattern | [PROCESSES](../../../../DS-IT-systems/aist_bot_newarchitecture/PROCESSES.md) |
| S33 | **L3 Restart** | [R11 Наладчик бота](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | Критическая ошибка | Service restart | R11 Наладчик бота | I7 bash | ⚡ health check fail | [PROCESSES](../../../../DS-IT-systems/aist_bot_newarchitecture/PROCESSES.md) |
| S34 | **L4 Escalate** | [R11 Наладчик бота](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | Нерешаемая ошибка | GitHub Issue | R6 Кодировщик | A1 Claude → I7 | ⚡ L2 failed 3x | [PROCESSES](../../../../DS-IT-systems/aist_bot_newarchitecture/PROCESSES.md) |
| S35 | **Metrics Collection** | [R10 Статистик](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | qa_history, user_profiles, feedback_triage | Агрегированные метрики | R10 (report) | I6 bash | ⏰ ежедн | — |
| S36 | **Analytics Report** | [R10 Статистик](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | Метрики, тренды | /analytics response | R14 Заказчик | I6 → A1 Claude | 👤 /analytics | — |
| S37 | **Bloom Eval** | [R12 Оценщик](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | Ответ ученика + эталон | Bloom-оценка (inline) | R3 Консультант | I8 → I1 Bot | ⚡ каждый ответ | [PROCESSES](../../../../DS-IT-systems/aist_bot_newarchitecture/PROCESSES.md) |
| S38 | **WP Validation** | [R12 Оценщик](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | Pack entity draft | Валидация по SPF | R2 Экстрактор | A1 Claude | 👤 по запросу | — |
| S39 | **Fleeting Note** | [R18 Автор заметок](../02-domain-entities/DP.ROLE.001-platform-roles.md#роли-пользователя-a2--7-ролей) | Мысль / наблюдение | .заметка → fleeting-notes.md | R1 (note-review) | R18 (A2 человек) | 👤 когда угодно | — |
| S40 | **Capture-to-Pack** | [R14 Заказчик](../02-domain-entities/DP.ROLE.001-platform-roles.md#роли-пользователя-a2--7-ролей) | Паттерн / различение / метод | Capture: X → Y | R2 Экстрактор | R14 + A1 Claude | 👤 на рубеже | — |
| S41 | **Strategy Session** | [R17 Стратег-интерактив](../02-domain-entities/DP.ROLE.001-platform-roles.md#роли-пользователя-a2--7-ролей) | Вопрос / неудовлетворённость | Решение, обновлённый план | R1 Стратег | R17 + A1 Claude (CLI) | 👤 по запросу | — |
| S42 | **Morning Check** | [R14 Заказчик](../02-domain-entities/DP.ROLE.001-platform-roles.md#роли-пользователя-a2--7-ролей) | Логи, артефакты за ночь | Статус ночных сервисов | R14 Заказчик | R14 + A1 Claude (CLI) | 👤 ежедн утро | — |
| S43 | **Time Tracking** | [R10 Статистик](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | Активность в VS Code (файлы, проекты, языки, ветки) | Дашборд + API метрик (время по проектам/языкам/файлам) | R1 Стратег (week review), R14 Заказчик | I10 WakaTime (SaaS + VS Code extension) | ⏰ непрерывно (фоновый) | [wakatime.com](https://wakatime.com) |
| S44 | **Calendar View** | [R1 Стратег](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | Google Calendar events (primary) | Таблица событий дня + свободные слоты (в DayPlan) | R14 Заказчик | A1 Claude (CLI) → I11 Google Calendar MCP | 👤 Day Open (шаг 4c) | [protocol-open.md §4c](../../../../../memory/protocol-open.md) |
| S45 | **Create Calendar Event** | [R1 Стратег](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | Описание события от пользователя | Google Calendar event | R14 Заказчик | A1 Claude (CLI) → I11 Google Calendar MCP | 👤 по запросу | [protocol-open.md §4c](../../../../../memory/protocol-open.md) |
| S46 | **Content Adaptation** | [R4 Автор](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | Согласованная club-версия поста | Адаптации для соцсетей (facebook, linkedin, telegram, tenchat, x, youtube) | R14 Заказчик | A1 Claude (CLI) | 👤 после согласования club | [PROCESSES](../../../../DS-Knowledge-Index-Tseren/PROCESSES.md) |
| S47 | **Multi-Channel Publish** | [R21 Публикатор постов клуба](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | Адаптация с status=ready + target={channel} | Пост в соцсети + frontmatter update (status→published) | Внешняя аудитория, R14 Заказчик | I? Publisher script → API каналов | 👤 `/publish {channel}` / ⏰ расписание | [PROCESSES](../../../../DS-Knowledge-Index-Tseren/PROCESSES.md) |
| S48 | **Practicum Messages Upload** | [R4 Автор](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | markdown-файлы сообщений (ss/ms-messages.md) | Шаблон сообщений в LMS Aisystant | R16 Ученик (через LMS) | I2 bash → [upload-to-lms.py](../../../../DS-ecosystem-development/A.Systems-Builder/A2.Systems-Builder/A2.3.Operations/Practicum-Messages/upload-to-lms.py) | 👤 по запросу | [README](../../../../DS-ecosystem-development/A.Systems-Builder/A2.Systems-Builder/A2.3.Operations/Practicum-Messages/README.md) |
| S49 | **Downstream Sync** | [R8 Синхронизатор](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | Changed Pack repos (git diff / коммиты за 24ч) | Синхронизированные downstream (reindex + projection + template) | R5 Архитектор, I4 knowledge-mcp | I2 bash → [update.sh](../../../../DS-IT-systems/DS-ai-systems/synchronizer/scripts/update.sh) | ⏰ ежедн 00:05 / 👤 Day Close | [PROCESSES](../../../../DS-IT-systems/DS-ai-systems/synchronizer/PROCESSES.md) |
| S50 | **Template Update** | [R9 Шаблонизатор](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | update-manifest.json (GitHub) + локальные файлы | Обновлённые платформенные файлы (CLAUDE.md, memory/, roles/, skills/) | R14 Заказчик | I2 bash → [update.sh](../../../../FMT-exocortex-template/update.sh) | 👤 `bash update.sh` | [PROCESSES](../../../../DS-IT-systems/DS-ai-systems/setup/PROCESSES.md) |
| S61 | **Cloud Scheduler** | [R8 Синхронизатор](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | Расписание + конфиг (day-rhythm-config.yaml) | Запуск задач (reindex, sync, backup, strategist) | R14 Заказчик | GitHub Actions (базовый) / VPS + Claude Agent SDK (продвинутый) | ⏰ cron (11x/день) | [DP.SC.019](../08-service-clauses/DP.SC.019-autonomous-cloud-runtime.md) |
| S62 | **IWE Telegram Gateway** | [R8 Синхронизатор](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | Telegram-команда (/plan, /note, /status) | Ответ (DayPlan, статус, подтверждение заметки) | R14 Заказчик | I1 Bot (Python, Railway) | ⚡ Telegram-команда | [DP.SC.019](../08-service-clauses/DP.SC.019-autonomous-cloud-runtime.md) |
| S51 | **Principles Training** | [R3 Консультант](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | Принцип + текущая глубина + cognitive level | Задание + ИИ-оценка ответа + прогресс (depth) | R16 Ученик | A1 Sonnet → I1 Bot | 👤 `/train` | [PROCESSES](../../../../DS-IT-systems/aist_bot_newarchitecture/PROCESSES.md) |
| S52 | **DT Profile Calculation** | [Профилировщик (DP.ROLE.116)](../02-domain-entities/DP.ROLE.116-profiler.md) | 2_collected (engagement), learning_history (BKT) | 3_derived в digital_twins (ступень, mastery, gaps, агентность) | digital-twin-mcp, tailor-mcp, R22 Оркестратор, R27 Портной | I11 Профилировщик (Python) | ⏰ 04:30 MSK / ⚡ learning event | [system.yaml](../../../../DS-IT-systems/DS-ai-systems/profiler/system.yaml) |
| S60 | **HW-Discussion** | [R3 Консультант](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | Замечание проверки + норматив + вопрос ученика | Разъяснение по замечанию (TG message) | R16 Ученик | A1 Haiku → I1 Bot | ⚡ вопрос по замечанию | — |
| S63 | **Billing Service** | Биллинг (описания роли нет) | Платёж (YooKassa/Stripe/Монета/Stars webhook) | Подтверждённая оплата + доступ | R16 Участник, R15 Бухгалтер | I1 Bot (Billing Module) + Aisystant LMS | ⚡ webhook от платёжного провайдера | handlers/showcase.py, handlers/workshop.py, [SC.112](../08-service-clauses/DP.SC.112-subscription-billing.md) |
| S64 | **CRM Panel** | CRM-менеджер (описания роли нет) | Оплаты из единого реестра (`bot_data`): Aisystant PG через cron, бот напрямую; ручной ввод (канал 8) — не работает, 403, см. WP-183 | Отчёты, выгрузки, ручные оплаты | R15 Бухгалтер, R23 Маркетолог, R19 Декан, R16 Преподаватели | Directus (Railway) | 👤 запрос менеджера | WP-183, [SC.114](../08-service-clauses/DP.SC.114-crm.md) |
| S65 | **Access Manager** | [R6 Кодировщик](../02-domain-entities/DP.ROLE.001-platform-roles.md#функциональные-роли-grade-0-со-смешанными-сценариями) | Подтверждённая оплата / подписка | Invite-ссылка в чат / одобрение заявки / кик неоплативших | R16 Участник | I1 Bot (workshop.py, showcase.py) | ⚡ оплата или ⏰ cron (маршрутка) | handlers/workshop.py, handlers/showcase.py, WP-181 |
| S66 | **Server-Side Strategist** | [R1 Стратег](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | user_prompt + context_artifacts (через Ory JWT) | GitHub commit в personal-guide/DS-my-strategy + run_id | R14 Заказчик (через claude.ai / ChatGPT) | A1 Claude → I12 agent-runner (FastAPI, Railway) | ⚡ MCP tool `run_strategist` через Aisystant MCP | [DP.SC.163](../08-service-clauses/DP.SC.163-server-agents-mvp.md), aisystant/agent-runner |
| S67 | **Server-Side Extractor** | [R2 Экстрактор](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | user_prompt + context_artifacts | inbox/captures/* commit + run_id | R14 Заказчик | A1 Claude → I12 agent-runner | ⚡ MCP tool `run_extractor` через Aisystant MCP | [DP.SC.163](../08-service-clauses/DP.SC.163-server-agents-mvp.md), aisystant/agent-runner |
| S68 | **Run Status Poll** | [R1/R2](../02-domain-entities/DP.ROLE.001-platform-roles.md#агентские-роли-grade-2) | run_id (Ory JWT) | status + error_code + result_url + committed_files | R14 Заказчик | I12 agent-runner (GET /v1/runs/{run_id}) | ⚡ MCP tool `get_run_status` (poll каждые 5-10с) | [DP.SC.163](../08-service-clauses/DP.SC.163-server-agents-mvp.md) |
| S69 | **Auto-Scope Provisioning** | R8 Синхронизатор | webhook installation_repositories.added (githubUsername, repo.name) | INSERT в agent_scopes_mvp (run_strategist + run_extractor) | I12 agent-runner | I13 gateway-mcp webhook → I12 agent-runner POST /v1/admin/scope-provision | ⚡ install GitHub App | [DP.SC.163 §Auto-scope provisioning (Ф4)](../08-service-clauses/DP.SC.163-server-agents-mvp.md) |

---

## Маппинг сервисов на обещания (SC)

> Какое обещание потребителю реализует каждый сервис. Один сервис может участвовать в нескольких SC (разные грани ценности).

| SC | Обещание | Сервисы |
|----|----------|---------|
| [SC.001](../08-service-clauses/DP.SC.001-daily-planning.md) | Планирование дня | S01, S42, S44, S45 |
| [SC.002](../08-service-clauses/DP.SC.002-weekly-planning.md) | Планирование и ревью недели | S02, S03, S05, S06, S07, S08, S41 |
| [SC.003](../08-service-clauses/DP.SC.003-learning-and-development.md) | Обучение и развитие | S12, S13, S14, S15, S16, S37, S48, S51, S52 |
| [SC.004](../08-service-clauses/DP.SC.004-knowledge-capture.md) | Фиксация и экстракция знаний | S04, S09, S10, S11, S22, S39, S40 |
| [SC.005](../08-service-clauses/DP.SC.005-content-publishing.md) | Публикация контента | S25, S26, S27, S28, S46, S47 |
| [SC.006](../08-service-clauses/DP.SC.006-automated-maintenance.md) | Автоматическое обслуживание | S17, S18, S19, S20, S21, S22, S23, S24, S49, S50 |
| [SC.007](../08-service-clauses/DP.SC.007-triage-and-techdebt.md) | Триаж и техдолг | S29, S30 |
| [SC.008](../08-service-clauses/DP.SC.008-self-healing.md) | Самовосстановление | S31, S32, S33, S34 |
| [SC.009](../08-service-clauses/DP.SC.009-analytics-and-metrics.md) | Аналитика и метрики | S35, S36, S38, S43 |
| [SC.010](../08-service-clauses/DP.SC.010-work-rhythm.md) | Рабочий ритм (ОРЗ) | S01, S02, S03, S04, S05, S42, S44, S09 |
| [SC.011](../08-service-clauses/DP.SC.011-strategizing.md) | Стратегирование | S02, S03, S05, S06, S07, S08, S41 |
| [SC.012](../08-service-clauses/DP.SC.012-onboarding.md) | Онбординг | S12, S23, S24 |
| [SC.043](../08-service-clauses/DP.SC.043-template-update.md) | Обновление экзокортекса | S50 |
| [SC.013](../08-service-clauses/DP.SC.013-work-session.md) | Рабочая сессия с Claude Code | S06, S09, S10, S40 |
| [SC.014](../08-service-clauses/DP.SC.014-pack-formalization.md) | Формализация знаний (Pack) | S09, S11, S38 |
| [SC.015](../08-service-clauses/DP.SC.015-system-development.md) | Развитие системы (DS) | S06, S20, S24, S30 |
| [SC.016](../08-service-clauses/DP.SC.016-collective-work-products.md) | Коллективное управление РП | S01, S02, S08 |
| [SC.017](../08-service-clauses/DP.SC.017-adaptive-daily-assignment.md) | Адаптивное задание на день | — (новые сервисы TBD) |
| [SC.018](../08-service-clauses/DP.SC.018-tier-upgrade-t3-t4.md) | Переход T3 → T4 | — (новые сервисы TBD) |
| [SC.112](../08-service-clauses/DP.SC.112-subscription-billing.md) | Подписки и биллинг | S63, S65 |
| [SC.114](../08-service-clauses/DP.SC.114-crm.md) | CRM | S64 |
| [SC.117](../08-service-clauses/DP.SC.117-async-homework-review.md) | Асинхронная проверка и обсуждение ДЗ | S13, S37, S60 |

---

## Статистика

| Показатель | Значение |
|------------|----------|
| Всего сервисов | 56 |
| По расписанию (⏰) | 24 |
| По событию (⚡) | 14 |
| По запросу (👤) | 18 |
| Уникальных ролей | 15 |
| Уникальных инструментов | 11 (I1-I11) |
| Систем | 12 |

## Как использовать

1. **При диагностике:** Ctrl+F по имени сервиса → проверить вход → проверить выход → ссылка на PROCESSES.md
2. **При добавлении:** Добавить строку сюда → убедиться, что роль есть в [DP.ROLE.001](../02-domain-entities/DP.ROLE.001-platform-roles.md) → добавить в PROCESSES.md системы
3. **При ArchGate:** Найти затронутые сервисы → оценить coupling через колонку «Кому»
4. **Инструменты исполнителя:** Эта таблица показывает сервисы (ЧТО делается). Для полного списка инструментов (ЧЕМ делается) каждого исполнителя → [Таблица РА §3.5](../02-domain-entities/DP.ROLE.001-platform-roles.md#35-таблица-ра-роли--исполнители--инструменты)

## Связь с другими картами

| Карта | Что показывает | Ссылка |
|-------|---------------|--------|
| DP.MAP.001 | Навигация по Pack-сущностям | [DP.MAP.001.md](DP.MAP.001.md) |
| DP.MAP.002 | **Эта карта** — потоки сервисов IWE | — |
| DP.ROLE.001 | Каталог ролей + исполнители (source-of-truth) | [DP.ROLE.001](../02-domain-entities/DP.ROLE.001-platform-roles.md) |

---

*Создано: 2026-02-23. Обновлять при добавлении/изменении сервисов.*
