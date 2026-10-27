"""Context packing, output protocols and patch application for each strategy.

B0  full rewrite          — whole doc in, whole doc out
B1  full doc + str_replace — whole doc in (cached, conversation grows), {old,new} edits out
B2  section only          — target section in, node-ID ops out, no dependency handling
S   semantic DOM          — cached skeleton + target + impacted dependents in, node-ID ops out
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from .dom import Document, Node, est_tokens
from .graph import SemanticGraph

STRATEGIES = ["B0", "B1", "B2", "S"]

SYS_COMMON = (
    "You are a precise document editor. Apply the user's requested edit. "
    "Also update any other text that the edit makes inconsistent (summaries, cross-references, "
    "repeated facts, defined terms), and change nothing else."
)
SYS = {
    "B0": SYS_COMMON + " Return the complete updated document as markdown and nothing else.",
    "B1": SYS_COMMON
    + (
        ' Return JSON {"edits":[{"old":...,"new":...}]}. Each `old` must be an exact, unique substring '
        "of the current document; keep it as short as uniqueness allows."
    ),
    "B2": SYS_COMMON
    + (
        " You see only part of the document, as nodes tagged [id]. Return JSON "
        '{"ops":[{"op":...,"id":...,"find":...,"replace":...}],"flagged":[...]}. op "edit": use find="" to '
        "replace the node's whole text, otherwise `find` must be an exact substring of that node. op "
        '"insert_after": add a new item after node `id` (or as the first item of section `id`) with text '
        '`replace`. op "delete": remove node `id` (find/replace ignored). Node text excludes the [id] tag and '
        "any leading '#'/'- ' markers. Put IDs of nodes you could not see but suspect need changes in `flagged`."
    ),
}
SYS["S"] = SYS["B2"] + " A document outline is provided for orientation; only nodes shown in full can be edited."
SYS_FOLLOWUP = SYS["S"] + (
    " This is a follow-up: the edit below was already applied (changes listed). Check only the nodes shown"
    " for anything now inconsistent with it and fix those; return no ops if nothing needs changing."
)
FOLLOWUP_BUDGET_TOKENS = 2000

OPS_SCHEMA = {
    "type": "object",
    "properties": {
        "ops": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "op": {"type": "string", "enum": ["edit", "insert_after", "delete"]},
                    "id": {"type": "string"},
                    "find": {"type": "string"},
                    "replace": {"type": "string"},
                },
                "required": ["op", "id", "find", "replace"],
                "additionalProperties": False,
            },
        },
        "flagged": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["ops", "flagged"],
    "additionalProperties": False,
}
EDITS_SCHEMA = {
    "type": "object",
    "properties": {
        "edits": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"old": {"type": "string"}, "new": {"type": "string"}},
                "required": ["old", "new"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["edits"],
    "additionalProperties": False,
}
SCHEMA = {"B1": EDITS_SCHEMA, "B2": OPS_SCHEMA, "S": OPS_SCHEMA}


@dataclass
class Packed:
    system: str
    stable: str  # cacheable document context (prefix)
    volatile: str  # per-request part
    context_ids: set[str] = field(default_factory=set)
    targets: list[str] = field(default_factory=list)


def _with_ancestors(doc: Document, ids: list[str]) -> list[str]:
    out: list[str] = []
    for nid in ids:
        chain: list[str] = []
        n: Node | None = doc.nodes[nid]
        while n is not None and n.kind != "doc":
            chain.append(n.id)
            n = n.parent
        for a in reversed(chain):
            if a not in out:
                out.append(a)
    return out


def render_nodes(doc: Document, ids: list[str]) -> str:
    order = {nid: i for i, nid in enumerate(doc.nodes)}
    lines = []
    for nid in sorted(ids, key=lambda i: order[i]):
        n = doc.nodes[nid]
        if n.kind == "section":
            lines.append(f"[{n.id}] {'#' * n.level} {n.text}")
        else:
            lines.append(f"[{n.id}] {'- ' if n.style == 'bullet' else ''}{n.text}")
    return "\n".join(lines)


def pack(
    strategy: str, doc: Document, graph: SemanticGraph | None, instruction: str, skeleton: str | None = None
) -> Packed:
    """Build request context. Pass a session-frozen `skeleton` to keep S's cached prefix byte-stable.

    B0/B1 send the whole document and need no graph (pass None, so their timing excludes building one)."""
    edit = f"Edit request: {instruction}"
    if strategy in ("B0", "B1"):
        return Packed(SYS[strategy], f"<document>\n{doc.render()}</document>", edit, set(doc.nodes) - {"doc"})
    if graph is None:
        raise ValueError(f"strategy {strategy} needs a SemanticGraph")
    impact = graph.impact(instruction)
    targets = impact.targets
    if strategy == "B2":
        secs = [doc.nodes[t].section() for t in targets] or []
        ids = [n.id for s in secs for n in s.walk()]
        ids = _with_ancestors(doc, ids)
        return Packed(SYS["B2"], "", f"<nodes>\n{render_nodes(doc, ids)}\n</nodes>\n{edit}", set(ids), targets)
    ids = _with_ancestors(doc, impact.all)
    stable = f"<outline>\n{skeleton if skeleton is not None else doc.skeleton()}\n</outline>"
    return Packed(SYS["S"], stable, f"<nodes>\n{render_nodes(doc, ids)}\n</nodes>\n{edit}", set(ids), targets)


def followup_pack(
    before: Document,
    after: Document,
    instruction: str,
    flagged: list[str],
    context_ids: set[str],
    skeleton: str,
) -> Packed | None:
    """Second request for nodes the model flagged but couldn't see (spec 004), or None if there are none."""
    ids: list[str] = []
    spent = 0
    for fid in flagged:
        node = after.nodes.get(fid)
        if node is None or fid in context_ids:
            continue
        for n in node.walk():
            if n.kind == "doc" or n.id in ids or n.id in context_ids:
                continue
            cost = est_tokens(n.text)
            if spent + cost > FOLLOWUP_BUDGET_TOKENS:
                break
            ids.append(n.id)
            spent += cost
    if not ids:
        return None
    changes = [
        f"[{i}] {before.nodes[i].text[:200]!r} -> {after.nodes[i].text[:200]!r}"
        for i in after.nodes
        if i in before.nodes and before.nodes[i].text != after.nodes[i].text
    ]
    volatile = (
        f"Original edit request: {instruction}\nChanges already applied:\n"
        + ("\n".join(changes) or "(none)")
        + f"\n<nodes>\n{render_nodes(after, _with_ancestors(after, ids))}\n</nodes>"
    )
    return Packed(SYS_FOLLOWUP, f"<outline>\n{skeleton}\n</outline>", volatile, set(ids))


# ---- offline output-size model --------------------------------------------
def est_output_tokens(strategy: str, doc: Document, changed: list[str]) -> int:
    """Expected output tokens if the model makes exactly the gold changes.

    Assumes new text ~ old text length. Thinking tokens are excluded (measure live).
    """
    if strategy == "B0":
        return est_tokens(doc.render())
    total = 12
    for nid in changed:
        t = est_tokens(doc.nodes[nid].text)
        if strategy == "B1":  # quoted old + new, needs enough context to be unique in the doc
            total += (2 * t if t <= 40 else 2 * 30) + 15
        else:  # node id makes short finds unique
            total += (t if t <= 30 else 2 * 15) + 12
    return total


# ---- applying model output --------------------------------------------------
def parse_json(text: str) -> dict[str, Any]:
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else {}


def apply_output(strategy: str, doc: Document, text: str) -> tuple[Document, list[str], list[str]]:
    """Apply a model response. Returns (new_doc, errors, flagged_ids)."""
    errors: list[str] = []
    if strategy == "B0":
        md = re.sub(r"^```(?:markdown)?\n|\n```\s*$", "", text.strip())
        return Document.parse(md, doc.doc_type), errors, []
    if strategy == "B1":
        md = doc.render()
        for e in parse_json(text).get("edits", []):
            c = md.count(e["old"])
            if c != 1:
                errors.append(f"old occurs {c}x: {e['old'][:40]!r}")
                continue
            md = md.replace(e["old"], e["new"], 1)
        return Document.parse(md, doc.doc_type), errors, []
    data = parse_json(text)
    new = Document.parse(doc.render(), doc.doc_type)  # copy with identical IDs
    for op in data.get("ops", []):
        n = new.nodes.get(op["id"])
        if n is None:
            errors.append(f"unknown id {op['id']}")
            continue
        kind = op.get("op", "edit")
        if kind == "delete":
            new.delete(n.id)
            continue
        if kind == "insert_after":
            new.insert_after(n.id, _unmark(op["replace"]))
            continue
        find, replace = _unmark(op["find"]), op["replace"]
        if find == "":
            new.set_text(n.id, _unmark(replace))
        elif find in n.text:
            new.set_text(n.id, n.text.replace(find, replace, 1))
        else:
            errors.append(f"find not in {n.id}: {op['find'][:40]!r}")
    # re-parse so bullets the model added inside a node become nodes, as they do for B0/B1
    return Document.parse(new.render(), doc.doc_type), errors, list(data.get("flagged", []))


def _unmark(text: str) -> str:
    """Drop a leading '- ' or '## ' marker the model may copy from the [id] rendering."""
    return re.sub(r"^(?:-|#{1,6})\s+", "", text)
