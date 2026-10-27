# Semantic DOM

Can a harness-side **semantic DOM** make iterative LLM editing of structured documents (CVs, ADRs, contracts)
cheaper than sending the whole document with prompt caching, without missing knock-on changes?

**Short answer:** from about 4k tokens up, yes: 22–58% cheaper with the baseline's cache always warm, and 65%
cheaper on a 24k-token document with realistic pauses between edits, with no detectable quality difference
(Claude Opus 5.5). On a 400-token CV it cost 57% more. Per edit it was as fast as the baseline, once the document
was indexed when opened. Full method, tables and caveats: **[docs/results.md](docs/results.md)**.

| Document size | Use |
|---|---|
| Under ~1k tokens (a page or two) | Whole document with prompt caching |
| 1k–4k tokens | Break-even is somewhere here (not measured) |
| 4k tokens and up (ADR logs, contracts, long specs) | Semantic DOM: 22–58% cheaper with a warm cache, 65% at 24k with real pauses |

## How it works

When someone asks an LLM to change one bullet, the usual options are to rewrite the whole document (slow,
expensive) or keep it in context with prompt caching and apply find-and-replace edits (cheap while the cache is
warm). Neither knows that changing a start date should also change "12 years of experience" in the summary.

This harness parses the document into addressable nodes (document → section → item) and builds dependency edges
between them: structural, per-document-type schema rules, and shared facts such as numbers, durations and defined
terms. When the document opens it indexes every node for hybrid retrieval (exact facts, BM25, `bge-small`
embeddings). Each edit sends the model a cached outline, the target and its dependents, and the model returns
patches by node ID.

## Where it doesn't win

- Small documents: the outline and patch format cost more than a cached read of the whole thing.
- Not faster, only level: 5.9 s vs 6.6 s per edit end to end. Indexing at open takes about 6 s at 24k tokens and
  17 s at 100k on a laptop CPU.
- No quality gain over the baseline, which sees the whole document; "no detectable difference" at ~25 checks per run.
- One model, 42 held-out edits, markdown only. Answer keys were drafted by the agent that built the harness and
  reviewed by the author.

## Strategies compared

| ID | Strategy |
|---|---|
| B0 | Full rewrite: whole doc in, whole doc out |
| B1 | Full doc in context, prompt caching, `{old,new}` find-and-replace edits (**the baseline to beat**; 5-minute and 1-hour cache) |
| S | Semantic DOM: cached outline + target + impacted dependents, node-ID patches |

## Reproduce

```bash
pip install anthropic rank_bm25 fastembed model2vec numpy ruff mypy pytest pytest-cov
```

```bash
python -m evalset.build
```

```bash
python -m tools.gate
```

```bash
python -m tools.paced results/paced/*.json
```

Live runs need `ANTHROPIC_API_KEY` in a gitignored `.env` file and are capped by `budget.json`. A dry run spends
nothing:

```bash
python run_live.py --docs fresh2-adr-govuk-infra --strategies S --preload --dry-run
```

The paced comparison, live:

```bash
python run_live.py --docs fresh2-adr-govuk-infra --strategies S --preload --gaps 2,7,3,12,4 --tag paced-S
```

Each result in the write-up names its files and the command that reproduces it.

## Layout

- `sdom/` — library (stdlib only): document model, dependency graph, strategies, cost model, budget
- `retrieval/` — BM25 and embedding retrievers (`--retriever regex` is the stdlib-only fallback)
- `evalset/` — seeded synthetic corpus with gold edit cases, and public real documents with sources in
  [`evalset/real/SOURCES.md`](evalset/real/SOURCES.md)
- `run_offline.py` — session simulator (cache TTLs, user pause patterns) and context-quality report
- `run_live.py` — API runner: real usage, latency, patch application, scoring, spend ledger
- `tools/` — quality gate, retriever comparison, graph ablation, paced and repeated-run summaries
- `results/` — the results behind every number in the write-up
- `.specify/memory/constitution.md` and `CLAUDE.md` — the rules the autonomous engineering loop worked under

## Licence

Code, write-up and results: [MIT](LICENSE). The documents under `evalset/real/` are third-party and keep their own
licences (Apache-2.0, MIT and CC BY 4.0), listed per document in
[`evalset/real/SOURCES.md`](evalset/real/SOURCES.md) and included alongside the originals in `evalset/real/sources/`.

## How this was built

The author designed the experiment and its rules (baselines, pre-registered answers, budget, quality gates) and
reviewed every result. The code was written by Claude Code running as an autonomous engineering loop under those
rules.
