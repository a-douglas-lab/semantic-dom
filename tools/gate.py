"""Quality gate (constitution Principle IV). Usage: python -m tools.gate [--fix]

Runs, in order: ruff lint, ruff format check, mypy (strict, sdom/), pytest with coverage (>=80% on sdom/).
Exits non-zero on the first failing stage.
"""

import subprocess
import sys

PY = sys.executable


def stages(fix: bool) -> list[tuple[str, list[str]]]:
    return [
        ("ruff lint", [PY, "-m", "ruff", "check", ".", *(["--fix"] if fix else [])]),
        ("ruff format", [PY, "-m", "ruff", "format", ".", *([] if fix else ["--check"])]),
        ("mypy", [PY, "-m", "mypy"]),
        ("pytest + coverage", [PY, "-m", "pytest", "--cov", "--cov-report=term-missing:skip-covered"]),
    ]


def main() -> int:
    fix = "--fix" in sys.argv
    for name, cmd in stages(fix):
        print(f"\n=== {name} ===", flush=True)
        if subprocess.run(cmd).returncode != 0:
            print(f"\nGATE FAILED at: {name}")
            return 1
    print("\nGATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
