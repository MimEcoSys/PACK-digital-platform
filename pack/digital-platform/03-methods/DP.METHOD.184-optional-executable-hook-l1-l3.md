---
id: DP.METHOD.184
name: "Optional-executable hook: L1 вызывает L3-расширение через проверку [ -x ]"
type: method
domain: DP
status: active
valid_from: 2026-07-14
source: "session-close 2026-07-09; DS-my-strategy commit c254cec (feat(day-open): extension-hook WP-470)"
related:
  see_also:
    - "DP.M.009: Template Extensibility (архитектурный уровень — drop-in/overlay/3-way merge)"
tags: [shell, extension-hook, l1, l3, optional, executable, iwe, drop-in]
---

# DP.METHOD.184 — Optional-executable hook: L1 вызывает L3-расширение через `[ -x ]`

## Суть

L1-шаблон определяет **hook-point**: именованный путь к исполняемому файлу.
При выполнении L1 проверяет существование и исполняемость hook через `[ -x path ]`.
Если hook существует — вызывает, захватывает stdout. Если нет — noop.
Вся доменная логика остаётся в L3-расширении; L1 не знает что именно делает hook.

## Механизм

```bash
# В L1-скрипте (например render_yesterday в day-open-scaffold.sh):
HOOK="$IWE/extensions/day-open.summary-extra.sh"
extra=""
if [ -x "$HOOK" ]; then
if ! extra=$("$HOOK" "$DATE_ARG"); then
  echo "optional hook failed: $HOOK; continuing without its output" >&2
  extra=""
fi
fi
# Использовать $extra в шаблоне вывода
```

**Конвенция hook-контракта:**
- Имя файла: `extensions/{protocol}.{hook-name}.sh`
- Аргументы: определяет L1 (стандартно: дата или другой контекст)
- Stdout: текст для вставки в шаблон
- Stderr: передаётся в журнал вызывающего протокола
- Exit code: ненулевой код явно журналируется, но не останавливает L1; ошибка hook = наблюдаемый noop

## Отличие от Drop-in (DP.M.009 §3.1)

| Критерий | Drop-in | Optional-exec hook |
|----------|---------|-------------------|
| L1 знает формат расширения | Да (читает config/YAML) | Нет (вызывает исполняемое, берёт stdout) |
| Реализация L3 | Declarative config | Любой язык (bash, python, SQL) |
| L1 знает о существовании | Нет (сканирует директорию) | Нет (проверяет конкретный путь) |
| Ошибка расширения | Зависит от формата | Неблокирующий noop с записью в stderr |

## Когда применять

- L3 вызывает доменную логику (база данных, API, форматирование) внутри L1-шаблона
- Логика непереносима или избыточна для L1 (конкретная схема, личные данные)
- Нужна полная изоляция: пользователи без расширения не затрагиваются
- L1 не должен зависеть от наличия конкретного расширения

## Когда не применять

- Hook должен изменять существующий вывод (use overlay from DP.M.009)
- Нужно несколько независимых расширений в одной точке (use drop-in directory scan)
- Hook-ошибка должна останавливать протокол (remove `|| true` and handle exit)
- Hook запускается через интерпретатор (`python3 hook.py`), а не прямым запуском файла: проверка `[ -x ]` годится только для прямого запуска, а при запуске через интерпретатор файл без бита исполнения молча выключает барьер (DP.FM.801; дополнение 2026-11-20).

## Применимость

Day-open/Day-close/Week-open L1-скрипты платформы IWE.
Любой shell-протокол с персонализированными секциями (health data, personal APIs, custom reports).

## Связи

- **DP.M.009** (Template Extensibility) — архитектурный уровень. Этот метод = конкретная shell-реализация одного из hook-point'ов drop-in паттерна
