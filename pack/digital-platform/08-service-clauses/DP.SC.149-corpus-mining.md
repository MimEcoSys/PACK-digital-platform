---
id: DP.SC.149
name: Ретроспективный майнинг корпуса в PACK-rhetoric
type: sc
status: active
layer: L4-Personal
summary: "Автор или агент получает пакет карточек иллюстраций из произвольного корпуса (клуб, руководства, книги) в формате RHE.FORM.001 при указании источника и фильтра тропа"
consumer: R15 Знание-Экстрактор (метод М-RM), R4 Автор руководств
created: 2026-05-19
updated: 2026-05-19
related:
  extends: [DP.SC.042]
  uses: [DP.SC.036]
  produces: [PACK-rhetoric/illustrations/]
---

# [DP.SC.149] Ретроспективный майнинг корпуса в PACK-rhetoric

## Обещание

**Кому:** Автор руководств (R4), агент-майнер R15 (ночной режим), Навигатор (MIM.R.007) при запросе иллюстрации к концепту

**Зачем:** Добывать риторические иллюстрации из накопленных корпусов (клуб, программы, книги) в формате PACK-rhetoric, не создавая их вручную.

**Что получит:**
- **Пакет карточек иллюстраций** в формате RHE.FORM.001 (id, trope_type, source_text, structural_core, illustrates[concept_id+pack_ref], breaks_when, quality_score)
- **Checkpoint-файл** при частичном результате — возможность продолжить с последнего обработанного поста
- **Отчёт качества** — сколько кандидатов найдено, сколько прошли валидацию RHE.FORM.002, сколько отложены в `illustrations/pending/`

**Критерий приёмки:**
- Каждая карточка содержит `structural_core` (не пустой) и `breaks_when` (не N/A для analogy/case/metaphor)
- Карточки аналогий: `structural_core` содержит реляционное (не атрибутивное) отношение
- Карточки кейсов: `source_text` содержит конфликт
- quality_score ≥ 0.6 для попадания в `illustrations/{type}/`, иначе → `illustrations/pending/`

## Инварианты (Правила)

| Правило | Смысл |
|---------|-------|
| **Анонимизация** | Карточки из клуба и авторских текстов — без личных имён, без биографических привязок. PII-gate (B7.3) обязателен. |
| **Routing** | Все карточки только в PACK-rhetoric. Нарушение routing — это нарушение DP.SC.036. |
| **Partial-first** | При частичном сбое сохранить checkpoint и partial results. Не молчать при ошибке. |
| **Human-in-loop** | quality_score ставится человеком или через engagement-сигнал (≥5 реакций). LLM-самооценка не является final. |

## Триггеры

| Триггер | Источник | Режим |
|---------|---------|-------|
| Ночной scheduler (02:00 МСК) | Клуб, начиная с 2026-01-01 → назад | Batch, async |
| Команда `/extract-illustrations <source>` | Руководство или файл | On-demand, sync |
| Embedding-resonance запрос | Концепт без иллюстрации → поиск по embedding | Semi-auto |

## Входы

| Вход | Тип | Откуда |
|------|-----|--------|
| `corpus_source` | enum: club \| guide_file \| book_text | Конфигурация / параметр |
| `trope_filter` | list: analogy, case, metaphor, example, counter_example \| all | Параметр |
| `since_date` | ISO date, опционально | Параметр для клуба |
| `concept_filter` | concept_id из Pack, опционально | Параметр для targeted mining |
| `min_engagement` | число реакций/комментариев (для клуба), default: 5 | Конфигурация |

## Выходы

| Выход | Формат | Получатель |
|-------|--------|------------|
| Карточки `active` | `illustrations/{type}/RHE.ILL.NNN-*.md` | PACK-rhetoric |
| Карточки `draft` | `illustrations/pending/RHE.ILL.NNN-*.md` | PACK-rhetoric (ревью) |
| Checkpoint | `illustrations/pending/.checkpoint-{source}-{date}.json` | Scheduler |
| Отчёт | Markdown в stdout / inbox | Автор / агент |

## Режим отказа

| Ситуация | Поведение |
|----------|-----------|
| Корпус недоступен (API down) | Сохранить checkpoint, уведомить, retry следующей итерацией |
| Карточка не прошла валидацию RHE.FORM.002 | Поместить в `pending/` со статусом `draft`, не блокировать остальные |
| LLM вернул structural_core атрибутивный (не реляционный) | Пометить `validation_fail: structural_core_not_relational`, в `pending/` |
| quality_score < 0.6 | В `pending/` со статусом `low_quality` — не в `active` |

---

## Сценарии использования

### SC-A: Ночной mining клуба (batch)

**Кто:** Scheduler (ночной агент R15 в режиме М-RM)
**Когда:** 02:00 МСК ежедневно
**Откуда:** Клуб /api/posts, paginated, начиная с 2026-01-01 → назад
**Фильтр качества:** посты с ≥5 реакций или ≥3 комментариями
**Поток:**
1. GET /posts (paginated, rate-limited)
2. Для каждого поста → R15 М-RM → candidates
3. Валидация RHE.FORM.002 для каждого кандидата
4. active → `illustrations/{type}/`, draft → `pending/`
5. Checkpoint после каждых 50 постов
6. Утренний отчёт в inbox

**Ожидаемый результат:** 5-20 новых карточек за ночь при активном клубе

### SC-B: On-demand при написании руководства

**Кто:** Автор (R4), пишет руководство и нуждается в иллюстрации для концепта
**Когда:** По команде во время сессии написания
**Откуда:** Конкретный файл или директория с руководством
**Поток:**
1. Автор вызывает: «найди иллюстрации к концепту PD.CHR.002 в этом файле»
2. R15 М-RM сканирует текст, извлекает кандидатов для указанного concept_id
3. Валидация → предложить 1-3 лучших карточки
4. Автор принимает/отклоняет → принятые интегрируются в PACK-rhetoric

**SLA:** ≤2 минуты для файла до 50 страниц

### SC-C: Embedding-resonance mining

**Кто:** Навигатор (MIM.R.007) или система рекомендаций
**Когда:** Концепт запрошен в контексте, но у него нет ни одной иллюстрации с quality_score ≥ 0.7
**Откуда:** Семантический поиск по корпусу клуба через embedding-расстояние
**Поток:**
1. Запрос: concept_id без иллюстраций с нужным trope_type и effect
2. Поиск ближайших по embedding постов/фрагментов
3. Топ-5 по cosine-сходству → R15 М-RM → карточки
4. Самый высокий quality_score предлагается пользователю

**Ожидаемый результат:** ≥1 кандидат для каждого «пустого» концепта

---

## Связанные документы

- [RHE.FORM.001](../../../../PACK-rhetoric/pack/rhetoric/05-formalizations/RHE.FORM.001-illustration-card.md) — формат карточки
- [RHE.FORM.002](../../../../PACK-rhetoric/pack/rhetoric/05-formalizations/RHE.FORM.002-trope-validation.md) — критерии валидации
- [DP.SC.042](DP.SC.042-knowledge-extraction.md) — базовый SC извлечения знаний (этот SC его расширяет)
- [DP.AISYS.013](../02-domain-entities/DP.AISYS.013-knowledge-extractor.md) — роль R15, метод М-RM
