# Semantic DOM — agent guide

> Published for reference: this is the guide the autonomous engineering loop worked under. The backlog and the
> per-experiment spec folders it refers to are not part of this repository.

Research harness testing whether a harness-side semantic DOM makes LLM editing of structured docs
cheaper/faster and more consistent than full-doc + prompt caching + find-and-replace (B1).

**Governance**: `.specify/memory/constitution.md` (principles, rubrics R1–R6, autonomy contract). Read it
before starting work. Backlog: `backlog.md`. Specs: `specs/NNN-name/` (Spec Kit: `/speckit-specify`,
`/speckit-plan`, `/speckit-tasks`, `/speckit-implement`).

## Engineering loop (run autonomously)
1. Take the top unblocked item from `backlog.md`; non-trivial → Spec Kit flow into `specs/NNN-name/`.
2. Tests first, then implement. `python -m tools.gate` must pass (ruff, mypy strict on `sdom/`, pytest + cov ≥80%).
3. `python run_offline.py`; live only if needed: `python run_live.py --docs ... --strategies ...` (budget-guarded).
4. Score against R1–R6, write findings into the spec folder, update `backlog.md`.
5. Commit locally on a feature branch (`NNN-name`). Never push.
6. Stop and ask only at the decision points the constitution lists (budget, constitution/rubric changes,
   publishing/pushing, new runtime deps in `sdom/`, deleting results).

## Commands
- Gate: `python -m tools.gate` (`--fix` to autofix lint/format)
- Corpus: `python -m evalset.build` · Offline: `python run_offline.py` · Live dry run: `python run_live.py --dry-run`
- Tools are invoked via `python -m` (ruff/mypy/pytest scripts are not on PATH).

## Conventions
- `sdom/` is stdlib-only and fully typed; the Anthropic SDK lives only in `run_live.py`; retrievers (rank_bm25,
  fastembed bge-small, model2vec) live in `retrieval/`. Default retriever: `all-bge` (regex + BM25 + bge, spec 009);
  `--retriever regex` is the stdlib-only fallback.
- Model default `claude-opus-5-5`, effort `low` for live edits. API key from env or `.env` (gitignored).
- Changing the corpus changes `tests/eval_floor.json`'s hash: update it deliberately and say why in the commit.
- Results must label estimates as estimates; report losses as prominently as wins.
