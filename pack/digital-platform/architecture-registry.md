---
id: DP.ARCH.001-registry-view
type: generated-view
source: pack/digital-platform/architecture-registry/*.yaml
generator: .github/scripts/architecture-registry.py
---

# Справочники архитектуры платформы и IWE

> Собрано программой из справочников `architecture-registry/`; руками не править. Правило и порядок изменения — абзац «Справочники имён и связей» в [DP.ARCH.001](02-domain-entities/DP.ARCH.001-platform-architecture.md). Имена систем, подсистем и модулей бери отсюда.

## Подсистемы

| Ключ | Имя | Другие имена | Система | Статус | Что делает |
|---|---|---|---|---|---|
| gatekeeper | Привратник |  | платформа | существует | устанавливает личность, тариф и права |
| tool-dispatcher | Диспетчер инструментов |  | платформа | существует | принимает вызовы MCP и передаёт их нужному бэкенду |
| shared-knowledge-provider | Поставщик общих знаний |  | платформа | существует | ищет и выдаёт паки, руководства, понятия |
| librarian | Библиотекарь |  | платформа | проектируется | хранит указатели на методы авторов из собрания «Библиотека методов» и их проверку (имя подсистемы — по роли, решение пилота 11.11.2026); определение — [ECO.ARCH.001 §3.1 «Библиотека методов»](https://github.com/MimEcoSys/PACK-ecosystem/blob/main/pack/ecosystem/02-domain-entities/ECO.ARCH.001-ecosystem-architecture.md) |
| personal-knowledge-keeper | Хранитель личных знаний |  | платформа | существует | индексирует и отдаёт личные и командные источники |
| portrait-keeper | Держатель портрета |  | платформа | существует | хранит характеристики и ступень человека |
| path-guide | Проводник по пути |  | платформа | существует | ведёт человека: онбординг, чек-лист, руководство, тренажёр |
| event-accountant | Учётчик событий |  | платформа | существует | принимает события и раскладывает их по базам, начисляет баллы |
| cashier | Кассир |  | платформа | существует | принимает платежи и ведёт подписки |
| mentor-workplace | Рабочее место наставника |  | платформа | существует | даёт наставнику карточку участника и разбор чата |
| server-agent-runner | Исполнитель серверных агентов |  | платформа | существует | выполняет работу агентов по поручению и расписанию |
| model-dispenser | Раздатчик моделей |  | платформа | существует | проверяет лимит и передаёт вызовы моделям |
| messenger | Собеседник в мессенджере |  | платформа | существует | ведёт диалог с человеком в Telegram |
| herald | Вестник |  | платформа | существует | доставляет уведомления всем пользователям по правилам платформы и по своим правилам человека: хранит правила и настройки, принимает выпуски, решает, когда и в какой канал доставить, ведёт ленту и учёт доставки (решение пилота 18.11.2026) |
| showcase | Витрина |  | платформа | существует | рассказывает о программах и ведёт к подключению |
| translator | Переводчик |  | платформа | существует | переводит для всех тексты шаблона IWE и карточки Библиотеки методов на английский по утверждённому словарю понятий; отдаёт словарь для инструкции ИИ клиента Open (решение пилота 10.11.2026, вариант «обе системы») |
| health-watchman | Сторож исправности |  | платформа | существует | замечает сбои и сообщает о них |
| backup-keeper | Хранитель копий |  | платформа | существует | держит резервные копии и подтверждение целостности |
| conversation-window | Окно разговора |  | платформа | проектируется | принимает сообщения человека в мессенджере и показывает ответы; рабочее имя (заявка РП-262, И-61 во входящих РП-611, 19.11.2026); окончательное имя и отношение к подсистеме «Собеседник в мессенджере» — решение пилота |
| interlocutor | Собеседник |  | платформа | проектируется | ведёт разговор с человеком о его личном IWE в обе стороны: отвечает, предлагает, пишет первым; рабочее имя (заявка РП-262, И-61 во входящих РП-611, 19.11.2026); окончательное имя и отношение к подсистеме «Собеседник в мессенджере» — решение пилота |
| write-controller | Контролёр записи |  | платформа | проектируется | выдаёт одноразовые разрешения на запись в шлюзе: запись только после явного подтверждения человека; рабочее имя (заявка РП-262, И-61 во входящих РП-611, 19.11.2026); окончательное имя и отношение к подсистеме «Собеседник в мессенджере» — решение пилота |
| interlocutor-executor-choice | Выбор исполнителя Собеседника |  | платформа | проектируется | по настройке человека выбирает исполнителя Собеседника: агент платформы или собственный агент владельца; рабочее имя (заявка РП-262, И-61 во входящих РП-611, 19.11.2026); окончательное имя и отношение к подсистеме «Собеседник в мессенджере» — решение пилота |

## Модули

| id | Имя | Другие имена | Вид | Система | Статус | Что делает |
|---|---|---|---|---|---|---|
| gateway-mcp | gateway-mcp | gateway-mcp (воркер gateway-mcp-v2) | программа | платформа | существует | Единая точка входа MCP: проверяет вход через Ory, подписку и права, собирает инструменты из программ-источников и перенаправляет вызовы; держит OAuth-шлюз. |
| TokenRefreshCoalescer | TokenRefreshCoalescer | TokenRefreshCoalescer (Durable Object шлюза) | программа | платформа | существует | Объединяет одновременные обновления токена, чтобы не гонять Ory лишними запросами. |
| REFRESH_TOKEN_KV | REFRESH_TOKEN_KV | REFRESH_TOKEN_KV (хранилище ключ-значение шлюза) | хранилище | платформа | существует | Кеш токенов обновления для входа через OAuth. |
| kimi-adapter | kimi-adapter | kimi-adapter (mim-iwe) | программа | платформа | существует | Демо-стенд и HTTP-адаптер: держит MCP-клиент к gateway-mcp для браузерного доступа. |
| knowledge-mcp | knowledge-mcp | knowledge-mcp (общий воркер знаний платформы) | программа | платформа | существует | Поиск, чтение и обход платформенных знаний (Паки, руководства, понятия) в режиме public; индексирует репозитории по расписанию. |
| full-ingest-batches | full-ingest-batches | full-ingest-batches (очередь и очередь отказов) | очередь | платформа | существует | Очередь пакетов полной индексации знаний; отказавшие пакеты уходят в full-ingest-batches-dlq. |
| guides-mcp | guides-mcp | guides-mcp (руководства) | программа | платформа | существует | Список, разделы, текст и смысловой поиск по платформенным руководствам из таблицы knowledge_chunk. |
| open-tserenov-com | open-tserenov-com | open-tserenov-com (открытый личный MCP Церена) | программа | платформа | существует | Публичный MCP search/fetch по открытому авторскому корпусу из встроенного бандла; ограничивает частоту обращений. |
| db:open-tserenov-com | D1 open-tserenov-com | D1 open-tserenov-com | база данных | платформа | существует | База D1 открытого личного MCP (назначение таблиц в этой проверке не снято). |
| open.system-school.ru | open.system-school.ru | open.system-school.ru (гостевой MCP FPF) | программа | платформа | существует | Анонимный MCP search/fetch по гиду FPF на MiniSearch и встроенном бандле. |
| open.aisystant.com | open.aisystant.com | open.aisystant.com (Open Aisystant, гостевой MCP мира) | программа | платформа | существует | Прокси к `mcp.fpf.tools`: те же инструменты поиска и чтения опубликованных FPF и DPF без аккаунта; собственный поисковый корпус не подтверждён (DP.MAP.004). Отвечает как сервер MCP (проверено 11.11.2026). Выпускающий — Андрей (§2). |
| plus.system-school.ru | plus.system-school.ru | plus.system-school.ru (MIM MCP, российский MCP по аккаунту и подписке; целевой) | программа | платформа | проектируется | Развёртывание кода Plus Андрея с российскими настройками (§7.1). Прежнее имя `mcp.system-school.ru`: по DP.MAP.004 — российский вход в gateway-mcp, по содержимому репозитория — копия гостевого сервера open.system-school.ru. |
| personal-knowledge-mcp | personal-knowledge-mcp | personal-knowledge-mcp (воркер личных знаний) | программа | платформа | существует | Личные источники пользователя: поиск, запись, переиндексация личных репозиториев; применяет защиту записи по правам. |
| reindex | reindex | reindex (очередь и очередь отказов); очередь reindex | очередь | платформа | существует | Очередь переиндексации личных источников; отказавшие сообщения — в reindex-dlq. |
| github-integration-service | github-integration-service |  | программа | платформа | существует | Принимает вебхуки GitHub App и OAuth установки, создаёт репозитории, ведёт статус подключения пользователя. |
| digital-twin-mcp | digital-twin-mcp | digital-twin-mcp (цифровой двойник) | программа | платформа | существует | Читает и пишет поля, профиль и показатели цифрового двойника ученика по метамодели. |
| learning-context-service | learning-context-service |  | программа | платформа | существует | Согласия, когнитивная справка, состояние онбординга и персональный гид. |
| iwe-profiler | iwe-profiler | iwe-profiler (Профилировщик); профилировщик | программа | платформа | существует | Пересчитывает производные профили в Neon раз в сутки (04:30 по Москве). |
| iwe-stage-evaluator | iwe-stage-evaluator и iwe-stage-controller | оценщик ступени | программа | платформа | существует | Оценивают ступень по данным и вычисляют контроллер ступеней. |
| iwe-stage-controller | iwe-stage-evaluator и iwe-stage-controller | контроллер ступеней | программа | платформа | существует | Оценивают ступень по данным и вычисляют контроллер ступеней. |
| event-gateway | event-gateway | event-gateway (приёмник событий) | программа | платформа | существует | Единственный писатель событий в learning.domain_event: проверяет источник, подпись и запрет персональных полей. |
| trace-accountant | trace-accountant |  | программа | платформа | существует | Принимает следы работы агентов, пишет в domain_event или в заглушки при отсутствии согласия, сверяет записи. |
| activity-hub | activity-hub |  | программа | платформа | существует | Собирает события активности (GitHub, WakaTime, LMS), считает стадии и когнитивные справки, хранит счёт в Neon. |
| bridge-2-events-poller | bridge-2-events-poller |  | программа | платформа | существует | Опрашивает legacy LMS (PostgreSQL, чтение) и отправляет события в event-gateway. |
| multi-domain-projection-worker | multi-domain-projection-worker |  | программа | платформа | существует | Переносит события из learning.domain_event в БД persona, subscription, indicators, rewards по правилам projection_rules. |
| fsm-mcp | fsm-mcp | fsm-mcp (Ассистент Ученика) | программа | платформа | существует | Выдаёт инструкции по состоянию ученика через конечный автомат; содержит неподключённый модуль проверки результата опроса. |
| simulator-proxy | simulator-proxy |  | программа | платформа | существует | Передаёт запросы с simulator.aisystant.com в программу simulator-lab. |
| checklist-mcp | checklist-mcp |  | программа | платформа | существует | Выдаёт чек-лист участника: факты, этап и прогресс. |
| iwe-guide-web | iwe-guide-web | iwe-guide-web (читалка руководств, guide.system-school.ru) | программа | платформа | существует | Показывает персональные и универсальные руководства пилотов IWE. |
| simulator-lab | simulator-lab |  | программа | платформа | существует | Программа-тренажёр, за которой стоит simulator-proxy. |
| iwe-onboarding-controller | iwe-onboarding-controller | контроллер онбординга | программа | платформа | существует | Контроллер онбординга пользователя (DP.ROLE.046) по таймеру. |
| iwe-render-pilot-guides | iwe-render-pilot-guides | iwe-render-pilot-guides (сборщик персональных руководств); сборщик персональных руководств; сборщик руководств | программа | платформа | существует | Собирает персональные руководства пилотов (день, неделя, очередь). |
| observability-webhook | observability-webhook |  | программа | платформа | существует | Принимает вебхук инцидентов Better Stack и пишет уведомления в Telegram-канал статуса; раз в минуту опрашивает состояние. |
| OBSERVABILITY_STATE | OBSERVABILITY_STATE | OBSERVABILITY_STATE (KV наблюдателя) | хранилище | платформа | существует | Хранит состояние уже отправленных уведомлений. |
| status-proxy | status-proxy |  | программа | платформа | существует | Перенаправляет status.aisystant.com (302) на страницу статуса Better Stack. |
| payment-receiver | payment-receiver |  | программа | платформа | существует | Принимает уведомления ЮKassa о платежах, проверяет адрес и подпись, пересылает событие в event-gateway и дальше. |
| payment-registry | программы синхронизации payment-registry | программы синхронизации payment-registry; программы синхронизации payment-registry (платежи, контракты, подписки); синхронизатор реестра платежей | набор программ | платформа | существует | Переносит платежи и подписки из LMS-базы в Neon (platform.finance_payments, subscription.contract). |
| db:platform | Neon: БД platform | Neon: БД platform; Neon: БД platform (finance_payments) | база данных | платформа | существует | Единый журнал платежей экосистемы. |
| agent-runner | agent-runner | agent-runner (iwe-agent-runner) | программа | платформа | существует | Выполняет серверных агентов run_strategist и run_extractor от имени пользователя: вызывает модель и коммитит файлы в его репозиторий. |
| agent-status-service | agent-status-service |  | программа | платформа | существует | Доска статусов агентов: кто работает, над чем и с какими файлами. |
| hermes-agent | hermes-agent | hermes-agent (рантайм Hermes) | программа | платформа | существует | Исполняет hermes_chat: вызывает модель через OpenRouter и хранит память диалога. |
| user-profile-service | user-profile-service |  | программа | платформа | существует | Профиль, тариф, статус GitHub и ключи моделей пользователя (BYOK); уведомляет бота. |
| bridge-scope-service | bridge-scope-service |  | программа | платформа | существует | Проверяет права агента на запись в репозиторий пользователя перед операцией; применяет защиту строк (RLS). |
| Ory | Ory | Ory (Hydra, Kratos); Ory Hydra; Ory Kratos | набор программ | платформа | существует | Единая учётная запись и OAuth-сервер платформы: вход, токены, идентичности. |
| mentorship-service | mentorship-service |  | программа | платформа | существует | Собирает карточку участника для наставника и хранит заметки наставника. |
| chat-analyst-service | chat-analyst-service | chat-analyst-service (аналитик чата) | программа | платформа | существует | Собирает сообщения закрытых Telegram-чатов, формирует дайджест и статистику для администратора чата. |
| Neon: проект mentorship | Neon: проект mentorship | Neon-проект mentorship | проект баз данных | платформа | существует | Архив переписки наставник–участник и заметки. |
| iwe-llm-proxy | iwe-llm-proxy | LLM-прокси; iwe-llm-proxy (auth-gateway) | программа | платформа | существует | Проверяет подписку и дневной лимит перед вызовами модели, переводит форматы Anthropic и OpenAI, ведёт журнал вызовов; отдаёт данные сессий для дашборда. |
| litellm | litellm | LiteLLM; litellm (прокси к моделям) | программа | платформа | существует | Маршрутизирует вызовы моделей (Claude, Kimi, GPT-4o-mini) через OpenRouter. |
| aist_bot_newarchitecture | aist_bot_newarchitecture | Telegram-бот; aist_bot_newarchitecture (бот @aist_me_bot, пилотный @aist_pilot_bot); бот; бот @aist_me_bot | программа | платформа | существует | Telegram-бот обучения: ленты, марафоны, оплата, обращения к платформе; тонкий клиент платформы. |
| SystemsSchool_bot | SystemsSchool_bot | SystemsSchool_bot (прежний Telegram-бот Школы); прежний бот Школы | программа | платформа | существует | Telegram-бот Школы системного менеджмента. |
| system-school.ru | system-school.ru | system-school.ru (сайт МИМ) | программа | платформа | существует | Статический сайт на VitePress; публикуется через werf. |
| ssm2025 | ssm2025 | ssm2025 (сайт ШСМ 2025) | программа | платформа | существует | VitePress-сайт с публикацией образа и деплоем в Nomad. |
| aisystant-com | aisystant-com | aisystant-com (сайт) | программа | платформа | существует | Сайт aisystant.com, образ публикуется workflow. |
| restic | restic | restic (программа резервного копирования баз Neon и локальных файлов) | программа | платформа | существует | Дампит базы Neon через pg_dump и шифрованно копирует в Backblaze B2; чистит старые копии. |
| bitcoind-ots-verify | bitcoind-ots-verify и программа якорения OpenTimestamps | bitcoind-ots-verify и программа якорения OpenTimestamps; bitcoind-ots-verify и программа якорения OpenTimestamps (wp455); программа якорения OpenTimestamps | набор программ | платформа | существует | Независимо проверяет якоря цепочки хешей в OpenTimestamps; делает новые якоря, наблюдает за ними. |
| Backblaze B2 бакет | Backblaze B2 | Backblaze B2 (бакет резервных копий) | хранилище | платформа | существует | Внешнее хранилище шифрованных копий Neon и файлов. |
| Metabase | Metabase |  | программа | платформа | существует | BI по шестнадцати источникам Neon. |
| Directus | Directus |  | программа | платформа | существует | Админка и CMS для справочников, платежей и ручных операций. |
| Neon: проект aisystant | Neon: проект aisystant | Neon: проект aisystant (кластер баз данных) | проект баз данных | платформа | существует | Миграции создают БД persona, journal, payment, subscription, indicators, learning, knowledge, reference, rewards, publication, community, lead, health, secrets и схемы audit, agent_trace, concept_graph. |
| Railway Postgres | Railway Postgres | Railway Postgres (bot_data, fsm, directus, railway) | проект баз данных | платформа | существует | Хранит состояние бота, FSM и метаданные Directus. |
| PostgreSQL 16 с pgvector на tsekh-1 | PostgreSQL 16 с pgvector на tsekh-1 | PostgreSQL 16 с pgvector на tsekh-1 (времянка для проверок переноса баз) | база данных | платформа | существует | Docker-compose: PostgreSQL 16 с pgvector и Caddy; проверки переноса баз. Описание сервера tsekh-1 целиком (PostgreSQL, restic, таймеры) хранит репозиторий hetzner-backstage — документ, по которому сервер пересобирают, а не модуль. |
| iwe-browser-extension | iwe-browser-extension |  | программа | IWE | существует | Расширение Chrome считает набор текста на claude.ai и отправляет боту. |
| DS-iwe-session-trigger | DS-iwe-session-trigger | DS-iwe-session-trigger (расширение VS Code) | программа | IWE | существует | Наблюдает за файлами сессий и запускает Claude Code автоматически. |
| DS-iwe-wp-panel | DS-iwe-wp-panel | DS-iwe-wp-panel (панель РП) | программа | IWE | существует | Расширение VS Code: панель проектов и сессий агентов. |
| local-gateway | local-gateway | local-gateway (iwe-local-gateway) | программа | IWE | существует | Локальный MCP для блокировок файлов и статусов параллельных агентов. |
| google-drive-mcp | google-drive-mcp |  | программа | IWE | существует | Локальный MCP-коннектор к Google Drive владельца. |
| agent-trace-recorder | agent-trace-recorder и agent-trace-uploader |  | программа | IWE | существует | Хуки записи трассы работы агентов и отправки её в event-gateway. |
| agent-trace-uploader | agent-trace-recorder и agent-trace-uploader |  | программа | IWE | существует | Хуки записи трассы работы агентов и отправки её в event-gateway. |
| translate-sync | перевод шаблона при обновлении |  | программа | платформа | существует | переводит тексты шаблона IWE при обновлении основной ветки (GitHub Actions) |
| iwe-translation-engine | движок перевода |  | программа | платформа | существует | перевод по утверждённому словарю понятий |
| db:persona | база persona | база persona; БД persona | база данных | платформа | существует | база в проекте Neon aisystant (§5.1, строка проекта) |
| db:journal | база journal | база journal; БД journal | база данных | платформа | существует | база в проекте Neon aisystant (§5.1, строка проекта) |
| db:payment | база payment | база payment; БД payment | база данных | платформа | существует | база в проекте Neon aisystant (§5.1, строка проекта) |
| db:subscription | база subscription | база subscription; БД subscription | база данных | платформа | существует | база в проекте Neon aisystant (§5.1, строка проекта) |
| db:indicators | база indicators | база indicators; БД indicators | база данных | платформа | существует | база в проекте Neon aisystant (§5.1, строка проекта) |
| db:learning | база learning | база learning; БД learning | база данных | платформа | существует | база в проекте Neon aisystant (§5.1, строка проекта) |
| db:knowledge | база knowledge | база knowledge; БД knowledge | база данных | платформа | существует | база в проекте Neon aisystant (§5.1, строка проекта) |
| db:reference | база reference | база reference; БД reference | база данных | платформа | существует | база в проекте Neon aisystant (§5.1, строка проекта) |
| db:rewards | база rewards | база rewards; БД rewards | база данных | платформа | существует | база в проекте Neon aisystant (§5.1, строка проекта) |
| db:publication | база publication | база publication; БД publication | база данных | платформа | существует | база в проекте Neon aisystant (§5.1, строка проекта) |
| db:community | база community | база community; БД community | база данных | платформа | существует | база в проекте Neon aisystant (§5.1, строка проекта) |
| db:lead | база lead | база lead; БД lead | база данных | платформа | существует | база в проекте Neon aisystant (§5.1, строка проекта) |
| db:health | база health | база health; БД health | база данных | платформа | существует | база в проекте Neon aisystant (§5.1, строка проекта) |
| db:secrets | база secrets | база secrets; БД secrets | база данных | платформа | существует | база в проекте Neon aisystant (§5.1, строка проекта) |
| db:railway-bot_data | база bot_data в Railway Postgres |  | база данных | платформа | существует | база в Railway Postgres (§5.1) |
| db:railway-fsm | база fsm в Railway Postgres |  | база данных | платформа | существует | база в Railway Postgres (§5.1) |
| db:railway-directus | база directus в Railway Postgres |  | база данных | платформа | существует | база в Railway Postgres (§5.1) |
| db:railway-railway | база railway в Railway Postgres |  | база данных | платформа | существует | база в Railway Postgres (§5.1) |
| iwe-interlocutor | агент-собеседник платформы |  | программа | платформа | проектируется | прототип РП-262 (хранилище aisystant/iwe-interlocutor); проверяет пропуск человека, обращается к шлюзу MCP его пропуском и к раздатчику моделей; постоянный владелец — команда ИТ (имя выбрал пилот 19.11, заявка И-61) |

## Системы окружения

| id | Другие имена | Что делает |
|---|---|---|
| Cloudflare | Cloudflare (Workers, KV, Durable Objects, Queues, D1, Rate Limiting, DNS aisystant.com) | исполнение воркеров, очереди и кеши, домены mcp/oauth/twin/simulator/status.aisystant.com и open.tserenov.com |
| Railway |  | запуск программ из Dockerfile или nixpacks: бот, activity-hub, agent-runner, user-profile-service, github-integration-service, checklist-mcp, trace-accountant, agent-status-service, mentorship-service, iwe-guide-web, bridge-2-events-poller, multi-domain-projection-worker, iwe-llm-proxy, litellm, hermes-agent, simulator-lab; Postgres (bot_data, fsm, directus) |
| GitHub | GitHub (репозитории, GitHub App, Actions, ghcr.io); GitHub Actions; GitHub App | хранение кода, Паков и репозиториев пользователей; сборка и выпуск воркеров; вебхуки установки приложения |
| Telegram Bot API | Telegram; Telegram (Bot API) | интерфейс ботов и уведомления |
| Anthropic |  | генерация ответов и эмбеддингов: Anthropic напрямую (ключ в боте), OpenRouter через litellm и hermes-agent, эмбеддинги text-embedding-3-small через OpenRouter и OpenAI |
| OpenRouter |  | генерация ответов и эмбеддингов: Anthropic напрямую (ключ в боте), OpenRouter через litellm и hermes-agent, эмбеддинги text-embedding-3-small через OpenRouter и OpenAI |
| OpenAI |  | генерация ответов и эмбеддингов: Anthropic напрямую (ключ в боте), OpenRouter через litellm и hermes-agent, эмбеддинги text-embedding-3-small через OpenRouter и OpenAI |
| рантаймы агентов | Claude Code; Claude Code, Codex, Kimi и другие рантаймы агентов; Codex; Kimi | клиенты MCP на стороне пользователя |
| Aisystant LMS | Aisystant LMS (legacy, PostgreSQL и API); Aisystant LMS PG; Aisystant LMS PostgreSQL; Aisystant LMS PostgreSQL (legacy); LMS API | исходный источник платежей, подписок и учебного прогресса ШСМ |
| ЮKassa |  | приём платежей |
| Telegram Stars |  | приём платежей |
| Discourse | Discourse (systemsworld.club); systemsworld.club | клуб: публикации и комментарии |
| Better Stack |  | мониторинг, страница статуса, heartbeat |
| Backblaze B2 |  | хранение зашифрованных резервных копий |
| Hetzner |  | аренда личного сервера автора tsekh-1 (Финляндия); платформа пользуется им временно, до переноса в GKE или VK Cloud |
| VK Cloud | VK Cloud (Kubernetes, registry); VK registry docker-registry.system-school.ru | российская площадка: system-school.ru, Ory, open.system-school.ru и plus.system-school.ru (целевой MIM MCP; прежнее имя mcp.system-school.ru); werf-деплой |
| Nomad |  | запуск ssm2025 |
| Langfuse |  | трассировка вызовов моделей |
| WakaTime |  | интеграции пользователя: учёт времени, задачи, календарь, файлы |
| Linear |  | интеграции пользователя: учёт времени, задачи, календарь, файлы |
| Google Calendar |  | интеграции пользователя: учёт времени, задачи, календарь, файлы |
| Google Drive |  | интеграции пользователя: учёт времени, задачи, календарь, файлы |
| FPF Library | FPF Library (mcp.fpf.tools); mcp.fpf.tools | внешний публичный MCP по FPF, исходный код не установлен |
| npm |  | поставка зависимостей и образов |
| PyPI |  | поставка зависимостей и образов |
| ghcr.io |  | поставка зависимостей и образов |

## Работает на: подсистема → модули

| Подсистема | Модуль | Когда |
|---|---|---|
| Хранитель копий | Backblaze B2 бакет | не установлено |
| Хранитель копий | bitcoind-ots-verify | не установлено |
| Хранитель копий | restic | не установлено |
| Кассир | Directus | при ручных правках платежей и выдаче подписки (DP.ARCH.001 §5.3) |
| Кассир | db:platform | не установлено |
| Кассир | payment-receiver | на уведомление ЮKassa о платеже |
| Кассир | payment-registry | не установлено |
| Учётчик событий | activity-hub | не установлено |
| Учётчик событий | bridge-2-events-poller | при опросе LMS (частота не установлена) |
| Учётчик событий | event-gateway | не установлено |
| Учётчик событий | multi-domain-projection-worker | не установлено |
| Учётчик событий | trace-accountant | когда принимает след работы агента |
| Привратник | Ory | при входе и выдаче токенов |
| Привратник | bridge-scope-service | перед операцией записи агента в репозиторий пользователя |
| Привратник | gateway-mcp | не установлено |
| Привратник | user-profile-service | не установлено |
| Сторож исправности | OBSERVABILITY_STATE | не установлено |
| Сторож исправности | observability-webhook | на вебхук инцидента и раз в минуту |
| Сторож исправности | status-proxy | когда открывают status.aisystant.com |
| Вестник | aist_bot_newarchitecture | не установлено |
| Собеседник | iwe-interlocutor | по сообщению человека в окне разговора и по собственной инициативе (проектируется) |
| Рабочее место наставника | Neon: проект mentorship | не установлено |
| Рабочее место наставника | chat-analyst-service | не установлено |
| Рабочее место наставника | mentorship-service | не установлено |
| Собеседник в мессенджере | SystemsSchool_bot | не установлено |
| Собеседник в мессенджере | aist_bot_newarchitecture | не установлено |
| Раздатчик моделей | iwe-llm-proxy | перед каждым вызовом модели и при его передаче |
| Раздатчик моделей | litellm | перед каждым вызовом модели и при его передаче |
| Проводник по пути | checklist-mcp | по вызову инструмента |
| Проводник по пути | fsm-mcp | по вызову инструмента |
| Проводник по пути | iwe-guide-web | не установлено |
| Проводник по пути | iwe-onboarding-controller | по таймеру |
| Проводник по пути | iwe-render-pilot-guides | не установлено |
| Проводник по пути | simulator-lab | не установлено |
| Проводник по пути | simulator-proxy | на запросы с simulator.aisystant.com |
| Хранитель личных знаний | github-integration-service | когда принимает вебхук GitHub App или установку через OAuth |
| Хранитель личных знаний | personal-knowledge-mcp | по вызову инструмента |
| Хранитель личных знаний | reindex | не установлено |
| Держатель портрета | digital-twin-mcp | по вызову инструмента |
| Держатель портрета | iwe-profiler | раз в сутки в 04:30 по Москве |
| Держатель портрета | iwe-stage-controller | не установлено |
| Держатель портрета | iwe-stage-evaluator | не установлено |
| Держатель портрета | learning-context-service | не установлено |
| Исполнитель серверных агентов | agent-runner | по вызову run_strategist и run_extractor |
| Исполнитель серверных агентов | agent-status-service | не установлено |
| Исполнитель серверных агентов | hermes-agent | по вызову hermes_chat |
| Поставщик общих знаний | db:open-tserenov-com | не установлено |
| Поставщик общих знаний | full-ingest-batches | не установлено |
| Поставщик общих знаний | guides-mcp | по вызову инструмента |
| Поставщик общих знаний | knowledge-mcp | по вызову инструмента; кроме того, индексирует репозитории по расписанию |
| Поставщик общих знаний | open-tserenov-com | по вызову инструмента |
| Поставщик общих знаний | open.aisystant.com | по вызову инструмента |
| Поставщик общих знаний | open.system-school.ru | по вызову инструмента |
| Поставщик общих знаний | plus.system-school.ru | по вызову инструмента |
| Витрина | aisystant-com | не установлено |
| Витрина | ssm2025 | не установлено |
| Витрина | system-school.ru | не установлено |
| Диспетчер инструментов | REFRESH_TOKEN_KV | не установлено |
| Диспетчер инструментов | TokenRefreshCoalescer | при одновременных обновлениях токена |
| Диспетчер инструментов | gateway-mcp | на каждый вызов MCP |
| Диспетчер инструментов | kimi-adapter | не установлено |
| Переводчик | iwe-translation-engine | не установлено |
| Переводчик | translate-sync | при обновлении основной ветки шаблона |

## Стоит на: площадка → модули (DP.ARCH.001 §5.1 «Где работает» — снято 01.11.2026)

| Площадка | Модули |
|---|---|
| Backblaze B2 | Backblaze B2 бакет |
| Cloudflare Workers | OBSERVABILITY_STATE, REFRESH_TOKEN_KV, TokenRefreshCoalescer, db:open-tserenov-com, digital-twin-mcp, event-gateway, fsm-mcp, full-ingest-batches, gateway-mcp, guides-mcp, knowledge-mcp, observability-webhook, open-tserenov-com, payment-receiver, personal-knowledge-mcp, reindex, simulator-proxy, status-proxy |
| GitHub Actions | translate-sync |
| Kubernetes через werf | SystemsSchool_bot |
| Neon | Neon: проект aisystant, Neon: проект mentorship, db:community, db:health, db:indicators, db:journal, db:knowledge, db:lead, db:learning, db:payment, db:persona, db:platform, db:publication, db:reference, db:rewards, db:secrets, db:subscription |
| Nomad | ssm2025 |
| Railway | Directus, Metabase, Railway Postgres, activity-hub, agent-runner, agent-status-service, aist_bot_newarchitecture, bridge-2-events-poller, checklist-mcp, db:railway-bot_data, db:railway-directus, db:railway-fsm, db:railway-railway, github-integration-service, hermes-agent, iwe-guide-web, iwe-llm-proxy, litellm, mentorship-service, multi-domain-projection-worker, simulator-lab, trace-accountant, user-profile-service |
| VK Cloud | Ory, open.system-school.ru, plus.system-school.ru, system-school.ru |
| VS Code пользователя | DS-iwe-session-trigger, DS-iwe-wp-panel |
| tsekh-1 | PostgreSQL 16 с pgvector на tsekh-1, bitcoind-ots-verify, iwe-onboarding-controller, iwe-profiler, iwe-render-pilot-guides, iwe-stage-controller, iwe-stage-evaluator, payment-registry, restic |
| браузер пользователя | iwe-browser-extension |
| машина пользователя | agent-trace-recorder, agent-trace-uploader, google-drive-mcp, local-gateway |
| не установлено | aisystant-com, bridge-scope-service, chat-analyst-service, iwe-interlocutor, iwe-translation-engine, kimi-adapter, learning-context-service, open.aisystant.com |

## Обращается к (DP.ARCH.001 §5.1 «Обращается к» (снято 01.11.2026), §10 и проба пути оплаты; «обращается» — направление не уточнено)

| Кто | Глагол | Кому |
|---|---|---|
| gateway-mcp | обращается | knowledge-mcp |
| gateway-mcp | обращается | digital-twin-mcp |
| gateway-mcp | обращается | personal-knowledge-mcp |
| TokenRefreshCoalescer | обращается | Ory |
| kimi-adapter | обращается | gateway-mcp |
| kimi-adapter | обращается | Ory |
| knowledge-mcp | обращается | db:knowledge |
| knowledge-mcp | обращается | OpenRouter |
| knowledge-mcp | обращается | OpenAI |
| guides-mcp | обращается | OpenRouter |
| open.aisystant.com | обращается | FPF Library |
| personal-knowledge-mcp | обращается | db:indicators |
| personal-knowledge-mcp | обращается | db:knowledge |
| personal-knowledge-mcp | обращается | OpenRouter |
| personal-knowledge-mcp | обращается | GitHub |
| github-integration-service | обращается | GitHub |
| github-integration-service | обращается | db:learning |
| github-integration-service | обращается | knowledge-mcp |
| github-integration-service | обращается | personal-knowledge-mcp |
| learning-context-service | обращается | db:learning |
| learning-context-service | читает | Aisystant LMS |
| learning-context-service | вызывает | event-gateway |
| iwe-profiler | обращается | db:indicators |
| iwe-stage-evaluator | обращается | db:learning |
| iwe-stage-evaluator | обращается | activity-hub |
| iwe-stage-controller | обращается | db:learning |
| iwe-stage-controller | обращается | activity-hub |
| event-gateway | пишет | db:learning |
| event-gateway | обращается | db:persona |
| trace-accountant | обращается | db:learning |
| trace-accountant | вызывает | Ory |
| activity-hub | пишет | db:learning |
| activity-hub | обращается | Aisystant LMS |
| activity-hub | обращается | GitHub |
| activity-hub | обращается | WakaTime |
| activity-hub | вызывает | event-gateway |
| activity-hub | обращается | Langfuse |
| bridge-2-events-poller | читает | Aisystant LMS |
| bridge-2-events-poller | вызывает | event-gateway |
| multi-domain-projection-worker | пишет | db:indicators |
| multi-domain-projection-worker | читает | db:learning |
| multi-domain-projection-worker | пишет | db:persona |
| multi-domain-projection-worker | обращается | db:reference |
| multi-domain-projection-worker | пишет | db:rewards |
| multi-domain-projection-worker | пишет | db:subscription |
| fsm-mcp | обращается | Ory |
| simulator-proxy | обращается | simulator-lab |
| iwe-guide-web | обращается | GitHub |
| observability-webhook | обращается | Better Stack |
| observability-webhook | обращается | Telegram Bot API |
| status-proxy | обращается | Better Stack |
| payment-receiver | вызывает | event-gateway |
| payment-registry | читает | Aisystant LMS |
| payment-registry | пишет | db:platform |
| payment-registry | пишет | db:subscription |
| agent-runner | обращается | db:indicators |
| agent-runner | обращается | iwe-llm-proxy |
| agent-status-service | обращается | db:indicators |
| agent-status-service | обращается | Ory |
| hermes-agent | обращается | OpenRouter |
| user-profile-service | читает | db:subscription |
| user-profile-service | вызывает | Ory |
| user-profile-service | обращается | aist_bot_newarchitecture |
| bridge-scope-service | обращается | db:indicators |
| mentorship-service | обращается | Neon: проект mentorship |
| mentorship-service | читает | Aisystant LMS |
| iwe-llm-proxy | обращается | litellm |
| litellm | обращается | OpenRouter |
| aist_bot_newarchitecture | обращается | db:indicators |
| aist_bot_newarchitecture | обращается | db:journal |
| aist_bot_newarchitecture | обращается | db:learning |
| aist_bot_newarchitecture | обращается | db:persona |
| aist_bot_newarchitecture | обращается | db:rewards |
| aist_bot_newarchitecture | обращается | db:subscription |
| system-school.ru | обращается | VK Cloud |
| ssm2025 | обращается | ghcr.io |
| restic | обращается | Backblaze B2 |
| Directus | обращается | Railway Postgres |
| iwe-browser-extension | обращается | aist_bot_newarchitecture |
| DS-iwe-session-trigger | обращается | рантаймы агентов |
| google-drive-mcp | обращается | Google Drive |
| agent-trace-uploader | обращается | event-gateway |
| payment-receiver | пишет | Neon: проект aisystant |
| gateway-mcp | читает | db:subscription |
| ЮKassa | вызывает | payment-receiver |
| aist_bot_newarchitecture | вызывает | iwe-interlocutor |
| iwe-interlocutor | вызывает | gateway-mcp |
| iwe-interlocutor | вызывает | iwe-llm-proxy |

## Что затронет отключение модуля

> По записанным связям; «затронет» значит «есть связь», а не «точно сломается». Через базу влияние идёт только по связям с явным «пишет»; связи «обращается» без направления к базе считаются чтением. Ссылки из раздела «Уточнить у владельцев модулей» в расчёт не входят.

- **gateway-mcp**: aist_bot_newarchitecture (вызывает iwe-interlocutor); iwe-browser-extension (вызывает aist_bot_newarchitecture); iwe-interlocutor (вызывает gateway-mcp); kimi-adapter (вызывает gateway-mcp); user-profile-service (вызывает aist_bot_newarchitecture)
- **TokenRefreshCoalescer**: по записанным связям ничего
- **kimi-adapter**: по записанным связям ничего
- **knowledge-mcp**: aist_bot_newarchitecture (вызывает iwe-interlocutor); gateway-mcp (вызывает knowledge-mcp); github-integration-service (вызывает knowledge-mcp); iwe-browser-extension (вызывает aist_bot_newarchitecture); iwe-interlocutor (вызывает gateway-mcp); kimi-adapter (вызывает gateway-mcp); user-profile-service (вызывает aist_bot_newarchitecture)
- **guides-mcp**: по записанным связям ничего
- **open-tserenov-com**: по записанным связям ничего
- **open.system-school.ru**: по записанным связям ничего
- **open.aisystant.com**: по записанным связям ничего
- **plus.system-school.ru**: по записанным связям ничего
- **personal-knowledge-mcp**: aist_bot_newarchitecture (вызывает iwe-interlocutor); gateway-mcp (вызывает personal-knowledge-mcp); github-integration-service (вызывает personal-knowledge-mcp); iwe-browser-extension (вызывает aist_bot_newarchitecture); iwe-interlocutor (вызывает gateway-mcp); kimi-adapter (вызывает gateway-mcp); user-profile-service (вызывает aist_bot_newarchitecture)
- **github-integration-service**: по записанным связям ничего
- **digital-twin-mcp**: aist_bot_newarchitecture (вызывает iwe-interlocutor); gateway-mcp (вызывает digital-twin-mcp); iwe-browser-extension (вызывает aist_bot_newarchitecture); iwe-interlocutor (вызывает gateway-mcp); kimi-adapter (вызывает gateway-mcp); user-profile-service (вызывает aist_bot_newarchitecture)
- **learning-context-service**: по записанным связям ничего
- **iwe-profiler**: по записанным связям ничего
- **iwe-stage-evaluator**: по записанным связям ничего
- **iwe-stage-controller**: по записанным связям ничего
- **event-gateway**: activity-hub (вызывает event-gateway); agent-runner (читает db:indicators, куда пишет multi-domain-projection-worker); agent-status-service (читает db:indicators, куда пишет multi-domain-projection-worker); agent-trace-uploader (вызывает event-gateway); aist_bot_newarchitecture (читает db:learning, куда пишет event-gateway); bridge-2-events-poller (вызывает event-gateway); bridge-scope-service (читает db:indicators, куда пишет multi-domain-projection-worker); gateway-mcp (читает db:subscription, куда пишет multi-domain-projection-worker); github-integration-service (читает db:learning, куда пишет event-gateway); iwe-browser-extension (вызывает aist_bot_newarchitecture); iwe-interlocutor (вызывает gateway-mcp); iwe-profiler (читает db:indicators, куда пишет multi-domain-projection-worker); iwe-stage-controller (читает db:learning, куда пишет event-gateway); iwe-stage-evaluator (читает db:learning, куда пишет event-gateway); kimi-adapter (вызывает gateway-mcp); learning-context-service (вызывает event-gateway); multi-domain-projection-worker (читает db:learning, куда пишет event-gateway); payment-receiver (вызывает event-gateway); personal-knowledge-mcp (читает db:indicators, куда пишет multi-domain-projection-worker); trace-accountant (читает db:learning, куда пишет event-gateway); user-profile-service (вызывает aist_bot_newarchitecture); ЮKassa (вызывает payment-receiver)
- **trace-accountant**: по записанным связям ничего
- **activity-hub**: agent-runner (читает db:indicators, куда пишет multi-domain-projection-worker); agent-status-service (читает db:indicators, куда пишет multi-domain-projection-worker); agent-trace-uploader (вызывает event-gateway); aist_bot_newarchitecture (читает db:learning, куда пишет activity-hub); bridge-2-events-poller (вызывает event-gateway); bridge-scope-service (читает db:indicators, куда пишет multi-domain-projection-worker); event-gateway (читает db:persona, куда пишет multi-domain-projection-worker); gateway-mcp (читает db:subscription, куда пишет multi-domain-projection-worker); github-integration-service (читает db:learning, куда пишет activity-hub); iwe-browser-extension (вызывает aist_bot_newarchitecture); iwe-interlocutor (вызывает gateway-mcp); iwe-profiler (читает db:indicators, куда пишет multi-domain-projection-worker); iwe-stage-controller (вызывает activity-hub); iwe-stage-evaluator (вызывает activity-hub); kimi-adapter (вызывает gateway-mcp); learning-context-service (читает db:learning, куда пишет activity-hub); multi-domain-projection-worker (читает db:learning, куда пишет activity-hub); payment-receiver (вызывает event-gateway); personal-knowledge-mcp (читает db:indicators, куда пишет multi-domain-projection-worker); trace-accountant (читает db:learning, куда пишет activity-hub); user-profile-service (вызывает aist_bot_newarchitecture); ЮKassa (вызывает payment-receiver)
- **bridge-2-events-poller**: по записанным связям ничего
- **multi-domain-projection-worker**: activity-hub (вызывает event-gateway); agent-runner (читает db:indicators, куда пишет multi-domain-projection-worker); agent-status-service (читает db:indicators, куда пишет multi-domain-projection-worker); agent-trace-uploader (вызывает event-gateway); aist_bot_newarchitecture (читает db:indicators, куда пишет multi-domain-projection-worker); bridge-2-events-poller (вызывает event-gateway); bridge-scope-service (читает db:indicators, куда пишет multi-domain-projection-worker); event-gateway (читает db:persona, куда пишет multi-domain-projection-worker); gateway-mcp (читает db:subscription, куда пишет multi-domain-projection-worker); github-integration-service (вызывает personal-knowledge-mcp); iwe-browser-extension (вызывает aist_bot_newarchitecture); iwe-interlocutor (вызывает gateway-mcp); iwe-profiler (читает db:indicators, куда пишет multi-domain-projection-worker); iwe-stage-controller (читает db:learning, куда пишет event-gateway); iwe-stage-evaluator (читает db:learning, куда пишет event-gateway); kimi-adapter (вызывает gateway-mcp); learning-context-service (вызывает event-gateway); payment-receiver (вызывает event-gateway); personal-knowledge-mcp (читает db:indicators, куда пишет multi-domain-projection-worker); trace-accountant (читает db:learning, куда пишет event-gateway); user-profile-service (читает db:subscription, куда пишет multi-domain-projection-worker); ЮKassa (вызывает payment-receiver)
- **fsm-mcp**: по записанным связям ничего
- **simulator-proxy**: по записанным связям ничего
- **checklist-mcp**: по записанным связям ничего
- **iwe-guide-web**: по записанным связям ничего
- **simulator-lab**: simulator-proxy (вызывает simulator-lab)
- **iwe-onboarding-controller**: по записанным связям ничего
- **iwe-render-pilot-guides**: по записанным связям ничего
- **observability-webhook**: по записанным связям ничего
- **status-proxy**: по записанным связям ничего
- **payment-receiver**: ЮKassa (вызывает payment-receiver)
- **payment-registry**: aist_bot_newarchitecture (читает db:subscription, куда пишет payment-registry); gateway-mcp (читает db:subscription, куда пишет payment-registry); iwe-browser-extension (вызывает aist_bot_newarchitecture); iwe-interlocutor (вызывает gateway-mcp); kimi-adapter (вызывает gateway-mcp); user-profile-service (читает db:subscription, куда пишет payment-registry)
- **agent-runner**: по записанным связям ничего
- **agent-status-service**: по записанным связям ничего
- **hermes-agent**: по записанным связям ничего
- **user-profile-service**: по записанным связям ничего
- **bridge-scope-service**: по записанным связям ничего
- **Ory**: TokenRefreshCoalescer (вызывает Ory); agent-status-service (вызывает Ory); fsm-mcp (вызывает Ory); kimi-adapter (вызывает Ory); trace-accountant (вызывает Ory); user-profile-service (вызывает Ory)
- **mentorship-service**: по записанным связям ничего
- **chat-analyst-service**: по записанным связям ничего
- **iwe-llm-proxy**: agent-runner (вызывает iwe-llm-proxy); aist_bot_newarchitecture (вызывает iwe-interlocutor); iwe-browser-extension (вызывает aist_bot_newarchitecture); iwe-interlocutor (вызывает iwe-llm-proxy); user-profile-service (вызывает aist_bot_newarchitecture)
- **litellm**: agent-runner (вызывает iwe-llm-proxy); aist_bot_newarchitecture (вызывает iwe-interlocutor); iwe-browser-extension (вызывает aist_bot_newarchitecture); iwe-interlocutor (вызывает iwe-llm-proxy); iwe-llm-proxy (вызывает litellm); user-profile-service (вызывает aist_bot_newarchitecture)
- **aist_bot_newarchitecture**: iwe-browser-extension (вызывает aist_bot_newarchitecture); user-profile-service (вызывает aist_bot_newarchitecture)
- **SystemsSchool_bot**: по записанным связям ничего
- **system-school.ru**: по записанным связям ничего
- **ssm2025**: по записанным связям ничего
- **aisystant-com**: по записанным связям ничего
- **restic**: по записанным связям ничего
- **bitcoind-ots-verify**: по записанным связям ничего
- **Metabase**: по записанным связям ничего
- **Directus**: по записанным связям ничего
- **iwe-browser-extension**: по записанным связям ничего
- **DS-iwe-session-trigger**: по записанным связям ничего
- **DS-iwe-wp-panel**: по записанным связям ничего
- **local-gateway**: по записанным связям ничего
- **google-drive-mcp**: по записанным связям ничего
- **agent-trace-recorder**: по записанным связям ничего
- **agent-trace-uploader**: по записанным связям ничего
- **translate-sync**: по записанным связям ничего
- **iwe-translation-engine**: по записанным связям ничего
- **iwe-interlocutor**: aist_bot_newarchitecture (вызывает iwe-interlocutor); iwe-browser-extension (вызывает aist_bot_newarchitecture); user-profile-service (вызывает aist_bot_newarchitecture)

## Путь 10: Участник оплачивает подписку (ветка ЮKassa, DP.ARCH.001 §10)

```mermaid
flowchart LR
  "ЮKassa" -- "присылает уведомление о платеже" --> "payment-receiver"
  "payment-receiver" -- "пересылает событие" --> "event-gateway"
  "event-gateway" -- "пишет в learning.domain_event" --> "db:learning"
  "multi-domain-projection-worker" -- "читает событие" --> "db:learning"
  "multi-domain-projection-worker" -- "записывает подписку" --> "db:subscription"
  "gateway-mcp" -- "читает право при вызове" --> "db:subscription"
```

## Путь 10-вход: Участник оплачивает подписку (входы, DP.ARCH.001 §11.2 Б строка 10)

```mermaid
flowchart LR
  "aist_bot_newarchitecture" -- "команды /buy, /subscribe_stars, /subscription" --> "Telegram Stars"
  "system-school.ru" -- "страница /quick-purchase (модуль страницы не установлен)" --> "ЮKassa"
```
Примечание: как оплата через Telegram Stars доходит до базы subscription — в DP.ARCH.001 не установлено; §11.2 не называет Кассира для этой потребности

## Уточнить у владельцев модулей

Ссылки из графы «Обращается к» DP.ARCH.001 §5.1, которые нельзя однозначно привязать (обрезаны в документе или не названа база):

- **gateway-mcp**: chec
- **knowledge-mcp**: Neon: схемы public и concept_graph, pgvector
- **guides-mcp**: Neon: knowledge_chunk с source=docs-courses; Neon (knowledge_chunk с source=docs-courses)
- **open-tserenov-com**: D1; бандл корпуса
- **open.system-school.ru**: бандл корпуса FPF
- **personal-knowledge-mcp**: bridge-scope-serv
- **digital-twin-mcp**: Neon: DATABASE_URL; Neon (DATABASE_URL); проверка токенов Ory и подписи шлюза (GATEWAY_JWKS_URL)
- **learning-context-service**: Neon: DATABASE_URL
- **event-gateway**: Neon: переменные DATABASE_URL_LEARNING, DATABASE_URL_PERS
- **trace-accountant**: Neon: public.domain_event
- **activity-hub**: Neon: др.
- **fsm-mcp**: проверка подписи шлюза (GATEWAY_JWKS_URL)
- **checklist-mcp**: Neon: NEON_DATABASE_URL, PANEL_DATABASE_URL; Neon (NEON_DATABASE_URL, PANEL_DATABASE_URL); проверка подписи шлюза
- **iwe-guide-web**: Neon: PostgreSQL; Neon (PostgreSQL)
- **simulator-lab**: Neon: политика simulator_ro в migrations 217; Neon (политика simulator_ro в migrations 217)
- **iwe-onboarding-controller**: Neon: onboarding_state; Neon (onboarding_state)
- **iwe-render-pilot-guides**: git-репозитории пилотов; Claude/LLM-прокси
- **observability-webhook**: KV
- **payment-receiver**: Neon: схема finance, FINTECH_DB_SCHEMA; Neon (схема finance, FINTECH_DB_SCHEMA); пересылка на FORWARD_URL
- **agent-runner**: Neon: личная БД знаний
- **bridge-scope-service**: Neon: DATABASE_URL
- **mentorship-service**: chec
- **chat-analyst-service**: собственная БД архива; LiteLLM/OpenRouter (в коде найдены упоминания)
- **iwe-llm-proxy**: Neon: proxy_calls, usage_cache; Neon (proxy_calls, usage_cache)
- **aist_bot_newarchitecture**: Neon: consent
- **restic**: Neon: строки подключения в /etc/restic/neon-connections; Neon (строки подключения в /etc/restic/neon-connections); Better S
- **bitcoind-ots-verify**: Neon: таблицы hash-chain, ots_anchors; Neon (таблицы hash-chain, ots_anchors)
- **Metabase**: Neon
- **Directus**: Neon
- **PostgreSQL 16 с pgvector на tsekh-1**: pgvector
- **DS-iwe-wp-panel**: карточки и реестр РП

Программы без подсистемы (с причиной):

- **Metabase**: отчёты для команды по базам Neon; функции платформы для пользователей не выполняет (решение 19.11.2026: «Общие базы и управление данными» — подпись группы, не подсистема)

Не перенесено как модуль:

- knowledge-mcp-template — документ (заготовка воркера), не модуль
- Aisystant LMS PostgreSQL — чужая система (§5.3); строка §5.1 — расхождение (Р8)

## Обратная сверка собранных таблиц DP.ARCH.001 со справочниками

- нет
