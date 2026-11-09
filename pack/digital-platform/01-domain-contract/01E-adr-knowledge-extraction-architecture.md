# ADR: Knowledge Extraction — triggered-on-Close архитектура

## Статус

**Accepted** (ArchGate 17 апр, 52/70 ЭМОГССБ)

## Контекст

Проблема: при завершении сессии (Day Close / Close) extract captures в Pack без явного решения (accept/reject/defer). Текущий механизм Session-Prep слепо удаляет extraction-reports старше 7 дней без учета статуса (pending-review → потеря), что нарушает инвариант **«capture не исчезает без решения»**.

Требование: Transforms неструктурированные captures (сессионные заметки, feedback-логи, решения) в структурированные Pack-сущности (правила, роли, методы, различения) с валидацией и историей решений.

### Рассмотренные варианты

| Вариант | Описание | Score |
|---------|---------|-------|
| **A — Чистый cron** | Cron каждые 6ч запускает extraction, Close ничего не знает | 43/70 |
| **B — Hook-on-Close** | Close блокируется, пока не завершится extraction в один такт | 48/70 |
| **C — Гибрид (Cron+Close)** | Cron экстрагирует фоном, Close блокируется на pending-review + вызывает /apply-captures для разбора | **52/70** ✅ |
| D — Event-driven (fswatch) | macOS-specific, не кроссплатформен | отклонён |
| E — Append-only captures | Captures как entries в одном .md без файлов-отчётов | рассмотрить в Ф0 SOTA |

## Решение

**Вариант C: Гибридная архитектура с Hard Gate в Close и отдельным `/apply-captures` скиллом.**

### Компоненты

1. **Фоновый cron (каждые 6ч):** S47 Knowledge Extractor (DP.AISYS.013)
   - Запускает экстракцию из captures.md + feedback-log.md
   - Генерирует KE-кандидатов (extraction-reports в `inbox/extraction-reports/*.md`)
   - Статус: `status: pending-review`
   - Не коммитит в Pack, не удаляет исходники

2. **Hard gate в protocol-close.md:**
   - Проверка: `if N extraction-reports со status:pending-review > 0 → блокирует Close`
   - Сообщение: «Есть N кандидатов знаний в ожидании решения. Команда: `/apply-captures` для разбора или `/defer-captures` для отложения»
   - SLA: pending-review разбирается ≤24ч до ближайшего Close
   - Fallback: если cron не сработал >7 дней → ручной запуск `/ke`

3. **Отдельный скилл `/apply-captures`:**
   - Триггер: пользователь вызывает явно (не inline в Close)
   - Роль: R15 Валидатор — читает KE-кандидатов, выбирает accept/reject/defer, пишет в feedback-log.md
   - Выход: коммит в Pack + обновление extraction-reports (status: accepted/rejected/deferred)
   - ВДВ-контракт явный (см. SKILL.md)

4. **Feedback-log.md** в DS-my-strategy/inbox/:
   - Каждая запись R15: `{candidate_id, decision, reason, pattern (если reject/defer), target_path}`
   - Используется R2 Экстрактором на следующий цикл (негативные примеры → уточнение гайдов)
   - Версионируется в git

### Рабочий процесс с KE-кандидатом

```
1. Close сессии → запускается cron
2. Cron: captures.md + feedback-log.md → extraction-report (pending-review)
3. Коммит: "docs: extraction-report N (pending-review)"
4. Close: проверка N pending-review
   - N > 0: блокировка, подсказка на /apply-captures
   - N = 0: Close завершается
5. Пользователь: /apply-captures
   - R15 читает отчёт, выбирает accept/reject/defer
   - accept: коммит в Pack + обновление extraction-report (accepted)
   - reject/defer: запись в feedback-log + обновление extraction-report (rejected/deferred)
6. Следующий цикл: R2 читает feedback-log, уточняет гайды экстракции
```

## Обоснование

| Критерий ЭМОГССБ | Вариант A | Вариант B | Вариант C (выбран) | Обоснование |
|------------------|----------|----------|-----------------|------------|
| **Э — Эволюционируемость** | 8/10 | 7/10 | **9/10** | Гибридный подход позволяет уточнять Extract-guide без перестройки Close; Ф0 SOTA исследует Вариант E (append-only) как 2.0 |
| **М — Масштабируемость** | 7/10 | 5/10 | **8/10** | Cron может масштабироваться горизонтально (N workers); Close не блокируется extraction-временем; /apply-captures async (не inline) |
| **О — Обучаемость** | 6/10 | 6/10 | **8/10** | Feedback-log как learning signal для R2; separation of concerns (extract vs apply) упрощает тестирование и debug |
| **Г — Генеративность** | 7/10 | 8/10 | **8/10** | Cron выстраивает KE-кандидаты; hard gate усиливает валидацию (не слепая integrация); R15 может генерировать контр-примеры в feedback-log |
| **С — Скорость** | 9/10 | 4/10 | **7/10** | Cron асинхронен (не медляет Close); /apply-captures может быть медленнее, чем inline (но это нормально — creativity work) |
| **С — Современность** | 6/10 | 7/10 | **9/10** | Hard gate + async apply-captures = паттерн из HITL-extraction (Stanford HAI), LangChain ReACT, agentic systems |
| **Б — Безопасность** | 9/10 | 9/10 | **9/10** | Валидация R15 перед коммитом в Pack; feedback-log как audit-trail; no loss of knowledge (hard gate) |
| **ЭМОГССБ Итого** | 52/70 | 46/70 | **58/70** | Лучший баланс скорости, валидации и эволюционируемости |

(Примечание: ArchGate 17 апр указал 52/70 для Варианта C, исправление на 58/70 по детальной ЭМОГССБ от 6 май)

## Зависимости

- **DP.SC.004** (Knowledge Extraction Service Clause): триггеры, инварианты, SLA, ВДВ-сценарии ✅
- **DP.ROLE.002** (R2 Экстрактор): inputs += feedback-log.md ✅
- **DP.ROLE.004** (R4 Автор): work_products += Pack-сущность ✅
- **DP.ROLE.015** (R15 Валидатор): inputs/actions/scenarios в ВДВ-формате ✅
- **WP-247-roles-methodology.md**: паттерн ролевого разбора для других SC ✅

## Реализация

### Ф2 (текущая): Формальная запись решения ✅
- Этот ADR (01E)
- Ссылка на SOTA из Ф0 (когда будет написана)

### Ф3–Ф8: Реализация Варианта C
- Ф3: Скилл `/apply-captures` (1.5h)
- Ф4: Hard gate в protocol-close.md (0.5h)
- Ф5: Feedback-log интеграция с R2 guides (1h)
- Ф6: Smoke-тестирование KE-цикла (1.5h)
- Ф7: Промоция feedback-log в FMT (1h)
- Ф8: Промоция /apply-captures и protocol-close в FMT (1h)

## Альтернатива (будущее)

**Вариант E — Append-only captures** (2.0, Ф0 SOTA рассмотрение):
- Captures как entries в одном `.md` вместо файлов-отчётов
- Преимущества: меньше файлов, проще версионирование, меньше I/O в cron
- Требует: переход с extraction-report на inline status (может потребовать миграции)
- ROI: актуально при 1000+ capture/год

## Принято

**Decision Date:** 2026-05-06  
**ArchGate Score:** 52/70 → уточнено в 58/70  
**Review:** WP-247 Ф2, acceptance vote пользователя на веке Ф3
