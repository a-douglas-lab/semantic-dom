"""Fresh held-out set (spec 008).

Authored 2026-10-16 BEFORE any retriever (BM25 / embeddings / hybrid) existed and before the
spec-007 rules were run on these documents. Never used for tuning; scored once params are frozen.
"""

from evalset.generators import Case

FRESH_DOCS = {  # corpus name -> (source file, doc type)
    "fresh-adr-moj": ("moj-adr.md", "adr"),
    "fresh-contract-commonpaper": ("commonpaper-csa.md", "contract"),
    "fresh-cv-rendercv": ("cv-rendercv.md", "cv"),
}

FRESH_CASES: dict[str, list[Case]] = {
    "fresh-adr-moj": [
        Case(
            "fresh-adr-moj-reword",
            "fresh-adr-moj",
            "local",
            'In "Use Concourse CI", reword "Replace self hosted Jenkins with self hosted Concourse CI pipeline" as a full sentence.',
            must=["Replace self hosted Jenkins with self hosted Concourse CI pipeline"],
        ),
        Case(
            "fresh-adr-moj-accept",
            "fresh-adr-moj",
            "status",
            'The "Shared Ingress Controllers for teams" ADR has now been accepted; update its status.',
            must=["@sub:Shared Ingress Controllers for teams|Status"],
            allowed=["@sec:Shared Ingress Controllers for teams"],
            checks=[("@sub:Shared Ingress Controllers for teams|Status", "(?i)accepted", True)],
        ),
        Case(
            "fresh-adr-moj-supersede",
            "fresh-adr-moj",
            "status",
            'ADR "26 Managed Prometheus" is superseded by a new ADR 60, Use Amazon Managed Grafana; update its status following the existing convention.',
            must=["@sub:26 Managed Prometheus|Status"],
            allowed=["@sec:26 Managed Prometheus"],
            checks=[("@sub:26 Managed Prometheus|Status", "(?i)superseded", True)],
        ),
        Case(
            "fresh-adr-moj-retitle",
            "fresh-adr-moj",
            "literal-ripple",
            'Rename ADR "36. Multi-cluster" to "36. Multi-cluster architecture"; update its title and every reference to it.',
            must=["36. Multi-cluster", "@sub:21. Multi-cluster|Status"],
            checks=[("@sub:21. Multi-cluster|Status", "Multi-cluster architecture", True)],
        ),
        Case(
            "fresh-adr-moj-concourse",
            "fresh-adr-moj",
            "literal-ripple",
            'We are replacing Concourse CI with GitHub Actions; update the "Use Concourse CI" decision record only (other records are historical).',
            must=["@allin:Use Concourse CI|Concourse"],
            allowed=["@sec:Use Concourse CI"],
            no_change=["is transitioning to Concourse CI", "self managed Concourse instance"],
            checks=[("@allin:Use Concourse CI|Concourse", "(?i)github actions", True)],
        ),
        Case(
            "fresh-adr-moj-remove",
            "fresh-adr-moj",
            "remove-item",
            'In "Use Concourse CI", remove the step "Spike into deploying Concourse CI into AWS or Kubernetes".',
            must=["Spike into deploying Concourse CI"],
            allowed=["@sec:Use Concourse CI"],
            checks=[("*", "Spike into deploying Concourse", False)],
        ),
    ],
    "fresh-contract-commonpaper": [
        Case(
            "fresh-contract-commonpaper-reword",
            "fresh-contract-commonpaper",
            "local",
            'Rewrite clause 1.2 ("Support") in plainer English.',
            must=["1.2 Support."],
        ),
        Case(
            "fresh-contract-commonpaper-xref",
            "fresh-contract-commonpaper",
            "literal-ripple",
            'Rename Section 10 "Confidentiality" to "Confidential Information"; update the heading and every cross-reference to it.',
            must=["10. Confidentiality", "@all:Section 10 (Confidentiality)"],
            checks=[("*", r"Section 10 \(Confidentiality\)", False)],
        ),
        Case(
            "fresh-contract-commonpaper-dispute",
            "fresh-contract-commonpaper",
            "paraphrase-ripple",
            "Extend the window to dispute an automatic payment from 30 days to 45 days.",
            must=["within 30 days of an automatic payment"],
            no_change=["undisputed balance on its account for more than 30 days", "following 30 days notice"],
            checks=[("4.4 Payment Dispute.", "45 days", True)],
        ),
        Case(
            "fresh-contract-commonpaper-rename",
            "fresh-contract-commonpaper",
            "rename",
            'Rename the defined term "Beta Product" to "Preview Feature" throughout.',
            must=["@all:Beta Product"],
            checks=[("*", "Beta Product", False)],
        ),
        Case(
            "fresh-contract-commonpaper-remove",
            "fresh-contract-commonpaper",
            "remove-item",
            'Delete sub-clause 2.1(b) ("Use of the Product must comply with all Documentation").',
            must=["Use of the Product must comply with all Documentation"],
            allowed=["@sec:2. Restrictions"],
            checks=[("*", "must comply with all Documentation", False)],
        ),
        Case(
            "fresh-contract-commonpaper-add",
            "fresh-contract-commonpaper",
            "add-item",
            'Add a clause to section "4. Payment & Taxes": "4.5 Late Payment. Overdue undisputed Fees accrue interest at 1% per month."',
            must=[],
            allowed=["@sec:4. Payment & Taxes"],
            checks=[("*", "accrue interest", True)],
        ),
    ],
    "fresh-cv-rendercv": [
        Case(
            "fresh-cv-rendercv-reword",
            "fresh-cv-rendercv",
            "local",
            'Make the bullet "Implemented novel self-supervised learning framework" more concise.',
            must=["Implemented novel self-supervised learning framework"],
        ),
        Case(
            "fresh-cv-rendercv-fulbright",
            "fresh-cv-rendercv",
            "literal-ripple",
            "The Fulbright Scholarship was awarded in 2017, not 2018.",
            must=["Fulbright Scholarship for Graduate Studies (2018)"],
            allowed=["Fulbright Scholarship recipient"],
            no_change=["BS — Boğaziçi University (2014-09–2018-06)"],
            checks=[("Fulbright Scholarship for Graduate Studies", "2017", True)],
        ),
        Case(
            "fresh-cv-rendercv-rename",
            "fresh-cv-rendercv",
            "rename",
            "Nexus AI has rebranded as Nexus Labs; update every mention.",
            must=["@all:Nexus AI"],
            checks=[("*", "Nexus AI", False)],
        ),
        Case(
            "fresh-cv-rendercv-skill",
            "fresh-cv-rendercv",
            "schema-ripple",
            'The work in "Developed proprietary inference optimization" also used Mojo; add it there and anywhere else the CV should reflect it.',
            must=["Developed proprietary inference optimization", "Languages: Python"],
            checks=[("Languages: Python", "Mojo", True)],
        ),
        Case(
            "fresh-cv-rendercv-series-a",
            "fresh-cv-rendercv",
            "literal-ripple",
            "The Series A was $20M, not $18M.",
            must=["Raised $18M Series A"],
            checks=[("*", r"\$18M", False)],
        ),
        Case(
            "fresh-cv-rendercv-remove",
            "fresh-cv-rendercv",
            "remove-item",
            'Remove the patent "Hardware-Aware Neural Architecture Search Method".',
            must=["Hardware-Aware Neural Architecture Search Method"],
            allowed=["@sec:Patents"],
            checks=[("*", "Hardware-Aware Neural Architecture Search Method", False)],
        ),
    ],
}
