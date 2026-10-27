import pytest

from sdom.local_ops import apply_local, plan_local


@pytest.mark.parametrize(
    ("instruction", "expected"),
    [
        ('Rename the defined term "Supplier" to "Provider" throughout.', ("Supplier", "Provider")),
        ("Initech has rebranded as Meridian Group; update every mention.", ("Initech", "Meridian Group")),
        ("Globex Systems was renamed to Globex Inc", ("Globex Systems", "Globex Inc")),
        ('Replace "Acme" with "Apex" everywhere.', ("Acme", "Apex")),
    ],
)
def test_plan_detects_explicit_renames(cv, instruction, expected):
    plan = plan_local(instruction)
    assert plan is not None and (plan.old, plan.new) == expected


@pytest.mark.parametrize(
    "instruction",
    [
        "Change the termination for convenience notice period from 90 days to 60 days.",
        "In ADR-064 we are switching from Kafka to Memgraph; update that ADR and the log.",
        'Rewrite the bullet "Led migration of the identity platform" to be more concise.',
        "Increase the Service Fee from £18,500 to £21,000 per month.",
        'My current title should be "Director of Engineering", not "Engineering Manager".',
    ],
)
def test_plan_ignores_non_renames(instruction):
    assert plan_local(instruction) is None


def test_apply_handles_suffixes_boundaries_and_articles(contract_snippet):
    from sdom.dom import Document

    doc = Document.parse(
        "# T\n\n## A\n\n- A Supplier and the Supplier's staff; all Suppliers.\n- SupplierX is unrelated.\n", "generic"
    )
    plan = plan_local('Rename the defined term "Supplier" to "Operator" throughout.')
    assert plan is not None
    new, changed = apply_local(doc, plan)
    assert new.nodes["s1.i1"].text == "An Operator and the Operator's staff; all Operators."
    assert new.nodes["s1.i2"].text == "SupplierX is unrelated."
    assert changed == ["s1.i1"]
    assert doc.nodes["s1.i1"].text.startswith("A Supplier")  # original untouched
