import json

import pytest

from sdom.budget import BudgetExceeded, Ledger
from sdom.costs import Usage, cost_usd, latency_s


def test_cost_opus_rates():
    u = Usage(uncached_in=1_000_000, cache_read=1_000_000, cache_write=1_000_000, out=1_000_000)
    assert cost_usd(u) == pytest.approx(4 + 0.2 + 5 + 20)
    assert cost_usd(u, ttl="1h") == pytest.approx(4 + 0.2 + 8 + 20)


def test_usage_accumulates_and_latency_monotonic():
    u = Usage(uncached_in=10)
    u += Usage(cache_read=5, out=3)
    assert (u.total_in, u.out) == (15, 3)
    cold = latency_s(Usage(uncached_in=100_000, out=100))
    warm = latency_s(Usage(cache_read=100_000, out=100))
    assert cold[0] > warm[0] and cold[1] > cold[0]


def test_ledger_caps(tmp_path):
    (tmp_path / "b.json").write_text(json.dumps({"per_run_usd": 1.0, "total_usd": 1.5}))
    led = Ledger(tmp_path / "b.json", tmp_path / "spend.json")
    led.check(0.9)
    led.record(0.9, "a")
    with pytest.raises(BudgetExceeded, match="per-run"):
        led.check(0.2)
    led2 = Ledger(tmp_path / "b.json", tmp_path / "spend.json")  # new run, ledger persisted
    assert led2.total_spent == pytest.approx(0.9)
    with pytest.raises(BudgetExceeded, match="total"):
        led2.check(0.7)


def test_ledgers_sharing_a_file_keep_each_others_entries(tmp_path):
    """Parallel runner processes must not overwrite each other's spend records."""
    budget = tmp_path / "budget.json"
    budget.write_text('{"per_run_usd": 1.0, "total_usd": 1.0}')
    path = tmp_path / "spend.json"
    a, b = Ledger(budget, path), Ledger(budget, path)
    a.record(0.4, "a1")
    b.record(0.4, "b1")
    assert [e["note"] for e in Ledger(budget, path).entries] == ["a1", "b1"]
    with pytest.raises(BudgetExceeded):
        a.check(0.3)  # 0.8 already spent across both processes
