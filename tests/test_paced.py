import json

from tools import paced


def _row(strategy, latency, harness_s, stop="end_turn", **extra):
    return {
        "strategy": strategy,
        "latency": latency,
        "harness_s": harness_s,
        "stop": stop,
        "cost": 0.1,
        "checks_passed": 1,
        "checks_total": 1,
        **extra,
    }


def test_v1_rows_get_end_to_end_latency_without_the_baselines_unused_graph():
    assert paced.e2e(_row("B1", 5.0, 30.0)) == 5.0  # V1 built a graph B1 never used
    assert paced.e2e(_row("S[all-bge]", 4.0, 3.0)) == 7.0
    assert paced.e2e(_row("S[all-bge]", 4.0, 3.0, e2e=6.5)) == 6.5  # V2 records it directly


def test_summary_splits_first_edit_from_later_edits(tmp_path):
    rows = [_row("S[all-bge]", 4.0, 20.0, e2e=24.0), _row("S[all-bge]", 4.0, 1.0, e2e=5.0)]
    files = []
    for i in range(2):
        f = tmp_path / f"run{i}.json"
        f.write_text(json.dumps({"meta": {"ttl": "5m"}, "rows": rows}))
        files.append(str(f))
    arms = paced.summarise(files)
    s = arms["S[all-bge] 5m"][0]
    assert (s["first"], s["later"], s["cost"]) == (24.0, 5.0, 0.2)
    assert "| S[all-bge] 5m | 2 |" in paced.render(arms)


def test_preloaded_sessions_are_labelled_and_include_the_prewarm_cost(tmp_path):
    rows = [_row("B1", 4.0, 0.0, e2e=4.0, preload_usd=0.25), _row("B1", 4.0, 0.0, e2e=4.0)]
    f = tmp_path / "run.json"
    f.write_text(json.dumps({"meta": {"ttl": "1h", "preload": True}, "rows": rows}))
    arms = paced.summarise([str(f)])
    assert abs(arms["B1 1h preload"][0]["cost"] - 0.45) < 1e-9
