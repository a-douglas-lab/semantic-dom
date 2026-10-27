"""Held-out edit cases on real documents (spec 006).

Authored 2026-10-16 from the converted documents BEFORE running any harness code on them
(pre-registered: impact rules must not be tuned on these). Gold forms as in evalset.generators, plus
@sub:<section quote>|<subsection title> -> the items of that subsection.
"""

from evalset.generators import Case

REAL_DOCS = {  # corpus name -> (source file, doc type)
    "real-cv-jsonresume": ("cv-jsonresume.md", "cv"),
    "real-adr-backstage": ("backstage-adr.md", "adr"),
    "real-adr-govuk": ("govuk-adr.md", "adr"),
}

CASES: dict[str, list[Case]] = {
    "real-cv-jsonresume": [
        Case(
            "real-cv-jsonresume-reword",
            "real-cv-jsonresume",
            "local",
            'Fix the grammar in the bullet "Build an algorithm for artist to detect".',
            must=["Build an algorithm for artist"],
        ),
        Case(
            "real-cv-jsonresume-end-year",
            "real-cv-jsonresume",
            "literal-ripple",
            "Richard actually left Pied Piper in 2016, not 2014.",
            must=["CEO/President — Pied Piper"],
            no_change=["University of Oklahoma (2011"],
            checks=[("CEO/President — Pied Piper", "2016", True)],
        ),
        Case(
            "real-cv-jsonresume-rename",
            "real-cv-jsonresume",
            "rename",
            "Pied Piper has rebranded as PiperNet; update every mention.",
            must=["@all:Pied Piper"],
            checks=[("*", "Pied Piper", False)],
        ),
        Case(
            "real-cv-jsonresume-add",
            "real-cv-jsonresume",
            "add-item",
            'Add a highlight to the CEO/President role: "Raised a Series A round."',
            must=[],
            allowed=["@sec:CEO/President — Pied Piper"],
            checks=[("*", "Series A", True)],
        ),
        Case(
            "real-cv-jsonresume-remove",
            "real-cv-jsonresume",
            "remove-item",
            "Remove the 'Teacher of the Month' award bullet from the volunteering section.",
            must=["Awarded 'Teacher of the Month'"],
            allowed=["@sec:Teacher — CoderDojo"],
            checks=[("*", "Teacher of the Month", False)],
        ),
    ],
    "real-adr-backstage": [
        Case(
            "real-adr-backstage-reword",
            "real-adr-backstage",
            "local",
            'In ADR007, reword the consequence "A little more code to write" to explain the trade-off.',
            must=["A little more code to write"],
        ),
        Case(
            "real-adr-backstage-supersede",
            "real-adr-backstage",
            "status",
            "ADR007 is now superseded by a new ADR016 (use Playwright route mocking); mark it as superseded following the existing convention.",
            must=["ADR007: Use MSW"],
            allowed=["@sec:ADR007: Use MSW"],
            checks=[("ADR007:", "(?i)superseded", True), ("*", "ADR016", True)],
        ),
        Case(
            "real-adr-backstage-filename",
            "real-adr-backstage",
            "literal-ripple",
            "The default catalog file name is now backstage.yaml instead of catalog-info.yaml.",
            must=["@all:catalog-info.yaml"],
            allowed=["@sec:ADR008: Default Catalog File Name"],
            checks=[("*", r"catalog-info\.yaml", False)],
        ),
        Case(
            "real-adr-backstage-luxon",
            "real-adr-backstage",
            "schema-ripple",
            "We are replacing Luxon with date-fns as the standard date library; update the affected decisions.",
            must=["@all:Luxon"],
            allowed=["@sec:ADR010: Use the Luxon", "@sec:ADR012: Use Luxon"],
            checks=[("*", r"\bLuxon\b", False)],
        ),
        Case(
            "real-adr-backstage-remove",
            "real-adr-backstage",
            "remove-item",
            'Remove the ADR010 consequence "Using a single date library avoids having to learn multiple library APIs".',
            must=["Using a single date library avoids"],
            allowed=["@sub:ADR010: Use the Luxon|Consequences"],
            checks=[("*", "avoids having to learn", False)],
        ),
    ],
    "real-adr-govuk": [
        Case(
            "real-adr-govuk-reword",
            "real-adr-govuk",
            "local",
            'In ADR 38, reword the consequence "AWS DocumentDB supports multiple users but with the important caveat" to be clearer.',
            must=["all users are effectively super users"],
        ),
        Case(
            "real-adr-govuk-reject",
            "real-adr-govuk",
            "status",
            "ADR 38 (Mongo Replacement by DocumentDB) has been rejected; update its status.",
            must=["@sub:38. Mongo Replacement|Status"],
            allowed=["@sec:38. Mongo Replacement"],
            checks=[("@sub:38. Mongo Replacement|Status", "(?i)rejected", True)],
        ),
        Case(
            "real-adr-govuk-supersede",
            "real-adr-govuk",
            "status",
            "ADR 21 (Use ACM for SSL purchases) is superseded by a new ADR 40, Use Let's Encrypt; update its status following the existing convention.",
            must=["@sub:21. Use ACM|Status"],
            allowed=["@sec:21. Use ACM"],
            checks=[("@sub:21. Use ACM|Status", "(?i)superseded", True)],
        ),
        Case(
            "real-adr-govuk-version",
            "real-adr-govuk",
            "literal-ripple",
            "Correct ADR 38: Licensify uses MongoDB 3.4.1, not 3.2.7.",
            must=["3.2.7 for Licensify"],
            checks=[("*", r"3\.2\.7", False)],
        ),
        Case(
            "real-adr-govuk-atlas",
            "real-adr-govuk",
            "literal-ripple",
            "In ADR 38 we have decided to use MongoDB Atlas instead of AWS DocumentDB; update the decision record.",
            must=["@all:DocumentDB"],
            allowed=["@sec:38. Mongo Replacement"],
            checks=[("*", "DocumentDB", False)],
        ),
        Case(
            "real-adr-govuk-add",
            "real-adr-govuk",
            "add-item",
            'Add a consequence to ADR 25 (Use Elasticache for Redis): "Redis version upgrades are managed by AWS."',
            must=[],
            allowed=["@sec:25. Use Elasticache"],
            checks=[("*", "upgrades are managed by AWS", True)],
        ),
    ],
}
