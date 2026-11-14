---
id: DP.CONCEPT.006
name: Согласие на трекинг не даёт ступени без учебных событий (opt_in ≠ instant stage)
type: domain-entity
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_consent_does_not_imply_activity.md (WP-188 Ф17.10, 12.05; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [DP.CONCEPT.007, PACK-digital-platform]
---

# DP.CONCEPT.006: opt_in ≠ ступень

## Суть
Согласие на трекинг само по себе не даёт расчёта ступени: stage_evaluator считает M1/M2/M4 из domain_event с `activity_domain IN ('practice','learning')`. У пользователя с одними operational-событиями (request_traced, notification_sent, tier_changed) stage_raw=0.

## Следствие для UX (honest consent flow)
1. Accept-сообщение /consent говорит явно: «opt_in сам по себе не даст ступень — нужны действия (/learn, /train) или ОРЗ-протоколы».
2. /consent status показывает practice+learning counts за 30 дней; при 0 — подсказка конкретными действиями.
3. Тексты broadcast не обещают ступень: «платформа узнает, что ты дал согласие — расчёт появится по мере действий».

## Граница классификации
- practice: day_plan_closed, day_close, week/month_plan_closed, slot_logged, iwe_session, pomodoro_completed, wp_closed/completed, strategy_session_completed, pack_updated.
- learning: lesson_completed, training_passed, marathon_step_completed, knowledge_extracted, note_to_capture, teaching_session, real_world_impact.
- operational (work) не считается ни тем, ни другим — re-classification не помогает.
