"""Spend ledger and budget guard for live API runs (constitution Principle VI)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class BudgetExceeded(RuntimeError):
    pass


class Ledger:
    def __init__(self, budget_path: Path, ledger_path: Path):
        cfg = json.loads(budget_path.read_text(encoding="utf-8"))
        self.per_run = float(cfg["per_run_usd"])
        self.total_cap = float(cfg["total_usd"])
        self.path = ledger_path
        self.entries: list[dict[str, Any]] = []
        self._reload()
        self.run_spent = 0.0

    def _reload(self) -> None:
        """Re-read the file so parallel runner processes see (and keep) each other's spend."""
        self.entries = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else []

    @property
    def total_spent(self) -> float:
        return sum(float(e["usd"]) for e in self.entries)

    def check(self, estimate_usd: float) -> None:
        """Raise before a call that could push spend over either cap."""
        self._reload()
        if self.run_spent + estimate_usd > self.per_run:
            raise BudgetExceeded(f"per-run cap ${self.per_run:.2f} (spent ${self.run_spent:.4f})")
        if self.total_spent + estimate_usd > self.total_cap:
            raise BudgetExceeded(f"total cap ${self.total_cap:.2f} (spent ${self.total_spent:.4f})")

    def record(self, usd: float, note: str) -> None:
        self.run_spent += usd
        self._reload()
        self.entries.append({"at": datetime.now().isoformat(timespec="seconds"), "usd": round(usd, 6), "note": note})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.entries, indent=2), encoding="utf-8")
