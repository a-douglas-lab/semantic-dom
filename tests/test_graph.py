from sdom.graph import SemanticGraph, heading_terms


def test_heading_terms():
    assert heading_terms("Lead Engineer — Initech (2020–Present)") == ["Lead Engineer", "Initech", "2020–Present"]
    assert heading_terms("ADR-007: Use Kafka for streaming") == ["ADR-007", "Use Kafka for streaming"]


def test_fact_extraction(cv):
    g = SemanticGraph(cv)
    facts = g.extract("Cut costs by 25% at Initech in 2019; see ADR-012; fee £18,500; 7 days")
    assert {"n:25", "t:Initech", "n:2019", "ref:ADR-012", "n:18500"} <= facts
    assert "n:7" not in facts  # single digits ignored


def test_duration_facts_normalise_words_units_and_legal_form():
    from sdom.graph import durations

    assert durations("on ninety (90) days written notice") == {"dur:90"}
    assert durations("three months notice by either party") == {"dur:90"}
    assert durations("resolved within 90 days") == {"dur:90"}
    assert durations("two weeks, 1 year and twenty-one days") == {"dur:14", "dur:365", "dur:21"}
    assert durations("within 14 Business Days") == set()  # qualified unit: not a plain duration
    assert durations("Severity 1 response: 30 minutes") == set()


def test_paraphrased_duration_is_a_literal_dependency(contract_snippet):
    g = SemanticGraph(contract_snippet)
    imp = g.impact("Change the termination for convenience notice period from 90 days to 60 days.")
    texts = [contract_snippet.nodes[i].text for i in imp.all]
    assert any("three months notice" in t for t in texts)


def test_generalised_facts_quantities_code_tokens():
    from sdom.graph import code_tokens, quantities

    # units normalised: lower-case, "x" multiplier == "×"
    assert quantities("handled 3× in minutes; a 1.4PB migration; 3x faster; 40% less") == {"q:3×", "q:1.4pb", "q:40%"}
    assert quantities("the x axis and 3 boxes") == set()
    assert "c:catalog-info.yaml" in code_tokens("The catalog file should be named catalog-info.yaml today")
    assert "c:node-fetch" in code_tokens("use the `node-fetch` package")
    assert code_tokens("well-known, state-of-the-art e.g. things") == set()  # prose hyphenation isn't code


def test_instruction_proper_nouns_locate_targets():
    from sdom.dom import Document

    doc = Document.parse(
        "# T\n\n## ADR010: Use the Luxon Date Library\n\nWe will use Luxon for dates.\n\n"
        "## ADR012: Presets\n\nUse Luxon presets.\n\n## Other\n\nThe team decided things.\n\n"
        "## More\n\nNothing here.\n\n## Again\n\nStill nothing.\n",
        "adr",
    )
    g = SemanticGraph(doc)
    imp = g.impact("We are replacing Luxon with date-fns as the standard date library.")
    assert {"s1", "s1.i1", "s2.i1"} <= set(imp.all)
    assert "s3.i1" not in imp.all  # "The"/"We" are not facts


def test_cv_summary_schema_matches_executive_summary():
    from sdom.dom import Document

    doc = Document.parse(
        "# CV\n\n## Executive summary\n\nLeader with 20+ years.\n\n## Experience\n\n### Eng — Acme (2010–2020)\n\n- Built things.\n",
        "cv",
    )
    imp = SemanticGraph(doc).impact("I started at Acme in 2008, not 2010.")
    assert "s1.i1" in imp.all


def test_locate_by_quote_and_by_facts(cv):
    g = SemanticGraph(cv)
    assert g.locate_targets('Rewrite "Cut costs by 25%" please') == ["s2.s1.i2"]
    # no quote: best fact overlap; section headings first
    assert g.locate_targets("I joined Globex in 2015, not 2016")[0] == "s2.s2"
    assert g.locate_targets("nothing matches here") == []


def test_schema_edge_pulls_summary_for_experience_edit(cv):
    g = SemanticGraph(cv)
    imp = g.impact("I joined Globex in 2015, not 2016")
    assert "s1.i1" in imp.dependents  # summary "10+ years" has no literal overlap
    assert any(r.startswith("schema:") for r in imp.reasons["s1.i1"])
    assert "s3.i1" in imp.dependents  # skills
    assert "s2.s2.i1" in imp.dependents  # structural: child of targeted heading
    assert set(imp.all) >= {"s2.s2", "s1.i1"}


def test_literal_edge_and_selectivity(cv):
    # Initech is in 4 of ~11 nodes: too common to follow by default...
    imp = SemanticGraph(cv).impact('Make "Cut costs by 25%" more specific')
    assert imp.targets == ["s2.s1.i2"]
    assert not any("literal:t:Initech" in r for rs in imp.reasons.values() for r in rs)
    # ...but followed when selectivity is relaxed
    imp = SemanticGraph(cv, max_fact_df=1.0).impact('Make "Cut costs by 25%" more specific')
    assert "literal:t:Initech" in imp.reasons["s1.i1"]
    # facts the user names explicitly are always followed
    imp = SemanticGraph(cv).impact("Initech is now called Initrode")
    assert {"s1.i1", "s2.s1", "s2.s1.i2"} <= set(imp.all)


def test_budget_limits_dependents(cv):
    g = SemanticGraph(cv, dep_budget_tokens=5)
    imp = g.impact("I joined Globex in 2015, not 2016")
    assert sum(len(cv.nodes[d].text) for d in imp.dependents) <= 5 * 4 + 4
