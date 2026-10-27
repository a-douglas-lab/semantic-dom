"""Convert cited public sources (see SOURCES.md) into the corpus markdown dialect.

Kept verbatim: titles, headings, wording, ordering. Flattened (parser v1 has no model for them):
code blocks -> one paragraph, tables -> one bullet per row, numbered/nested lists -> flat bullets,
wrapped list lines -> joined. Front matter is dropped except the title.

Usage: python -m evalset.real.convert
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "sources"


def flatten(body: str, demote: int) -> list[str]:
    out: list[str] = []
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("```"):
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                if lines[i].strip():
                    code.append(lines[i].strip())
                i += 1
            out += ["Code: " + " ⏎ ".join(code), ""]
        elif line.startswith(":::"):
            label = re.sub(r"^:::\s*(\w+)(?:\[(.*)\])?.*$", lambda m: (m.group(2) or m.group(1)).strip(), line)
            if label:
                out += [f"Note ({label}):"]
        elif m := re.match(r"^(#{1,6})\s+(.*)$", line):
            out += ["#" * min(6, len(m.group(1)) + demote) + " " + m.group(2), ""]
        elif line.startswith("|"):
            if not re.match(r"^\|[\s:|-]+\|?$", line):
                cells = [c.strip() for c in line.strip("|").split("|")]
                out.append("- " + " | ".join(cells))
        elif m := re.match(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$", line):
            num = re.match(r"^\s*(\d+[.)])\s", line)
            out.append("- " + (num.group(1) + " " if num else "") + m.group(1))
        elif line.startswith((" ", "\t")) and out and out[-1].startswith("- ") and line.strip():
            out[-1] += " " + line.strip()
        else:
            out.append(line.strip())
        i += 1
    # bullets must be separated from following paragraphs by a blank line
    fixed: list[str] = []
    for ln in out:
        if fixed and fixed[-1].startswith("- ") and ln and not ln.startswith(("- ", "#")):
            fixed.append("")
        fixed.append(ln)
    return fixed


def split_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    _, fm, body = text.split("---", 2)
    meta = {}
    for ln in fm.strip().splitlines():
        k, _, v = ln.partition(":")
        meta[k.strip()] = v.strip().strip("'\"")
    return meta, body


def backstage() -> str:
    d = SRC / "backstage"
    md = ["# Backstage Architecture Decision Records", ""]
    meta, body = split_front_matter((d / "index.md").read_text(encoding="utf-8"))
    md += [f"## {meta.get('sidebar_label', 'Overview')}", "", *flatten(body, demote=1)]
    for f in sorted(d.glob("adr0*.md")):
        if f.name.startswith("adr000"):  # the template, not a decision
            continue
        meta, body = split_front_matter(f.read_text(encoding="utf-8"))
        md += ["", f"## {meta['title']}", "", *flatten(body, demote=1)]
    return "\n".join(md)


def govuk() -> str:
    d = SRC / "govuk-aws"
    md = ["# GOV.UK AWS Architecture Decision Records", ""]
    for f in sorted(d.glob("0*.md")):
        text = f.read_text(encoding="utf-8")
        title, _, body = text.partition("\n")
        md += ["", "## " + title.lstrip("# ").strip(), "", *flatten(body, demote=1)]
    return "\n".join(md)


def jsonresume() -> str:
    r = json.loads((SRC / "jsonresume" / "sample.resume.json").read_text(encoding="utf-8"))
    b = r["basics"]
    md = [f"# {b['name']} — Curriculum Vitae", "", b.get("label", ""), "", "## Summary", "", b.get("summary", ""), ""]
    md += ["## Experience", ""]
    for w in r.get("work", []):
        end = w.get("endDate") or "Present"
        md += [f"### {w['position']} — {w['name']} ({w['startDate'][:4]}–{end[:4] if end != 'Present' else end})", ""]
        if w.get("summary"):
            md += [w["summary"], ""]
        md += [f"- {h}" for h in w.get("highlights", [])] + [""]
    for key, heading in [("volunteer", "Volunteering"), ("projects", "Projects")]:
        items = r.get(key, [])
        if items:
            md += [f"## {heading}", ""]
            for v in items:
                title = v.get("position") or v.get("name")
                md += [f"### {title} — {v.get('organization', v.get('entity', ''))}".rstrip(" —"), ""]
                if v.get("summary") or v.get("description"):
                    md += [v.get("summary") or v.get("description"), ""]
                md += [f"- {h}" for h in v.get("highlights", [])] + [""]
    md += (
        ["## Education", ""]
        + [
            f"- {e['studyType']} {e['area']}, {e['institution']} ({e['startDate'][:4]}–{e.get('endDate', '')[:4]})"
            for e in r.get("education", [])
        ]
        + [""]
    )
    if r.get("awards"):
        md += (
            ["## Awards", ""] + [f"- {a['title']} — {a['awarder']}: {a.get('summary', '')}" for a in r["awards"]] + [""]
        )
    if r.get("publications"):
        md += (
            ["## Publications", ""]
            + [f"- {p['name']} — {p['publisher']}: {p.get('summary', '')}" for p in r["publications"]]
            + [""]
        )
    md += (
        ["## Skills", ""]
        + [f"- {s['name']} ({s.get('level', '')}): {', '.join(s.get('keywords', []))}" for s in r.get("skills", [])]
        + [""]
    )
    if r.get("languages"):
        md += ["## Languages", ""] + [f"- {lang['language']}: {lang['fluency']}" for lang in r["languages"]] + [""]
    if r.get("interests"):
        md += (
            ["## Interests", ""] + [f"- {i['name']}: {', '.join(i.get('keywords', []))}" for i in r["interests"]] + [""]
        )
    return "\n".join(md)


def moj() -> str:
    d = SRC / "moj-cloud-platform"
    md = ["# MOJ Cloud Platform Architecture Decision Records", ""]
    for f in sorted(d.glob("[0-9]*.md")):
        title, _, body = f.read_text(encoding="utf-8").partition("\n")
        md += ["", "## " + title.lstrip("# ").strip(), "", *flatten(body, demote=1)]
    return "\n".join(md)


def commonpaper() -> str:
    """Common Paper CSA: '1. Heading' -> section; nested '1.' clauses -> 'N.M Title. text' paragraphs; 'a.' -> bullets."""
    text = (SRC / "commonpaper-csa" / "CSA.md").read_text(encoding="utf-8")
    md: list[str] = []
    for raw in text.splitlines():
        ids = re.findall(r'id="([\d.a-z]+)"', raw)
        line = re.sub(r"<[^>]+>", "", raw).rstrip()
        if not line.strip():
            continue
        if line.startswith("# "):
            md += [line, ""]
        elif m := re.match(r"^(\d+)\.\s+(.*)$", line):  # top-level clause heading
            md += [f"## {m.group(1)}. {m.group(2).strip()}", ""]
        elif m := re.match(r"^\s{4}\d+\.\s+(.*)$", line):  # numbered clause
            num = next((i for i in ids if "." in i), "")
            md += [f"{num} {m.group(1).strip()}".strip(), ""]
        elif m := re.match(r"^\s{8,}([a-z]{1,4})\.\s+(.*)$", line):  # lettered sub-clause
            md.append(f"- ({m.group(1)}) {m.group(2).strip()}")
        else:
            md += [line.strip(), ""]
    return "\n".join(md)


def rendercv() -> str:
    import yaml

    cv = yaml.safe_load((SRC / "rendercv" / "John_Doe_ClassicTheme_CV.yaml").read_text(encoding="utf-8"))["cv"]
    md = [f"# {cv['name']} — Curriculum Vitae", "", f"{cv.get('location', '')}", ""]
    for title, entries in cv["sections"].items():
        md += [f"## {title[:1].upper() + title[1:]}", ""]
        for e in entries:
            if isinstance(e, str):
                md.append(f"- {e}")
                continue
            if "company" in e or "institution" in e or "name" in e:
                head = e.get("position") or e.get("degree") or e.get("name") or ""
                org = e.get("company") or e.get("institution") or ""
                when = "–".join(str(x) for x in (e.get("start_date"), e.get("end_date")) if x) or str(
                    e.get("date") or ""
                )
                md += ["", f"### {head} — {org} ({when})".replace(" — )", ")").replace(" ()", ""), ""]
                if e.get("area"):
                    md += [f"{e['degree']} in {e['area']}, {e.get('location', '')}".strip(", "), ""]
                if e.get("summary"):
                    md += [str(e["summary"]), ""]
                md += [f"- {h}" for h in e.get("highlights") or []] + [""]
            elif "label" in e:
                md.append(f"- {e['label']}: {e['details']}")
            elif "bullet" in e:
                md.append(f"- {e['bullet']}")
            else:
                md.append("- " + "; ".join(f"{k}: {v}" for k, v in e.items() if v))
        md.append("")
    return "\n".join(md)


def adr_dir(subdir: str, title: str, pattern: str = "[0-9]*.md") -> str:
    """Generic ADR folder: each file's first '# ' line becomes a section heading (verbatim)."""
    d = SRC / subdir
    md = [f"# {title}", ""]
    for f in sorted(d.glob(pattern)):
        if "template" in f.name.lower():
            continue
        text = re.sub(r"^(?:\s*<!--.*?-->\s*\n)+", "", f.read_text(encoding="utf-8"))  # leading lint directives
        head, _, body = text.partition("\n")
        md += ["", "## " + head.lstrip("# ").strip(), "", *flatten(body, demote=1)]
    return "\n".join(md)


def bonterms() -> str:
    """Bonterms Cloud Terms: '**N. Title**. text' -> section + paragraph; '**N.M.** text' -> clause; '(a)' -> bullet."""
    text = (SRC / "bonterms" / "Cloud-Terms.md").read_text(encoding="utf-8")
    md: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# "):
            md += [line, ""]
        elif m := re.match(r"^\*\*(\d+)\.\s+([^*]+?)\*\*\.?\s*(.*)$", line):
            md += [f"## {m.group(1)}. {m.group(2).strip()}", ""]
            if m.group(3):
                md += [m.group(3).strip(), ""]
        elif m := re.match(r"^\*\*(\d+\.\d+)\.?\*\*\.?\s*(.*)$", line):
            md += [f"{m.group(1)} {m.group(2).strip()}", ""]
        elif m := re.match(r"^\(([a-z]{1,4})\)\s+(.*)$", line):
            md.append(f"- ({m.group(1)}) {m.group(2)}")
        else:
            md += [line, ""]
    return "\n".join(md)


def best_resume_ever() -> str:
    import yaml

    raw = (SRC / "best-resume-ever" / "data.yml").read_text(encoding="utf-8")
    raw = raw.split("`", 1)[1].rsplit("`", 1)[0]  # strip the JS template-literal wrapper
    cv = yaml.safe_load(raw)
    name = f"{cv['name']['first']} {cv['name']['last']}"
    md = [
        f"# {name} — Curriculum Vitae",
        "",
        cv.get("position", ""),
        "",
        "## About",
        "",
        " ".join(cv["about"].split()),
        "",
    ]
    md += ["## Experience", ""]
    for e in cv.get("experience", []):
        md += [f"### {e['position']} — {e['company']} ({e['timeperiod']})", "", e["description"], ""]
    md += ["## Education", ""]
    for e in cv.get("education", []):
        md += [f"### {e['degree']} ({e['timeperiod']})", "", e["description"], ""]
    md += ["## Skills", ""] + [f"- {s['name']}: {s['level']}/100" for s in cv.get("skills", [])] + [""]
    if cv.get("knowledge"):
        md += [" ".join(str(cv["knowledge"]).split()), ""]
    if cv.get("projects"):
        md += ["## Projects", ""]
        for p in cv["projects"]:
            md.append(
                f"- {p['name']} ({p.get('platform', '')}, {p.get('timeperiod', '')}): {' '.join(str(p.get('description', '')).split())}"
            )
        md.append("")
    for key in ("contributions",):
        if cv.get(key):
            md += [f"## {key.title()}", ""]
            for item in cv[key]:
                if isinstance(item, dict):
                    md.append("- " + "; ".join(f"{k}: {v}" for k, v in item.items() if v))
                else:
                    md.append(f"- {item}")
            md.append("")
    return "\n".join(md)


def main() -> None:
    from sdom.dom import Document, est_tokens

    for name, fn, kind in [
        ("backstage-adr", backstage, "adr"),
        ("govuk-adr", govuk, "adr"),
        ("cv-jsonresume", jsonresume, "cv"),
        # fresh held-out set (spec 008)
        ("moj-adr", moj, "adr"),
        ("commonpaper-csa", commonpaper, "contract"),
        ("cv-rendercv", rendercv, "cv"),
        # second fresh held-out set (spec 009): unquoted instructions
        ("log4brains-adr", lambda: adr_dir("log4brains", "Log4brains Architecture Decision Records", "2*.md"), "adr"),
        (
            "govuk-infra-adr",
            lambda: adr_dir("govuk-infrastructure", "GOV.UK Infrastructure Architecture Decision Records"),
            "adr",
        ),
        ("bonterms-cloud", bonterms, "contract"),
        ("cv-best-resume", best_resume_ever, "cv"),
    ]:
        doc = Document.parse(fn(), kind)
        md = doc.render()
        (HERE / f"{name}.md").write_text(md, encoding="utf-8")
        print(f"{name:<14} ~{est_tokens(md):>6,} tokens  {len(doc.nodes):>4} nodes")


if __name__ == "__main__":
    main()
