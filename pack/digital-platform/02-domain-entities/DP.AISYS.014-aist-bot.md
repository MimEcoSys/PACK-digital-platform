---
id: DP.AISYS.014
name: AIST Bot
type: ai-system-passport
status: draft
summary: "Telegram-бот экосистемы: тонкий клиент с сервисным реестром, ИИ-консультантом, биллингом и связью с цифровым двойником"
created: 2026-02-11
trust:
  F: 3
  G: domain
  R: 0.5
epistemic_stage: emerging
orientation: human
initiative: both
interface: dialogue
updated: 2026-02-18
related:
  specializes: [U.System]
  uses: [DP.ARCH.001, DP.ARCH.002, DP.ROLE.001, DP.NAV.001, DP.M.004, DP.RUNBOOK.001]
  integrates: [DP.AISYS.012, DP.AISYS.013]
---

# AIST Bot (@aist_me_bot)

> **Implementation Note.** Бот как тонкий клиент, сервисный реестр, 5-слойная архитектура, UX-принципы, FAQ — домен. Конкретная реализация (aiogram 3.x, FSM state names, Claude model routing Haiku/Sonnet, MCP server names) — текущая реализация. Детали: [C2.IT-Platform / System-Implementations](../../../DS-ecosystem-development/C.IT-Platform/C2.IT-Platform/C2.2.Architecture/System-Implementations/).

## 1. Определение

**AIST Bot** — ИИ-система (Telegram-бот), которая является основной точкой входа пользователя в экосистему. Тонкий клиент с сервисным реестром: подключает развитие, планирование, заметки, консультант, биллинг и цифровой двойник через единый интерфейс.

> Бот ≠ платформа. Бот = тонкий клиент, который маршрутизирует пользователя к сервисам.

## 2. Классификация

| Характеристика | Значение | Пояснение |
|----------------|----------|-----------|
| **Ориентация** | human | Работает напрямую с пользователем в Telegram |
| **Инициатива** | both | Отвечает на команды (reactive) и отправляет уведомления (proactive) |
| **Интерфейс** | dialogue | Telegram chat + inline keyboards + Mini Apps (для сложного UI) |

## 3. Архитектурные характеристики

| Характеристика | Определение | Как реализуется |
|----------------|-------------|-----------------|
| **Эволюционируемость** | Бесконечное подключение сервисов, БД, MCP без изменения структуры | Сервисный реестр: новый сервис = запись в реестре → меню обновляется |
| **Масштабируемость** | Бесконечное подключение пользователей без изменения архитектуры | `menu(user) = registry.filter(access).render()` — персонализация при росте |
| **Обучаемость** | Платформа улучшает решения на основе данных и обратной связи | Аналитика поведения → адаптивное меню + консультант с self-knowledge |
| **Генеративность** | Платформа порождает созидателей | Путь знания (заметка → Pack → продукт) + fork шаблона экзокортекса |

## 4. Слоёная архитектура

```
┌─────────────────────────────────────────────┐
│         СЛОЙ 1: Консультант (Self-Help)      │
│  Всегда доступен, знает бота, deep links     │
│  База знаний: о боте + о домене (через MCP)  │
├─────────────────────────────────────────────┤
│         СЛОЙ 2: Меню-генератор               │
│  menu(user) = registry.filter(access).render │
│  Сервисный реестр → фильтр по роли/подписке  │
├─────────────────────────────────────────────┤
│         СЛОЙ 3: Сервисы (домены)             │
│  Развитие | Планы | Заметки | Двойник | ...  │
│  Каждый сервис = модуль с собственным SM     │
├─────────────────────────────────────────────┤
│         СЛОЙ 4: Доступ + Биллинг             │
│  Роли, подписки, покупки курсов, paywall     │
│  3 типа: подписка + курсы + фичи            │
├─────────────────────────────────────────────┤
│         СЛОЙ 5: Аналитика + Обучаемость      │
│  Поведение → адаптация меню → улучшение UX   │
│  Цифровой двойник → персональная траектория  │
└─────────────────────────────────────────────┘
```

### 4.1. Слой 1: Консультант (Self-Help)

Консультант — это **слой поверх всего бота**, не отдельный домен в меню.

| Свойство | Значение |
|----------|----------|
| Доступ | Текстовый ввод без команды + кнопка `❓` в каждом меню |
| Знание о боте | База знаний о структуре, командах, путях (обновляется из реестра сервисов) |
| Знание о домене | Через MCP (guides, knowledge) |
| Deep links | Может не только объяснить, но и перенаправить в нужный сервис |

#### 4.1.1. Self-Knowledge (Самознание)

Трёхуровневая модель самознания — бот знает о себе и может точно отвечать на вопросы о своей структуре и возможностях. **Эта секция — source-of-truth** для знаний бота о себе. Бот читает её при запуске и кеширует.

| Уровень | Содержит | Источник | Обновляется | Скорость |
|---------|----------|----------|-------------|----------|
| **L1: Кеш** | Описания, сценарии, FAQ (из этой секции) + граф сервисов из реестра | Pack (этот файл) → кеш в памяти | Раз в день / при рестарте | ~100ms |
| **L2: MCP** | Полная база знаний Pack через MCP + быстрая модель | MCP-запрос к Pack | По запросу | ~1-3 сек |
| **L3: Полный поиск** | MCP guides + knowledge + Sonnet | MCP-поиск + Claude | По запросу | ~3-8 сек |

**Реализация:** `core/self_knowledge.py` — читает эту секцию из Pack, мержит с ServiceRegistry, кеширует по языкам.

**Три пути обработки вопросов:**
- L1: FAQ-матч или частый вопрос → мгновенный ответ из кеша
- L2: Вопрос о боте, не в кеше → Claude Haiku + self-knowledge (без MCP-поиска)
- L3: Доменный вопрос → MCP-поиск + Claude Sonnet + self-knowledge в system prompt

**Persistent Session:** После ответа бот остаётся в стейте консультации. Текст без `?` трактуется как follow-up. Claude получает conversation history (до 5 пар вопрос-ответ, обрезанных до 800 символов). Три механизма выхода: кнопка «Завершить», таймаут 5 мин неактивности, глобальная команда (/mode, /learn и т.п.).

##### Идентичность бота

**Имя:** AIST Bot (@aist_me_bot)

**Назначение (ru):** Бот-наставник для систематического развития. Помогает изучать системное мышление через структурированные программы, отвечает на вопросы, ведёт заметки и отслеживает прогресс.

**Назначение (en):** Mentor bot for systematic development. Helps study systems thinking through structured programs, answers questions, keeps notes, and tracks progress.

**Как задать вопрос (ru):** Начни сообщение с `?` чтобы задать вопрос консультанту в любой момент.

**Как задать вопрос (en):** Start your message with `?` to ask the consultant a question at any time.

##### Сценарии

Статусы: ✅ реализовано, 🚧 в разработке, 📋 запланировано. Бот показывает пользователю только ✅.

| # | Сценарий | Команда | Статус | Описание (ru) | Описание (en) |
|---|----------|---------|--------|---------------|---------------|
| 1 | Онбординг | `/start` | ✅ | Первый запуск: знакомство, заполнение профиля, выбор режима | First launch: introduction, profile setup, mode selection |
| 2 | Выбор режима | `/mode` | ✅ | Переключение между Марафоном, Лентой и другими программами | Switch between Marathon, Feed, and other programs |
| 3 | Марафон | `/learn` (mode=marathon) | ✅ | 14-дневная программа: каждый день теория → вопрос на понимание → бонусный вопрос → практическое задание. Прогресс сохраняется | 14-day program: daily theory → comprehension question → bonus question → practical task. Progress is saved |
| 4 | Лента | `/feed` | ✅ | Гибкий режим: выбираешь до 3 тем, получаешь ежедневные дайджесты с углублением | Flexible mode: choose up to 3 topics, receive daily digests with increasing depth |
| 5 | Тест систематичности | `/test` (`/assessment`) | ✅ | Data-driven тест: 16 вопросов → состояние (Хаос/Тупик/Поворот/Развитие; при равенстве баллов — «смешанное») → адаптация контента Марафона и Ленты через DP.M.004 (стиль, bloom_level, тематика) | Data-driven assessment: 16 questions → state (Chaos/Deadlock/Turning Point/Development; a tie is stored as mixed) → content adaptation for Marathon and Feed via DP.M.004 (style, bloom_level, topics) |
| 6 | Консультация | `?вопрос` | ✅ | Задать вопрос консультанту из любого места в боте. Persistent session: после первого ответа можно задавать follow-up вопросы без «?». Claude получает историю диалога (до 5 пар). Выход: кнопка «Завершить» / таймаут 5 мин / глобальная команда. Ответ на основе базы знаний и MCP | Ask the consultant a question from anywhere in the bot. Persistent session: after the first answer you can ask follow-up questions without `?`. Claude receives conversation history (up to 5 pairs). Exit: "End session" button / 5 min timeout / global command. Answer based on knowledge base and MCP |
| 7 | Заметки | `.текст` | ✅ | Четыре способа: 1) `.текст` — прямая заметка; 2) `.` (или `. комментарий`) + reply — объединить с сообщением, на которое отвечаешь; 3) `. комментарий` → forward — написать комментарий, потом переслать: комментарий станет заголовком; 4) forward → `.` (или `. комментарий`) — сначала переслать, потом добавить точку. Бот ждёт вторую часть 10 сек и объединяет. | Four ways: 1) `.text` — direct note; 2) `.` (or `.comment`) + reply — merge with the replied message; 3) `.comment` → forward — write a comment, then forward: comment becomes the title; 4) forward → `.` (or `.comment`) — forward first, then add dot. Bot waits 10 sec for the second part and merges. |
| 8 | Прогресс | `/progress` | ✅ | Статистика активности: пройденные темы, текущий день марафона, выполненные задания | Progress stats: completed topics, current marathon day, completed tasks |
| 9 | Планы (Стратег) | `/rp`, `/plan`, `/report` | ✅ | Интеграция со Стратегом: список рабочих продуктов, план на неделю, отчёт | Strategist integration: work products list, weekly plan, report |
| 10 | Настройки | `/settings` (`/update`) | ✅ | Язык, подключения, сброс марафона/статистики | Language, connections, marathon/stats reset |
| 11 | Профиль | `/profile` | ✅ | Персональные данные: имя, профессия, интересы, цели, оценка систематичности | Personal data: name, occupation, interests, goals, systematicity assessment |
| 12 | Мои данные | `/mydata` | ✅ | Просмотр данных пользователя по 5 категориям с ИИ-объяснениями | View user data in 5 categories with AI explanations |
| 13 | Помощь | `/help` | ✅ | Справка и полный список команд бота | Help and full list of bot commands |
| 14 | Язык | `/language` | ✅ | Быстрая смена языка интерфейса (ru, en, es, fr) | Quick interface language change (ru, en, es, fr) |
| 15 | Цифровой двойник | `/twin` | ✅ | Подключение и синхронизация с персональным цифровым двойником через Gateway MCP. Чтение/запись ЦД, степени квалификации, insights. Профиль → ЦД через Ory OAuth | Connect and sync with personal digital twin via Gateway MCP. Read/write DT, qualification degrees, insights. Profile → DT via Ory OAuth |
| 16 | Экспорт | `/export` | 📋 | Экспорт данных пользователя | Export user data |
| 17 | Аналитика (dev) | `/analytics` | ✅ | Сводная аналитика IWE: DAU/WAU/MAU, сессии, latency, retention D1/D7/D30, тренды. Только для разработчика | IWE summary analytics: DAU/WAU/MAU, sessions, latency, retention D1/D7/D30, trends. Dev-only |
| 18 | L1 Unstick | — (auto) | ✅ | Автоматическое восстановление застрявших пользователей: 3+ ошибки за 5 мин или stuck в state >60 мин → сброс FSM → mode_select + извинение. Scheduler каждые 5 мин | Automatic recovery of stuck users: 3+ errors in 5 min or stuck in state >60 min → FSM reset → mode_select + apology. Scheduler every 5 min |
| 19 | L2 Auto-Fix | — (auto+approval) | ✅ | Автоматическая диагностика L2-ошибок: scheduler каждые 15 мин → Claude Sonnet анализирует ошибку + исходный код → диагноз + ArchGate-оценка → TG-сообщение разработчику с кнопками [✅ Применить / ❌ Отклонить] → на ✅ создаётся GitHub PR с исправлением. Безопасность: max 3 файла, protected files, always PR. См. DP.RUNBOOK.001 §6 | Automatic L2 error diagnosis: scheduler every 15 min → Claude Sonnet analyzes error + source code → diagnosis + ArchGate evaluation → TG message to developer with [✅ Apply / ❌ Reject] buttons → on ✅ creates GitHub PR with fix. Safety: max 3 files, protected files, always PR. See DP.RUNBOOK.001 §6 |
| 20 | Grafana Alerting | — (auto) | ✅ | Независимый мониторинг через Grafana Cloud: 4 правила (L3+ Critical, Unknown Spike, Error Rate Anomaly, Heartbeat Lost) → TG-уведомления. Не зависит от процесса бота. См. DP.RUNBOOK.001 §5 | Independent monitoring via Grafana Cloud: 4 rules (L3+ Critical, Unknown Spike, Error Rate Anomaly, Heartbeat Lost) → TG notifications. Independent of bot process. See DP.RUNBOOK.001 §5 |
| 21 | Подключение IWE | `/connect` | ✅ | Пошаговые инструкции для подключения AI-клиентов к платформе через Gateway MCP. Поддерживает: claude.ai, Cursor/Windsurf/Cline, ChatGPT, Claude Code. Единый URL: https://mcp.aisystant.com/mcp. Доступно из /start (новые) и меню T2+ | Step-by-step instructions for connecting AI clients to the platform via Gateway MCP. Supports: claude.ai, Cursor/Windsurf/Cline, ChatGPT, Claude Code. Single URL: https://mcp.aisystant.com/mcp. Available from /start (new users) and T2+ menu |

##### FAQ

| # | Вопрос (ru) | Вопрос (en) | Ключевые слова | Ответ (ru) | Ответ (en) |
|---|-------------|-------------|----------------|------------|------------|
| 1 | Как начать работу? | How to start? | начать, старт, start, begin | Используй `/learn`. Если ещё не выбран режим — бот предложит выбрать Марафон или Ленту через `/mode`. | Use `/learn`. If no mode is selected yet, the bot will offer to choose Marathon or Feed via `/mode`. |
| 2 | Как работает Марафон? | How does the Marathon work? | марафон, marathon, 14 дн | Марафон — 14-дневная программа. Каждый день: теоретический материал + практическое задание. Прогресс сохраняется, можно продолжить с того места, где остановился. | Marathon is a 14-day program. Each day: theory material + practical task. Progress is saved, you can continue where you left off. |
| 3 | Как работает Лента? | How does the Feed work? | лент, feed, дайджест | Лента — гибкий формат развития. Выбираешь до 3 интересных тем, получаешь ежедневные дайджесты с постепенным углублением. | Feed is a flexible development format. Choose up to 3 topics, receive daily digests with gradual deepening. |
| 4 | Как сменить язык? | How to change the language? | язык, language, english | Открой `/settings` и выбери нужный язык. Доступны: русский, английский, испанский, французский. | Open `/settings` and select the desired language. Available: Russian, English, Spanish, French. |
| 5 | Как создать заметку? | How to create a note? | замет, note, запис | Четыре способа: 1) `.текст` — точка и текст сразу. 2) Ответь на сообщение с `.` или `. комментарий` — бот объединит. 3) `. комментарий` и потом перешли сообщение — комментарий станет заголовком заметки. 4) Перешли сообщение и потом отправь `.` или `. комментарий`. Бот ждёт 10 сек и объединяет оба. | Four ways: 1) `.text` — dot and text at once. 2) Reply to a message with `.` or `.comment` — bot merges them. 3) Write `.comment` then forward a message — comment becomes the note title. 4) Forward a message then send `.` or `.comment`. Bot waits 10 sec and merges both. |
| 6 | Как пройти тест? | How to take the test? | тест, оценк, assessment, уров, влия | Используй `/test` — 16 вопросов определят твоё состояние (Хаос, Тупик, Поворот или Развитие); если баллы поровну, бот покажет все лидирующие состояния. После теста бот адаптирует контент: стиль занятий, сложность вопросов и темы Ленты подстраиваются под твоё состояние. Повторный тест через 2-4 недели покажет прогресс. | Use `/test` — 16 questions identify your state (Chaos, Deadlock, Turning Point, or Development); on a tie the bot shows all leading states. After the test, the bot adapts content: session style, question difficulty, and Feed topics adjust to your state. Retake after 2-4 weeks to see progress. |
| 7 | Как задать вопрос? | How to ask a question? | помощ, помог, help, вопрос, сесси, session | Начни сообщение с `?` и напиши вопрос. Например: `?Что такое системное мышление?` После ответа ты останешься в режиме консультации — можно задавать уточняющие вопросы без `?`. Консультант помнит контекст (до 5 вопросов). Для выхода нажми «Завершить» или подожди 5 минут. | Start with `?` and type your question. Example: `?What is systems thinking?` After the answer you stay in consultation mode — you can ask follow-up questions without `?`. The consultant remembers context (up to 5 questions). To exit, tap "End session" or wait 5 minutes. |
| 8 | Как работать с планами? | How to work with plans? | план, рп, plan, report | Используй `/rp` для списка рабочих продуктов, `/plan` для плана на неделю, `/report` для отчёта. Интегрировано со Стратегом. | Use `/rp` for work products, `/plan` for weekly plan, `/report` for a report. Integrated with the Strategist. |
| 9 | Кто ты? | Who are you? | кто ты, кто вы, who are you, what are you | Я — AIST Bot (@aist_me_bot), бот-наставник в экосистеме развития интеллекта.\n\nЭкосистема — это среда, где люди развивают мышление и становятся созидателями. В ней три компонента: Мастерская (практикумы, семинары), Сообщество 13 000+ инженеров-менеджеров (systemsworld.club) и ИИ-платформа — интеллектуальная рабочая среда (IWE).\n\nЯ — часть IWE. Через меня ты получаешь персонализированные материалы, тренируешь принципы, задаёшь вопросы ИИ-консультанту (по базе ~5 300 документов), ведёшь заметки, отслеживаешь прогресс и управляешь развитием.\n\nС чего начать: `/mode` — выбрать режим, `/about` — подробнее о нас. | I'm AIST Bot (@aist_me_bot), a mentor bot in the Ecosystem for Intelligence Development.\n\nThe ecosystem is an environment where people develop thinking and become creators. It has three components: Workshop (practicums, seminars), Community of 13,000+ engineers-managers (systemsworld.club), and AI Platform — Intellectual Work Environment (IWE).\n\nI'm part of IWE. Through me you get personalized materials, train principles, ask the AI consultant questions (powered by ~5,300 documents), keep notes, track progress, and manage your development.\n\nWhere to start: `/mode` — choose a mode, `/about` — more about us. |
| 10 | Что ты умеешь? | What can you do? | умеешь, можешь, умеет, capabilities, what can | Развитие:\n• Марафон (`/learn`) — бесплатная 14-дневная программа с персонализированными материалами и заданиями\n• Лента (`/feed`) — ежедневные дайджесты по выбранным темам с углублением\n• Тренировка (`/train`) — интерактивная отработка принципов с ИИ-обратной связью\n• Тест (`/test`) — 12 вопросов, определяющих состояние и адаптирующих контент\n\nИИ-консультант:\n• `?вопрос` — ответы на основе базы знаний, с сохранением контекста диалога\n\nОрганизация:\n• `.текст` — заметки (4 способа: прямая, reply, forward, комбо)\n• `/progress` — статистика и серии активных дней\n• `/rp` `/plan` `/report` — планы через интеграцию со Стратегом\n\nНастройки: `/mode` (режим), `/settings` (язык, профиль, подключения), `/profile` (персонализация). | Development:\n• Marathon (`/learn`) — free 14-day program with personalized materials and tasks\n• Feed (`/feed`) — daily digests on chosen topics with increasing depth\n• Training (`/train`) — interactive principle practice with AI feedback\n• Test (`/test`) — 12 questions that identify your state and adapt content\n\nAI Consultant:\n• `?question` — answers from knowledge base, with conversation context\n\nOrganization:\n• `.text` — notes (4 ways: direct, reply, forward, combo)\n• `/progress` — stats and activity streaks\n• `/rp` `/plan` `/report` — plans via Strategist integration\n\nSettings: `/mode` (mode), `/settings` (language, profile, connections), `/profile` (personalization). |
| 11 | Как сбросить марафон? | How to reset the marathon? | сброс, сбросить, reset, обнулить, заново, restart | Открой `/settings` → кнопка «Сброс» → «Сбросить марафон» → подтверди. Прогресс обнулится, марафон начнётся с 1-го дня. Также можно сбросить через `/profile`. | Open `/settings` → "Reset" button → "Reset marathon" → confirm. Progress resets, marathon starts from day 1. You can also reset via `/profile`. |
| 12 | Как сбросить статистику? | How to reset statistics? | сброс стат, статистик, reset stats, обнулить стат | Открой `/settings` → кнопка «Сброс» → «Сбросить статистику» → подтверди. Сбрасываются серии активных дней. Ответы и прогресс сохраняются. | Open `/settings` → "Reset" button → "Reset statistics" → confirm. Active day streaks are reset. Answers and progress are preserved. |
| 13 | Как работает персонализация? | How does personalization work? | персонал, адапт, подстра, adapt, personaliz, customize | Бот хранит твой профиль в одном месте (БД бота) и использует его при генерации контента.\n\nПрофиль (/profile) — имя, профессия, интересы, цели. Бот подстраивает примеры, стиль и контент.\n\nТест систематичности (/test) — определяет состояние (Хаос/Тупик/Поворот) и адаптирует стиль занятий, сложность и темы Ленты.\n\nОпционально: Цифровой двойник — при подключении профиль экспортируется в ЦД для построения индивидуальной траектории. Это однонаправленный экспорт (бот → ЦД), не отдельный «уровень» хранения. | The bot stores your profile in one place (bot DB) and uses it when generating content.\n\nProfile (/profile) — name, occupation, interests, goals. The bot tailors examples, style, and content.\n\nSystematicity test (/test) — determines your state (Chaos/Deadlock/Turning Point) and adapts session style, difficulty, and Feed topics.\n\nOptionally: Digital twin — when connected, the profile is exported to the DT for building an individual trajectory. This is a one-way export (bot → DT), not a separate storage "level". |
| 14 | Что делает бот в составе IWE? | What does the bot do in IWE? | бот, iwe, роль, зачем, что делает, purpose, role, what does | @aist_me_bot — платформенный сервис (L2), общий для всех. Не нужно разворачивать своего. Бот делает: Марафон (14-дневная программа), Лента (дайджесты по выбранным темам), Консультации (ответы по базе ~5300 документов), Заметки (быстрые мысли, которые потом обрабатывает Стратег), Планы (дневной/недельный план через GitHub strategy-репо), Прогресс (streak, сложность), Тест систематичности, Цифровой двойник, интеграции (GitHub, WakaTime). Бот — один из интерфейсов платформы, не центр. Центр — экзокортекс и агенты. Бот, Claude Code, веб — разные окна в одну среду. | @aist_me_bot is a platform service (L2), shared by all users. No need to deploy your own. The bot provides: Marathon (14-day program), Feed (digests on chosen topics), Consultations (answers from ~5300 docs), Notes (quick thoughts processed by Strategist), Plans (daily/weekly via GitHub strategy repo), Progress (streak, complexity), Systematicity Test, Digital Twin, integrations (GitHub, WakaTime). The bot is one of the platform's interfaces, not the center. The center is the exocortex and agents. Bot, Claude Code, web — different windows into one environment. |
| 15 | Нужен ли мне свой бот? | Do I need my own bot? | свой бот, own bot, развернуть, deploy, разработать, build | Зависит от цели. Если хочешь пользоваться марафоном, лентой, консультациями — @aist_me_bot уже работает, свой не нужен. Если хочешь Стратега с планами — это работает через IWE-шаблон (экзокортекс + Claude Code), бот подтягивает результат. Если хочешь разрабатывать свою платформу — тогда свой бот имеет смысл, но это другая задача. | Depends on your goal. If you want to use marathon, feed, consultations — @aist_me_bot already works, no need for your own. If you want a Strategist with plans — that works through the IWE template (exocortex + Claude Code), the bot pulls the result. If you want to develop your own platform — then your own bot makes sense, but that's a different task. |

##### Troubleshooting (Решение проблем)

> Пользовательские проблемы и решения. Консультант использует эту таблицу для помощи пользователям.
> Отличие от DP.RUNBOOK.001: Runbook = для агентов/разработчиков (технические действия). Troubleshooting = для пользователей (что делать самому).

| # | Проблема (ru) | Problem (en) | Ключевые слова | Решение (ru) | Solution (en) |
|---|---------------|--------------|----------------|-------------|---------------|
| T1 | Бот не отвечает | Bot doesn't respond | не отвечает, молчит, тишина, not responding, silent, no response | Подожди 10-15 секунд — иногда ответ генерируется дольше обычного. Если бот молчит больше минуты, отправь `/start` для перезапуска. Если не помогло — подожди 5 минут и попробуй снова, возможно идёт техническое обслуживание. | Wait 10-15 seconds — sometimes responses take longer than usual. If the bot is silent for more than a minute, send `/start` to restart. If that doesn't help, wait 5 minutes and try again — maintenance may be in progress. |
| T2 | Я застрял, ничего не работает | I'm stuck, nothing works | застрял, stuck, завис, не работает, not working, broken, зависло | Отправь `/mode` — это вернёт тебя в главное меню выбора режима. Если не помогает — отправь `/start`. Бот также автоматически обнаруживает застревания и восстанавливает пользователей каждые 5 минут. | Send `/mode` — this will return you to the main mode selection menu. If that doesn't help — send `/start`. The bot also automatically detects stuck users and recovers them every 5 minutes. |
| T3 | Кнопки пропали / не нажимаются | Buttons disappeared / don't work | кнопки, buttons, нажать, не нажимается, пропали, disappeared, click, press | Иногда кнопки в старых сообщениях перестают работать. Отправь `/mode` или `/start` — бот пришлёт новое сообщение с рабочими кнопками. Если кнопка показывает часики — подожди, запрос обрабатывается. | Sometimes buttons in old messages stop working. Send `/mode` or `/start` — the bot will send a new message with working buttons. If a button shows a loading spinner — wait, the request is being processed. |
| T4 | Мой прогресс пропал | My progress is lost | прогресс, пропал, потерял, progress, lost, исчез, disappeared, данные | Твой прогресс сохраняется в базе данных и НЕ теряется. Проверь через `/progress`. Если ты видишь «День 1» — возможно, был случайный сброс марафона. Проверь `/settings` → «Сброс». Если проблема остаётся — напиши `.баг прогресс пропал` чтобы разработчик увидел. | Your progress is saved in the database and is NOT lost. Check via `/progress`. If you see "Day 1" — the marathon might have been accidentally reset. Check `/settings` → "Reset". If the problem persists — write `.bug progress lost` so the developer can see it. |
| T5 | Бот отвечает на чужом языке | Bot responds in wrong language | язык, language, другой язык, wrong language, не тот язык, english, russian | Отправь `/language` и выбери нужный язык. Доступны: русский, английский, испанский, французский. Если команда не работает — найди кнопку `🌐 Language` в главном меню (она всегда на английском). | Send `/language` and choose the desired language. Available: Russian, English, Spanish, French. If the command doesn't work — find the `🌐 Language` button in the main menu (it's always in English). |
| T6 | Ответ очень долгий | Response takes too long | долго, медленно, ждать, slow, waiting, long, тормозит, loading | Обычно ответ приходит за 2-5 секунд. Если ждёшь больше 15 секунд — скорее всего, сервис ИИ перегружен. Подожди минуту и повтори вопрос. Консультация (`?вопрос`) может занимать до 8 секунд — это нормально, идёт поиск по базе знаний. | Usually responses arrive in 2-5 seconds. If you wait more than 15 seconds — the AI service is likely overloaded. Wait a minute and repeat your question. Consultation (`?question`) can take up to 8 seconds — this is normal, the knowledge base is being searched. |
| T7 | Бот написал «произошла ошибка» | Bot said "an error occurred" | ошибка, error, сбой, что-то пошло не так, something went wrong | Это временная проблема — просто повтори действие. Если ошибка повторяется 3+ раза — бот автоматически вернёт тебя в главное меню. Для сообщения об ошибке напиши `.баг описание проблемы` — разработчик получит уведомление. | This is a temporary issue — just retry the action. If the error repeats 3+ times — the bot will automatically return you to the main menu. To report a bug, write `.bug description of the problem` — the developer will be notified. |
| T8 | Не приходят ежедневные материалы/дайджесты | Daily materials/digests not arriving | не приходят, уроки, занятие, занятия, дайджест, урок, не получаю, not receiving, no materials, digest, напоминания, reminders | Проверь время доставки в `/settings` → установи удобное время. Убедись, что ты не заблокировал бота в Telegram. Если в Ленте — убедись, что выбраны темы (через `/feed`). Если в Марафоне — отправь `/learn` чтобы продолжить. | Check delivery time in `/settings` → set a convenient time. Make sure you haven't blocked the bot in Telegram. If in Feed — make sure topics are selected (via `/feed`). If in Marathon — send `/learn` to continue. |
| T9 | Хочу начать всё заново | I want to start over | заново, сначала, start over, reset everything, с нуля, обнулить всё | Есть два вида сброса в `/settings` → «Сброс»:\n\n1) «Сбросить марафон» — начнёшь с 1-го дня, ответы сохранятся.\n2) «Сбросить статистику» — обнулятся серии активных дней.\n\nЕсли хочешь сменить режим (Марафон ↔ Лента) — используй `/mode`. Полный сброс всех данных: `/settings` → «Сброс» → все варианты. | There are two types of reset in `/settings` → "Reset":\n\n1) "Reset marathon" — start from day 1, answers are preserved.\n2) "Reset statistics" — active day streaks reset.\n\nIf you want to switch mode (Marathon ↔ Feed) — use `/mode`. Full data reset: `/settings` → "Reset" → all options. |
| T10 | Консультант не понимает мой вопрос | Consultant doesn't understand my question | не понимает, не знает, глупый, doesn't understand, wrong answer, неправильный ответ, не по теме | Попробуй переформулировать вопрос — начни с `?` и будь конкретнее. Например, вместо `?системы` напиши `?что такое системное мышление и зачем оно нужно?`. Консультант лучше отвечает на полные вопросы. Если ответ не помог — нажми 👎 чтобы дать обратную связь, это поможет улучшить консультанта. | Try rephrasing your question — start with `?` and be more specific. For example, instead of `?systems`, write `?what is systems thinking and why is it needed?`. The consultant works better with complete questions. If the answer didn't help — tap 👎 to give feedback, this helps improve the consultant. |

##### Модель платформы

> Когда пользователь спрашивает о своём «уровне», «статусе», «доступе», «тарифе», «подписке», «возможностях», «что доступно», «как расти», «что бесплатно», «сколько стоит» — он спрашивает об этой модели.

Платформа имеет 5 основных тиров участника (T0-T4) и 3 ортогональные оси: TM (наставники), TA (администраторы), TD (разработчики). Каждый следующий T-тир включает всё из предыдущего. T5-T9 зарезервированы.

**🟢 T0/T1 — Старт** (бесплатно):
- Марафон 14 дней (/learn) — бесплатно навсегда
- Тест систематичности (/test) — определяет состояние и адаптирует контент
- Прогресс (/progress) — статистика активности
- Профиль (/profile) и Настройки (/settings)
- Лента, консультации, заметки, планы — только по подписке БР

**📘 T2 — Изучение** (подписка БР):
- Лента (/feed) — персональные ежедневные дайджесты по выбранным темам
- Консультант (?вопрос) — ответы на основе базы знаний с расширенным контекстом
- Заметки (.текст) — сохранение мыслей и идей
- Планы (/rp /plan /report) — интеграция со Стратегом

**Подписка:** «Бесконечное развитие» (БР) на system-school.ru — единственная подписка. TG Stars — опциональные донаты, не подписка.

**🧬 T3 — Персонализация** (подключён любой AI-клиент):
- Персональное руководство под твои цели, ступень и активные РП
- Гермес знает твою историю (Память.Derived)
- Усиленная адаптация контента

Как перейти на T3 (нужна активная подписка + подключить любой AI-клиент — WP-406 Ф13):
- В боте: /connect_external — подключить через Telegram
- Или в claude.ai: Connect → Aisystant MCP (OAuth)
- Или Claude Code / VS Code с Aisystant MCP
- Профиль (/profile) и тест (/test) повышают качество персонализации, но T3 открывает именно подключённый AI-клиент

**🚀 T4 — Созидание** (локальный экзокортекс):
- Claude Code + агенты (Стратег, Экстрактор, Синхронизатор)
- Личная база знаний (Pack)
- GitHub-интеграция (/settings → Подключения)

**Ортогональные оси** (назначаются владельцем):
- **TA1-TA4** — администраторы: управление потоками и финансами
- **TM1-TM3** — наставники: проверка ДЗ и обратная связь
- **TD1** — разработчик: исходный код, деплой, управление standard/

**Цифровой двойник:** персональное хранилище целей, проблем, интересов и самооценки. Позволяет боту давать индивидуальные рекомендации.

**Программы развития на платформе:**
- Личное развитие (ЛР) — вводная, подходит всем
- Рабочее развитие (РР) — для менеджеров и инженеров
- Исследовательское развитие (ИР) — для исследователей

Посмотреть свои данные и текущий уровень: /mydata.

[EN]

When a user asks about their "level", "status", "access", "plan", "subscription", "capabilities", "what's available", "how to grow", "what's free", "how much" — they are asking about this model.

The platform has 5 learner tiers (T0-T4) and 3 orthogonal axes: TM (mentors), TA (admins), TD (developers). Each T-tier includes everything from the previous one. T5-T9 are reserved.

**🟢 T0/T1 — Start** (free):
- 14-day Marathon (/learn) — free forever
- Systematicity Test (/test) — identifies state and adapts content
- Progress (/progress) — activity statistics
- Profile (/profile) and Settings (/settings)
- Feed, consultations, notes, plans — subscription only

**📘 T2 — Study** (БР subscription):
- Feed (/feed) — personal daily digests on chosen topics
- Consultant (?question) — knowledge-base answers with extended context
- Notes (.text) — saving thoughts and ideas
- Plans (/rp /plan /report) — Strategist integration

**Subscription:** «Бесконечное развитие» (БР) on system-school.ru — the only subscription. TG Stars are optional donations, not a subscription.

**🧬 T3 — Personalization** (any AI client connected):
- Personal guide tailored to your goals, mastery stage and active work products
- Hermes knows your history (Memory.Derived)
- Enhanced content adaptation

How to reach T3 (active subscription + connect any AI client — WP-406 Ф13):
- In the bot: /connect_external — connect via Telegram
- Or in claude.ai: Connect → Aisystant MCP (OAuth)
- Or Claude Code / VS Code with Aisystant MCP
- Profile (/profile) and test (/test) improve personalization quality, but T3 is unlocked by a connected AI client

**🚀 T4 — Creation** (local exocortex):
- Claude Code + agents (Strategist, Extractor, Synchronizer)
- Personal knowledge base (Pack)
- GitHub integration (/settings → Connections)

**Orthogonal axes** (assigned by owner):
- **TA1-TA4** — admins: stream management and finances
- **TM1-TM3** — mentors: homework review and feedback
- **TD1** — developer: source code, deploy, standard/ management

**Digital Twin:** personal storage for goals, problems, interests, and self-assessment. Enables the bot to give individual recommendations.

**Development programs on the platform:**
- Personal Development (ЛР) — introductory, fits everyone
- Professional Development (РР) — for managers and engineers
- Research Development (ИР) — for researchers

View your data and current level: /mydata.

### 4.2. Слой 2: Меню-генератор

Меню **генерируется** из реестра сервисов, а не захардкожено.

```
Реестр сервисов (конфиг/БД)
  → Фильтр по роли + подписке пользователя
    → Группировка по категориям
      → Генерация inline keyboard
```

**Принцип:** добавил новый MCP-сервис → добавил запись в реестр → меню обновилось. Ноль изменений в UI-коде.

### 4.3. Слой 3: Сервисы (домены)

| Домен | Что делает | Текущий статус |
|-------|-----------|----------------|
| **Развитие** | Марафон (14 дней) + Лента (гибкий режим) + тестирование | Active |
| **Планы** | Интеграция со Стратегом: /rp, /plan, /report | Active |
| **Заметки** | Исчезающие заметки: «.текст», «.» + reply/forward | Active |
| **Консультант** | ИИ через MCP: ответы на вопросы по знаниям | In progress |
| **Цифровой двойник** | Персональный профиль + индивидуальная траектория | In progress |
| **Расписание** | Курсы, события, уведомления | Planned |
| **Биллинг** | Подписка + курсы + фичи | Planned |

**Каждый домен = отдельный модуль** (handler + states + engine). Добавление нового домена не затрагивает существующие.

### 4.4. Слой 4: Доступ + Биллинг

> Тиры платформы (T0–T4 + TM + TA + TD) определяют конфигурацию среды: какие знания, данные, роль ИИ, действия и рабочее пространство доступны. Подробнее: [DP.ARCH.002 Тиры платформы](DP.ARCH.002-service-tiers.md).
> Бот реализует T0 (без Ory), T1 (Старт) и T2 (Изучение), частично T3 (Персонализация). T4 и TD1 работают через Claude Code.

Биллинг — **слой доступа**, не домен в меню.

| Тип платного | Механизм | Как влияет на UI |
|-------------|----------|------------------|
| **Подписка** | Рекуррентная (бот) | Определяет набор доступных сервисов |
| **Курсы** | Разовая покупка | Открывает конкретный курс в сервисе «Развитие» |
| **Фичи** | Paywall на функцию | Показывает paywall в момент попытки доступа |

```
user.has_access(service) = user.subscription ∪ user.purchases ∪ user.role
```

### 4.5. Слой 5: Аналитика + Цифровой двойник

| Функция | Данные | Результат |
|---------|--------|-----------|
| **Адаптивная персонализация** | assessment_state из /test | Стиль контента + bloom_level + тематика Ленты (DP.M.004) |
| **Session tracking** | user_sessions (30-мин timeout) | Avg duration, requests/session, entry/exit points |
| **/analytics** (dev) | DAU/WAU/MAU, sessions, latency, retention | Сводный отчёт для разработчика |
| **L1 Unstick** | error_logs (3+ за 5 мин), request_traces (stuck >60 мин) | Автоматический reset FSM → mode_select |
| Частотный анализ | Какие кнопки нажимают | Адаптивный порядок меню |
| Анализ застреваний | Где нажимают «Назад» | Упрощение навигации |
| Цифровой двойник | Профиль + прогресс + заметки | **Персональная траектория развития** |
| Индивидуальные сценарии | Двойник + контекст | Рекомендации: что учить следующим |

#### 4.5.1. Маппинг данных: Бот → Цифровой двойник

> **Implementation Note.** Конкретные поля БД, пути в ЦД, индикаторы, реализация синхронизации → [C2.IT-Platform / System-Implementations / DP.AISYS.014-aist-bot-implementation.md](../../../DS-ecosystem-development/C.IT-Platform/C2.IT-Platform/C2.2.Architecture/System-Implementations/DP.AISYS.014-aist-bot-implementation.md).

**Доменный принцип:** При подключении ЦД данные из профиля бота автоматически переливаются в ЦД. Три механизма: при подключении (полный sync), при обновлении профиля (инкрементальный), ежечасная проверка (safety net). 10 полей профиля, системные поля не переливаются.

## 5. UX-принципы

### 5.1. Progressive Disclosure

- Главное меню: до 8 кнопок-сервисов (scenario + system)
- Каждый домен раскрывается в под-меню
- Глубина навигации: **максимум 3 уровня**
- Новые функции появляются по мере роста пользователя

### 5.2. Inline Keyboard vs Mini App

| Инструмент | Когда |
|-----------|-------|
| **Inline Keyboard** | Выбор из 2-8 опций, подтверждения, навигация ≤3 уровней |
| **Mini App (WebApp)** | Расписание (календарь), дашборд прогресса, оплата, длинные формы |

**Критерий перехода:** если keyboard уходит глубже 3 уровней или показывает >50 элементов → Mini App.

### 5.3. Навигация

- **Persistent Menu** (`/start`, `/learn`, `/plan`, `/help`) — всегда через «/»
- **Контекстное меню** — после каждого действия 2-3 релевантные кнопки
- **Callback routing** — паттерн `domain:action:param` (масштабируемый)
- **`edit_message_reply_markup`** вместо нового сообщения (чат не засоряется)
- **Кнопка «← Назад»** на каждом уровне

### 5.4. Антипаттерны

- Стена кнопок (>8 в одном сообщении)
- Глубокая навигация без «Назад»
- Смешение доменов в одном меню
- Повторная отправка всего меню (вместо `edit_message`)

### 5.5. Языковая доступность (Language Accessibility)

**Принцип:** Пользователь, не знающий текущего языка бота, ДОЛЖЕН найти переключатель языка за ≤1 клик.

**Реализация (3 уровня избыточности):**

| Уровень | Механизм | Почему работает |
|---------|----------|-----------------|
| **Главное меню** | Кнопка `🌐 Language` (всегда на EN) | Визуально распознаётся по эмодзи + lingua franca |
| **BotCommands** | `/language` в Telegram-меню команд | Доступна из любого стейта |
| **Onboarding** | Выбор языка ДО ввода имени (unsupported languages) | Не допускает ситуацию «застрял в чужом языке» |

**Ключевое решение:** Кнопка `🌐 Language` в главном меню **НЕ локализуется** — она всегда на английском. Это единственное исключение из правила i18n, обоснованное тем, что целевой пользователь по определению не читает текущий язык.

**Failure mode (до исправления):** Пользователь с неподдерживаемым языком Telegram (DE, KO, AR...) попадал в русский интерфейс и не мог найти смену языка без чтения «Настройки» → «Сменить язык» на русском.

## 6. Текущая реализация

> **Implementation Note.** State Machine (YAML-driven), aiogram 3.x, Claude API model routing (Haiku/Sonnet), MCP интеграция, PostgreSQL, GitHub OAuth — текущая реализация → [C2.IT-Platform / System-Implementations / DP.AISYS.014-aist-bot-implementation.md](../../../DS-ecosystem-development/C.IT-Platform/C2.IT-Platform/C2.2.Architecture/System-Implementations/DP.AISYS.014-aist-bot-implementation.md).

**Доменные принципы:**
- YAML-driven SM: transitions.yaml → states/ → handlers/
- Mode-aware routing: единая точка определения целевого стейта по режиму
- Model routing: дешёвая модель для структурированных задач, мощная — для creative reasoning

## 7. Переносимость (отчуждаемость)

> Platform-space ≠ User-space (DP.D.011)

**Platform-space (одинаково для всех):**
- State Machine engine (core/machine.py)
- Сервисный реестр (генерация меню)
- Слой биллинга (подписки, paywall)
- i18n framework (4 языка)
- Шаблоны стейтов (BaseState lifecycle)

**User-space (уникально для пользователя):**
- Контент курсов (topics/, knowledge_structure.yaml)
- MCP-подключения (конкретные Pack'и)
- Настройки биллинга (цены, планы подписки)
- Брендирование (имя бота, тексты)

## 8. Эволюция (фазы)

| Фаза | Цель | Архитектурное изменение |
|------|------|------------------------|
| **0 (текущая)** | Mode-aware routing + стабилизация | SM + handlers |
| **1** | Сервисный реестр + консультант | Меню из реестра, self-help слой |
| **2** | Тонкий клиент + агенты | Бот = UI, вся логика в MCP/агентах |
| **3** | Цифровой двойник + траектории | Индивидуальные сценарии, адаптивное развитие |

### 8.1. Модель сопровождения (Umbrella WP)

> **Implementation Note.** Конкретные номера WP, context files, Issue Funnel реализация → [C2.IT-Platform / System-Implementations / DP.AISYS.014-aist-bot-implementation.md](../../../DS-ecosystem-development/C.IT-Platform/C2.IT-Platform/C2.2.Architecture/System-Implementations/DP.AISYS.014-aist-bot-implementation.md).

**Доменный принцип:** Гибридная модель (Variant C): зонтичные РП (развитие + техдолг) + эпизодические (≥4h). Done-пункты удаляются, не накапливаются. Issue Funnel: двухуровневый триаж (auto-classify + review).

## 9. Реализация (Downstream)

> Исходный код: DS-IT-systems (downstream). Детали: [C2.IT-Platform / System-Implementations](../../../DS-ecosystem-development/C.IT-Platform/C2.IT-Platform/C2.2.Architecture/System-Implementations/).

## 10. Связанные документы

- [DP.ARCH.001 Архитектура платформы](DP.ARCH.001-platform-architecture.md) — бот = Слой 1 (Interface)
- [DP.ROLE.001 ИИ-агенты](DP.ROLE.001-platform-roles.md) — классификация, реестр
- [DP.AISYS.012 Стратег](DP.ROLE.012-strategist/00-role-passport.md) — интеграция /rp, /plan, /report
- [DP.AISYS.013 Знание-Экстрактор](DP.AISYS.013-knowledge-extractor.md) — заметки → inbox → Pack
- [DP.CONCEPT.001 Концепция платформы](DP.CONCEPT.001-platform-concept.md) — общая концепция
- [DP.NAV.001 Навигация знаний](DP.NAV.001-knowledge-navigation.md) — MCP-поиск
