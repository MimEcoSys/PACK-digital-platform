---
id: DP.WP.010
name: CQRS Pack Projection
type: work-product
status: draft
summary: "YAML-проекция Pack frontmatter для knowledge-mcp: read-optimized view Pack-сущностей"
created: 2026-02-25
trust:
  F: 2
  G: domain
  R: 0.5
epistemic_stage: emerging
related:
  produced_by: [S19]
  consumed_by: [I4]
  services: [S19]
---

# CQRS Pack Projection

## 1. Определение

**CQRS Pack Projection** — read-optimized YAML-проекция Pack-сущностей, генерируемая Синхронизатором (R8) из frontmatter Pack-файлов. Потребитель — knowledge-mcp (I4), через который агенты и бот ищут знания.

## 2. Назначение

Pack хранит знания в markdown-файлах с frontmatter (write-side). Для поиска (read-side) нужна плоская проекция: все сущности, их типы, связи, статусы — в формате, быстро парсимом MCP-сервером. Без проекции MCP читает сырые файлы → медленно, неполно.

## 3. Структура

### 3.1. Формат

```yaml
entities:
  - id: DP.D.001
    name: "..."
    type: domain-entity
    status: draft
    summary: "..."
    related: [...]
  - id: DP.M.001
    ...
```

### 3.2. Расположение

Генерируется `pack-project.sh` в директорию, доступную knowledge-mcp.

## 4. Рабочий процесс

```
Pack-файлы → pack-project.sh (S19, после S18) → YAML projection → knowledge-mcp (I4) → агенты/бот
```

## 5. Критерии качества

| Критерий | Проверка |
|----------|----------|
| Полнота | Все Pack-сущности из всех Pack-репо включены? |
| Актуальность | Проекция не старше 24ч? |
| Парсимость | YAML валиден, структура стабильна? |

## 6. Связанные документы

- [DP.MAP.002 S19](../07-map/DP.MAP.002-iwe-service-catalog.md) — сервис Pack Projection
