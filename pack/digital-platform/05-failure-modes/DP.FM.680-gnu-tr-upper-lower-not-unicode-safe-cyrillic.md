---
id: DP.FM.680
name_ru: "GNU `tr '[:upper:]' '[:lower:]'` фолдит только однобайтовые символы — кириллица на Linux остаётся заглавной"
name_en: "GNU `tr '[:upper:]' '[:lower:]'` folds only single-byte characters — Cyrillic stays uppercase on Linux"
summary: "На Linux (GNU coreutils) `tr '[:upper:]' '[:lower:]'` фолдит только однобайтовые (ASCII) символы — двухбайтовая кириллица в UTF-8 остаётся заглавной, и триггер-фраза хука не распознаётся. На macOS тот же код работает штатно (BSD tr Unicode-safe для этой локали). Семь хуков репозитория приводили текст к нижнему регистру через tr и были подвержены дефекту одного класса; фикс — общая библиотека text-lower.sh с python3 UTF-8-safe приведением и tr-фоллбеком при отсутствии python3."
type: failure-mode
status: draft
created: "2026-10-24"
valid_from: "2026-10-24"
pack: PACK-digital-platform
domain: digital-platform / shell-portability
schema_version: 1
trust: observed
epistemic_stage: forming
related:
  see_also: [DP.FM.588]
source: "git commit a13ea9c в iwe-local-config"
source_capture: "DS-my-strategy/inbox/captures/2026-10.md:6684"
extraction_report: "DS-my-strategy/inbox/extraction-reports/2026-10-25-inbox-check.md"
source_candidate: 5
tags: [shell, tr, unicode, cyrillic, cross-platform, hooks]
---

# DP.FM.680 — GNU `tr` не Unicode-safe для кириллицы на Linux

## Симптом

Триггер-фраза хука («Закрывай») не распознавалась на платформе tsekh-1 (Linux) после приведения текста к нижнему регистру через `tr '[:upper:]' '[:lower:]'` — кириллица оставалась заглавной, и команда закрытия пропускалась. Тот же код на macOS работал штатно.

## Причина

`tr '[:upper:]' '[:lower:]'` на GNU/Linux (coreutils) фолдит регистр только для однобайтовых (ASCII) символов класса `[:upper:]`/`[:lower:]` в текущей локали; двухбайтовые UTF-8 символы кириллицы не распознаются этим классом символов и остаются без изменений. BSD `tr`, поставляемый по умолчанию на macOS, в тех же условиях фолдит кириллицу корректно — то есть один и тот же вызов даёт разный результат на двух платформах без ошибки или предупреждения на стороне, где он не работает.

Семь хуков репозитория (close-gate-reminder, pipeline-gate-reminder, inject-principle-nudge, lazy-context-loader, iwe-orz-tracker, inject-personality-activation, protocol-stop-gate) использовали этот паттерн для приведения проверяемого текста к нижнему регистру — все подвержены дефекту одного класса.

## Тест обнаружения

«Shell-скрипт приводит нелатинский (кириллица, и шире — любой не-ASCII) текст к нижнему/верхнему регистру через POSIX `tr '[:upper:]' '[:lower:]'`, и должен выполняться хотя бы на одной GNU/Linux системе?» Да → риск тихого несрабатывания сравнения/детекции именно на Linux, не воспроизводимого на macOS.

## Противодействие

Заменить `tr` на UTF-8-safe построчное приведение регистра (`python3`, `perl`, ICU) для текста, который может содержать не-ASCII алфавит; `tr`-фоллбек оставить только при отсутствии интерпретатора. Решение в этом инциденте — общая библиотека `text-lower.sh` с python3-приведением и tr-фоллбеком. Локальный тест только на macOS не поймает этот дефект — для обнаружения нужен прогон/CI на Linux.

## Связи

- **DP.FM.588** (bash4 `${var,,}` падает на стоковом bash 3.2 macOS) — тот же общий кластер «понижение регистра не переносимо между платформами», но направление и механизм противоположны: там синтаксис современного bash ломается с явной ошибкой парсера на macOS, и `tr` предлагается как POSIX-совместимая замена; здесь сам `tr` даёт тихо неверный результат для нелатинского алфавита на Linux, без ошибки. Рекомендация DP.FM.588 заменить `${var,,}` на `tr` неполна для текста с кириллицей — нужна явная оговорка о не-ASCII алфавитах при следующей правке этой карточки.

## Источник

git commit `a13ea9c` в iwe-local-config. WP-568, peer-session 2026-10-24-02-bot-dump-triage-wp568. Захват: `DS-my-strategy/inbox/captures/2026-10.md:6684`.
