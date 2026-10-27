"""Cache/session model behaviour of the offline simulator."""

import run_offline as sim
from sdom.graph import SemanticGraph


def _run(corpus, doc, strategy, ttl, gaps):
    d, cases = corpus[doc]
    return sim.simulate(d, SemanticGraph(d), cases, strategy, ttl, gaps, passes=1)


def test_b1_cold_cache_costs_more_than_warm(corpus):
    warm = _run(corpus, "adr-M", "B1", "5m", [1])
    cold = _run(corpus, "adr-M", "B1", "5m", [30])
    assert cold["cost"] > 2 * warm["cost"]
    assert warm["read"] > 0 and cold["read"] == 0


def test_one_hour_ttl_survives_long_gaps(corpus):
    assert _run(corpus, "adr-M", "B1", "1h", [30])["read"] > 0


def test_b1_history_grows_each_turn(corpus):
    turns = _run(corpus, "cv-M", "B1", "5m", [1])["turns"]
    ins = [t["in"] for t in turns]
    assert ins == sorted(ins) and ins[-1] > ins[0]


def test_s_cheaper_than_b1_on_large_doc_human_gaps(corpus):
    s = _run(corpus, "adr-L", "S", "5m", sim.SCENARIOS["human"])
    b1h = _run(corpus, "adr-L", "B1", "1h", sim.SCENARIOS["human"])
    assert s["cost"] < 0.5 * b1h["cost"]


def test_b2_has_no_cache_breakpoint(corpus):
    r = _run(corpus, "cv-S", "B2", "5m", [1])
    assert r["read"] == 0 and r["write"] == 0
