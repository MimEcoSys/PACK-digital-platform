---
id: DP.SOTA.020
name: Quantum-Like Modeling Lens (FPF C.26*, 2026)
type: sota
status: active
summary: "Математическая линза для систем с probe-coupled state change, order effects, incompatibility, false composition. QL-lite режим как дополнение к классическому набору, не замена."
created: 2026-04-27
edition: "2026-04"
trust:
  F: 4
  G: external
  R: 0.7
related:
  integrates_with: [DP.SOTA.001, DP.SOTA.011, DP.SOTA.015]
  extends: [DP.ARCH.001]
tags: [quantum-like, fpf, c26, probe-coupled, entanglement, order-effects, decision-theory, modeling-lens]
---

# Quantum-Like Modeling Lens (FPF C.26*, 2026)

## 1. Определение

**Quantum-Like Modeling Lens** — формализм моделирования макроскопических социотехнических, организационных и когнитивных систем, в которых:

- наблюдение является **взаимодействием** (probe-coupled), а не read-only чтением;
- существенны **order effects** (порядок измерений меняет исход);
- встречается **incompatibility** (разные измерения несравнимы / некоммутативны);
- состояние **enacted** в момент измерения, а не существует «до» него;
- система демонстрирует **entanglement-like non-separability** (нельзя моделировать части отдельно и «склеивать»).

Это **representational lens**, а не утверждение, что система «физически квантовая». Заимствуется математика, не онтология квантовой механики.

## 2. Статус SOTA (апрель 2026)

**Live extension к FPF.** Включён в FPF как кластер C.26* в апреле 2026 после ~2 лет инкубации; источник — Андрей Илевский, итог 12-стадийного hardening цикла (intake СМС25 2022 → DRR ~300K → 4 новых паттерна + правки 13 существующих → 113 атомарных замечаний внешней проверки).

- **FPF C.26 Quantum-Like Modeling Lens** (root)
- **C.26.1 Probe-Coupled Boundary Interaction**
- **C.26.2 Enacted Distributed State Evidence**
- **C.26.3 Viability-Envelope Boundary Regulation**
- Plus updates: C.11 Decision Theory, A.6 Signature Stack, A.6.B Boundary Norm Square, A.6.P Relational Precision Restoration, A.6.8 Service Polysemy Unpacking, F.9 Alignment and Bridge across Contexts, A.15 Role-Method-Work Alignment, C.25 Q-Bundle, A.10 Evidence Graph Referring, B.3 Trust Assurance Calculus, C.16 Measurement Metrics Characterization, A.6.3.CSC Controlled Semantic Coarsening, A.6.3.RT Representation Transduction.

Базовая работа измерения-в-cognition (Khrennikov и др.) — `arxiv.org/abs/2503.05859` (FPF C.11 anchor).

## 3. Четыре паттерна кластера C.26*

| Паттерн | Что моделирует | Когда применять |
|---------|----------------|-----------------|
| **C.26 Quantum-Like Modeling Lens** | Корневой паттерн-линза | Когда классический набор (измерение, доказательство, понятийные мосты, роли, Q-bundle, coarsening) не закрывает остаточную «запутанность» |
| **C.26.1 Probe-Coupled Boundary Interaction** | Зонд/запрос системы меняет её состояние через границу контекста | KPI лидерборд → люди оптимизируют KPI; Гудхарт; диагностический вопрос меняет диагностируемого |
| **C.26.2 Enacted Distributed State Evidence** | Состояние не существует «до» измерения, оно порождается процессом измерения | Ответ респондента на нечётко определённый вопрос со-конструируется в момент опроса; диалог Диагноста (DP.ROLE.042) |
| **C.26.3 Viability-Envelope Boundary Regulation** | Регулирование границ жизнеспособности при изменяющихся контекстах | Архитектура↔команда (Конвей): нельзя менять границу одной без сдвига границы другой |

## 4. Триггеры применения (когда «обычный набор» исчерпан)

Сначала пробуем **классический набор**:
1. Простое измерение и анализ
2. Доказательство в рамках одного контекста
3. Понятийные мосты между контекстами (FPF F.9)
4. Работа ролей (FPF A.15)
5. Определение качества (FPF C.25 Q-bundle)
6. Coarsening / упрощение представления (FPF A.6.3.CSC)

**QL-lite активируется**, когда после этих шагов остаются:

- **Order effects:** ответ на «X→Y» отличается от ответа на «Y→X».
- **Incompatibility:** два измерения системы дают несовместимые результаты не из-за шума.
- **Probe-coupling:** сам факт измерения изменил то, что измеряется (метрика стала целью).
- **False composition:** соединение «частичных истин» даёт нерабочий результат.
- **Cross-context evidence transfer:** свидетельство из контекста A нельзя перенести в контекст B без перестройки.

## 5. Предохранители при применении (QL-lite discipline)

При активации линзы агент **обязан назвать**:

1. **Обычного владельца** ответственности (responsible party) — кто отвечает за систему до квантовоподобного моделирования.
2. **Конкретный сбой представления** — какое именно классическое представление не сработало.
3. **Самый слабый допустимый вывод** — минимально необходимое утверждение, ради которого вводится линза.
4. **Что вы хотите сделать** — какое решение/действие зависит от модели.
5. **Когда остановиться в моделировании** — критерий выхода из QL-режима обратно в классический.

Без всех 5 — линза не активирована, остаёмся в классическом наборе.

## 6. Ключевые различения

- **Quantum-like ≠ physical quantum.** Линза заимствует математику (incompatibility, non-commuting observables, Hilbert-space-like state), не физическую квантовость носителя.
- **Linear Hilbert-space dynamics** часто **проще** нелинейной классической биофизической динамики (см. quantum-like в biology, Khrennikov 2020) — это представительный выигрыш, а не онтологическое утверждение.
- **QL-lite ≠ полный quantum-like state-space package.** В FPF C.26 явно: «one minimal mathematical floor versus premature heavy formalism».
- **Probe-coupling ≠ простая связность (coupling).** Coupling Model (DP.SOTA.011) измеряет статическую зависимость; probe-coupling — динамическое изменение состояния под действием измерения.

## 7. Применение в IWE / экзокортексе

| Где | Что было классически | Что добавляет QL-линза |
|-----|--------------------|----------------------|
| **Метрики (DP.SOTA.015 observability)** | KPI как нейтральный индикатор | KPI = probe → меняет систему; проектировать с учётом feedback-loop поведения (Гудхарт) |
| **Диагност (DP.ROLE.042; специализация МИМ — MIM.R.009)** | Анкета считывает ступень | Диалог со-конструирует ступень; order effects в последовательности вопросов; Enacted Distributed State Evidence |
| **Карта 12 БД (DP.ARCH.004)** | Database-per-service независимы | Конвей: схема БД ↔ команда-владелец = entangled; смена одной без другой ломает viability-envelope |
| **Memory vs Persona (HD #27, DP.D.050)** | Memory.Derived (расчёт из событий) — байесовская | Persona (декларации) — quantum-like: акт записи меняет автора |
| **Strategy Session** | Обсуждение целей выявляет цели | Обсуждение **меняет** цели (probe-coupled); порядок неудовлетворённостей важен |
| **Verification class (HD #32)** | trivial / closed-loop / open-loop / problem-framing | problem-framing часто = QL-ситуация; open-loop = вероятный probe-coupling |

## 8. Антипаттерны

- **«Прыжок в QL»**: применять линзу там, где работают классические средства (нарушает Q-bundle FPF C.25 — сначала простое, потом сложное).
- **Prestige-branch citation**: цитировать quantum-like как модное название без указания, какое ограничение классического подхода она ремонтирует (FPF CC-C11.8).
- **Heavy-formalism overclaim**: тащить полный Hilbert-space package там, где достаточно «order effects matter» (FPF CC-C11.9).
- **Physical quantum claim**: утверждать, что социотехническая система «физически квантовая».
- **Bias первых самолётов**: либо игнорировать линзу из-за «у других не получилось», либо превращать в обязательную бюрократию.

## 9. Источники

- **FPF C.26 Quantum-Like Modeling Lens** + C.26.1 / C.26.2 / C.26.3 (FPF Spec, edition 2026-04)
- Илевский А., пост: <https://systemsworld.club/t/kvantovopodobnost-quantum-like-uzhe-v-fpf/38642> (2026-04-26/27)
- Khrennikov A. et al. — Quantum-like modeling in biology (Sciencedirect, 2020): <https://www.sciencedirect.com/science/article/pii/S0303264720301994>
- Measurement-theory decision/cognition anchor (2025): <https://arxiv.org/abs/2503.05859>
