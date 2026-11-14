---
id: DP.FM.767
name: declare -A (ассоциативные массивы) недоступны в системном bash 3.2 macOS — pattern string+grep
type: failure-mode
trust: empirical
epistemic_stage: pattern
status: draft
created: 2026-11-14
sources:
  - "memory/lessons_bash_assoc_arrays_macos.md (01.07, session-guard.sh; перенос РП-7 Ф309 пачка 2)"
related:
  see_also: [DP.FM.403, PACK-digital-platform]
---

# DP.FM.767: bash 3.2 macOS — нет declare -A

## Симптом
Скрипт с `#!/usr/bin/env bash` и `declare -A` падает/молчит на stock macOS (системный bash 3.2, лицензионная заморозка версии; смена login shell не влияет на git-хуки и скрипты).

## Антипаттерн → Паттерн
- **Антипаттерн:** `declare -A SEEN; SEEN["$key"]=1; [ "${SEEN[$key]+x}" ] && continue`
- **Паттерн (bash 3.2 compatible):**
```bash
_seen=""
echo "$_seen" | grep -qxF "$key" && continue
_seen="$_seen
$key"
```

## Тест обнаружения
Скрипт исполняется системным bash независимо от шелла автора (DP.FM.403 — тот же корень). Проверка на `declare -A` в скриптах, которые должны работать на macOS из коробки.
