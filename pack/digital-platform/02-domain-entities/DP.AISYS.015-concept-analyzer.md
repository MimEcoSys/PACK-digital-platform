---
id: DP.AISYS.015
name: Анализатор проговаривания и письма
type: ai-system-passport
status: active
summary: "ИИ-система анализа текста/речи на предмет использования понятий, выявления мемов и обновления модели мастерства ученика"
created: 2026-04-07
trust:
  F: 3
  G: domain
  R: 0.6
epistemic_stage: emerging
orientation: system
initiative: by-request
interface: api
related:
  specializes: [U.System]
  uses: [DP.ROLE.001]
  part_of: [DP.AISYS.014]
  realizes: [DP.SC.208]
  depends_on: [DP.AISYS.008]
tags: [concept-graph, verbalization, misconceptions, learner-model]
s2r_families: [F5]
---

# Анализатор проговаривания и письма (Concept Analyzer)

## 1. Определение

**Анализатор проговаривания** — ИИ-система, которая оценивает качество проговаривания (вербализации) и письма ученика по конкретной теме. Определяет покрытие понятий, выявляет мемы (подмены понятий), обновляет модель мастерства ученика.

> Отличие от ДЗ-чекера (DP.AISYS.008): ДЗ-чекер оценивает ответ по нормативам из руководств (правильно/неправильно). Анализатор оценивает глубину владения понятиями (понятийное покрытие, связность, мемы).

## 2. Классификация

| Характеристика | Значение | Пояснение |
|----------------|----------|-----------|
| **Ориентация** | system | Вызывается другими системами через MCP |
| **Инициатива** | by-request | Запускается при анализе текста/ответа |
| **Интерфейс** | api | MCP tools через Gateway |
| **Grade** (дидактическая метка, не критерий допуска) | 2 | LLM + concept graph (решения в рамках scope) |

## 3. IPO (Input → Process → Output)

### Input

| Параметр | Тип | Описание |
|----------|-----|----------|
| text | string | Текст ученика (ДЗ, эссе, проговаривание) |
| topic | string? | Тема/раздел для сравнения |
| domain | string? | Фильтр по домену (MIM, PD, DP) |
| user_id | string? | Ory UUID — для обновления mastery |

### Process

1. Загрузка подграфа понятий по теме (embedding similarity, top-50)
2. LLM-as-judge определение использованных понятий (GPT-4o-mini)
3. Подсчёт coverage (matched/total) и edge coverage
4. LLM-as-judge детекция мемов по каталогу CAT.001 (GPT-4o-mini)
5. Bayesian update mastery (α=0.3) при наличии user_id
6. Генерация рекомендаций

### Output

| Поле | Тип | Описание |
|------|-----|----------|
| coverage | float | Доля использованных понятий (0.0–1.0) |
| matched_concepts | array | Использованные понятия с confidence |
| missed_concepts | array | Пропущенные ключевые понятия |
| misconceptions_found | array | Обнаруженные мемы с объяснением |
| edge_coverage | float | Связность использованных понятий |
| recommendations | array | Рекомендации для ученика |
| mastery_updated | bool | Обновлена ли модель мастерства |

## 4. MCP Tools

| Tool | Назначение |
|------|-----------|
| `analyze_verbalization` | Анализ текста: покрытие, мемы, рекомендации |
| `graph_stats` | Статистика графа понятий |
| `learner_progress` | Прогресс ученика по освоению понятий |

## 5. Инфраструктура

| Компонент | Технология |
|-----------|-----------|
| Runtime | Cloudflare Workers (knowledge-mcp) |
| Граф понятий | Neon PostgreSQL, schema `concept_graph` |
| Эмбединги | pgvector HNSW, 1024d (OpenAI text-embedding-3-small) |
| LLM (matching) | GPT-4o-mini ($0.001/вызов) |
| LLM (мемы) | GPT-4o-mini ($0.001/вызов) |
| Маршрутизация | Gateway MCP (prefix: `knowledge_`) |

## 6. Граф понятий (платформенный ресурс)

| Метрика | Значение |
|---------|----------|
| Понятий | 1 129 |
| Связей | 2 984 |
| Мемов (CAT.001) | 72 |
| Уровни | ZP (6), FPF (175), Pack (524), Guide (376), Course (48) |
| Типы связей | related, specializes, prerequisite, part_of |
| Learner mastery | Bayesian per-user per-concept |

## 7. Потребители

| Потребитель | Способ | Что использует |
|-------------|--------|---------------|
| ДЗ-чекер (DP.AISYS.008) | HTTP → knowledge-mcp | analyze_verbalization |
| Портной (SC.020) | Gateway MCP | analyze_verbalization + learner_progress |
| Навигатор (R27) | Gateway MCP | learner_progress |
| Бот (DP.AISYS.014) | Gateway MCP | analyze_verbalization |
| Экзокортекс | Gateway MCP | все 3 tools |

## 8. Стоимость

~$0.003/оценка (2 LLM вызова GPT-4o-mini). При 100 оценок/день = ~$9/месяц.
