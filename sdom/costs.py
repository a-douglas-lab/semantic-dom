"""Pricing and latency model. Prices: Claude Opus 5.5 list rates (USD per 1M tokens, 2026-10).

Latency constants are ASSUMPTIONS to be replaced by live measurements.
"""

from dataclasses import dataclass

PRICES = {
    "claude-opus-5-5": {"in": 4.00, "out": 20.00, "cache_read": 0.20, "write_5m": 5.00, "write_1h": 8.00},
    "claude-sonnet-5-5": {"in": 2.00, "out": 10.00, "cache_read": 0.20, "write_5m": 2.50, "write_1h": 4.00},
    "claude-haiku-5-5": {"in": 0.10, "out": 0.50, "cache_read": 0.01, "write_5m": 0.125, "write_1h": 0.20},
}
MIN_CACHEABLE = 512  # tokens, current-generation models

# Calibrated from 144 live calls (claude-opus-5-5, 2026-10-16): real input ~= 1.2-1.4 x chars/4 estimate,
# plus ~450 fixed tokens on requests using structured output (json_schema), ~70 without.
TOKEN_SCALE = 1.22  # prose documents (B0/B1)
TOKEN_SCALE_TAGGED = 1.44  # [id]-tagged node lists and outlines (B2/S)
SCHEMA_OVERHEAD = 450
PLAIN_OVERHEAD = 70

# latency assumptions (seconds / tokens-per-second)
BASE_LATENCY_S = 0.6
PREFILL_TPS = 8000  # uncached input processing
CACHED_PREFILL_TPS = 200_000
DECODE_TPS = 60


@dataclass
class Usage:
    uncached_in: int = 0
    cache_read: int = 0
    cache_write: int = 0
    out: int = 0

    def __iadd__(self, o: "Usage") -> "Usage":
        self.uncached_in += o.uncached_in
        self.cache_read += o.cache_read
        self.cache_write += o.cache_write
        self.out += o.out
        return self

    @property
    def total_in(self) -> int:
        return self.uncached_in + self.cache_read + self.cache_write


def cost_usd(u: Usage, model: str = "claude-opus-5-5", ttl: str = "5m") -> float:
    p = PRICES[model]
    w = p["write_1h"] if ttl == "1h" else p["write_5m"]
    return (u.uncached_in * p["in"] + u.cache_read * p["cache_read"] + u.cache_write * w + u.out * p["out"]) / 1e6


def latency_s(u: Usage) -> tuple[float, float]:
    """(time to first token, total)."""
    ttft = BASE_LATENCY_S + (u.uncached_in + u.cache_write) / PREFILL_TPS + u.cache_read / CACHED_PREFILL_TPS
    return ttft, ttft + u.out / DECODE_TPS
