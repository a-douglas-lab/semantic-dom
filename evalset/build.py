"""Generate the corpus (markdown docs) and resolved gold cases into evalset/corpus/.

Synthetic docs come from evalset/generators.py; held-out real docs from evalset/real/ (spec 006).
"""

import json
from dataclasses import asdict
from pathlib import Path

from evalset.generators import GENERATORS, resolve_case
from evalset.real.cases import CASES as REAL_CASES
from evalset.real.cases import REAL_DOCS
from evalset.real.fresh2_cases import FRESH2_CASES, FRESH2_DOCS
from evalset.real.fresh_cases import FRESH_CASES, FRESH_DOCS
from sdom.dom import Document, est_tokens

OUT = Path(__file__).parent / "corpus"
REAL = Path(__file__).parent / "real"


def _write(name: str, doc_type: str, size: str, md: str, cases: list, real: bool) -> dict:
    doc = Document.parse(Document.parse(md, doc_type).render(), doc_type)
    md = doc.render()  # canonical form
    (OUT / f"{name}.md").write_text(md, encoding="utf-8")
    resolved = [{**asdict(c), "gold": resolve_case(doc, c)} for c in cases]
    (OUT / f"{name}.cases.json").write_text(json.dumps(resolved, indent=2), encoding="utf-8")
    return {
        "doc": name,
        "type": doc_type,
        "size": size,
        "tokens_est": est_tokens(md),
        "nodes": len(doc.nodes),
        "cases": len(cases),
        "real": real,
    }


def build() -> list[dict]:
    OUT.mkdir(exist_ok=True)
    manifest = []
    for doc_type, (gen, sizes) in GENERATORS.items():
        for size in sizes:
            md, cases = gen(size)
            manifest.append(_write(f"{doc_type}-{size}", doc_type, size, md, cases, real=False))
    for name, (src, doc_type) in REAL_DOCS.items():
        md = (REAL / src).read_text(encoding="utf-8")
        manifest.append(_write(name, doc_type, "real", md, REAL_CASES[name], real=True))
    for name, (src, doc_type) in FRESH_DOCS.items():
        md = (REAL / src).read_text(encoding="utf-8")
        manifest.append(_write(name, doc_type, "fresh", md, FRESH_CASES[name], real=True))
    for name, (src, doc_type) in FRESH2_DOCS.items():
        md = (REAL / src).read_text(encoding="utf-8")
        manifest.append(_write(name, doc_type, "fresh2", md, FRESH2_CASES[name], real=True))
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    for m in build():
        print(f"{m['doc']:<20} ~{m['tokens_est']:>7,} tokens  {m['nodes']:>5} nodes  {m['cases']} cases")
