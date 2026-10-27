"""Live runner plumbing, exercised with the oracle (no network)."""

import json

import run_live
from sdom.graph import SemanticGraph
from sdom.strategies import apply_output, pack


def test_oracle_round_trip_hits_all_gold(corpus):
    doc, cases = corpus["contract-S"]
    for strategy in ("B0", "B1", "S"):
        for case in cases:
            if case["kind"] == "rename" and strategy == "B1":
                continue  # oracle quotes whole nodes; duplicates make B1 old-strings ambiguous
            p = pack(strategy, doc, SemanticGraph(doc), case["instruction"])
            text = run_live.Oracle().respond(strategy, doc, p, case)
            new, errors, _ = apply_output(strategy, doc, text)
            s = run_live.score(doc, new, case["gold"])
            in_ctx = set(case["gold"]["must"]) <= p.context_ids
            assert s["collateral"] == 0
            if in_ctx and not errors:
                assert s["must_recall"] == 1.0, (strategy, case["id"])


def test_allowed_section_covers_new_children():
    assert run_live._covered("s4.s5.i3", {"s4.s5"})
    assert run_live._covered("s4.s5", {"s4.s5"})
    assert not run_live._covered("s4.s50.i1", {"s4.s5"})
    assert not run_live._covered("s4.s6.i1", {"s4.s5"})


def test_load_dotenv(tmp_path, monkeypatch):
    monkeypatch.delenv("SDOM_TEST_KEY", raising=False)
    monkeypatch.setenv("SDOM_KEEP", "env")
    (tmp_path / ".env").write_text('# comment\nSDOM_TEST_KEY="abc"\nSDOM_KEEP=file\n')
    run_live.load_dotenv(tmp_path / ".env")
    run_live.load_dotenv(tmp_path / "missing.env")
    import os

    assert os.environ["SDOM_TEST_KEY"] == "abc" and os.environ["SDOM_KEEP"] == "env"
    monkeypatch.delenv("SDOM_TEST_KEY")


def test_score_checks_and_distractors(cv):
    gold = {
        "must": ["s1.i1"],
        "allowed": [],
        "no_change": ["s3.i1"],
        "checks": [("s1.i1", r"11\+", True), ("*", "Globex", False)],
    }
    new, _, _ = apply_output(
        "S",
        cv,
        json.dumps(
            {
                "ops": [
                    {"id": "s1.i1", "find": "10+", "replace": "11+"},
                    {"id": "s3.i1", "find": "AWS", "replace": "GCP"},
                ],
                "flagged": [],
            }
        ),
    )
    s = run_live.score(cv, new, gold)
    assert s["must_recall"] == 1.0 and s["distractor_changed"] == 1 and s["collateral"] == 1
    assert (s["checks_passed"], s["checks_total"]) == (1, 2)


def test_build_request_cache_markers():
    from sdom.strategies import Packed

    p = Packed("sys", "<document>doc</document>", "Edit request: x")
    r1 = run_live.build_request("B1", p, [], "claude-opus-5-5", "low")
    assert r1["output_config"]["format"]["type"] == "json_schema"
    hist = [*run_live.strip_cache_markers(r1["messages"]), {"role": "assistant", "content": "{}"}]
    r2 = run_live.build_request("B1", p, hist, "claude-opus-5-5", "low")
    markers = sum("cache_control" in b for m in r2["messages"] if isinstance(m["content"], list) for b in m["content"])
    assert markers == 2  # doc block + latest turn
    r0 = run_live.build_request("B0", p, [], "claude-opus-5-5", "low")
    assert "format" not in r0["output_config"]


def test_cache_salt_changes_only_the_system_prefix():
    from sdom.strategies import Packed

    p = Packed("sys", "<document>doc</document>", "Edit request: x")
    plain = run_live.build_request("B1", p, [], "claude-opus-5-5", "low")
    salted = run_live.build_request("B1", p, [], "claude-opus-5-5", "low", salt="v2-r1")
    assert plain["system"][0]["text"] == "sys"  # no salt: identical to V1 requests
    assert "v2-r1" in salted["system"][0]["text"]
    assert salted["messages"] == plain["messages"]


def test_baselines_need_no_graph(cv):
    from sdom.strategies import pack

    p = pack("B1", cv, None, "Change Initech to Acme.")
    assert "<document>" in p.stable
    import pytest

    with pytest.raises(ValueError):
        pack("S", cv, None, "Change Initech to Acme.")


def test_dry_run_records_end_to_end_latency_and_skips_graph_for_baselines(monkeypatch):
    import argparse

    calls: list[str] = []
    real_make_graph = run_live.make_graph

    def counting(doc, variant, **kw):
        calls.append(variant)
        return real_make_graph(doc, variant, **kw)

    monkeypatch.setattr(run_live, "make_graph", counting)
    manifest = {m["doc"]: m for m in run_live.build()}
    args = argparse.Namespace(
        docs="cv-S",
        strategies="B1,S",
        model="claude-opus-5-5",
        effort="low",
        dry_run=True,
        ttl="5m",
        retriever="regex",
        edges="structural,schema,literal",
        gaps="",
        salt="",
        preload=False,
    )
    rows: list[dict] = []
    run_live.run(args, manifest, None, None, run_live.Oracle(), rows)
    n_cases = sum(1 for r in rows if r["strategy"] == "B1")
    assert len(calls) == sum(1 for r in rows if r["strategy"] == "S" and r["stop"] != "local")
    assert n_cases and calls
    for r in rows:  # local ops have no API call: their latency already is the harness time
        want = r["latency"] if r["stop"] == "local" else r["harness_s"] + r["latency"]
        assert r["e2e"] == want


def test_prewarm_request_shares_the_cached_prefix_of_the_first_edit():
    from sdom.strategies import Packed

    p = Packed("sys", "<document>doc</document>", "Edit request: x")
    first = run_live.build_request("B1", p, [], "claude-opus-5-5", "low", "1h", "v3")
    warm = run_live.prewarm_request("B1", p, "claude-opus-5-5", "low", "1h", "v3")
    assert warm["system"] == first["system"] and warm["output_config"] == first["output_config"]
    assert warm["messages"][0]["content"][0] == first["messages"][0]["content"][0]  # cached block
    assert warm["max_tokens"] == run_live.PREWARM_MAX_TOKENS


def test_dry_run_preload_happens_once_per_session_outside_edit_timing():
    import argparse

    manifest = {m["doc"]: m for m in run_live.build()}
    args = argparse.Namespace(
        docs="cv-S",
        strategies="B1,S",
        model="claude-opus-5-5",
        effort="low",
        dry_run=True,
        ttl="5m",
        retriever="regex",
        edges="structural,schema,literal",
        gaps="",
        salt="",
        preload=True,
    )
    rows: list[dict] = []
    run_live.run(args, manifest, None, None, run_live.Oracle(), rows)
    for strategy in ("B1", "S"):
        rs = [r for r in rows if r["strategy"] == strategy]
        assert "preload_index_s" in rs[0] and all("preload_index_s" not in r for r in rs[1:])
        assert rs[0]["preload_usd"] == 0.0  # dry run makes no prewarm call
    assert next(r for r in rows if r["strategy"] == "B1")["preload_index_s"] == 0.0  # baselines need no index
