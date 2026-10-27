import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evalset.build import OUT as CORPUS  # noqa: E402
from evalset.build import build  # noqa: E402
from sdom.dom import Document  # noqa: E402

CV = """# Jane Doe — CV

## Summary

Engineer with 10+ years of experience, currently Lead Engineer at Initech.

## Experience

### Lead Engineer — Initech (2020–Present)

- Built a Kafka pipeline handling 40k events per second.
- Cut costs by 25% at Initech.

### Engineer — Globex (2016–2020)

- Shipped the billing API on PostgreSQL.

## Skills

- Platforms: AWS, Docker
"""


CONTRACT = """# Agreement

## 5. Termination

5.1 Either party may terminate this Agreement for convenience on ninety (90) days written notice.

5.2 Either party may terminate immediately on written notice for material breach.

## 6. Disputes

6.1 Invoices disputed in good faith shall be resolved within 90 days.

6.2 Each party shall notify the other within 14 Business Days.

6.3 The Supplier shall keep records for 120 months.

6.4 The Customer shall pay within 30 days of invoice.

6.5 Audits may occur once every 12 months.

6.6 The Supplier shall maintain insurance for 6 years.

6.7 Notices are deemed received after 2 Business Days.

6.8 The parties shall meet quarterly.

6.9 Escalation within 10 days.

6.10 Records retained for 7 years.

6.11 Credits apply within 45 days.

6.12 Reviews happen every 180 days.

## Schedule 3 — Key Terms Summary

- Termination for convenience: three months notice by either party.
- Liability cap: 150% of fees paid.
"""


@pytest.fixture
def cv() -> Document:
    return Document.parse(CV, "cv")


@pytest.fixture
def contract_snippet() -> Document:
    return Document.parse(CONTRACT, "contract")


@pytest.fixture(scope="session")
def corpus() -> dict[str, tuple[Document, list[dict]]]:
    manifest = build()
    out = {}
    for m in manifest:
        md = (CORPUS / f"{m['doc']}.md").read_text(encoding="utf-8")
        cases = json.loads((CORPUS / f"{m['doc']}.cases.json").read_text(encoding="utf-8"))
        out[m["doc"]] = (Document.parse(md, m["type"]), cases)
    return out
