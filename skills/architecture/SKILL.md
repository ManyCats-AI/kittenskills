---
name: architecture
description: Design, evaluate, or refactor software architecture with security and privacy built in from the first step (data inventory, threat model, trust boundaries, identity, authorization, tenant isolation, data minimization) alongside performance, module boundaries, data flow, and technology choices, and show it as a visual review page the user approves before anything is built. Use when the user asks how to structure a system or feature, wants a design reviewed or diagrammed, plans a large refactor or migration, or is choosing between architectural approaches. Not for line-level review (`code-review`) or tuning one hot path (`performance-optimization`).
---

# Architecture

Good architecture makes the likely changes cheap, keeps the system fast under real load, and makes the dangerous mistakes hard. Security and privacy come first: they decide where the boundaries go, what data exists at all, and who can touch it, so they're designed in from the first sketch, never reviewed in at the end. Performance is the other requirement that's far cheaper to design in than to bolt on.

## Related skills

| When | Use |
|---|---|
| Estimating load, latency budgets, storage, or cost | `math` |
| Evaluating unfamiliar technologies, vendors, or known failure stories | `deep-research` |
| A bottleneck needs measuring, or the design needs validating under load | `performance-optimization` |
| Threat-modeling the design, or auditing the implementation that follows | `security-audit` |
| Reviewing the code that implements the design | `code-review` |
| Building the design with a multi-agent team that must agree on it | `team-orchestration` |

## Files

| What | Where |
|---|---|
| Visual review page the user looks at and approves (copy and fill) | `assets/architecture-review.html` |
| Which diagrams to draw, Mermaid conventions, and pitfalls | `references/diagrams.md` |

## Workflow

### 1. Understand before proposing

Ground every recommendation in the real codebase and the real constraints.

- **Map what exists.** Find entry points, core domain types, persistence, external integrations, and how a request flows end to end. Read the code; don't infer structure from directory names alone.
- **Find the forces.** Ask, or work out from context:
  - What has to change soon (features, scale, team growth)?
  - What can't change (deployment targets, compliance, existing contracts, team skills)?
  - What hurts today (slow builds, tangled modules, incidents, latency, security findings)?
- **Size the problem.** A 2-person prototype and a 50-engineer platform need different answers. Match the solution to the scale.

### 2. Design security and privacy in from the start

Security and privacy are structural requirements, settled before performance and before options are compared. Every option in step 5 is judged against them, and a design that needs them added later is the wrong design. Anything that depends on law or regulation (GDPR, HIPAA, PCI DSS, COPPA, data residency) is researched with sources (→ `deep-research`), never assumed.

**a. Data inventory.** For every kind of data the system holds or touches, record:

| Data | Class | Purpose | Stored and copied in | Who can read | Retention and deletion |
|---|---|---|---|---|---|

Classes: public, internal, confidential, personal, sensitive personal (health, biometric, precise location, children's, financial, government ID), secret. "Copied in" includes caches, search indexes, logs, analytics, error trackers, backups, exports, and third parties. **Data with no purpose is not collected.**

**b. Privacy by design.**

- **Minimize**: the fewest fields, the coarsest granularity that works (age band, not birth date; city, not GPS), the shortest retention.
- **Purpose limitation**: data collected for one purpose isn't reused for another without a new, explicit decision.
- **Separate identity from activity**: logs, analytics, and events carry pseudonymous IDs; the mapping to real identity lives in one guarded place.
- **Encrypt by sensitivity**: application-level encryption for fields that database admins, backups, or support tools shouldn't read. Per-user or per-tenant keys make deletion possible by destroying the key (crypto-shredding), including in backups.
- **Deletion and export are features**: design the flows that find and remove (or export) one person's data from every copy listed in the inventory.
- **Data leaving the system**: list every third party that receives data, exactly what it gets, and why. Send the minimum. Prefer options that don't need plaintext (tokenization, hosted payment forms, self-hosting for sensitive data).
- **No personal data in logs, URLs, or error reports.** Telemetry and analytics are opt-in.
- **Consider whether the server needs plaintext at all**: end-to-end encryption or local-first storage removes whole classes of breach.
- **Privacy threats per data flow (LINDDUN)**: linking records to each other, identifying people, non-repudiation (being unable to deny an action), detecting that someone uses the system, data disclosure, unawareness (users don't know what's collected), non-compliance.

**c. Threat model** (→ `security-audit` for depth):

- **Assets**: credentials, keys, personal data, payment data, admin capabilities, availability.
- **Actors**: anonymous users, authenticated users, other tenants, insiders and support staff, compromised dependencies, compromised internal services.
- **Trust boundaries**: draw them on the diagram. Every arrow that crosses one needs authentication, authorization, and input validation at the receiving side.
- **STRIDE per boundary**: spoofing, tampering, repudiation, information disclosure, denial of service, elevation of privilege. Note the control for each one that applies and how it will be tested.
- **Abuse cases**: how would a malicious user, a curious user, a competitor, or a stolen account misuse each major feature?
- **Blast radius**: if this component is fully compromised, what else falls? Design so the answer is "not much".

**d. Security decisions made now, not later:**

- **Identity**: where users are authenticated, the session or token model, and how services authenticate each other (mTLS or workload identity; no shared static credentials).
- **Authorization model**: role-, attribute-, or relationship-based; enforced by the component that owns the data, deny by default, and testable as a role × resource × action matrix.
- **Tenant isolation enforced by structure** (row-level security, separate schemas or databases, per-tenant keys), not by every query remembering a `WHERE tenant_id = ?`.
- **Secrets and keys**: a managed store or KMS, short-lived credentials, rotation, separate per environment.
- **Network**: private by default; only the edge is public. Components that fetch user-supplied URLs go through an egress allowlist (SSRF).
- **Risky processing is sandboxed**: file conversion, image and PDF processing, user code, and LLM agents with tools run with minimal privileges.
- **Audit log**: who did what to which record, append-only, without logging the sensitive data itself.
- **Supply chain**: every dependency is code you run; keep them few, pinned, and scanned.
- **Failure**: fail closed when an auth service, policy, or config is unavailable; any break-glass access is audited.

**Done when** the data inventory, the boundaries with their STRIDE and LINDDUN threats and controls, and the decisions above are written down and appear on the review page (step 7). Every control names how it will be verified.

### 3. Set performance requirements

Turn "it should be fast" into numbers before you design (→ `math` for the estimates).

- **Load profile**: requests per second (average and peak), read/write ratio, data volume now and in 12–24 months, and growth rate.
- **Latency targets**: p50 and p99 for the critical user paths.
- **Latency budget**: split the target across every hop in the request path (network, auth, service calls, DB, rendering). If the budget doesn't add up on paper, it won't add up in production.
- **Back-of-envelope capacity**: rows per table, bytes per request, QPS per DB node, cache hit rate needed, and monthly cost. Order-of-magnitude accuracy is enough to rule designs out.
- **Hot paths**: which 2–3 operations dominate load or matter most to users? Design those first and optimize the data model for them.

### 4. Identify the real decisions

Most of a design follows from a few key decisions. Name them explicitly:

- **Boundaries**: which modules, packages, or services exist, and what does each one own?
- **Data ownership**: what is the source of truth for each piece of data, and who is allowed to write it?
- **Data access patterns**: how is each hot path served? Which indexes, denormalizations, read models, or caches does it need?
- **Communication**: in-process calls, synchronous RPC, events, or a shared database? How many sequential network hops does a hot path cross?
- **Consistency**: what must be strongly consistent, and where is eventual consistency acceptable?
- **Security and privacy**: the identity, authorization, tenant isolation, secrets, and data-handling decisions from step 2. They constrain every other decision on this list.
- **Failure modes**: what happens when each dependency is slow or down, and how does each one degrade?

### 5. Generate and compare options

For each key decision, consider at least two real options, including "keep it as is". Compare them on:

| Criterion | Question |
|---|---|
| Security | How many trust boundaries and public entry points does it add? What's the blast radius of a compromise? Does access control sit with the data owner? |
| Privacy | Does it copy personal data to more places (caches, events, third parties, logs)? Can one person's data still be found and deleted everywhere? |
| Change cost | How many places must change for the most likely next feature? |
| Performance | Does it meet the latency budget and load profile on paper? How many hops and round trips does the hot path take? |
| Scalability | What's the first thing to saturate as load grows 10×, and how is that fixed? |
| Failure isolation | What happens when this component is slow or down? |
| Operability | How is it deployed, observed, and debugged at 3am? |
| Cognitive load | Can a new engineer find where X happens within minutes? |
| Reversibility | How expensive is it to back out if we're wrong? |
| Migration path | Can we get there incrementally from where we are now? |

**Design it twice for one-way doors.** For a decision that's expensive to reverse (a public API, a data model, a service split), have two or three subagents design it independently in parallel, each told to take a different direction (for example: smallest interface; most flexible; optimized for the hot path). Using different model families where available widens the spread. Score each against the requirements criterion by criterion, pick a base, and port in the one or two best ideas from the others by hand. If all designs converge on one shape, that's strong evidence. If they diverge wildly, the requirements are underspecified: go back to step 1.

Choose cheap, reversible decisions when uncertainty is high. Save irreversible commitments for things you know with confidence. When an option depends on an unfamiliar technology's performance or security record, research it first (→ `deep-research`). If the decision hinges on real numbers, build a quick prototype and measure it (→ `performance-optimization`).

### 6. Recommend and document

Give one clear recommendation, not a menu. Use a lightweight ADR format:

```markdown
## Decision: <short title>
**Context:** The forces and constraints that make this decision necessary.
**Decision:** What we will do, stated concretely.
**Performance:** Load assumptions, latency budget, capacity estimate, first bottleneck at 10×.
**Security:** Trust boundaries, threats considered, mitigations, residual risk.
**Alternatives considered:** Each option, and why it lost.
**Consequences:** What gets easier, what gets harder, what we must watch.
**Migration:** Incremental steps from today's code, each one shippable.
```

### 7. Show it visually and get approval

People judge structure much faster by looking than by reading. Before any implementation starts, the user sees the architecture drawn and explicitly approves it. For anything beyond a one-component change, this step is mandatory.

1. **Build the review page.** Copy `<skill-dir>/assets/architecture-review.html` from this skill's folder to `docs/architecture/<slug>.html` if the project keeps design docs, otherwise to a scratch location, and tell the user the path. Fill every `FILL` block and delete sections that don't apply. Draw the diagrams described in `references/diagrams.md`:
   - **System context**: actors and external systems around the system as one box
   - **Components and trust boundaries**: what runs where; every boundary-crossing arrow labeled with protocol and auth
   - **Hot path sequence** with the latency budget table beside it
   - **Options side by side**: the same problem drawn each way, recommended one outlined
   - **Before / after** for refactors and migrations, with new parts green and removed parts red
   - **Security and privacy**: the data inventory, threats and controls per boundary, and data leaving the system (step 2)
   - **Data ownership** table: one writer per field
2. **Check it yourself first.** Open it in a browser (or render headlessly and look at the screenshot). Every diagram must render without errors, be legible at normal width, and match the text. A diagram the reader has to decode is a failed diagram: split it rather than cram it.
3. **Show it to the user.**
   - If the environment has an artifact or preview tool, publish the page there.
   - Otherwise open it: `xdg-open <file>` (Linux), `open <file>` (macOS), `start <file>` (Windows), and give the absolute path.
   - Always also put the main components diagram in the chat as a fenced `mermaid` block, plus a short ASCII sketch if the user is in a plain terminal, so the gist is visible without leaving the conversation.
4. **Ask for a verdict**, with the specific questions you need answered: approve, approve with changes, pick a different option, or rework. The page's review form produces a pasteable verdict.
5. **Iterate on the same file.** Bump the revision number, apply the feedback, and say in one line per change what moved. Don't start implementation until the verdict is an approval.

## Performance principles

- **Design the data model around the hot paths.** Most performance problems are data access problems: wrong shape, missing index, too many round trips.
- **Count round trips.** Sequential network calls on a hot path add up fast. Batch, parallelize, or co-locate data that's read together.
- **Keep the hot path short.** Move non-essential work (emails, analytics, thumbnails, webhooks) to async jobs or queues.
- **Bound everything.** Every queue, cache, pool, page size, payload, and retry loop needs a limit. Unbounded resources become outages and DoS vectors.
- **Use backpressure and timeouts.** Every remote call needs a timeout. Retries need backoff, jitter, and a budget. Shed load before the system falls over.
- **Cache deliberately.** Decide what's cached, the key (including tenant and user scope), the TTL, the invalidation rule, and what happens on a stampede.
- **Scale the bottleneck, not everything.** Know which resource saturates first: DB connections, CPU, memory, a third-party rate limit, or a single lock.
- **Make performance observable.** Emit latency histograms, saturation metrics, and traces at every boundary from day one.

## Security and privacy principles

- **Secure by default.** New endpoints, buckets, and features start closed. Access is granted explicitly.
- **Authorize at the boundary that owns the data.** Never rely on the caller, the UI, or an upstream gateway alone to enforce access.
- **Least privilege everywhere.** Give users, services, DB accounts, CI tokens, and cloud roles only what they need.
- **Defense in depth.** Assume any single layer can fail. Validate input, encode output, isolate tenants, and encrypt sensitive data.
- **Keep untrusted input away from powerful interpreters.** Use parameterized queries and safe APIs, and never build shell commands, templates, or file paths from user data.
- **Minimize the attack surface.** Fewer public endpoints, fewer dependencies, fewer admin backdoors, and no debug routes in production.
- **Keep secrets out of code and images.** Use a secret manager with rotation, and short-lived credentials where possible.
- **Log security events.** Record auth failures, permission denials, and admin actions, with the actor attached and secrets left out.
- **Fail closed.** Missing config, an unreachable policy service, or an expired key denies access; it never grants it.
- **Collect less.** Every field of personal data is a liability: breach exposure, deletion work, legal duties. Don't collect it without a purpose, and delete it when the purpose ends.
- **Every copy counts.** Personal data in a cache, search index, event stream, log, backup, or third party is still personal data, with the same access rules and deletion duty.
- **Privacy by default.** The most private setting is the default; sharing, tracking, and telemetry are opt-in.

## General principles

- **Cohesion over layering.** Group code by what changes together (a feature or domain), not by technical role.
- **Depend toward stability.** Volatile code should depend on stable abstractions, never the reverse. Keep core domain logic free of framework and I/O.
- **Deep modules.** Prefer small interfaces that hide substantial complexity over many shallow pass-through layers.
- **One writer per piece of data.** Shared mutable state across boundaries, especially a shared database between services, is the most common source of architectural rot.
- **Monolith first.** Split into services only for independent scaling, independent deployment by separate teams, or hard isolation needs. Every split adds network latency and a new trust boundary.
- **Make illegal states unrepresentable.** Use types and schema constraints to enforce invariants instead of scattered runtime checks.
- **Add abstractions late.** Wait for two or three concrete cases before abstracting.

## Red flags to call out

**Performance**
- Synchronous call chains across services on a user-facing path
- N+1 access patterns baked into the API or data model
- Unbounded queries, queues, caches, or fan-out
- One database serving both OLTP traffic and heavy analytics
- No timeouts, or retries without backoff
- Caches added to hide a design problem, with no invalidation story

**Security**
- Authorization done only in the UI or the API gateway
- Internal services that trust any caller on the network
- Shared credentials between services or environments
- Tenant isolation that depends on every query remembering a `WHERE tenant_id = ?`
- Secrets in config files, images, or environment dumps
- Admin or debug functionality reachable from the public internet
- Services that fetch user-supplied URLs with no egress restriction

**Privacy**
- Personal data with no stated purpose or retention period
- Personal data in logs, URLs, analytics events, or error reports
- Event streams or caches that copy personal data with no deletion path
- "Delete account" that leaves data in backups, search indexes, or third parties without saying so
- Production data copied into dev, staging, or test environments
- Third parties receiving more data than their function needs

**General**
- Circular dependencies between modules or services
- A "utils", "common", or "shared" module that everything imports and that keeps growing
- Distributed monolith: services that must deploy together
- Business logic in controllers, ORM models, or UI components
- The same concept modeled differently in several places with manual syncing

## Refactors and migrations

- Prefer **strangler fig** over big-bang rewrites: route new behavior through the new structure and migrate callers incrementally.
- Every step must leave the system shippable and tested.
- Add characterization tests around behavior you're about to move before you move it.
- Benchmark the critical paths before and after each step so a migration doesn't quietly make things slower.
- Keep the security checks working throughout the migration. Moving a route or splitting a service is when authorization checks most often get lost.
- Define the "done" state and the point where the old path gets deleted. Half-migrations that never finish are worse than either end state.

## Output checklist

- [ ] Recommendation is grounded in the actual code and stated constraints
- [ ] Architecture drawn on the review page, checked for rendering, shown to the user, and approved before implementation
- [ ] Performance requirements are numeric, with a latency budget and capacity estimate
- [ ] Data inventory written: class, purpose, every copy, readers, retention and deletion
- [ ] Trust boundaries drawn; STRIDE and LINDDUN threats addressed per boundary, each control with how it's verified
- [ ] Identity, authorization, tenant isolation, secrets, and data-leaving-the-system decided before options were compared
- [ ] Legal or regulatory requirements researched with sources, not assumed
- [ ] Key decisions are named, with alternatives and trade-offs
- [ ] Failure modes and data ownership are explicit
- [ ] There is an incremental path from the current state
- [ ] Complexity is proportional to the problem's real scale
