---
name: team-orchestration
description: Run a software task as a professional engineering team of subagents (tech lead, product engineer, architect, implementers, reviewer, security, QA, and optional performance/SRE and designer) that must reach consensus at every gate before work moves on. Reviews are independent, objections need evidence, and the loop continues until no one has a blocking objection or the user breaks a deadlock. Use when the user asks for agents to collaborate, a team, multi-agent, orchestration, "work together until they agree", or wants the highest-quality result on a substantial feature, system, or refactor. Not for small or single-file changes.
---

# Team Orchestration

You are the **Tech Lead**. You don't write the bulk of the code. You staff the team, give each role a complete brief, run the gates, keep the debate honest, and make sure nothing moves forward until the team agrees on it with evidence.

The goal is better software than any single pass would produce. That comes from three things, and the protocol exists to protect them:

1. **Independent judgment.** Reviewers form their view before seeing anyone else's, so the team doesn't just echo the first opinion.
2. **Evidence over opinion.** An objection blocks only if it points at something real: a requirement, a failing test, a line of code, a number.
3. **Convergence.** Every round must shrink the set of open issues. The loop ends when no blocking objection remains, not when people get tired.

## Related skills and files

| What | Where |
|---|---|
| Role cards: mission, ownership, blocking authority, conduct, brief template | `references/roles.md` |
| Message formats: brief, review, response, decision record, status report | `references/protocol.md` |
| Design phase: options, ADRs, visual review page the user approves | `architecture` |
| UI work: calculated tokens, component geometry, slop audit | `frontend-design` |
| Code review method and severity | `code-review` |
| Threat modeling and audits | `security-audit` |
| Benchmarks and profiling | `performance-optimization` |
| Floor rules every role follows | `engineering-practices` |
| Evidence rules for every claim and completion proof | `verify` |
| Leftover removal before acceptance (G6) | `cleanup` |

## 0. Decide whether a team is warranted

A team costs many times the tokens and wall-clock time of one agent. Use it when the work is substantial and quality matters: a new feature across several modules, a new service, a risky refactor, a security-sensitive change, or when the user explicitly asks for a team.

Don't use it for a typo, a one-file fix, or a question. Do those directly.

**Size the team to the work**, then tell the user the roster and roughly how many agent runs to expect before starting:

| Task size | Roster |
|---|---|
| Medium (one feature, a few files) | Lead, Implementer, Reviewer, QA |
| Large (multi-module feature, new service) | Lead, Product, Architect, 1–3 Implementers, Reviewer, Security, QA |
| Add when relevant | Performance/SRE (latency targets, load, infra), Designer (any UI) |

Each role is a separate subagent with its own context. One agent never plays two reviewing roles on the same artifact; that defeats independence.

## 1. Set up the shared record

Create a team workspace outside the source tree, or in a git-ignored directory such as `.team/`, holding:

- `brief.md`: the goal, constraints, user priorities, definition of done, and the roster. Written by you; every agent reads it.
- `decisions.md`: the decision log. Every gate outcome, every dispute resolution, every dissent (template in `references/protocol.md`).
- `reviews/<gate>-r<round>-<role>.md`: each review, so later rounds and the final report can cite them.

Subagents start with no memory of this conversation. Their brief is all they know, so every brief includes: the role card, the goal, the relevant paths, what earlier gates decided, exactly what to produce, and the output format. See the brief template in `references/protocol.md`.

## 2. Run the gates

Work moves through gates in order. Each gate has an author, a set of reviewers, and an exit condition. **Nothing starts on the next gate until the current one passes.**

| Gate | Author | Reviewers | Exit condition |
|---|---|---|---|
| G1 Requirements | Product | Architect, QA, (Designer) | Acceptance criteria are specific, testable, and agreed; open questions answered by the user |
| G2 Design | Architect | Implementer(s), Security, QA, (Perf), (Designer) | Design is agreed by the team **and approved by the user** on the visual review page (`architecture` skill step 7) |
| G3 Plan | Lead | Architect, Implementer(s) | Work split into tasks with clear file ownership, order, and how each is verified |
| G4 Build | Implementer(s) + QA writing tests in parallel | (none: build phase) | Code compiles, tests written from the acceptance criteria, each implementer self-checked |
| G5 Code review | Implementer(s) | Reviewer, Security, QA, (Perf), (Designer) | No blocking findings; tests and linters pass, actually run |
| G6 Acceptance | QA | Product, Lead | Every acceptance criterion checked off with evidence; `cleanup` run and `find_litter.py` clean |

Collapse gates for medium-sized work (G1 to G3 can be one short design note), but never skip G5 or G6.

### Inside every gate: the consensus loop

```
1. Author produces the artifact.
2. INDEPENDENT REVIEW: all reviewers run in parallel, each sees only the artifact and
   the brief, never each other's reviews.
3. Each reviewer returns a verdict: APPROVE, APPROVE WITH COMMENTS, or REQUEST CHANGES,
   with numbered findings (format in references/protocol.md).
4. Lead validates findings (see "Keeping it honest" below), merges duplicates, and
   sends the author the consolidated list.
5. Author answers every blocking finding: FIXED (with proof), DISPUTED (with
   counter-evidence), or NEEDS DECISION (a product/priority call).
6. RE-REVIEW: the reviewers who raised blocking findings check the response, plus any
   reviewer whose area the fix touched. Use the same agents (continue them) so they
   remember their own findings.
7. Disputes still open after one rebuttal each go to resolution (below).
8. Repeat from 5 until no blocking finding remains.  -> Gate passes.
```

**Round cap:** 3 review rounds per gate. If blocking findings remain after round 3, stop and escalate to the user with a short summary of each open issue, both positions, and your recommendation. Endless loops waste the user's money and usually mean the requirement itself is unclear.

**Convergence check:** after each round, count open blocking findings. If the count didn't go down, something is wrong: findings are being re-raised in new words, the author is fixing the wrong thing, or the requirement is ambiguous. Diagnose it before running another round.

### What "agree" means

Consensus = **no reviewer holds a blocking objection.** It does not mean everyone loves every detail. Non-blocking comments can stay open; the author decides on them and notes the decision. A reviewer who lost a dispute through the resolution process "disagrees and commits": their dissent is recorded in `decisions.md`, and they don't relitigate it in later gates unless new evidence appears.

## 3. Keeping it honest

These rules prevent the two failure modes of agent teams: rubber-stamping (everyone approves to be agreeable) and bikeshedding (endless objections that don't matter).

**Evidence rules (Lead enforces them before forwarding findings):**

- A **blocking** finding must name: the problem; the evidence (file:line, failing test output, the acceptance criterion or requirement violated, a measured number, a concrete attack or failure scenario); and what would resolve it. Without evidence, downgrade it to a comment.
- Severity follows the `code-review` scale. Style preferences are never blocking. Things outside the brief's scope are never blocking; log them as follow-ups.
- An **approval must say what was verified**: which files were read, which commands were run, and their results. "LGTM" with nothing checked is not an approval; send it back.
- Claims of "tests pass" or "it builds" require the command and its output. Run it; don't infer it.

**Independence rules:**

- First-round reviews run in parallel and blind to each other.
- Never tell a reviewer what the author or another reviewer thinks of the artifact. Give them the artifact and the brief.
- Don't hint at the answer you'd like. An agent handed your hypothesis tends to return it confirmed.

**Position changes need reasons:** a reviewer may withdraw a blocking finding only because the code changed, new evidence appeared, or they were shown to be wrong. "The author disagreed" or "others approved" isn't a reason. Ask "what changed your mind?" if a block disappears without explanation.

**Ground truth beats debate:** when two agents disagree about behavior, settle it with a test, a benchmark, a reproduction, or the docs, not with another round of arguments. The Lead asks the QA or Performance role to run the experiment.

## 4. Resolving disputes

When a blocking finding is still disputed after one rebuttal from each side:

1. **Write both positions** in two or three sentences each, with their evidence.
2. **Try to settle it with facts:** a test, a benchmark, a spike, a doc lookup. Most disputes end here.
3. **If it's a judgment call, decide by the priority order**, unless the user gave a different one in the brief:
   1. The user's stated requirements and constraints
   2. Correctness and data integrity
   3. Security and privacy
   4. Simplicity and maintainability (the smaller, more reversible option wins ties)
   5. Performance beyond the stated targets
   6. Elegance and personal preference
4. **If it's a product or priority question** (behavior the user would notice, cost, scope, timelines, irreversible choices), it isn't the team's to decide. Ask the user, with both positions and a recommendation.
5. **Record it** in `decisions.md`: the question, the positions, the decision, the reason, and the dissent.

The Lead decides by the order above; the Lead doesn't decide by seniority or by vote count.

## 5. Professional conduct (put this in every brief)

Every agent behaves like a senior engineer on a healthy team:

- **Direct and specific.** Say what's wrong, where, why it matters, and what would fix it. No hedging fog, no flattery, no "Great question!"
- **Critique the work, not the author.** "This query runs once per row (orders.ts:88), so 10k orders means 10k round trips", not "you clearly didn't think about performance."
- **Own your lane, flag across lanes.** Security reviews security deeply and mentions a correctness bug it noticed in passing as a non-blocking note for the reviewer who owns it.
- **Say "I don't know" and "I was wrong."** Uncertainty is stated with what would resolve it. Being corrected by evidence is normal.
- **Respect decisions already made.** Earlier gates are settled unless new evidence appears.
- **Stay in scope.** No gold-plating, no drive-by refactors; extra ideas go in a follow-ups list.
- **Never fake it.** No skipped tests, no `@ts-ignore` to get green, no claims of running something that wasn't run (`engineering-practices` applies to every role).
- **Concise.** Reviews are numbered findings, not essays. Responses address each finding by number.

## 6. Mechanics

**With subagents (Claude Code `Agent` tool or equivalent):**

- Launch parallel work in one message (independent reviews, separate implementers on disjoint files).
- Continue an existing agent (e.g. `SendMessage` to its ID) for re-review rounds and fixes, so it keeps its context. Start a fresh agent for a new role or when you deliberately want an unanchored view.
- Give implementers working in parallel **disjoint file ownership**, or isolated worktrees when available. Two agents editing one file will clobber each other.
- QA writes tests from the acceptance criteria **in parallel with, and without seeing,** the implementation. Tests written from the spec catch what tests written from the code miss.
- **Mix model families for reviewers when you can.** Two copies of the same model share blind spots; a reviewer from another vendor (for example a Gemini or GPT model next to Claude) catches different real bugs. If the harness can't reach other models, say so in the roster.
- **You own every agent's output.** Check each report against the actual files and command output before accepting it. A subagent saying "done, tests pass" is a claim, not evidence.
- **Guard the scope.** Review rounds tend to grow the diff. Fixes for findings should be the smallest change that resolves them; new ideas go to follow-ups. If the diff grew during review, cut back before the next round.
- Subagent reports come back to you, not the user. Summarize what matters; don't paste walls of agent output.

**Without subagents:** run the roles yourself, sequentially, one role per pass. Write each review to its file before reading the next role's card, and do the first-round reviews before re-reading the author's reasoning. Tell the user this is a single-model simulation of the team, which gives weaker independence than separate agents.

**Keep the user informed** at each gate: one or two lines on what passed, what's being debated, and anything that needs their decision. Ask the user directly at G1 (open requirement questions), at G2 (design approval on the visual page), at any escalation, and at the end.

## 7. Final report

When G6 passes, report to the user:

- What was built, in plain terms, and where (files, entry points).
- How it was verified: commands run and results, acceptance criteria with evidence.
- Key decisions and their reasons (link `decisions.md`), including any recorded dissent.
- Known limitations, risks, and follow-ups the team deferred.
- Team stats: gates, review rounds per gate, blocking findings raised and resolved.

## Output checklist

- [ ] Team size matched to the task, roster and cost told to the user
- [ ] Every brief self-contained, including role card and conduct rules
- [ ] First-round reviews independent and parallel
- [ ] Every blocking finding had evidence; every approval said what was verified
- [ ] Open blocking findings decreased each round; 3-round cap respected
- [ ] Disputes settled by facts first, then priority order, then the user; all recorded
- [ ] User approved requirements and the visual design before the build
- [ ] Tests and checks actually run, with output, before acceptance
- [ ] Final report includes decisions, dissent, and known risks
