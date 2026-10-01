---
id: DP.FM.457
type: failure-mode
status: active
created: "2026-09-14"
valid_from: "2026-09-14"
name: "Под pipefail `echo большого_значения | grep -q шаблон` может дать ложный отказ на SIGPIPE"
name_ru: "Под pipefail `echo большого_значения | grep -q шаблон` может дать ложный отказ на SIGPIPE"
name_en: "Under pipefail, `echo large_value | grep -q pattern` can misreport a true match as false via SIGPIPE"
summary: "week-open-проверки использовали `echo \"$PLAN_BLOCK\" | grep -q pattern` под `set -o pipefail`; grep -q выходит по первому совпадению, echo, ещё дописывающий вывод, получает SIGPIPE — и весь конвейер иногда читается как false при реальном совпадении. Флакало на большом входе (800-строчный план W37)."
pack: PACK-digital-platform
domain: digital-platform
schema_version: 1
trust: medium
epistemic_stage: forming
source: "git commit 4c119a93e в DS-my-strategy (WP-484, WP-561)"
source_capture: "DS-my-strategy/inbox/captures/2026-09.md:1987, DS-my-strategy/inbox/captures/2026-09.md:3777"
related:
  see_also: []
---

# DP.FM.457 — pipefail превращает `echo | grep -q` в источник ложного отказа на SIGPIPE

## Тезис и механизм ошибки

week-open-проверки использовали `echo "$PLAN_BLOCK" | grep -q pattern` под `set -o pipefail` во всех пяти однотипных проверках. `grep -q` завершается сразу по первому совпадению; `echo`, ещё дописывающий вывод в закрытый конец пайпа, получает SIGPIPE — и в зависимости от гонки пайплайн иногда регистрируется как неуспешный (`pipefail` учитывает ненулевой exit code любого сегмента, включая упавший от SIGPIPE `echo`), несмотря на то что совпадение реально было. На большом входе (800-строчный план W37) grep -q exits on the first match; with pipefail the echo of a large PLAN_BLOCK then dies of SIGPIPE and the whole pipeline reads as false, so a true match flipped to a miss at random — поймано флакающим смоук-тестом бюджета.

## Диагностический принцип

`pipefail` защищает от одного класса ошибки (провал первой команды конвейера остаётся незамеченным без него) и создаёт другой на конвейерах вида `echo <большой_текст> | grep -q <паттерн>`: ранний выход `grep -q` по первому совпадению убивает `echo` сигналом SIGPIPE, чей ненулевой exit code `pipefail` учитывает как провал всего конвейера — истинное совпадение регистрируется как ложное. Это не отсутствие `pipefail`, а его прямое следствие на конвейерах с ранним выходом читающей стороны.

## Границы

Различение применимо к конвейерам, где вторая (или последующая) команда способна завершиться раньше, чем первая исчерпает весь вывод (типично для `grep -q`, `head`, `sed -q` и аналогов с ранним выходом), и где под pipefail любой ненулевой exit code любого сегмента считается провалом всего конвейера. Не применимо к конвейерам без early-exit читающей стороны или без `pipefail`.

## Проверка

«Конвейер вида `echo/cat большой_вход | grep -q/head/…` работает под `set -o pipefail`, и читающая команда способна завершиться раньше конца ввода?» Да → воспроизведён DP.FM.457, истинное совпадение может флакающе читаться как ложное. Фикс — here-string (`grep -q pattern <<< "$var"`) вместо пайпа: убирает вторую команду и связанную с ней гонку по SIGPIPE целиком.

Если производитель — не переменная, а команда с большим потоком (`cat big.md | grep -q`, `git log | grep -q`), here-string потребовал бы буферизации всего вывода; тогда читать статус именно grep — `"${PIPESTATUS[1]}"` сразу после конвейера (в bash `PIPESTATUS` живёт только до следующей команды), не итоговый `$?`. Верификация любого из двух фиксов обязана включать два входа: совпадение в начале большого файла (грозит SIGPIPE) и в конце (SIGPIPE невозможен) — одна позиционная проверка гонку не воспроизводит.

## Происхождение и статус проверки

Источник: git commit 4c119a93e в DS-my-strategy (WP-484, WP-561). Захват: `DS-my-strategy/inbox/captures/2026-09.md:1987`. Связь: WP-484, WP-561, peer-session 2026-09-14-07-pochemu-ne-sostoyalos.

Обратная сторона уже записанной 12.09 карточки «`cmd1|cmd2 || fallback` не защищает от провала cmd1 без `set -o pipefail`» — здесь `pipefail` ЕСТЬ, и именно он создаёт новый отказ в противоположном направлении: истинное совпадение регистрируется как ложное.

Второй инстанс: git commit a02d73e98 в DS-my-strategy (`fpf-sync`, `fpf-check-references.sh`) — конвейер `producer | grep -q code` под `pipefail` репортил ранние совпадения как «broken» в зависимости от позиции кода в файле; вскрылось на известном переименовании A.6.8 → A.6.P, фикс через `PIPESTATUS[1]`, проверено на known-good (71/71) и known-bad окнах. Захват: `DS-my-strategy/inbox/captures/2026-09.md:3777`.

Описанная проверка задаёт критерий приёмки. Её прохождение исходной реализацией этой карточкой не утверждается.
