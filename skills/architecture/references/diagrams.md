# Architecture diagrams

A diagram earns its place when it lets the user judge the structure at a glance: what exists, what talks to what, where the trust lines are, and what changes. Each diagram answers **one** question. If a diagram tries to answer three, split it.

## Which diagrams to draw

| Diagram | Question it answers | Mermaid type | When |
|---|---|---|---|
| System context | Who and what does the system talk to? | `flowchart LR` | Always |
| Components + trust boundaries | What runs where, who calls whom, which calls cross a trust line? | `flowchart LR` with subgraphs | Always |
| Hot path sequence | What happens, in order, on the request that matters most, and where does the time go? | `sequenceDiagram` | When there's a latency target or a multi-hop flow |
| Options side by side | How do the alternatives differ structurally? | one `flowchart TB` per option | When there's a real choice (almost always) |
| Before / after | What moves, appears, or disappears? | two `flowchart`s, same layout | Refactors and migrations |
| Data model | Which entities, which relationships, which keys? | `erDiagram` | When the schema is part of the decision |
| State machine | What states can an entity be in, and what moves it? | `stateDiagram-v2` | Workflows, orders, jobs, payments |
| Deployment | What runs on which infrastructure, in which zone? | `flowchart` with subgraphs per zone | When infrastructure is part of the decision |

Plus the **data ownership table** (HTML table, not a diagram): one row per entity, its source of truth, its single writer, its readers, its sensitivity.

## Conventions (match the review page's legend)

Use the same shape and class for the same kind of thing everywhere. The review page styles these classes from its tokens, so they work in light and dark mode. Don't add inline `style` or `classDef` colors.

| Kind | Shape | Class | Example |
|---|---|---|---|
| Person / role | stadium `([ ])` | `k-actor` | `user([Shopper]):::k-actor` |
| Our component (service, module, job) | rectangle `[ ]` | `k-service` | `api[Orders API]:::k-service` |
| Datastore, cache, bucket | cylinder `[( )]` | `k-store` | `db[(Postgres)]:::k-store` |
| Queue, stream, topic | subroutine `[[ ]]` | `k-queue` | `q[[orders.events]]:::k-queue` |
| External system (not ours) | hexagon `{{ }}` | `k-external` | `psp{{Stripe}}:::k-external` |
| New in this design | its usual shape | `k-new` | `w[Delivery worker]:::k-new` |
| Removed by this design | its usual shape | `k-removed` | `cron[Nightly sync]:::k-removed` |
| Trust boundary / network zone | `subgraph` | (automatic) | `subgraph vpc["Private network"] ... end` |

**Subgraphs mean trust boundaries or deployment zones, nothing else.** The page draws every subgraph as a dashed boundary. Don't use subgraphs to group things for tidiness.

**Edges:**

- Solid arrow `-->` is a synchronous call. Dotted `-.->` is asynchronous (events, polling, queues).
- Arrows point in the direction of the **request** (caller to callee), not the data.
- Label every edge that crosses a boundary with protocol and auth: `-- "HTTPS, mTLS" -->`, `-- "gRPC, service token" -->`.
- Label hot-path edges with what's sent or the budget: `-- "1 txn: order + outbox" -->`.
- Quote labels containing punctuation: `-- "POST /v1/orders" -->`.

**Naming:** node IDs short and stable (`api`, `db`, `worker`); labels are the names people use. Keep labels to 1–4 words; put details in the fig-note under the diagram, not in the box.

## Layout rules

- **5–12 nodes per diagram.** Fewer than 5: a sentence is enough. More than 12: split by subsystem or zoom level.
- **Direction:** `LR` for request flows (reads like a sentence), `TB` for layered dependencies and for diagrams shown side by side in the half-width options grid.
- **Before / after pairs** use the same direction, the same node IDs, and the same order of declaration, so things stay in the same place and only the change stands out.
- **Sequence diagrams:** at most ~6 participants and ~15 messages. Use `autonumber`. Mark where the user-facing path ends with a `Note`. Use `alt`/`else` for failure handling and `loop` for polling or retries.
- **Order declarations** in the order you want them read: Mermaid lays out roughly in declaration order.

## Mermaid pitfalls

These break rendering or layout. The review page shows any render error in place of the diagram, but check before showing the user.

- `;` ends a statement in sequence diagrams: `A->>B: BEGIN; INSERT` breaks. Use commas or "then".
- Unquoted labels with `()`, `[]`, `{}`, `:`, `#`, or `|` break flowcharts. Quote them: `n["Postgres (primary)"]`.
- The word `end` in lowercase as a node ID or label ends a block. Use `End` or `finish`.
- Node IDs can't contain spaces; labels can.
- `<br>` works in labels for a line break; prefer short labels instead.
- Very long edge labels wreck layout. Move the detail to the fig-note.
- In `erDiagram`, attribute types come before names: `uuid id PK`.

## Verifying the page renders

Mermaid renders asynchronously after page load, so a naive headless screenshot can capture blank boxes or raw source mid-render. Either look at it in a real browser, or delay the screenshot until rendering finishes (for example, serve the page locally and add an `<img>` that takes several seconds to load, which holds the `load` event open). Check that:

- No "Diagram error" messages appear.
- Every diagram is readable at normal width without expanding (the Expand button is for detail, not for basic legibility).
- Both light and dark color schemes look right.
- The diagrams agree with the text and the tables: same names, same arrows, same numbers.

## ASCII fallback for the chat

In a plain terminal, give a quick sketch alongside the page path:

```
 Shopper ──HTTPS──▶ Orders API ──1 txn──▶ [(Postgres: orders + outbox)]
                                                  ▲
 ┌ private network ────────────┐                  ┆ poll
 │  Delivery worker (NEW) ─────┼──── HTTPS ───▶ {Merchant endpoint}
 └─────────────────────────────┘
```

Keep it to the main path; the page carries the full picture.
