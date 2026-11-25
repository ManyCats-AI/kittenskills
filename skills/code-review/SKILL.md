---
name: code-review
description: Review code changes (a diff, branch, PR, or set of files) for correctness bugs, security issues, performance problems, maintainability, and missing tests, then report a plain-language summary of what changed and why, followed by prioritized, actionable findings. Use when the user asks to review, check, or give feedback on code or a pull request, or before merging significant changes.
---

# Code Review

The goal is to catch the problems that would hurt in production and to say nothing that wastes the author's time. One real bug is worth more than twenty style nits.

## Workflow

### 1. Establish scope and intent

- Find the change: `git diff`, `git diff main...HEAD`, `gh pr diff <n>`, or the files the user named.
- Understand **what the change is trying to do**: read the PR description, commit messages, and linked issues. A review that misunderstands intent produces wrong findings.
- Read the project's conventions (`CLAUDE.md`, `CONTRIBUTING.md`, linter config, neighboring code) so you can judge the change against local norms rather than personal taste.

### 2. Read with context, not just the diff

A diff shows what changed, not what it broke. For every non-trivial hunk:

- Open the full surrounding function and its callers.
- Check how changed functions, types, or signatures are used elsewhere (`grep` for every call site).
- Check what the changed code relies on: preconditions, invariants, nullability, ordering, locking.
- **Look where grep stops.** Callers are the easy part. Also follow what a symbol search misses: JSON shapes an API returns, database columns, wire formats, another language or service reading the same data, feature flags, config keys, code run by naming convention, and the source of the pinned library version the change calls into.
- **Find the one fact the change is safe because of.** Most risky-looking changes are safe because of a single fact ("this only drops cache entries that are already dead"). Name it, then check it against the code. If it holds, whole classes of risk clear at once; if it doesn't, that's your top finding.

### 3. Hunt for defects, in priority order

**Correctness (highest priority)**
- Off-by-one errors, wrong boundary conditions, inverted conditionals
- Null/undefined/empty handling; missing error paths; swallowed exceptions
- State mutations with unintended sharing (aliasing, mutable defaults, shared caches)
- Race conditions, non-atomic check-then-act, missing awaits, unhandled promise rejections
- Resource leaks: unclosed files, connections, listeners, timers
- Broken callers: changed signatures, return shapes, or semantics without updating every use
- Incorrect assumptions about external data: encoding, time zones, locale, integer overflow, float precision

**Security**
- Untrusted input reaching queries, shells, file paths, templates, redirects, or deserializers
- Missing authorization checks on new endpoints or actions
- Secrets in code, logs, or error messages
- See the `security-audit` skill for a deeper pass when the change touches auth, crypto, or input handling.

**Performance**
- N+1 queries, queries in loops, or missing indexes for new access patterns
- Unbounded work on user input: no pagination, no size limits, whole files or tables loaded into memory
- Accidental O(n²) behavior on collections that grow
- Remote calls without timeouts; new synchronous calls on hot paths
- Caches without invalidation or without user or tenant scoping in the key
- For changes made specifically to speed things up, ask for benchmark numbers. See the `performance-optimization` skill.

**Data and compatibility**
- Schema migrations that lock tables, lose data, or can't run alongside old code during deploy
- Breaking changes to public APIs, wire formats, config, or CLI flags
- Changed defaults that silently alter behavior for existing users

**Tests**
- Is the new behavior tested? Do tests assert outcomes, or only that code ran?
- Are the edge cases you found above covered?
- Were tests weakened, skipped, or rewritten to match buggy output?
- Would each test fail if the behavior broke? (See `testing` for the checks.)

**Practices** (see `engineering-practices`)
- Scope creep: unrelated changes bundled into the diff
- Faked success: weakened or deleted tests, suppressed errors, lint or type ignores, hardcoded outputs
- Insecure defaults: new endpoints without auth, things bound to `0.0.0.0`, public resources, debug left on, secrets in code
- New dependencies that aren't justified or verified

**Maintainability (lower priority, only when it matters)**
- Duplicated logic that will drift, or reimplementing something that already exists in the codebase
- Misleading names, or comments that contradict the code
- Unnecessary complexity: abstractions with one use, dead code, speculative generality

### 4. Verify before reporting

For each candidate finding, push it as far down this ladder as is cheap, and say where it stopped:

1. **Asserted**: you said so. Not enough to report as a bug.
2. **Pointed at**: a real `file:line`, or the library's own source.
3. **Traced**: you walked a concrete input or state through the code to the wrong result.
4. **Ran**: a test, script, or command against the real code shows the wrong output. Paste the command and its output.

Blocking findings should reach level 3 or 4. Drop findings that stay at level 1, or ask them as questions. For large or risky changes, write the failing test or repro for each blocking finding: it proves the bug and becomes the regression test for the fix.

False positives destroy trust in a review. When unsure, ask a question instead of asserting a bug.

### 5. Report

Every review ends with a **change summary** first, so anyone (including someone who never opens the diff) knows what the change does and why. Then come the findings, grouped by severity with the most important first. If fixes were applied during the review, finish with a summary of those too.

Write the summaries in plain language (→ `plain-speech`). Explain *why* in terms of behavior and risk, not just mechanics. "Login now locks the account after 5 failed tries, so passwords can't be guessed" beats "added a counter to auth.ts."

```markdown
## What this change does
Two to four sentences: the purpose of the change and its overall effect on the system.

## Changes and why
| Area / file | What changed | Why |
|---|---|---|
| `src/auth/login.ts` | Locks the account after 5 failed attempts | Stops password guessing |
| `migrations/0042_*.sql` | Adds a `failed_attempts` column | Stores the counter |

Notable side effects: behavior changes users will notice, config or migration steps, breaking changes.

## Verdict
One or two sentences: overall assessment, the top risk, and whether it's ready to merge.

## Blocking
1. **path/to/file.ts:42: <one-line claim>**
   Failure scenario: <concrete input/state → wrong result>.
   Suggested fix: <specific change, with code if short>.

## Should fix
...

## Nits (optional, keep short)
...

## Questions
...

## Fixes applied during review (only if you changed code)
| Finding | What was changed | Why this fixes it | How it was verified |
|---|---|---|---|
| Blocking #1 | Added an owner check before loading the invoice | Users could open other people's invoices by changing the ID | New test `invoice_access.test.ts` fails before the fix, passes after |

Findings left unfixed, and why.
```

Base the change summary on the actual diff, not just the PR description. If the two disagree (for example, the description says "refactor" but the behavior changed), say so as a finding.

Rules for findings:
- Anchor every finding to `file:line`.
- State the **failure scenario**, not just a principle ("this could be null" → "when `user.org` is absent for SSO users, line 42 throws").
- Propose a fix. If several fixes are possible, recommend one.
- Don't restate what the code does, and don't praise filler.
- Leave out formatting nits that a linter or formatter would catch.

## Calibration

- **Small, low-risk change:** a quick pass with a few high-confidence findings, or "no issues found" is a fine result.
- **Large or risky change** (auth, payments, migrations, concurrency, public API): read every hunk with full context and check every caller.
- If the change is too large to review well, say so and suggest how to split it.
- **High stakes** (security, data loss, concurrency, money): if other models are available, get an independent review from a different model family too, given only the diff and the intent. Different models catch different real bugs.
- **When fixing findings**, make the smallest fix: prefer deleting or narrowing code over adding a lock, cache, helper, or option. If review fixes grew the diff, cut back before re-reviewing. Agreeing with a finding just to end the review is not a fix; push back with evidence when it's wrong.
