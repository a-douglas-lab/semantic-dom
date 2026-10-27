"""Synthetic, seeded test documents with planted relationships and gold edit cases.

Each generator returns (markdown, cases). Gold is expressed as quotes that the
case builder resolves to node IDs after parsing, so IDs never drift from the text.

Planted relationship kinds:
- literal:    the same fact/term appears in several nodes (catchable by literal edges)
- schema:     a summary depends on detail without sharing literal text (catchable by schema edges)
- paraphrase: the same fact restated in different words (NOT catchable in v1 — measures the gap)
- distractor: same literal value with a different meaning (must NOT change; tests precision/collateral)
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

from sdom.dom import Document

TECH = [
    "PostgreSQL",
    "Kafka",
    "Redis",
    "Terraform",
    "GraphQL",
    "gRPC",
    "Snowflake",
    "Airflow",
    "Elasticsearch",
    "RabbitMQ",
    "DynamoDB",
    "Spark",
    "Flink",
    "Vault",
    "Envoy",
    "Istio",
    "Prometheus",
    "Grafana",
    "Rust",
    "TypeScript",
    "React",
    "Django",
    "FastAPI",
    "Celery",
    "MongoDB",
    "Cassandra",
    "ClickHouse",
    "dbt",
    "Pulsar",
    "NATS",
    "Consul",
    "Nomad",
    "Pulumi",
    "Ansible",
    "Jenkins",
    "ArgoCD",
    "Temporal",
    "Kotlin",
    "Scala",
    "Haskell",
    "Erlang",
    "Elixir",
    "Svelte",
    "Vue",
    "Next.js",
    "Deno",
    "Bun",
    "Zig",
    "OCaml",
    "Neo4j",
    "InfluxDB",
    "TimescaleDB",
    "CockroachDB",
    "Vitess",
    "Trino",
    "Presto",
    "Iceberg",
    "Delta Lake",
    "Hudi",
    "Kinesis",
    "BigQuery",
    "Dataflow",
    "Beam",
    "Ray",
    "Dask",
    "Polars",
    "DuckDB",
    "SQLite",
    "Memcached",
]
AREAS = [
    "order storage",
    "event streaming",
    "session caching",
    "infrastructure provisioning",
    "public API",
    "service-to-service calls",
    "analytics warehouse",
    "batch orchestration",
    "search indexing",
    "task queues",
    "feature flags",
    "secrets management",
    "observability",
    "edge routing",
    "identity",
    "billing pipeline",
    "notification fan-out",
    "audit logging",
    "ML feature store",
    "mobile sync",
]
VERBS = [
    "reduces operational toil",
    "simplifies onboarding",
    "improves tail latency",
    "lowers cost per request",
    "increases deployment safety",
    "clarifies ownership boundaries",
    "removes a single point of failure",
    "shortens recovery time",
    "keeps compliance evidence in one place",
    "makes capacity planning predictable",
]
FILLER = [
    "The team reviewed the trade-offs in a series of design sessions and consulted the platform group.",
    "Existing tooling was evaluated against reliability, cost, operability and the skills already in the team.",
    "Several incidents over the previous quarters highlighted the limits of the current approach.",
    "Stakeholders from product, security and finance were asked to state their constraints up front.",
    "A small spike was run to validate the assumptions before committing to a direction.",
    "Migration risk was assessed per service, with rollback plans agreed for each stage.",
    "The decision favours boring, well-understood technology where the domain allows it.",
    "Documentation and runbooks will be updated as part of the definition of done.",
]


@dataclass
class Case:
    id: str
    doc: str
    kind: str  # local | literal-ripple | schema-ripple | paraphrase-ripple | rename | status
    instruction: str
    must: list[str]  # quotes -> nodes that must change
    allowed: list[str] = field(default_factory=list)  # quotes -> nodes that may change
    checks: list[tuple[str, str, bool]] = field(default_factory=list)  # (quote|"*", regex, should_match)
    no_change: list[str] = field(default_factory=list)  # quotes -> distractors that must stay identical


def _words(rng: random.Random, n: int) -> str:
    return " ".join(rng.choice(FILLER) for _ in range(n))


# ---------------------------------------------------------------- CV -----
COMPANIES = [
    "Northwind Traders",
    "Globex Systems",
    "Initech",
    "Umbrella Health",
    "Stark Logistics",
    "Wayne Analytics",
    "Hooli Cloud",
    "Vandelay Imports",
    "Cyberdyne Labs",
    "Soylent Foods",
    "Tyrell Robotics",
    "Oscorp Media",
    "Wonka Retail",
    "Gringotts Payments",
]
TITLES = [
    "Software Engineer",
    "Senior Software Engineer",
    "Lead Engineer",
    "Principal Engineer",
    "Engineering Manager",
    "Senior Engineering Manager",
]
BULLETS = [
    "Led migration of the {a} platform to {t}, cutting p95 latency by {n}%.",
    "Built a {t}-based {a} service handling {n}k requests per second at peak.",
    "Mentored {n} engineers, {m} of whom were promoted within eighteen months.",
    "Reduced cloud spend on {a} by {n}% through rightsizing and {t} adoption.",
    "Introduced on-call practices for {a} that lowered incident volume by {n}%.",
    "Designed the {a} roadmap with product and secured budget for {m} new hires.",
    "Delivered {a} on {t} {n} weeks ahead of the regulatory deadline.",
    "Ran a hiring loop of {n} candidates per quarter and redesigned the {a} interview.",
]


def gen_cv(size: str, seed: int = 1) -> tuple[str, list[Case]]:
    rng = random.Random(seed)
    n_roles = {"S": 4, "M": 10}[size]
    n_bullets = {"S": 4, "M": 6}[size]
    companies = rng.sample(COMPANIES, n_roles)
    techs = rng.sample(TECH, n_roles * n_bullets)
    start = 2026 - 3 * n_roles
    years = 2026 - start
    roles = []
    for i, co in enumerate(companies):
        s, e = start + 3 * i, start + 3 * (i + 1)
        title = TITLES[min(len(TITLES) - 1, i * len(TITLES) // n_roles)]
        roles.append((title, co, s, "Present" if i == n_roles - 1 else str(e)))
    cur_title, cur_co = roles[-1][0], roles[-1][1]
    used_nums: set[int] = set()

    def num():
        while True:
            v = rng.randint(11, 89)
            if v not in used_nums and str(v) not in str(start):
                used_nums.add(v)
                return v

    md = [
        "# Alex Morgan — Curriculum Vitae",
        "",
        "## Summary",
        "",
        f"Engineering leader with {years} years of experience building distributed systems, currently "
        f"{cur_title} at {cur_co}.",
        "",
        "Known for pragmatic architecture, calm incident leadership and growing teams that ship.",
        "",
        "## Experience",
        "",
    ]
    bullets_by_role = []
    for ri, (title, co, s, e) in enumerate(reversed(roles)):
        md += [f"### {title} — {co} ({s}–{e})", ""]
        bl = []
        for _ in range(n_bullets):
            b = (
                rng.choice(BULLETS).format(a=rng.choice(AREAS), t=techs.pop(), n=num(), m=rng.randint(2, 9))
                + " "
                + _words(rng, 2)
            )
            bl.append(b)
        if ri == 1:  # cross-company mention for the rename case
            bl.append(f"Partnered with {roles[1][1]} on a joint {rng.choice(AREAS)} integration.")
        md += [f"- {b}" for b in bl] + [""]
        bullets_by_role.append(bl)
    platforms = ", ".join(rng.sample(["AWS", "GCP", "Azure", "Docker", "Linux"], 3))
    md += [
        "## Skills",
        "",
        "- Languages: Python, Go, TypeScript, SQL",
        f"- Platforms: {platforms}",
        "- Practices: incident command, architecture reviews, hiring",
        "",
    ]
    md += ["## Education", "", "- BSc Computer Science, University of Leeds", ""]
    if size == "M":
        md += ["## Selected Projects", ""]
        for _ in range(12):
            md += [
                f"- {rng.choice(BULLETS).format(a=rng.choice(AREAS), t=rng.choice(TECH), n=num(), m=3)} "
                f"{_words(rng, 1)}"
            ]
        md += ["", "## Talks and Writing", ""]
        for _ in range(8):
            md += [f'- "{rng.choice(AREAS).title()} at scale" — {_words(rng, 2)}']
        md += [""]
    markdown = "\n".join(md)

    doc_id = f"cv-{size}"
    earliest = roles[0]
    reword = bullets_by_role[0][1]
    skill_b = bullets_by_role[1][0]
    rename_co = roles[1][1]
    remove_role = list(reversed(roles))[2]  # third most recent role (untouched by other cases)
    remove_b = bullets_by_role[2][1]
    cases = [
        Case(
            f"{doc_id}-reword",
            doc_id,
            "local",
            f'Rewrite the bullet "{reword[:45]}" to be more concise.',
            must=[reword[:45]],
        ),
        Case(
            f"{doc_id}-start-year",
            doc_id,
            "schema-ripple",
            f"I actually started at {earliest[1]} in {earliest[2] - 2}, not {earliest[2]}.",
            must=[f"{earliest[1]} ({earliest[2]}", "years of experience"],
            checks=[
                (f"{earliest[1]} (", str(earliest[2] - 2), True),
                ("years of experience", f"{years + 2} years", True),
            ],
        ),
        Case(
            f"{doc_id}-title",
            doc_id,
            "literal-ripple",
            f'My current title should be "Director of Engineering", not "{cur_title}".',
            must=[f"{cur_title} — {cur_co}", "years of experience"],
            checks=[("*", f"{cur_title} at", False), ("years of experience", "Director of Engineering", True)],
        ),
        Case(
            f"{doc_id}-add-skill",
            doc_id,
            "schema-ripple",
            f'The work in "{skill_b[:40]}" also used Kubernetes; add it there and anywhere else the CV should reflect it.',
            must=[skill_b[:40], "Platforms:"],
            allowed=["Engineering leader with"],
            checks=[("Platforms:", "Kubernetes", True)],
        ),
        Case(
            f"{doc_id}-rename",
            doc_id,
            "rename",
            f"{rename_co} has rebranded as Meridian Group; update every mention.",
            must=[rename_co],
            checks=[("*", rename_co, False)],
        ),
        Case(
            f"{doc_id}-add-item",
            doc_id,
            "add-item",
            f'Add a bullet to the "{cur_title} — {cur_co}" role: "Introduced blameless postmortems across six teams."',
            must=[],
            allowed=[f"@sec:{cur_title} — {cur_co}", "Engineering leader with"],
            checks=[("*", "blameless postmortems", True)],
        ),
        Case(
            f"{doc_id}-remove-item",
            doc_id,
            "remove-item",
            f'Remove the bullet "{remove_b[:45]}".',
            must=[remove_b[:45]],
            allowed=[f"@sec:{remove_role[0]} — {remove_role[1]}"],
            checks=[("*", re.escape(remove_b[:45]), False)],
        ),
    ]
    return markdown, cases


# --------------------------------------------------------------- ADR -----
def gen_adr(size: str, seed: int = 2) -> tuple[str, list[Case]]:
    rng = random.Random(seed)
    n = {"S": 4, "M": 30, "L": 190}[size]
    techs = rng.sample(TECH, min(n, len(TECH)))
    while len(techs) < n:
        techs.append(f"{rng.choice(TECH)} v{len(techs)}")
    adrs = []
    for k in range(1, n + 1):
        area = rng.choice(AREAS)
        adrs.append({"k": k, "tech": techs[k - 1], "title": f"Use {techs[k - 1]} for {area}", "status": "Accepted"})
    md = ["# Architecture Decision Records", "", "## ADR Log", ""]
    md += [f"- ADR-{a['k']:03d}: {a['title']} — {a['status']}" for a in adrs] + [""]
    for a in adrs:
        k, tech = a["k"], a["tech"]
        related = rng.sample([x for x in range(1, n + 1) if x != k], min(2, n - 1))
        md += [f"## ADR-{k:03d}: {a['title']}", "", "### Status", "", a["status"], "", "### Context", ""]
        md += [_words(rng, 4), "", _words(rng, 4), "", _words(rng, 3), ""]
        md += ["### Decision", "", f"We will use {tech} for {a['title'].split(' for ')[1]}. {_words(rng, 3)}", ""]
        md += ["### Consequences", ""]
        md += [
            f"- {tech} {v}; {f.lower()}" for v, f in zip(rng.sample(VERBS, 4), rng.sample(FILLER, 4), strict=False)
        ] + [""]
        md += ["### Related", ""] + [f"- ADR-{r:03d}: {rng.choice(VERBS)}" for r in related] + [""]
    markdown = "\n".join(md)

    doc_id = f"adr-{size}"
    a, b = adrs[n // 2], adrs[-1]
    c = adrs[n // 3] if n > 3 else adrs[0]
    d = adrs[(2 * n) // 3] if n > 3 else adrs[1]
    cons_line = next(ln for ln in md if ln.startswith(f"- {a['tech']} "))[2:]
    e = adrs[0]  # ADR-001: untouched by the other cases
    remove_line = next(ln for ln in md if ln.startswith(f"- {e['tech']} "))[2:]
    cases = [
        Case(
            f"{doc_id}-reword",
            doc_id,
            "local",
            f'Reword the consequence "{cons_line}" to be clearer.',
            must=[cons_line],
        ),
        Case(
            f"{doc_id}-supersede",
            doc_id,
            "status",
            f"ADR-{b['k']:03d} now supersedes ADR-{a['k']:03d}; update the records.",
            must=[f"ADR-{a['k']:03d}: {a['title']} — Accepted", f"@status:{a['k']}"],
            allowed=[f"@status:{b['k']}", f"@related:{b['k']}", f"@related:{a['k']}", f"@decision:{a['k']}"],
            checks=[
                (f"@status:{a['k']}", f"Superseded by ADR-{b['k']:03d}", True),
                (f"ADR-{a['k']:03d}: {a['title']} —", "Superseded", True),
            ],
        ),
        Case(
            f"{doc_id}-deprecate",
            doc_id,
            "status",
            f"Mark ADR-{c['k']:03d} as Deprecated.",
            must=[f"ADR-{c['k']:03d}: {c['title']} — Accepted", f"@status:{c['k']}"],
            allowed=[f"@related:{c['k']}"],
            checks=[
                (f"@status:{c['k']}", "Deprecated", True),
                (f"ADR-{c['k']:03d}: {c['title']} —", "Deprecated", True),
            ],
        ),
        Case(
            f"{doc_id}-switch-tech",
            doc_id,
            "literal-ripple",
            f"In ADR-{d['k']:03d} we are switching from {d['tech']} to Memgraph; update that ADR and the log.",
            must=[f"@all:{d['tech']}"],
            checks=[("*", rf"\b{re.escape(d['tech'])}\b", False)],
        ),
        Case(
            f"{doc_id}-add-item",
            doc_id,
            "add-item",
            f'Add a consequence to ADR-{e["k"]:03d}: "Requires a quarterly cost review."',
            must=[],
            allowed=[f"@consequences:{e['k']}"],
            checks=[("*", "quarterly cost review", True)],
        ),
        Case(
            f"{doc_id}-remove-item",
            doc_id,
            "remove-item",
            f'Remove the consequence "{remove_line}" from ADR-{e["k"]:03d}.',
            must=[remove_line],
            allowed=[f"@consequences:{e['k']}"],
            checks=[("*", re.escape(remove_line), False)],
        ),
    ]
    return markdown, cases


# ---------------------------------------------------------- contract -----
CLAUSES = [
    "Confidentiality",
    "Data Protection",
    "Intellectual Property",
    "Warranties",
    "Insurance",
    "Force Majeure",
    "Assignment",
    "Subcontracting",
    "Audit",
    "Notices",
    "Dispute Resolution",
    "Governing Law",
    "Anti-Bribery",
    "Non-Solicitation",
    "Publicity",
    "Variation",
    "Entire Agreement",
]
CLAUSE_SENT = [
    "The {p} shall {v} in accordance with Good Industry Practice and the requirements of this Agreement.",
    "Each party shall bear its own costs in relation to {o}, save as expressly provided in this Agreement.",
    "The {p} shall maintain complete and accurate records relating to {o} for not less than {n} months.",
    "Nothing in this clause shall limit the {p}'s obligations in respect of {o}.",
    "The {p} shall notify the other party within {n} Business Days of becoming aware of any breach of {o}.",
    "Any amendment to {o} shall be agreed in writing and signed by an authorised signatory of each party.",
]
OBJ = [
    "the Services",
    "Customer Data",
    "the Deliverables",
    "the Personnel",
    "third-party software",
    "the Service Levels",
    "the security policy",
    "the exit plan",
    "the disaster recovery plan",
    "the Documentation",
]


def gen_contract(size: str, seed: int = 3) -> tuple[str, list[Case]]:
    rng = random.Random(seed)
    n_filler = {"S": 6, "M": 45, "L": 220}[size]
    fee, fee2 = 18500, 21000

    def party():
        return rng.choice(["Supplier", "Customer"])

    def filler_items(k: int, count: int) -> list[str]:
        return [
            f"{k}.{j} "
            + rng.choice(CLAUSE_SENT).format(
                p=party(),
                v=rng.choice(["perform its obligations", "provide the Services", "cooperate"]),
                o=rng.choice(OBJ),
                n=rng.choice([14, 21, 45, 120, 180]),
            )
            for j in range(1, count + 1)
        ]

    md = [
        "# Master Services Agreement",
        "",
        "This Agreement is made between Acme Retail Ltd (the Customer) and Brightline Services Ltd (the Supplier).",
        "",
        "## 1. Definitions",
        "",
        '"Supplier" means Brightline Services Ltd and its permitted successors.',
        "",
        '"Customer" means Acme Retail Ltd.',
        "",
        f'"Service Fee" means the monthly fee of £{fee:,} set out in Schedule 1.',
        "",
        '"Business Day" means a day other than a Saturday, Sunday or public holiday in England.',
        "",
        "## 2. Services",
        "",
    ]
    md += [x + "\n" for x in filler_items(2, 3)]
    md += [
        "## 3. Payment",
        "",
        f"3.1 The Customer shall pay the Service Fee of £{fee:,} per month within thirty (30) days of invoice.",
        "",
        "3.2 Invoices disputed in good faith shall be resolved within 90 days of the date of dispute.",
        "",
        "## 4. Service Credits",
        "",
        "4.1 If Availability falls below 99.9% in any month, the Supplier shall credit 5% of the monthly Service Fee.",
        "",
        "## 5. Termination",
        "",
        "5.1 Either party may terminate this Agreement for convenience on ninety (90) days written notice.",
        "",
        "5.2 Either party may terminate immediately on written notice if the other commits a material breach.",
        "",
    ]
    k = 6
    for i in range(n_filler):
        name = CLAUSES[i % len(CLAUSES)] + ("" if i < len(CLAUSES) else f" (Part {i // len(CLAUSES) + 1})")
        md += [f"## {k}. {name}", ""] + [x + " " + _words(rng, 2) + "\n" for x in filler_items(k, rng.randint(4, 7))]
        k += 1
    md += [
        "## Schedule 1 — Fees",
        "",
        f"- Monthly Service Fee: £{fee:,}",
        "- Fees are exclusive of VAT.",
        "",
        "## Schedule 2 — Service Levels",
        "",
        "- Availability target: 99.9% per calendar month.",
        "- Severity 1 response: 30 minutes.",
        "",
        "## Schedule 3 — Key Terms Summary",
        "",
        "- Termination for convenience: three months notice by either party.",
        "- Liability cap: 150% of fees paid in the preceding twelve months.",
        "",
    ]
    markdown = "\n".join(md)

    doc_id = f"contract-{size}"
    cases = [
        Case(
            f"{doc_id}-reword",
            doc_id,
            "local",
            'Rewrite clause 5.2 ("Either party may terminate immediately") in plainer English.',
            must=["Either party may terminate immediately"],
        ),
        Case(
            f"{doc_id}-notice",
            doc_id,
            "paraphrase-ripple",
            "Change the termination for convenience notice period from 90 days to 60 days.",
            must=["for convenience on ninety", "Termination for convenience:"],
            checks=[
                ("for convenience on", "60", True),
                ("Termination for convenience:", r"(60|sixty|two months)", True),
            ],
            no_change=["Invoices disputed in good faith"],
        ),
        Case(
            f"{doc_id}-fee",
            doc_id,
            "literal-ripple",
            f"Increase the Service Fee from £{fee:,} to £{fee2:,} per month.",
            must=['"Service Fee" means', "3.1 The Customer shall pay", "Monthly Service Fee:"],
            checks=[("*", f"£{fee:,}", False), ("Monthly Service Fee:", f"£{fee2:,}", True)],
        ),
        Case(
            f"{doc_id}-sla",
            doc_id,
            "literal-ripple",
            "Raise the availability target from 99.9% to 99.95%.",
            must=["Availability target:", "If Availability falls below"],
            checks=[("*", r"99\.9%", False)],
        ),
        Case(
            f"{doc_id}-rename-term",
            doc_id,
            "rename",
            'Rename the defined term "Supplier" to "Provider" throughout.',
            must=["@all:Supplier"],
            checks=[("*", r"\bSupplier\b", False)],
        ),
        Case(
            f"{doc_id}-add-item",
            doc_id,
            "add-item",
            'Add a clause to section "5. Termination": "Either party may terminate immediately if the other becomes insolvent."',
            must=[],
            allowed=["@sec:5. Termination"],
            checks=[("*", "insolvent", True)],
        ),
        Case(
            f"{doc_id}-remove-item",
            doc_id,
            "remove-item",
            'Delete clause 3.2 ("Invoices disputed in good faith").',
            must=["Invoices disputed in good faith"],
            allowed=["@sec:3. Payment"],
            checks=[("*", "disputed in good faith", False)],
        ),
    ]
    return markdown, cases


GENERATORS = {
    "cv": (gen_cv, ["S", "M"]),
    "adr": (gen_adr, ["S", "M", "L"]),
    "contract": (gen_contract, ["S", "M", "L"]),
}


# ---------------------------------------------------- gold resolution -----
def resolve(doc: Document, quote: str) -> list[str]:
    """Resolve a gold quote to node IDs. Special forms: @all:<text>, @status:<k>, @related:<k>, @decision:<k>."""
    if quote.startswith("@all:"):  # lookarounds, not \b: terms may end in punctuation, e.g. "(Confidentiality)"
        rx = re.compile(r"(?<!\w)" + re.escape(quote[5:]) + r"(?!\w)")
        return [n.id for n in doc.nodes.values() if n.kind != "doc" and rx.search(n.text)]
    if quote.startswith("@allin:"):  # nodes under a section containing a term: "@allin:<section quote>|<term>"
        sec_q, term = quote[7:].split("|")
        sec = next(n for n in doc.nodes.values() if n.kind == "section" and sec_q in n.text)
        rx = re.compile(r"\b" + re.escape(term) + r"\b")
        return [n.id for n in sec.walk() if rx.search(n.text)]
    if quote.startswith("@sub:"):  # items of a named subsection under a section: "@sub:<section quote>|<title>"
        sec_q, sub = quote[5:].split("|")
        for n in doc.nodes.values():
            if n.kind == "section" and sec_q in n.text:
                s = next((c for c in n.children if c.kind == "section" and c.text == sub), None)
                if s is not None:
                    return [c.id for c in s.children]
        raise ValueError(f"gold subsection not found: {quote!r}")
    if quote.startswith("@sec:"):  # a whole section: changes anywhere under it are allowed
        return [n.id for n in doc.nodes.values() if n.kind == "section" and quote[5:] in n.text][:1]
    if quote.startswith("@"):
        kind, k = quote[1:].split(":")
        sub = {"status": "Status", "related": "Related", "decision": "Decision", "consequences": "Consequences"}[kind]
        for n in doc.nodes.values():
            if n.kind == "section" and n.text.startswith(f"ADR-{int(k):03d}:"):
                sec = next(c for c in n.children if c.kind == "section" and c.text == sub)
                # list sections: include the section itself so bullets the model adds there count as allowed
                return ([sec.id] if kind in ("related", "consequences") else []) + [c.id for c in sec.children]
        return []
    hits = doc.locate(quote)
    if not hits:
        raise ValueError(f"gold quote not found: {quote!r}")
    return hits


def resolve_case(doc: Document, case: Case) -> dict:
    must = sorted({i for q in case.must for i in resolve(doc, q)})
    allowed = sorted({i for q in case.allowed for i in resolve(doc, q)})
    no_change = sorted({i for q in case.no_change for i in resolve(doc, q)})
    checks = []
    for q, rx, want in case.checks:
        ids = ["*"] if q == "*" else resolve(doc, q)
        checks += [(i, rx, want) for i in ids]
    return {"must": must, "allowed": allowed, "no_change": no_change, "checks": checks}
