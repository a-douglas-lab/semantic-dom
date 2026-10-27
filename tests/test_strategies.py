import json

import pytest

from sdom.graph import SemanticGraph
from sdom.strategies import STRATEGIES, apply_output, est_output_tokens, pack, parse_json


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_pack_shapes(cv, strategy):
    p = pack(strategy, cv, SemanticGraph(cv), "I joined Globex in 2015, not 2016")
    assert p.system and p.volatile.endswith("not 2016")
    if strategy in ("B0", "B1"):
        assert "<document>" in p.stable and len(p.context_ids) == len(cv.nodes) - 1
    elif strategy == "B2":
        assert p.stable == "" and "s1.i1" not in p.context_ids  # no summary: section only
    else:
        assert "<outline>" in p.stable and "s1.i1" in p.context_ids and "[s1.i1]" in p.volatile


def test_pack_uses_frozen_skeleton(cv):
    frozen = cv.skeleton()
    cv.set_text("s2", "Career History")
    p = pack("S", cv, SemanticGraph(cv), "I joined Globex in 2015, not 2016", skeleton=frozen)
    assert "Experience" in p.stable and "Career History" not in p.stable


def test_followup_pack_expands_flags_and_summarises_changes(cv):
    from sdom.strategies import followup_pack

    p = pack("B2", cv, SemanticGraph(cv), 'Make "Cut costs by 25%" more specific')  # section-only context
    after_out = json.dumps({"ops": [{"id": "s2.s1.i2", "find": "25%", "replace": "27%"}], "flagged": []})
    after, _, _ = apply_output("S", cv, after_out)
    fu = followup_pack(cv, after, "Make it specific", ["s3", "s2.s1.i2", "zz9"], p.context_ids, "outline")
    assert fu is not None
    assert "[s3.i1]" in fu.volatile  # flagged section expanded to its items
    assert "25%" in fu.volatile and "27%" in fu.volatile  # before -> after summary
    assert "zz9" not in fu.volatile and fu.stable == "<outline>\noutline\n</outline>"
    assert followup_pack(cv, after, "x", ["s2.s1.i2", "nope"], p.context_ids, "o") is None  # nothing new


def test_apply_ops_find_replace_and_errors(cv):
    out = json.dumps(
        {
            "ops": [
                {"id": "s1.i1", "find": "10+", "replace": "11+"},
                {"id": "s2.s2", "find": "", "replace": "Engineer — Globex (2015–2020)"},
                {"id": "s9", "find": "", "replace": "x"},
                {"id": "s3.i1", "find": "Azure", "replace": "GCP"},
            ],
            "flagged": ["s4"],
        }
    )
    new, errors, flagged = apply_output("S", cv, out)
    assert "11+ years" in new.nodes["s1.i1"].text
    assert new.nodes["s2.s2"].text.endswith("(2015–2020)")
    assert len(errors) == 2 and flagged == ["s4"]
    assert cv.nodes["s1.i1"].text.startswith("Engineer with 10+")  # original untouched


def test_ops_tolerate_copied_markers_and_added_bullets(cv):
    out = json.dumps(
        {
            "ops": [
                {"id": "s2.s1.i1", "find": "- Built a Kafka", "replace": "Built a Pulsar"},
                {"id": "s3.i1", "find": "", "replace": "- Platforms: AWS, Docker, Kubernetes\n- Tools: Terraform"},
            ],
            "flagged": [],
        }
    )
    new, errors, _ = apply_output("S", cv, out)
    assert not errors
    assert new.nodes["s2.s1.i1"].text.startswith("Built a Pulsar")
    assert new.nodes["s3.i1"].text == "Platforms: AWS, Docker, Kubernetes"
    assert new.nodes["s3.i2"].text == "Tools: Terraform"  # added bullet became a node


def test_structural_ops_insert_and_delete(cv):
    out = json.dumps(
        {
            "ops": [
                {"op": "insert_after", "id": "s2.s1.i1", "find": "", "replace": "- Ran the on-call rota."},
                {"op": "delete", "id": "s2.s2.i1", "find": "", "replace": ""},
                {"op": "edit", "id": "s1.i1", "find": "10+", "replace": "11+"},
                {"op": "delete", "id": "nope", "find": "", "replace": ""},
            ],
            "flagged": [],
        }
    )
    new, errors, _ = apply_output("S", cv, out)
    assert [c.text for c in new.nodes["s2.s1"].children][:2] == [cv.nodes["s2.s1.i1"].text, "Ran the on-call rota."]
    assert "billing API" not in new.render() and "11+" in new.nodes["s1.i1"].text
    assert errors == ["unknown id nope"]


def test_apply_b1_str_replace(cv):
    out = json.dumps({"edits": [{"old": "10+ years", "new": "11+ years"}, {"old": "Initech", "new": "X"}]})
    new, errors, _ = apply_output("B1", cv, out)
    assert "11+ years" in new.nodes["s1.i1"].text
    assert errors and "occurs" in errors[0]  # Initech is not unique


def test_apply_b0_full_doc(cv):
    md = "```markdown\n" + cv.render().replace("10+", "12+") + "```"
    new, errors, _ = apply_output("B0", cv, md)
    assert not errors and "12+" in new.nodes["s1.i1"].text


def test_parse_json_tolerates_prose():
    assert parse_json('Here you go: {"ops": []} thanks') == {"ops": []}
    assert parse_json("no json") == {}


def test_output_estimates_order(cv, corpus):
    changed = ["s1.i1", "s2.s2"]
    b0, b1, s = (est_output_tokens(x, cv, changed) for x in ("B0", "B1", "S"))
    assert b0 >= b1 > s  # tiny doc: full rewrite ~ quoted edits; ids make S cheapest
    big, _ = corpus["adr-M"]
    assert est_output_tokens("B0", big, ["s1.i1"]) > 50 * est_output_tokens("B1", big, ["s1.i1"])
