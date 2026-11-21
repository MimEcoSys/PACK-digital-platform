#!/usr/bin/env python3
"""Architecture registry of the platform and IWE (WP-611 F34).

Source of truth: pack/digital-platform/architecture-registry/*.yaml
  subsystems.yaml   - subsystems (stable key, name, other names, status)
  modules.yaml      - modules: programs, program sets, databases, stores, queues
  environment.yaml  - environment systems (not ours) and sites
  links.yaml        - performs, located_in, calls, deployed, paths
Generated view: pack/digital-platform/architecture-registry.md (do not edit).
Generated tables: DP.ARCH.001 §4.1 and §11.1а between the markers
  <!-- architecture-registry:begin <label> --> ... <!-- architecture-registry:end <label> -->
  (the «Модули» column and, in §11.1а, the «when» column come from the registry;
  the «Что делает для целого» text of §4.1 stays hand-written).

Usage:
  architecture-registry.py build   # validate, write the generated view and tables
  architecture-registry.py check   # validate, fail if the view or the tables are stale (CI)
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2] / "pack" / "digital-platform"
REGISTRY = ROOT / "architecture-registry"
VIEW = ROOT / "architecture-registry.md"
ARCH_DOC = ROOT / "02-domain-entities" / "DP.ARCH.001-platform-architecture.md"

MODULE_KINDS = {"программа", "набор программ", "база данных", "проект баз данных", "хранилище", "очередь"}
RUNNABLE = {"программа", "набор программ"}
STATUSES = {"существует", "проектируется", "есть только функция или метод"}
VERBS = {"читает", "пишет", "вызывает", "обращается"}
REQUIRED = {
    "подсистема": ("id", "name", "system", "status", "purpose"),
    "модуль": ("id", "name", "kind", "system", "status", "purpose"),
    "система окружения": ("id", "purpose"),
}
COMPARED_TABLES = {
    "4.1": ("### 4.1. Платформа", "Подсистема", "Модули"),
    "11.1а": ("### 11.1а.", "Функциональная подсистема", "Модули"),
}


class Registry:
    def __init__(self, folder: Path):
        def read(name):
            return yaml.safe_load((folder / name).read_text())

        env = read("environment.yaml")
        self.subsystems = read("subsystems.yaml")["subsystems"]
        modules_doc = read("modules.yaml")
        self.modules = modules_doc["modules"]
        self.excluded = modules_doc.get("excluded", [])
        self.environment = env["environment"]
        self.sites = {site["id"] for site in env["sites"]}
        self.links = read("links.yaml")
        self.module_by_id = {m.get("id"): m for m in self.modules}
        self.environment_ids = {e.get("id") for e in self.environment}
        self.subsystem_ids = {s.get("id") for s in self.subsystems}


def check_records(records, kind, errors):
    ids = [r.get("id") for r in records]
    for duplicate in sorted({i for i in ids if ids.count(i) > 1}, key=str):
        errors.append(f"{kind}: повтор id {duplicate}")
    for record in records:
        missing = [field for field in REQUIRED[kind] if not record.get(field)]
        if missing:
            errors.append(f"{kind} {record.get('id', '?')}: нет полей {', '.join(missing)}")


def check_values(reg: Registry, errors):
    for s in reg.subsystems:
        if s.get("status") not in STATUSES:
            errors.append(f"подсистема {s.get('id')}: недопустимый статус {s.get('status')}")
    for m in reg.modules:
        if m.get("kind") not in MODULE_KINDS:
            errors.append(f"модуль {m.get('id')}: недопустимый вид {m.get('kind')}")
        if m.get("status") not in STATUSES:
            errors.append(f"модуль {m.get('id')}: недопустимый статус {m.get('status')}")
    names = {}
    for record in reg.modules + reg.environment + reg.subsystems:
        for name in filter(None, [record.get("id"), *record.get("aliases", [])]):
            if names.setdefault(name, record.get("id")) != record.get("id"):
                errors.append(f"имя «{name}» указывает на {names[name]} и {record.get('id')}")


def check_links(reg: Registry, errors):
    links = reg.links
    known = set(reg.module_by_id) | reg.environment_ids
    for link in links["performs"]:
        if link["module"] not in reg.module_by_id:
            errors.append(f"работает на: неизвестный модуль {link['module']}")
        if link["subsystem"] not in reg.subsystem_ids:
            errors.append(f"работает на: неизвестная подсистема {link['subsystem']}")
    for link in links["located_in"]:
        container = reg.module_by_id.get(link["in"], {})
        if link["module"] not in reg.module_by_id or container.get("kind") != "проект баз данных":
            errors.append(f"находится в: {link['module']} → {link['in']} — неизвестный модуль или не проект баз")
    for call in links["calls"]["items"]:
        for ref in (call["from"], call["to"]):
            if ref not in known:
                errors.append(f"обращается: неизвестное имя {ref}")
        if call["verb"] not in VERBS:
            errors.append(f"обращается {call['from']} → {call['to']}: недопустимый глагол {call['verb']}")
    for item in links["deployed"]["items"]:
        if item["module"] not in reg.module_by_id:
            errors.append(f"стоит на: неизвестный модуль {item['module']}")
        if item["site"] not in reg.sites:
            errors.append(f"стоит на {item['module']}: неизвестная площадка {item['site']}")
    for path in links["paths"]:
        for step in path["steps"]:
            for ref in (step["from"], step["to"]):
                if ref not in known:
                    errors.append(f"путь {path['id']}: неизвестное имя {ref}")
    performing = {link["module"] for link in links["performs"]}
    for m in reg.modules:
        if m.get("no_subsystem") and m.get("id") in performing:
            errors.append(f"{m['id']}: указано «подсистемы нет», но связь «работает на» есть")
        elif (m.get("kind") in RUNNABLE and m.get("system") == "платформа"
              and m.get("id") not in performing and not m.get("no_subsystem")):
            errors.append(f"{m['kind']} {m['id']} не работает ни на одну подсистему "
                          "(или укажи no_subsystem с причиной)")


def validate(reg: Registry):
    errors = []
    check_records(reg.subsystems, "подсистема", errors)
    check_records(reg.modules, "модуль", errors)
    check_records(reg.environment, "система окружения", errors)
    if not errors:
        check_values(reg, errors)
        check_links(reg, errors)
    return errors


def split_outside_parentheses(cell: str):
    parts, depth, current = [], 0, []
    for char in cell:
        depth += (char == "(") - (char == ")")
        if char in ",;" and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def table_rows(doc: str, heading: str, key_col: str, value_col: str):
    lines = doc[doc.index(heading):].splitlines()[1:]
    rows, header = {}, None
    for line in lines:
        if line.startswith("#"):
            break
        if not line.startswith("|"):
            if header is not None:
                break
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = cells
        elif not set(cells[0]) <= {"-", " "}:
            row = dict(zip(header, cells))
            rows[row[key_col]] = row.get(value_col, "")
    return rows


def lookup(index, name):
    """Exact name, then the name without a trailing explanation in brackets."""
    return index.get(name) or index.get(re.split(r" \(", name, maxsplit=1)[0].strip())


def compare_with_document(reg: Registry, doc: str):
    """Hand-written subsystem → modules tables of DP.ARCH.001 vs the registry."""
    index = {}
    for record in reg.modules + reg.environment:
        for name in filter(None, [record.get("id"), record.get("name"), *record.get("aliases", [])]):
            index.setdefault(name, record["id"])
    expected = defaultdict(set)
    for link in reg.links["performs"]:
        expected[link["subsystem"]].add(link["module"])
    findings = []
    for label, (heading, key_col, value_col) in COMPARED_TABLES.items():
        if heading not in doc:
            findings.append(f"§{label}: заголовок «{heading}» не найден — сверка таблицы пропущена")
            continue
        rows = table_rows(doc, heading, key_col, value_col)
        for s in platform_subsystems(reg):
            cell = rows.get(s["name"])
            if cell is None:
                findings.append(f"§{label}: нет строки «{s['name']}»")
                continue
            if cell in EMPTY_CELLS:
                cell = ""
            written = [part for n in split_outside_parentheses(cell) for part in n.split(" и ")]
            known = {n: lookup(index, n) for n in written}
            resolved = {module_id for module_id in known.values() if module_id}
            findings += [f"§{label} «{s['name']}»: «{n}» нет в справочниках" for n, m in known.items() if not m]
            findings += [f"§{label} «{s['name']}»: не указан {m}" for m in sorted(expected[s["id"]] - resolved)]
            findings += [f"§{label} «{s['name']}»: указан {m}, связи «работает на» нет"
                         for m in sorted(resolved - expected[s["id"]])]
    return findings


MARKER_BEGIN = "<!-- architecture-registry:begin {} -->"
MARKER_END = "<!-- architecture-registry:end {} -->"
NO_MODULES = {"проектируется": "нет (подсистема проектируется)"}
NO_MODULES_DEFAULT = "не назначены"
EMPTY_CELLS = {*NO_MODULES.values(), NO_MODULES_DEFAULT}


def module_label(reg: Registry, module_id: str) -> str:
    """Programs are shown by program name (the id, decision Р4), stores by their name."""
    record = reg.module_by_id[module_id]
    return module_id if record["kind"] in RUNNABLE else record["name"]


def performed_by(reg: Registry, subsystem_id: str):
    """(label, when, runnable) per distinct label, in registry order."""
    seen, rows = set(), []
    for link in reg.links["performs"]:
        if link["subsystem"] != subsystem_id:
            continue
        label = module_label(reg, link["module"])
        if label not in seen:
            seen.add(label)
            runnable = reg.module_by_id[link["module"]]["kind"] in RUNNABLE
            rows.append((label, link.get("when") or "не установлено", runnable))
    return rows


def platform_subsystems(reg: Registry):
    return [s for s in reg.subsystems if s["system"] == "платформа"]


def modules_cell(subsystem, pairs, separator):
    if pairs:
        return separator.join(label for label, _, _ in pairs)
    return NO_MODULES.get(subsystem["status"], NO_MODULES_DEFAULT)


def table_41(reg: Registry, doc: str):
    heading, key_col, _ = COMPARED_TABLES["4.1"]
    purposes = table_rows(doc, heading, key_col, "Что делает для целого")
    rows = ["| Подсистема | Что делает для целого | Модули |", "| --- | --- | --- |"]
    for s in platform_subsystems(reg):
        purpose = purposes.get(s["name"]) or cell(s["purpose"])
        modules = modules_cell(s, performed_by(reg, s["id"]), ", ")
        rows.append(f"| {s['name']} | {purpose} | {cell(modules)} |")
    return rows


def table_111a(reg: Registry, doc: str):
    rows = ["| Функциональная подсистема | Модули | Когда модуль работает на подсистему |", "|---|---|---|"]
    for s in platform_subsystems(reg):
        pairs = performed_by(reg, s["id"])
        programs = [(label, w) for label, w, runnable in pairs if runnable]
        if any(w != "не установлено" for _, w in programs):
            when = "; ".join(f"{label} — {w}" for label, w in programs)
        else:
            when = "не установлено"
        rows.append(f"| {s['name']} | {cell(modules_cell(s, pairs, '; '))} | {cell(when)} |")
    return rows


DOC_TABLES = {"4.1": table_41, "11.1а": table_111a}


def render_document(reg: Registry, doc: str):
    """DP.ARCH.001 with the generated tables put between their markers.
    Returns (document, errors); a missing or broken marker pair is an error,
    so a target place cannot silently drop out of generation."""
    errors = []
    for label, make_table in DOC_TABLES.items():
        begin, end = MARKER_BEGIN.format(label), MARKER_END.format(label)
        heading = COMPARED_TABLES[label][0]
        if doc.count(begin) != 1 or doc.count(end) != 1 or doc.index(begin) > doc.index(end):
            errors.append(f"DP.ARCH.001 §{label}: нет пары меток сборки «{begin}» … «{end}»")
            continue
        head, rest = doc.split(begin, 1)
        inside, tail = rest.split(end, 1)
        if "architecture-registry:" in inside:
            errors.append(f"DP.ARCH.001 §{label}: внутри пары меток сборки стоит чужая метка")
            continue
        if heading not in head:
            errors.append(f"DP.ARCH.001 §{label}: заголовок «{heading}» не найден перед метками сборки")
            continue
        doc = head + "\n".join([begin, *make_table(reg, doc), end]) + tail
    return doc, errors


def access_maps(reg: Registry):
    """Callers, writers and readers. «обращается» (direction unknown) is a call to
    a program or an environment system and a read of a database, store or queue;
    data flows through a store only along an explicit «пишет», so an unclear
    link never makes the whole platform look affected."""
    callers, writes, readers = defaultdict(set), defaultdict(set), defaultdict(set)
    for call in reg.links["calls"]["items"]:
        source, target, verb = call["from"], call["to"], call["verb"]
        is_store = reg.module_by_id.get(target, {}).get("kind") not in RUNNABLE and target in reg.module_by_id
        if verb == "вызывает" or (verb == "обращается" and not is_store):
            callers[target].add(source)
        elif verb == "пишет":
            writes[source].add(target)
        else:
            readers[target].add(source)
    return callers, writes, readers


def affected_by(module_id: str, maps):
    callers, writes, readers = maps
    affected, queue = {}, [module_id]
    while queue:  # sorted iteration: the generated view must be byte-identical between runs
        current = queue.pop(0)
        for caller in sorted(callers[current] - affected.keys() - {module_id}):
            affected[caller] = f"вызывает {current}"
            queue.append(caller)
        for store in sorted(writes[current]):
            for reader in sorted(readers[store] - affected.keys() - {module_id, current}):
                affected[reader] = f"читает {store}, куда пишет {current}"
                queue.append(reader)
    return affected


def cell(text):
    return str(text).replace("|", "/").replace("\n", " ")


def render(reg: Registry, findings):
    subsystem_name = {s["id"]: s["name"] for s in reg.subsystems}
    out = ["---", "id: DP.ARCH.001-registry-view", "type: generated-view",
           "source: pack/digital-platform/architecture-registry/*.yaml",
           "generator: .github/scripts/architecture-registry.py", "---", "",
           "# Справочники архитектуры платформы и IWE",
           "",
           "> Собрано программой из справочников `architecture-registry/`; руками не править. "
           "Правило и порядок изменения — абзац «Справочники имён и связей» в "
           "[DP.ARCH.001](02-domain-entities/DP.ARCH.001-platform-architecture.md). "
           "Имена систем, подсистем и модулей бери отсюда.", ""]
    out += ["## Подсистемы", "", "| Ключ | Имя | Другие имена | Система | Статус | Что делает |", "|---|---|---|---|---|---|"]
    out += [f"| {s['id']} | {s['name']} | {cell('; '.join(s.get('aliases', [])))} | {s['system']} | {s['status']} | "
            f"{cell(s['purpose'])} |" for s in reg.subsystems]
    out += ["", "## Модули", "", "| id | Имя | Другие имена | Вид | Система | Статус | Что делает |", "|---|---|---|---|---|---|---|"]
    out += [f"| {m['id']} | {cell(m['name'])} | {cell('; '.join(m.get('aliases', [])))} | {m['kind']} | {m['system']} | "
            f"{m['status']} | {cell(m['purpose'])} |" for m in reg.modules]
    out += ["", "## Системы окружения", "", "| id | Другие имена | Что делает |", "|---|---|---|"]
    out += [f"| {e['id']} | {cell('; '.join(e.get('aliases', [])))} | {cell(e['purpose'])} |" for e in reg.environment]
    out += ["", "## Работает на: подсистема → модули", "", "| Подсистема | Модуль | Когда |", "|---|---|---|"]
    out += [f"| {subsystem_name[link['subsystem']]} | {link['module']} | {cell(link['when'])} |"
            for link in sorted(reg.links["performs"], key=lambda l: (l["subsystem"], l["module"]))]
    by_site = defaultdict(list)
    for item in reg.links["deployed"]["items"]:
        by_site[item["site"]].append(item["module"])
    out += ["", f"## Стоит на: площадка → модули ({reg.links['deployed']['snapshot']})", "", "| Площадка | Модули |", "|---|---|"]
    out += [f"| {site} | {', '.join(sorted(mods))} |" for site, mods in sorted(by_site.items())]
    out += ["", f"## Обращается к ({reg.links['calls']['snapshot']})", "", "| Кто | Глагол | Кому |", "|---|---|---|"]
    out += [f"| {c['from']} | {c['verb']} | {c['to']} |" for c in reg.links["calls"]["items"]]
    maps = access_maps(reg)
    out += ["", "## Что затронет отключение модуля", "",
            "> По записанным связям; «затронет» значит «есть связь», а не «точно сломается». "
            "Через базу влияние идёт только по связям с явным «пишет»; связи «обращается» "
            "без направления к базе считаются чтением. Ссылки из раздела «Уточнить у владельцев модулей» "
            "в расчёт не входят.", ""]
    for m in reg.modules:
        if m["kind"] in RUNNABLE:
            affected = affected_by(m["id"], maps)
            listed = "; ".join(f"{name} ({why})" for name, why in sorted(affected.items()))
            out.append(f"- **{m['id']}**: {listed or 'по записанным связям ничего'}")
    for path in reg.links["paths"]:
        out += ["", f"## Путь {path['id']}: {path['need']}", "", "```mermaid", "flowchart LR"]
        out += [f'  "{s["from"]}" -- "{s["action"]}" --> "{s["to"]}"' for s in path["steps"]]
        out += ["```"]
        if path.get("note"):
            out.append(f"Примечание: {path['note']}")
    unresolved = [(m["id"], m["calls_unresolved"]) for m in reg.modules if m.get("calls_unresolved")]
    out += ["", "## Уточнить у владельцев модулей", "",
            "Ссылки из графы «Обращается к» DP.ARCH.001 §5.1, которые нельзя однозначно привязать "
            "(обрезаны в документе или не названа база):", ""]
    out += [f"- **{module_id}**: {'; '.join(tokens)}" for module_id, tokens in unresolved]
    out += ["", "Программы без подсистемы (с причиной):", ""]
    out += [f"- **{m['id']}**: {m['no_subsystem']}" for m in reg.modules if m.get("no_subsystem")]
    out += ["", "Не перенесено как модуль:", ""] + [f"- {reason}" for reason in reg.excluded]
    out += ["", "## Обратная сверка собранных таблиц DP.ARCH.001 со справочниками", ""]
    out += [f"- {f}" for f in findings] or ["- нет"]
    return "\n".join(out) + "\n"


def main(argv):
    if len(argv) != 2 or argv[1] not in ("build", "check"):
        sys.exit(__doc__)
    try:
        reg = Registry(REGISTRY)
        errors = validate(reg)
    except (KeyError, TypeError, AttributeError, yaml.YAMLError) as exc:
        print(f"справочники архитектуры: файл повреждён или не хватает раздела ({type(exc).__name__}: {exc})")
        return 1
    if errors:
        print(f"справочники архитектуры: ошибок {len(errors)}")
        print("\n".join(f"ОШИБКА: {e}" for e in errors))
        return 1
    current_doc = ARCH_DOC.read_text()
    doc, doc_errors = render_document(reg, current_doc)
    if doc_errors:
        print("\n".join(f"ОШИБКА: {e}" for e in doc_errors))
        return 1
    findings = compare_with_document(reg, doc)
    view = render(reg, findings)
    if argv[1] == "check":
        stale = [name for name, fresh in ((VIEW.name, VIEW.exists() and VIEW.read_text() == view),
                                          (ARCH_DOC.name, current_doc == doc)) if not fresh]
        if stale:
            print(f"справочники архитектуры: устарело ({', '.join(stale)}) — запусти build; "
                  "таблицы между метками сборки руками не правят")
            return 1
        print(f"справочники архитектуры: ошибок нет; расхождений собранных таблиц DP.ARCH.001: {len(findings)}")
        return 0
    VIEW.write_text(view)
    ARCH_DOC.write_text(doc)
    print(f"справочники архитектуры: собрано; расхождений собранных таблиц DP.ARCH.001: {len(findings)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
