# Protocol templates

Use these formats so every agent's output can be merged, counted, and cited. Keep them short; the structure does the work.

## Agent brief

Every subagent gets a brief like this. It must be self-contained: the agent knows nothing else.

```markdown
# Role: <role name>
<paste the role card from references/roles.md>

## Conduct
<paste section 5 of SKILL.md>

## The project
Goal: <one paragraph, in the user's terms>
User priorities and constraints: <list>
Definition of done: <list>
Repository: <path>. Read first: <specific files, docs, conventions files>

## Decided so far (don't relitigate without new evidence)
- <gate>: <decision, one line each, with link to decisions.md>

## Your task
<exactly what to produce, for which gate, and which files you own (implementers)>

## Constraints
- Stay within: <scope>
- Do not: <e.g. edit files outside X, add dependencies, contact external services>
- Skills to follow: <architecture / code-review / security-audit / ...>

## Output
<the template below that applies: review, response, artifact>
Write it to: <.team/reviews/G5-r1-security.md>, and return a summary of at most 10 lines.
```

## Review (any reviewer, any gate)

```markdown
# Review: <gate> round <n>, <role>
Verdict: APPROVE | APPROVE WITH COMMENTS | REQUEST CHANGES

## Verified
- Read: <files / sections>
- Ran: `<command>` -> <result, e.g. "142 passed, 0 failed">
- Checked: <acceptance criteria / diagram boundaries / tokens>

## Findings
### F1 [BLOCKING | MAJOR | MINOR | NIT] <one-line title>
Where: <file:line, section, or criterion ID>
Evidence: <test output, quoted code, number, attack or failure scenario, violated requirement>
Impact: <what goes wrong, for whom>
Resolve by: <concrete fix, or the condition that would satisfy this reviewer>

### F2 ...

## Out of scope / follow-ups (never blocking)
- <idea>
```

Only BLOCKING findings stop a gate. A review with REQUEST CHANGES must contain at least one BLOCKING finding; an APPROVE must contain none.

## Author response

```markdown
# Response: <gate> round <n>
F1 FIXED: <what changed, where> Proof: `<command>` -> <result>
F2 DISPUTED: <why, with evidence: test, doc link, measurement, code reference>
F3 NEEDS DECISION: <the product or priority question, the options>
F4 (comment) ACKNOWLEDGED, not changing: <one-line reason>
```

## Re-review

Sent to the same reviewer agent that raised the finding (continued, not fresh).

```markdown
Re-review of your findings from round <n>. The author's response is below and the code is updated.
For each of your blocking findings, reply: RESOLVED, STILL BLOCKING (say what's still wrong,
with evidence), or WITHDRAWN (say what changed your mind). Also check whether the fixes
introduced new problems in your area. Don't raise new issues outside your role.
```

## Dispute record (in decisions.md)

```markdown
## D<n>: <question>  (gate <G>, <date>)
Position A (<role>): <2-3 sentences + evidence>
Position B (<role>): <2-3 sentences + evidence>
Fact-finding: <experiment run and result, or "not resolvable by experiment">
Decision: <what we do>
Decided by: <evidence | priority rule #k | user>
Dissent: <role, one line>; revisit if <condition>
```

## Gate record (in decisions.md)

```markdown
## Gate <G> passed (<date>), <rounds> rounds
Artifact: <path / summary>
Approved by: <roles, each with its verification line>
Blocking findings: <raised> raised, <resolved> resolved, <escalated> escalated
Open comments carried forward: <list or none>
```

## Status update to the user (one per gate)

```
G2 Design: passed after 2 rounds. Security's token-scope finding was fixed; Perf and the
Architect disagreed on caching and the team settled it with a benchmark (no cache: p99 40 ms,
under the 100 ms target). Design page is ready for your approval: <path>.
```

## Escalation to the user (after the round cap, or a product call)

```markdown
The team can't settle this without you:

**<question>**
- Option A (<role>): <one sentence>; trade-off: <one sentence>
- Option B (<role>): <one sentence>; trade-off: <one sentence>
- My recommendation: <A or B>, because <reason tied to your stated priorities>
```
