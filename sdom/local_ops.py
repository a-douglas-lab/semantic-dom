"""Deterministic local edits the harness can make without an LLM call (spec 003).

Only explicit, document-wide rename intents trigger; anything needing judgment goes to the model.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .dom import Document

_CAP = r"[A-Z][\w&.-]*(?: [A-Z][\w&.-]*)*"
_PATTERNS = [
    re.compile(r"\brename (?:the )?(?:defined )?(?:term )?\"(?P<old>[^\"]+)\" (?:to|as) \"(?P<new>[^\"]+)\"", re.I),
    re.compile(r"\breplace \"(?P<old>[^\"]+)\" with \"(?P<new>[^\"]+)\" (?:everywhere|throughout)", re.I),
    re.compile(rf"(?P<old>{_CAP}) has rebranded as (?P<new>{_CAP})"),
    re.compile(rf"(?P<old>{_CAP}) (?:was|has been) renamed (?:to|as) (?P<new>{_CAP})"),
]


@dataclass(frozen=True)
class LocalPlan:
    old: str
    new: str


def plan_local(instruction: str) -> LocalPlan | None:
    """Return a rename plan for explicit document-wide rename requests, else None."""
    for rx in _PATTERNS:
        if m := rx.search(instruction):
            return LocalPlan(m.group("old").strip(), m.group("new").strip())
    return None


def _article(new: str, original: str) -> str:
    art = "an" if new[:1].lower() in "aeiou" else "a"
    return art.capitalize() if original[:1].isupper() else art


def apply_local(doc: Document, plan: LocalPlan) -> tuple[Document, list[str]]:
    """Apply a rename to a copy of the document. Returns (new_doc, changed node ids)."""
    term = re.compile(r"\b" + re.escape(plan.old) + r"(?=(?:'s|s)?\b)")
    article = re.compile(r"\b(an?|An?) (?=" + re.escape(plan.new) + r"\b)")
    new = Document.parse(doc.render(), doc.doc_type)
    changed = []
    for node in new.nodes.values():
        text = term.sub(plan.new, node.text)
        if text != node.text:
            text = article.sub(lambda m: _article(plan.new, m.group(1)) + " ", text)
            new.set_text(node.id, text, origin="local")
            changed.append(node.id)
    return new, changed
