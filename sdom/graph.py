"""Dependency edges and impact analysis over a semantic DOM.

Edge types (cheapest / most reliable first):
- structural: parent/child (implicit in the tree)
- schema:     per doc-type rules, e.g. a CV Summary depends on Experience
- literal:    nodes sharing a fact — number, year, money, ADR id, defined term, heading phrase
Semantic (embedding) edges are deliberately absent in v1; see backlog.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from .dom import Document, Node, est_tokens

NUM = re.compile(r"(?<![\w.])[£$€]?\d[\d,]*(?:\.\d+)?%?")
ADR = re.compile(r"\bADR-\d+\b")
QUOTED = re.compile(r"[\"“]([^\"”]{3,})[\"”]")
DEFINED = re.compile(r"^[\"“]([^\"”]+)[\"”]\s+means\b")

# (source section title regex, dependent section title regex)
SCHEMAS: dict[str, list[tuple[str, str]]] = {
    "cv": [
        (r"^Experience$", r"(?i)^((executive|professional|personal) )?(summary|profile)$"),
        (r"^Experience$", r"^Skills$"),
    ],
    "adr": [(r"^ADR-\d+", r"^ADR Log$")],
    "contract": [(r"Service Levels", r"Service Credits"), (r"Service Credits", r"Service Levels")],
    "paper": [(r"^Results", r"^(Abstract|Conclusion|Discussion)$")],
}


def _norm_num(tok: str) -> str | None:
    core = tok.strip("£$€%").replace(",", "")
    if len(core.split(".")[0]) < 2:  # skip single digits: too noisy
        return None
    return "n:" + core


_ONES = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
]
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
_WORD_VALUES = {w: i for i, w in enumerate(_ONES)} | _TENS
_NUMBER = r"\d+|(?:" + "|".join(_TENS) + r")(?:-(?:" + "|".join(_ONES[1:10]) + r"))?|" + "|".join(_ONES)
DURATION = re.compile(
    rf"\b(?P<num>{_NUMBER})(?:\s*\((?P<paren>\d+)\))?\s+(?P<unit>day|week|month|year)s?\b", re.IGNORECASE
)
_UNIT_DAYS = {"day": 1, "week": 7, "month": 30, "year": 365}


def _word_to_int(word: str) -> int:
    if word.isdigit():
        return int(word)
    total = 0
    for part in word.lower().split("-"):
        total += _WORD_VALUES[part]
    return total


def durations(text: str) -> set[str]:
    """Normalise stated durations to days: "ninety (90) days", "90 days", "three months" -> dur:90."""
    out = set()
    for m in DURATION.finditer(text):
        n = int(m.group("paren")) if m.group("paren") else _word_to_int(m.group("num"))
        out.add(f"dur:{n * _UNIT_DAYS[m.group('unit').lower()]}")
    return out


QUANTITY = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(×|x|%|PB|TB|GB|MB|bn|k|K|M)(?![A-Za-z])")
BACKTICK = re.compile(r"`([^`\s][^`]*)`")
FILE_TOKEN = re.compile(r"(?<![\w./-])[\w@][\w./-]*\.(?:ya?ml|json|md|tsx?|jsx?|py|cs|toml|xml|txt|sh|tf)\b")
PROPER = re.compile(r"\b[A-Z][A-Za-z0-9]*[a-z0-9][A-Za-z0-9]*(?:[.-][A-Za-z0-9]+)*\b")
STOPWORDS = set(
    [
        "The",
        "This",
        "That",
        "These",
        "Those",
        "We",
        "Our",
        "Us",
        "It",
        "Its",
        "In",
        "On",
        "At",
        "For",
        "From",
        "To",
        "With",
        "And",
        "Or",
        "But",
        "If",
        "When",
        "Then",
        "A",
        "An",
        "I",
        "My",
        "Me",
        "Add",
        "Remove",
        "Delete",
        "Rewrite",
        "Reword",
        "Mark",
        "Change",
        "Correct",
        "Fix",
        "Replace",
        "Update",
        "Rename",
        "Make",
        "Move",
        "Use",
        "Set",
        "Keep",
        "ADR",
        "Note",
        "Code",
    ]
)


def quantities(text: str) -> set[str]:
    """Numbers with units/multipliers, any digit count: "3×", "3x", "1.4PB", "40%" -> q:3×, q:1.4pb, q:40%."""
    out = set()
    for num, unit in QUANTITY.findall(text):
        out.add(f"q:{num}{'×' if unit in ('x', '×') else unit.lower()}")
    return out


def code_tokens(text: str) -> set[str]:
    """Backticked text and file-name-shaped tokens: `node-fetch`, catalog-info.yaml -> c:<token>."""
    out = {"c:" + t.strip() for t in BACKTICK.findall(text)}
    out.update("c:" + t for t in FILE_TOKEN.findall(text))
    return out


def heading_terms(title: str) -> list[str]:
    parts = re.split(r"\s[—–|:]\s|[():,]", title)
    return [p.strip() for p in parts if len(p.strip()) >= 4 and re.search(r"[A-Z]", p) and not p.strip().isdigit()]


@dataclass
class Impact:
    targets: list[str]
    dependents: list[str]
    reasons: dict[str, list[str]]  # node id -> why it was included

    @property
    def all(self) -> list[str]:
        return self.targets + [d for d in self.dependents if d not in self.targets]


class Matcher(Protocol):
    """Pluggable retriever (spec 008): BM25, embeddings, … fitted over a document's nodes."""

    name: str

    def locate(self, query: str) -> list[str]:
        """Best-matching node IDs for an instruction (target location)."""
        ...

    def related(self, query: str) -> list[tuple[str, float]]:
        """Nodes related to a query (instruction + target text), already thresholded, best first."""
        ...


class SemanticGraph:
    def __init__(
        self,
        doc: Document,
        max_fact_df: float = 0.08,
        dep_budget_tokens: int = 4000,
        edges: frozenset[str] = frozenset({"structural", "schema", "literal"}),
        use_facts: bool = True,
        matchers: Sequence[Matcher] = (),
    ):
        """`edges` selects edge types (ablations); `use_facts` toggles regex-fact matching and
        `matchers` adds retrievers, so matching methods can be compared with the rest held constant."""
        self.doc = doc
        self.edges = edges
        self.use_facts = use_facts
        self.matchers = list(matchers)
        self.max_fact_df = max_fact_df
        self.dep_budget = dep_budget_tokens
        self.build()

    # ---- scan ---------------------------------------------------------
    def build(self) -> None:
        nodes = [n for n in self.doc.nodes.values() if n.kind != "doc"]
        self.glossary: set[str] = set()
        for n in nodes:
            if n.kind == "section":
                self.glossary.update(heading_terms(n.text))
            elif m := DEFINED.match(n.text):
                self.glossary.add(m.group(1))
        self._gloss_re = {t: re.compile(r"\b" + re.escape(t) + r"\b") for t in self.glossary}
        self.facts: dict[str, set[str]] = {n.id: self.extract(n.text) for n in nodes}
        self.index: dict[str, set[str]] = defaultdict(set)
        for nid, fs in self.facts.items():
            for f in fs:
                self.index[f].add(nid)
        self.n_nodes = max(1, len(nodes))

    def extract(self, text: str) -> set[str]:
        out: set[str] = set()
        for tok in NUM.findall(text):
            if f := _norm_num(tok):
                out.add(f)
        out.update("ref:" + a for a in ADR.findall(text))
        out |= durations(text)
        out |= quantities(text)
        out |= code_tokens(text)
        out.update("t:" + t for t, rx in self._gloss_re.items() if rx.search(text))
        return out

    def instruction_facts(self, instruction: str) -> set[str]:
        """Facts named in an instruction: extracted facts plus selective proper nouns found in the doc."""
        out = self.extract(instruction)
        limit = max(3, self.max_fact_df * self.n_nodes)
        for term in set(PROPER.findall(instruction)) - STOPWORDS:
            key = "p:" + term
            if key not in self.index:
                rx = re.compile(r"\b" + re.escape(term) + r"\b")
                self.index[key] = {n.id for n in self.doc.nodes.values() if n.kind != "doc" and rx.search(n.text)}
            if 0 < len(self.index[key]) <= limit:
                out.add(key)
        return out

    def is_selective(self, fact: str) -> bool:
        return len(self.index.get(fact, ())) / self.n_nodes <= self.max_fact_df

    # ---- locate -------------------------------------------------------
    def locate_targets(self, instruction: str) -> list[str]:
        for q in QUOTED.findall(instruction):
            hits = self.doc.locate(q)
            if hits:
                return hits
        if self.use_facts:
            scores: dict[str, int] = defaultdict(int)
            for f in self.instruction_facts(instruction):
                for nid in self.index.get(f, ()):
                    scores[nid] += 1
            if scores:
                best = max(scores.values())
                hits = [nid for nid, s in scores.items() if s == best]
                hits.sort(key=lambda i: self.doc.nodes[i].kind != "section")  # headings first
                return hits[:20]
        for m in self.matchers:
            if hits := m.locate(instruction):
                return hits
        return []

    # ---- impact -------------------------------------------------------
    def impact(self, instruction: str, targets: list[str] | None = None) -> Impact:
        targets = targets or self.locate_targets(instruction)
        reasons: dict[str, list[str]] = defaultdict(list)
        # facts the user named explicitly are always followed; target facts only if selective
        seed = set(self.instruction_facts(instruction))
        for t in targets:
            seed |= {f for f in self.facts.get(t, ()) if self.is_selective(f)}
        for f in seed if "literal" in self.edges and self.use_facts else ():
            for nid in self.index.get(f, ()):
                if nid not in targets:
                    reasons[nid].append(f"literal:{f}")
        # retrievers: relate nodes to the instruction plus what the targets say
        query = " ".join([instruction] + [self.doc.nodes[t].text[:500] for t in targets])
        for m in self.matchers:
            for nid, s in m.related(query):
                if nid not in targets:
                    reasons[nid].append(f"{m.name}:{s:.2f}")
        # structural: a targeted section brings its own subtree
        for t in targets if "structural" in self.edges else ():
            if self.doc.nodes[t].kind == "section":
                for c in self.doc.nodes[t].walk():
                    if c.id not in targets:
                        reasons[c.id].append("structural:child-of-target")

        # schema edges
        rules = SCHEMAS.get(self.doc.doc_type, []) if "schema" in self.edges else []
        anchor_facts = set(seed)
        for t in targets:
            node = self.doc.nodes[t]
            p = node if node.kind == "section" else node.parent
            while p is not None and p.kind != "doc":
                anchor_facts |= {f for f in self.facts.get(p.id, ()) if self.is_selective(f)}
                p = p.parent
        for t in targets:
            titles = self.doc.nodes[t].path_titles() or [self.doc.nodes[t].text]
            for src, dep in rules:
                if not any(re.search(src, x) for x in titles):
                    continue
                for sec in self._sections(dep):
                    items = [c for c in sec.walk() if c.kind == "item"]
                    small = sum(est_tokens(c.text) for c in items) <= 250
                    for c in items:
                        if c.id in targets:
                            continue
                        if small or (self.facts[c.id] & anchor_facts):
                            reasons[c.id].append(f"schema:{src}->{dep}")

        # rank and apply budget: more reasons first, then document order
        order = {nid: i for i, nid in enumerate(self.doc.nodes)}
        ranked = sorted(reasons, key=lambda k: (-len(reasons[k]), order[k]))
        deps, spent = [], 0
        for nid in ranked:
            cost = est_tokens(self.doc.nodes[nid].text)
            if spent + cost > self.dep_budget:
                continue
            deps.append(nid)
            spent += cost
        return Impact(targets, deps, dict(reasons))

    def _sections(self, title_rx: str) -> list[Node]:
        return [n for n in self.doc.nodes.values() if n.kind == "section" and re.search(title_rx, n.text)]
