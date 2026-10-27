# Architecture: how the pieces fit

The Document does not call the strategies. A **runner** (`run_live.py`, or `run_offline.py` for the
simulator) controls each edit. It parses the document, builds a graph over it, asks a strategy to
package the context, sends that to the model, and gives the reply back to the strategy, which applies it.
The strategies are plain functions in one module, not classes.

## Who calls whom

```mermaid
flowchart TD
    Runner["Runner<br/>run_live.py / run_offline.py"]

    subgraph core["sdom/ (core, standard library only)"]
        Document["Document<br/>dom.py"]
        Node["Node<br/>dom.py"]
        Graph["SemanticGraph<br/>graph.py"]
        Impact["Impact<br/>graph.py"]
        Matcher(["Matcher (interface)<br/>graph.py"])
        Strategies["strategies module<br/>pack · apply_output · followup_pack"]
        Packed["Packed<br/>strategies.py"]
        Local["plan_local · apply_local<br/>local_ops.py"]
        Ledger["Ledger<br/>budget.py"]
        Costs["Usage · cost_usd<br/>costs.py"]
    end

    subgraph retrieval["retrieval/ (third-party libraries)"]
        Factory["make_graph<br/>retrieval/__init__.py"]
        BM25["BM25Matcher<br/>bm25.py"]
        Embed["EmbeddingMatcher<br/>embed.py"]
    end

    API[("Claude API<br/>run_live.py only")]

    Runner -->|"1. parse markdown"| Document
    Document -->|"holds a tree of"| Node
    Runner -->|"2. build graph for this doc"| Factory
    Factory -->|creates| Graph
    Factory -->|"creates 0..n"| BM25
    Factory -->|"creates 0..n"| Embed
    BM25 -.->|implements| Matcher
    Embed -.->|implements| Matcher
    Graph -->|"reads nodes and facts"| Document
    Graph -->|"asks: which nodes match?"| Matcher
    Graph -->|returns| Impact
    Runner -->|"3. pack(strategy, doc, graph)"| Strategies
    Strategies -->|"graph.impact(instruction)"| Graph
    Strategies -->|returns| Packed
    Runner -->|"4. check budget, then record spend"| Ledger
    Runner -->|"5. send request"| API
    Runner -->|"6. apply_output(reply)"| Strategies
    Strategies -->|"edit by node ID, re-parse"| Document
    Runner -->|"price the call"| Costs
    Runner -.->|"SL variant: no model call"| Local
    Local -.->|edits| Document
```

## One edit, step by step (strategy S)

```mermaid
sequenceDiagram
    participant R as Runner
    participant D as Document
    participant F as make_graph
    participant G as SemanticGraph
    participant M as Matchers (BM25, embeddings)
    participant S as strategies
    participant L as Ledger
    participant C as Claude API

    R->>D: parse(markdown) once per session, then skeleton() frozen for caching
    loop each edit request
        R->>F: make_graph(doc, retriever)
        F->>M: fit over the document's nodes
        F->>G: SemanticGraph(doc, matchers)
        R->>S: pack("S", doc, graph, instruction, skeleton)
        S->>G: impact(instruction)
        G->>G: locate targets (quoted text, then facts, then matchers)
        G->>M: related(instruction + target text)
        G->>G: add structural and schema dependents, trim to token budget
        G-->>S: Impact(targets, dependents, reasons)
        S-->>R: Packed(system, cached outline, target and dependent nodes)
        R->>L: check(estimated cost)
        R->>C: request
        C-->>R: JSON ops by node ID, plus flagged IDs
        R->>L: record(actual cost)
        R->>S: apply_output("S", doc, reply)
        S->>D: set_text / insert_after / delete, then re-parse
        S-->>R: new document, errors, flagged
        R->>R: score against the answer key, and the new doc replaces the old
    end
```

## What each part is for

| Part | Role | Why it is separate |
|---|---|---|
| `Document` / `Node` (`dom.py`) | Parses markdown into a tree of sections and items with stable IDs. Renders it back, makes the outline ("skeleton"), and applies edits by ID. | Everything else addresses the document by node ID, not by text position. |
| `SemanticGraph` (`graph.py`) | For an instruction, finds the **targets** and the **dependents** that the edit might make inconsistent. Returns them as an `Impact`. | It holds the research idea: the dependency graph. It is kept apart so its pieces can be switched on and off for ablations. |
| `Matcher` (interface) | Contract any retriever must meet: `locate()` and `related()`. | Lets BM25 and embeddings be swapped or combined without changing the graph. |
| `BM25Matcher`, `EmbeddingMatcher` (`retrieval/`) | Keyword and meaning-based search over the nodes. | They need third-party libraries, so they live outside the dependency-free core. |
| `make_graph` (`retrieval/__init__.py`) | Factory: builds the graph with the retriever mix chosen on the command line (default `all-bge`). | One place defines the variants that were compared. |
| strategies module (`strategies.py`) | For each strategy (B0, B1, B2, S), decides what context to send, then applies the model's reply. | Keeps the comparison fair: every strategy goes through the same pack-and-apply steps. |
| `Packed` | The request content, split into a cacheable part and a per-request part. | Prompt caching depends on the cached prefix staying byte-for-byte identical. |
| `local_ops.py` | Simple edits done without calling the model (the SL variant). | Tests whether some edits need no model at all. |
| `Ledger` (`budget.py`) | Refuses a call that would exceed the budget, and records every spend. | Spending limit for an autonomous agent. |
| `Usage` / `cost_usd` (`costs.py`) | Token counts and list-price cost. | Shared by the simulator and live runs, so estimates and measured costs are priced the same way. |

The four strategies: **B0** sends the whole document and gets the whole document back. **B1** sends the
whole document (cached) and gets find-and-replace edits back; this is the strong baseline. **B2** sends
only the target section. **S** (semantic DOM) sends a cached outline plus the targets and their dependents.
