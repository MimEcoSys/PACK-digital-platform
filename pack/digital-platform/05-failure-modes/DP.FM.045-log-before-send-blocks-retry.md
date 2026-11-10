---
id: DP.FM.045
name: "log-after-success violation: idempotency-log записан ДО side-effect → retry невозможен"
type: failure-mode
domain: digital-platform
pack: PACK-digital-platform
trust: observed
epistemic_stage: formalized
category: delivery
severity: critical
valid_from: 2026-05-30
related:
  remediated_by: [DP.M.086]
  see_also: [DP.FM.099, DP.M.420, DP.D.328, DP.M.610]
tags: [idempotency, notification, delivery, at-least-once, silent-drop, retry-blocked]
source: "WP-330 peer-session 2026-05-29-29 review-01 Critical (handlers/marathon.py marathon_practice flow)"
schema_version: 1
---

# DP.FM.045 — log-after-success violation: idempotency-log записан ДО side-effect → retry невозможен

## Описание

Class-bug в notification/delivery-пайплайнах, где write в idempotency-log и сам side-effect (отправка сообщения, HTTP-запрос, push) реализованы в неправильном порядке: сначала `try_insert_notification(log)`, затем `send_message()`. Если `send_message` падает (network error, downstream 5xx, rate limit) — log уже зафиксировал «отправлено», и следующая попытка retry видит UNIQUE conflict → считает «уже доставлено» → silent drop.

Failure mode асимметричный: пользователь не получает уведомление, но monitoring/dashboard зелёные («one row inserted, treated as success»). Обнаруживается только через жалобу пользователя или ручной reconcile.

## Симптом

- `notification_log` / `idempotency_keys` показывает row, но получатель утверждает «не приходило».
- Retry-механизм (background worker, cron) на повторном tick фиксирует «already sent», skip.
- Логи `send_message` показывают exception в окне между insert log и send.
- Нет alerting, потому что row в log = success-сигнал.

## Механизм

1. Дизайн «сначала пометь, потом сделай» (precaution against concurrent double-send).
2. Реализация: `INSERT INTO notification_log(...) ON CONFLICT DO NOTHING; send_message(...)`.
3. На rare transient failure `send_message` бросает exception → транзакция INSERT уже committed (или autocommit).
4. Retry: `INSERT INTO notification_log(...) ON CONFLICT DO NOTHING` → `0 rows affected` → код интерпретирует как «уже доставлено».
5. Side-effect не происходит, monitoring видит «one row inserted» = success.

## Тест применимости

«Есть ли в коде паттерн `try_insert(log_key); side_effect()` без compensating rollback log при failure side-effect?»
- **Да** → red flag, переставить порядок (log-after-success pattern, DP.M.086) или выйти на двухфазный outbox.
- **Нет** → проверь, что компенсирующий rollback атомарен с try/catch вокруг side-effect.

## Remediation

См. DP.M.086 (notification_log как cheap idempotency state) — каноническая последовательность: `(was_notification_sent?) → send_message() → only-on-success try_insert_notification()`. Альтернатива при concurrent-race — outbox pattern с двухфазным `scheduled → sent` статусом.

## Сигналы

- Pre-commit grep правило: «строки `try_insert.*log` НЕ должны предшествовать `send_message`/`http.post`/`publish` без try/except и rollback».
- Code review red flag: PR добавляет idempotency-log → требуется test на failed-send scenario (mock-send raises → log должен быть пустым ИЛИ помечен `failed`).

## Антипод

Prepay-pattern в финансовых транзакциях: списать ДО доставки (риск-модель «доставка вернёт деньги обратно»). У уведомлений другая риск-модель: «не доставлено» дороже «доставлено дважды» (для большинства типов нотификаций), поэтому log-after-success предпочтительнее log-before-send.

## Дополнение 2026-11-10 (РП-170, отчёт 2026-11-09-inbox-check-7, кандидат 1): окно лимитёра и журнал повторов — тот же порядок

Тот же отказ возникает не только с журналом идемпотентности. Любое состояние, которое глушит следующие сообщения, ведёт себя так же, если его записать до подтверждённой доставки:

- **Окно ограничения частоты.** Уведомление «сводка опоздала» занимало окно «не чаще раза в 6 часов» до отправки. Если отправка срывалась (сеть, ключи, ошибка 4xx), получатель ничего не получал, а следующее уведомление глушилось ещё 6 часов.
- **Журнал повторов.** Служебное уведомление записывалось в журнал повторов как исходное сообщение. Получался ложный «повтор» исходного на 24 часа, хотя исходный текст не уходил.
- **Подмена текста.** Если очередь не приняла запись, в чат должен уйти исходный текст, а не служебное уведомление, которое его скроет.

Исправление (ревью Fable, сессия 2026-11-04, доработка bb051bebe): окно возвращается, если доставка не подтверждена, и следующее сообщение пробует снова.

**Правило.** Лимитёр, дедуп и журналы отправки обновляются по факту подтверждённой доставки (DP.D.328) и только для того сообщения, которое действительно ушло. Окно «одно сообщение о сбое не чаще N» из DP.M.610 считается занятым только после такой доставки. DP.M.420 («запись state — только при фактической отправке алерта») уточняется тем же критерием: попытка отправки ≠ подтверждённая доставка.

**Тест.** «Что заблокирует запись, сделанная до отправки, если отправка сорвётся? И к какому сообщению привязана запись — к ушедшему или к исходному?»

Оговорка: один ревью-случай. Захват: `DS-my-strategy/inbox/captures/2026-11.md` — «Окно ограничения частоты занимать только после подтверждённой доставки…».

## Связи

- **Remediated by:** DP.M.086 (notification_log как cheap idempotency state)
- **See also:** DP.FM.099 (notify-subscription-tied-to-connection — другой класс silent-drop)
- **See also:** DP.M.420 (файл состояния алерта), DP.D.328 (HTTP-успех ≠ подтверждённая доставка), DP.M.610 (окно одного сообщения о сбое при неработающей сводке)
- **Source:** WP-330 peer-session 2026-05-29-29 review-01 Critical fix (handlers/marathon.py:_process_marathon_queue marathon_practice branch)
