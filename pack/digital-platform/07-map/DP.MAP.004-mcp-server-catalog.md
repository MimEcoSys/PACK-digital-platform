---
id: DP.MAP.004
name: MCP Server Catalog
type: map
status: draft
summary: "Единый реестр MCP: адрес, gateway и его источники, готовность, данные, инструменты, репозитории"
created: 2026-10-08
updated: 2026-10-09
related:
  extends: [DP.MAP.002]
---

<!-- index-health: skip-cells — каталог MCP-серверов (жанр: справочная таблица доменных сущностей), длинные ячейки описаний — не дамп контекста (Day Close 2026-10-09) -->

# [DP.MAP.004] Реестр MCP-серверов

> **Назначение:** одно место для действующих, локальных и запланированных MCP платформы, личных серверов создателя и прямо связанных внешних серверов. Копия в `DS-my-strategy/current` удаляется; карточки РП содержат историю решений, а не вторую версию реестра.
>
> **Граница факта:** «код есть» не означает, что работает публичный адрес. «План» не означает созданный сервер. Дата последней живой проверки указана отдельно; состав инструментов подключённого шлюза зависит от конфигурации и прав пользователя. Если код или живой вызов не проверены, это явно написано.

**Gateway — Да** означает, что одна MCP-идентичность собирает несколько самостоятельных источников. После «Да» в таблице перечислены входящие или запланированные уникальные MCP. **Нет** означает собственный источник, служебный интерфейс или прокси ровно одного источника; название `gateway` само по себе не меняет тип. «Уникальный» относится к ответственности и данным сервиса, а не к доменному имени.

## Адреса и самостоятельные реализации

| Название и адрес | Gateway? Уникальные MCP в составе | Готовность | Где используется | Какие данные выдаёт | Инструменты | Репозитории и подтверждение |
|---|---|---|---|---|---|---|
| **Aisystant MCP** · `mcp.aisystant.com/mcp` | **Да — сейчас ядро: `knowledge-mcp`, `digital-twin-mcp`, `personal-knowledge-mcp`, `checklist-mcp`.** Дополнительно через настраиваемый реестр могут входить `agent-status-service`, `learning-context-service`, `trace-accountant`, `user-profile-service`, `mentorship-service`; фактическое включение каждого проверяется отдельно | Работает: инструменты доступны в подключённой сессии; состав зависит от прав и конфигурации | Личный вход в Claude, ChatGPT, Codex и чат МИМ | Общие знания, личные источники, цифровой двойник, чек-лист, профиль, учебный контекст и действия платформы | Семейства `knowledge_*`, `dt_*`, `personal_*`, `checklist_*`, `agent_status_*`, `learning_ctx_*`, `capture_*`, `user_profile_*` плюс собственные инструменты шлюза | [aisystant/gateway-mcp](https://github.com/aisystant/gateway-mcp), `src/index.ts`, `getBackends()`; текущий список инструментов сессии |
| **Aisystant Open** · `open.aisystant.com/mcp` | **Нет — прокси одного `mcp.fpf.tools`, собственный поисковый корпус не подтверждён** | Работал при прямой проверке 8 октября; после этого маршрут не перепроверен | Гостевой вход без аккаунта МИМ | Опубликованные FPF и DPF; личные данные и Паки IWE в нынешней выдаче не подтверждены | Те же семь инструментов, что у `mcp.fpf.tools` | Репозиторий действующего прокси **не установлен**. [MimEcoSys/open.system-school.ru](https://github.com/MimEcoSys/open.system-school.ru) — код другой гостевой реализации, не доказанный код нынешнего прокси. Корпус: [ailev/FPF](https://github.com/ailev/FPF). Живая сверка: [РП-581](https://github.com/TserenTserenov/DS-my-strategy/blob/main/inbox/WP-581/WP-581.md) |
| **FPF Library** · `mcp.fpf.tools/mcp` | **Нет — уникальный внешний сервер Анатолия** | Работает: публичное подключение описано владельцем; семь инструментов проверены 8 октября | Прямое подключение; нынешний источник Aisystant Open | Опубликованные FPF и DPF, их разделы и связи | `search`, `read_section`, `read_pattern`, `get_table_of_contents`, `list_publications`, `backlinks`, `get_corpus_status` | Репозиторий **серверного кода не установлен**. [ailev/FPF](https://github.com/ailev/FPF) — публикации, не код MCP. [Описание подключения](https://fpf.tools/connect) |
| **Личный MCP Церена** · имя `mcp.tserenov.com` | **Нет — уникальный авторский источник** | Локальный stdio-сервер работает; удалённый HTTPS-адрес не развёрнут | Локально у владельца | Поиск и чтение авторского корпуса; черновики исключены правилами допуска | `search`, `fetch` | [TserenTserenov/mcp.tserenov.com](https://github.com/TserenTserenov/mcp.tserenov.com), `src/tools.ts`, `src/corpus-policy.ts`; исходный индекс [DS-Knowledge-Index-Tseren](https://github.com/TserenTserenov/DS-Knowledge-Index-Tseren) |
| **Открытый личный MCP Церена** · `open.tserenov.com` | **Да — планируются `mcp.fpf.tools`, `knowledge-mcp` только в открытом режиме и авторский открытый корпус; возможное подключение через `mcp.tserenov.com` ещё не закреплено** | Только план: сервера и репозитория агрегатора нет; встраивание FPF ждёт отдельного согласия Анатолия | План: любой читатель | Объединённая публичная подборка трёх источников с атрибуцией каждого результата; личный слой знаний исключён | Контракт инструментов не утверждён; `search`/`fetch` — предварительный вариант | Репозиторий агрегатора не создан. Кандидаты источников: `mcp.fpf.tools` (код не установлен), [aisystant/knowledge-mcp](https://github.com/aisystant/knowledge-mcp), [TserenTserenov/mcp.tserenov.com](https://github.com/TserenTserenov/mcp.tserenov.com). Основание: [РП-590](https://github.com/TserenTserenov/DS-my-strategy/blob/main/inbox/WP-590/WP-590.md) |
| **Российский гостевой Open** · `open.system-school.ru/mcp` | **Нет — уникальный сервер со своим индексом в нынешнем коде** | Код готов; публичный адрес и клиентская приёмка не подтверждены | План: российский гостевой вход | Закреплённый снимок опубликованного FPF и страницы гида; нынешний код использует MiniSearch и локальный бандл. Прямой публичный Qdrant — отдельный план | `search`, `fetch` | [MimEcoSys/open.system-school.ru](https://github.com/MimEcoSys/open.system-school.ru), `src/http-server.ts`, `src/mcp-tools.ts`; корпус [ailev/FPF](https://github.com/ailev/FPF) |
| **Российский персональный MCP** · `mcp.system-school.ru/mcp` | **Да — при запуске тот же Aisystant gateway: `knowledge-mcp`, `digital-twin-mcp`, `personal-knowledge-mcp`, `checklist-mcp`; дополнительные уникальные MCP зависят от будущей конфигурации** | Адрес ещё не создан; отдельный серверный код не установлен | План: вошедшие пользователи МИМ в России | После развёртывания — платформенные и личные данные по правам пользователя | Ожидается набор Aisystant MCP; точный `tools/list` проверяется после развёртывания | Планируется переиспользование [aisystant/gateway-mcp](https://github.com/aisystant/gateway-mcp); основание: [РП-589](https://github.com/TserenTserenov/DS-my-strategy/blob/main/inbox/WP-589/WP-589.md) |
| **knowledge-mcp** | **Нет — уникальный источник платформенных знаний** | Код подтверждён; инструменты видны через Aisystant MCP, отдельная приёмка backend здесь не проводилась | За Aisystant MCP | Паки, руководства, индексированные знания и понятия; один код с режимами `public`/`private`, открытая выдача не включает личный слой | Поиск, чтение, обход структуры; в закрытом режиме также запись и управление источниками | [aisystant/knowledge-mcp](https://github.com/aisystant/knowledge-mcp), `src/index.ts`, `src/mode.ts`, `src/rls.ts` |
| **personal-knowledge-mcp** | **Нет — уникальный пользовательский источник, отдельный от `knowledge-mcp`** | Код подтверждён; отдельная живая приёмка backend не проводилась | За Aisystant MCP, обычно префикс `personal_*` | Личные подключённые источники пользователя | 16 инструментов: поиск, чтение, запись, управление источниками и переиндексация | [aisystant/personal-knowledge-mcp](https://github.com/aisystant/personal-knowledge-mcp), `src/index.ts` |
| **digital-twin-mcp** | **Нет — уникальный источник цифрового двойника** | Код подтверждён; три основных инструмента видны через Aisystant MCP | За Aisystant MCP, префикс `dt_*` | Поля, профиль и показатели цифрового двойника | `describe_by_path`, `read_digital_twin`, `write_digital_twin`; ещё четыре инструмента только в локальном stdio-режиме | [aisystant/digital-twin-mcp](https://github.com/aisystant/digital-twin-mcp), `src/tool-catalog.js` |
| **fsm-mcp** | **Нет — уникальный сценарный сервер** | Код MCP подтверждён; публичное развёртывание не проверено | «Проводник» ученика | Инструкции по состоянию ученика | `get_instruction` | [aisystant/fsm-mcp](https://github.com/aisystant/fsm-mcp), `src/index.ts` |
| **guides-mcp** | **Нет — уникальный источник руководств** | Код MCP подтверждён; публичное развёртывание не проверено | Подключения к руководствам | Список, разделы, текст и смысловой поиск по руководствам | `get_guides_list`, `get_guide_sections`, `get_section_content`, `semantic_search` | [aisystant/guides-mcp](https://github.com/aisystant/guides-mcp), `src/index.ts` |
| **google-drive-mcp** | **Нет — уникальный локальный коннектор** | Код stdio MCP подтверждён; подключение в этой сессии не проверено | Локальный Google Drive владельца | Файлы и сопоставления в разрешённом Drive | `gdrive_sync`, `gdrive_list_mappings`, `gdrive_upload`, `gdrive_add_mapping` | [TserenTserenov/google-drive-mcp](https://github.com/TserenTserenov/google-drive-mcp), `mcp_server.py` |
| **iwe-local-gateway** | **Нет — координационная служба, не агрегатор корпусов знаний** | Локальные блокировки и статусы работали 9 октября | Параллельные сессии агентов на одном компьютере | Состояние блокировок файлов и статусов агентов | `gateway_status`, `acquire_file_lock`, `release_file_lock`, `update_peer_status`, `list_peer_statuses` | Текущий код: [TserenTserenov/iwe-local-gateway](https://github.com/TserenTserenov/iwe-local-gateway), `src/tools.ts`; ещё один репозиторий того же пакета: [iwesys/iwe-local-gateway](https://github.com/iwesys/iwe-local-gateway), самостоятельное развёртывание не проверено |

## Служебные MCP-интерфейсы внутри сервисов

Следующие проекты реализуют `tools/list` и `tools/call` для платформенного шлюза. Это подтверждает MCP-интерфейс в коде, но не самостоятельное подключение произвольного внешнего клиента. Для каждого Gateway = **Нет**: сервис отвечает за собственные данные или действие.

| Проект | Gateway? | Готовность | Данные и инструменты | Репозиторий и подтверждение |
|---|---|---|---|---|
| `checklist-mcp` | Нет | Код `/mcp` подтверждён; отдельная живая приёмка не проводилась | Факты, этап и прогресс чек-листа участника; `get_checklist_status` | [aisystant/checklist-mcp](https://github.com/aisystant/checklist-mcp), `app/main.py` |
| `agent-status-service` | Нет | Код `/mcp` подтверждён; обновление статуса через подключённый инструмент проверено 9 октября | Статусы агентных сессий; `update`, `list` | [aisystant/agent-status-service](https://github.com/aisystant/agent-status-service), `src/mcp-handler.ts` |
| `learning-context-service` | Нет | Код `/mcp` подтверждён; отдельная живая приёмка не проводилась | Согласия, учебный контекст, оценка ступени и персональный гид; 8 инструментов | [MimEcoSys/learning-context-service](https://github.com/MimEcoSys/learning-context-service), `src/mcp-handler.ts` |
| `mentorship-service` | Нет | Код `/mcp` подтверждён; консультационные инструменты зависят от настройки | Карточка и заметка участника, синхронизация назначений; 3 основных инструмента и 4 для консультационных кейсов | [MimEcoSys/mentorship-service](https://github.com/MimEcoSys/mentorship-service), `src/mcp-handler.ts` |
| `trace-accountant` | Нет | Код `/mcp` подтверждён; отдельная живая приёмка не проводилась | След работы, ожидающие записи и отчёт сверки; `trace`, `get_pending_stubs`, `get_reconciler_report` | [aisystant/trace-accountant](https://github.com/aisystant/trace-accountant), `src/mcp-handler.ts` |
| `user-profile-service` | Нет | Код `/mcp` подтверждён; отдельная живая приёмка не проводилась | Профиль, тариф, GitHub и ключи моделей; 7 инструментов | [aisystant/user-profile-service](https://github.com/aisystant/user-profile-service), `src/mcp-handler.ts` |

## Границы и обновление

- **Адрес ≠ серверный код.** `mcp.system-school.ru` — планируемый региональный вход в существующий gateway. `open.aisystant.com` 8 октября передавал запросы внешнему `mcp.fpf.tools`; репозиторий действующего прокси не установлен. Код `open.system-school.ru` не следует приписывать действующему мировому прокси без проверки развёртывания.
- **Репозиторий корпуса ≠ репозиторий MCP.** [ailev/FPF](https://github.com/ailev/FPF) содержит публикации, но код сервера `mcp.fpf.tools` при этой сверке не установлен.
- **Вне реестра серверов.** `kimi-adapter` — клиент/адаптер. Для `agent-runner`, `bridge-scope-service`, `event-gateway`, `github-integration-service`, `observability-webhook`, `payment-receiver`, `simulator-proxy`, `status-proxy` самостоятельный MCP-интерфейс по проверенному коду не установлен.
- При изменении gateway сначала сверить `getBackends()` и фактический `tools/list`, затем после «Да» перечислить добавленные или убранные уникальные MCP и отметить их состояние. Для планов не переносить готовность из исходного репозитория на публичный адрес.

## Связь с другими картами

| Карта | Что показывает | Ссылка |
|---|---|---|
| DP.MAP.002 | Методы и исполнители платформы | [DP.MAP.002](DP.MAP.002-iwe-service-catalog.md) |
| DP.MAP.004 | Адреса и MCP-интерфейсы как инфраструктура | Эта карта |
