"""Semantic DOM: a document as a tree of addressable, versioned nodes.

Hierarchy: doc -> section (any heading depth) -> item (bullet or paragraph).
Node IDs are structural paths (e.g. ``s3.s1.i2``) assigned at scan time and kept
stable for the session; new nodes get fresh suffixed IDs rather than renumbering.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterator
from dataclasses import dataclass, field

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
BULLET = re.compile(r"^-\s+(.*)$")


def est_tokens(text: str) -> int:
    """Cheap token estimate (~4 chars/token). Calibrate against count_tokens in live runs."""
    return max(1, round(len(text) / 4))


@dataclass
class Node:
    id: str
    kind: str  # "doc" | "section" | "item"
    text: str  # heading title for doc/section, content for item
    level: int = 0  # heading level for doc/section
    style: str = ""  # "bullet" | "para" for items
    children: list[Node] = field(default_factory=list)
    parent: Node | None = field(default=None, repr=False)
    history: list[str] = field(default_factory=list)  # previous texts, oldest first

    @property
    def hash(self) -> str:
        return hashlib.sha1(self.text.encode()).hexdigest()[:10]

    def walk(self) -> Iterator[Node]:
        yield self
        for c in self.children:
            yield from c.walk()

    def section(self) -> Node:
        """Nearest enclosing section (self if a section)."""
        n = self
        while n.kind == "item" and n.parent is not None:
            n = n.parent
        return n

    def path_titles(self) -> list[str]:
        out, n = [], self if self.kind != "item" else self.parent
        while n is not None and n.kind != "doc":
            out.append(n.text)
            n = n.parent
        return list(reversed(out))


class Document:
    def __init__(self, root: Node, doc_type: str = "generic"):
        self.root = root
        self.doc_type = doc_type
        self.log: list[dict[str, object]] = []  # event log: {seq, id, old, new, origin}
        self._index()

    # ---- construction -------------------------------------------------
    @classmethod
    def parse(cls, markdown: str, doc_type: str = "generic") -> Document:
        lines = markdown.splitlines()
        root = Node("doc", "doc", "", level=1)
        stack = [root]
        counters: dict[str, list[int]] = {}

        def next_id(parent: Node, prefix: str) -> str:
            c = counters.setdefault(parent.id, [0, 0])
            idx = 0 if prefix == "s" else 1
            c[idx] += 1
            base = "" if parent.kind == "doc" else parent.id + "."
            return f"{base}{prefix}{c[idx]}"

        para: list[str] = []

        def flush_para() -> None:
            if para:
                parent = stack[-1]
                n = Node(next_id(parent, "i"), "item", " ".join(para), style="para", parent=parent)
                parent.children.append(n)
                para.clear()

        for line in lines:
            if m := HEADING.match(line):
                flush_para()
                level, title = len(m.group(1)), m.group(2).strip()
                if level == 1 and root.text == "":
                    root.text = title
                    continue
                while stack[-1].kind != "doc" and stack[-1].level >= level:
                    stack.pop()
                parent = stack[-1]
                n = Node(next_id(parent, "s"), "section", title, level=level, parent=parent)
                parent.children.append(n)
                stack.append(n)
            elif m := BULLET.match(line):
                flush_para()
                parent = stack[-1]
                parent.children.append(
                    Node(next_id(parent, "i"), "item", m.group(1).strip(), style="bullet", parent=parent)
                )
            elif line.strip() == "":
                flush_para()
            else:
                para.append(line.strip())
        flush_para()
        return cls(root, doc_type)

    def _index(self) -> None:
        self.nodes: dict[str, Node] = {n.id: n for n in self.root.walk()}

    # ---- rendering ----------------------------------------------------
    def render(self) -> str:
        out = [f"# {self.root.text}", ""]

        def emit(node: Node) -> None:
            prev_style = None
            for c in node.children:
                if c.kind == "section":
                    if prev_style == "bullet":
                        out.append("")
                    out.extend([f"{'#' * c.level} {c.text}", ""])
                    emit(c)
                    prev_style = None
                elif c.style == "bullet":
                    out.append(f"- {c.text}")
                    prev_style = "bullet"
                else:
                    if prev_style == "bullet":
                        out.append("")
                    out.extend([c.text, ""])
                    prev_style = "para"
            if prev_style == "bullet":
                out.append("")

        emit(self.root)
        return "\n".join(out).rstrip() + "\n"

    def render_node(self, node: Node, with_ids: bool = True) -> str:
        """Render a node (and descendants) as an addressable block."""
        lines = []
        for n in node.walk():
            tag = f"[{n.id}] " if with_ids else ""
            if n.kind == "section":
                lines.append(f"{tag}{'#' * n.level} {n.text}")
            elif n.kind == "item":
                lines.append(f"{tag}{'- ' if n.style == 'bullet' else ''}{n.text}")
        return "\n".join(lines)

    def skeleton(self, summary_words: int = 8, max_level: int = 2) -> str:
        """Compact outline: top-level section IDs, titles, item counts and a short gist.

        Kept byte-stable within a session so it can sit in the cached prefix.
        """
        lines = [f"# {self.root.text}"]
        for n in self.root.walk():
            if n.kind != "section" or n.level > max_level:
                continue
            items = [c for c in n.walk() if c.kind == "item"]
            subs = sum(1 for c in n.children if c.kind == "section")
            gist = ""
            if items:
                words = items[0].text.split()
                gist = " — " + " ".join(words[:summary_words]) + ("…" if len(words) > summary_words else "")
            indent = "  " * (n.level - 2)
            shape = f"{subs} subsections, {len(items)} items" if subs else f"{len(items)} items"
            lines.append(f"{indent}[{n.id}] {n.text} ({shape}){gist}")
        return "\n".join(lines)

    # ---- editing & versioning -----------------------------------------
    def set_text(self, node_id: str, new: str, origin: str = "llm") -> bool:
        n = self.nodes[node_id]
        if n.text == new:
            return False
        n.history.append(n.text)
        self.log.append({"seq": len(self.log), "id": node_id, "old": n.text, "new": new, "origin": origin})
        n.text = new
        return True

    def insert_after(self, node_id: str, text: str, origin: str = "llm") -> str:
        """Insert a new item after an item (same style), or as the first item of a section. Returns its ID."""
        anchor = self.nodes[node_id]
        if anchor.kind == "item":
            parent, style, pos = anchor.parent, anchor.style, None
        else:
            parent, pos = anchor, 0
            first = next((c for c in anchor.children if c.kind == "item"), None)
            style = first.style if first else "bullet"
        assert parent is not None
        if pos is None:
            pos = parent.children.index(anchor) + 1
        new_id = f"{node_id}+{len(self.log)}"  # fresh, never reused; re-parse renumbers
        node = Node(new_id, "item", text, style=style, parent=parent)
        parent.children.insert(pos, node)
        self.nodes[new_id] = node
        self.log.append({"seq": len(self.log), "id": new_id, "old": None, "new": text, "origin": origin})
        return new_id

    def delete(self, node_id: str, origin: str = "llm") -> bool:
        """Remove a node (and its subtree); the event log keeps the old text."""
        node = self.nodes.get(node_id)
        if node is None or node.parent is None:
            return False
        node.parent.children.remove(node)
        for n in list(node.walk()):
            self.nodes.pop(n.id, None)
        self.log.append({"seq": len(self.log), "id": node_id, "old": node.text, "new": None, "origin": origin})
        return True

    def revert(self, node_id: str) -> bool:
        n = self.nodes[node_id]
        if not n.history:
            return False
        old = n.history.pop()
        self.log.append({"seq": len(self.log), "id": node_id, "old": n.text, "new": old, "origin": "revert"})
        n.text = old
        return True

    def snapshot(self) -> dict[str, str]:
        return {nid: n.text for nid, n in self.nodes.items()}

    # ---- locating -----------------------------------------------------
    def locate(self, quote: str) -> list[str]:
        """Find nodes containing a quoted snippet (case-insensitive)."""
        q = quote.lower()
        return [n.id for n in self.nodes.values() if n.kind != "doc" and q in n.text.lower()]

    def offset_fraction(self, node_id: str) -> float:
        """Position of a node in render order (0..1) — used to model cache invalidation."""
        order = [n.id for n in self.root.walk()]
        return order.index(node_id) / max(1, len(order) - 1)


def diff_ids(before: dict[str, str], after: dict[str, str]) -> set[str]:
    """IDs whose text changed, plus IDs added or removed."""
    keys = set(before) | set(after)
    return {k for k in keys if before.get(k) != after.get(k)}
