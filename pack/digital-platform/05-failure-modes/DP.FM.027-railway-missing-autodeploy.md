---
id: DP.FM.027
name: Railway Missing Auto-Deploy (Ручной деплой без git-интеграции)
category: deployment
severity: major
status: active
summary: "Railway-проект развёртывается вручную (кнопкой), а не через git-webhook. Признак: отсутствие RAILWAY_GIT_* env-переменных и reason='deploy'/'redeploy' вместо 'github_push' в deployments API. Следствие: код в git не соответствует задеплоенному без явного ручного действия."
created: 2026-05-12
valid_from: 2026-05-12
related:
  see_also: [DP.FM.010, DP.FM.009]
  prevented_by: [F5-compliance-check]
tags: [deployment, railway, ci-cd, 12factor, F5]
source: "WP-307 Ф9 диагностика, 12 мая 2026 — peaceful-vision проект, 5 production workers"
---

# [DP.FM.027] Railway Missing Auto-Deploy

## Суть паттерна

Railway-проект считается «задеплоенным из git», но на деле — все деплои ручные. Команда не замечает этого, потому что Railway деплоит успешно в обоих случаях.

## Диагностический признак

При **git-интеграции** Railway автоматически выставляет:
- `RAILWAY_GIT_REPO_OWNER`
- `RAILWAY_GIT_BRANCH`
- `RAILWAY_GIT_COMMIT_SHA`

**Если эти переменные отсутствуют** — git-интеграция не настроена. Подтверждение: deployments API возвращает `reason: "deploy"` или `"redeploy"` вместо `"github_push"`.

## Механизм

1. Railway позволяет деплоить без подключения git-репо (через UI / CLI / API).
2. Команда подключает git-репо позже или не подключает вовсе.
3. CI/CD «работает» — приложение запускается — но не из git-коммитов автоматически.
4. Drift накапливается: `git log` не соответствует тому, что в production.

## Где проявляется в IWE

| Ситуация | Риск |
|----------|------|
| 12-factor F5 audit (Build/Release/Run) | ✅ помечается без проверки git-интеграции |
| Hotfix в git без ручного деплоя | Production не обновляется — silent failure |
| Rollback через git revert | Не работает — нужен ручной redeploy |

Второй случай: 2026-11-02, WP-612 Ф7 — два прод-фикса `chat-analyst-service` закоммичены, идентификатор развёртывания не сменился: у сервиса не было триггера на git push, в отличие от соседних ботов. Источник: git commit f68c63efa в DS-my-strategy; захват `DS-my-strategy/inbox/captures/2026-11.md`.

## Профилактика

1. **При создании Railway-сервиса:** проверить `Settings → Source` — подключён ли git-репо.
2. **При F5-audit:** проверить наличие `RAILWAY_GIT_*` в env ИЛИ убедиться в наличии `.github/workflows/` с deploy-шагом.
3. **Тест:** `railway variables | grep RAILWAY_GIT` — если пусто, деплой ручной.
4. **После пуша прод-фикса:** считать фикс выложенным только когда (а) у сервиса появилось новое развёртывание, собранное из нужного коммита (сменился идентификатор развёртывания, коммит развёртывания = коммит фикса), и (б) живой запрос к сервису показывает исправленное поведение. Факт пуша и зелёный CI это не доказывают.

## Связи

- Расширяет: 12-factor F5 (Build/Release/Run)
- Паттерн verifikации: `lessons_railway_git_deploy_verification.md`
- Compliance rule: `feedback_compliance_audit_dod.md §CI Evidence`
