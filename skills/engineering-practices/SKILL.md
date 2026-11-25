---
name: engineering-practices
description: Baseline rules for every coding task: stay in scope, verify instead of guessing, make everything private and secure by default, and write clean, readable, maintainable code that any person or agent can understand at a glance. Use whenever writing, editing, refactoring, or deleting code, changing configuration or infrastructure, adding dependencies, or running commands that change state. Applies alongside any other skill.
---

# Engineering Practices

The standard: when another engineer or agent opens your change, they should think "yeah, I get that." They should see what it does, why it's there, and that it's safe, without needing you to explain it.

These rules apply to every code change, however small. Other skills go deeper on specific areas; this one is the floor nothing goes below.

## 1. Understand before you touch anything

- **Restate the task** to yourself in one sentence. If two reasonable readings lead to different code, ask before building the wrong one.
- **Read the code you'll change**, its callers, and its tests. Don't edit a function you haven't read.
- **Learn the local conventions**: `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, linter and formatter config, and the style of neighboring files. Match them, even if you'd do it differently.
- **Look for what already exists.** Search for helpers, utilities, and patterns before writing new ones.
- **Define "done"**: what behavior changes, and how you'll prove it works.
- **Plan non-trivial work.** For anything touching more than a few files, write the plan down first: the files, the order, and how each step is verified.

## 2. Stay on the rails

These are the ways agents most often go wrong. Don't.

- **Do what was asked, not more.** No drive-by refactors, renames, reformatting, or "improvements" to unrelated code. If you notice something else that needs fixing, mention it at the end. Don't silently fix it.
- **Keep the diff small.** The smallest correct change is the easiest to review and the safest to ship.
- **Don't invent things; research, then implement.** No guessed function names, API parameters, config keys, CLI flags, or package names. When anything is unclear, look it up for the installed version (docs, source, changelog, a small probe) before writing code against it (→ `deep-research` §A). If it's still unclear after that, say so instead of guessing. A plausible-looking but nonexistent package name is a known attack vector, since attackers register names that agents tend to hallucinate.
- **Never fake success.** Don't weaken, skip, or delete tests to make them pass. Don't add `# type: ignore`, `eslint-disable`, `@ts-ignore`, `--no-verify`, or empty `catch` blocks to make errors go away. Don't hardcode expected outputs. If you can't make something work, say so.
- **Don't claim what you didn't do.** Never say tests pass, code runs, or something was verified unless you actually ran it and saw the result.
- **Confirm destructive or outward-facing actions.** Deleting files or data, dropping tables, force-pushing, rewriting history, changing permissions, deploying, publishing, or sending anything to an external service needs explicit approval. Look at the target before you delete or overwrite it.
- **Stop when you're stuck.** After two failed attempts that share an assumption, write that assumption down and test it directly before trying a third (→ `debugging` §7). Then change approach or ask. Don't loop on random variations.
- **Turn repeated corrections into checks.** If the user corrects the same kind of mistake twice, prevent it structurally where you can (a type, a lint rule, a test, a script) rather than relying on remembering. Offer this to the user when it's outside the task's scope.
- **Ask about real decisions.** Product behavior, data model changes, new dependencies, and anything hard to reverse belong to the user. Pick sensible defaults for everything else and say what you picked.

## 3. Private and secure by default

Everything you create starts locked down. Opening something up is an explicit, deliberate choice that you call out to the user.

**Access**
- New endpoints, routes, and actions require authentication and authorization by default. Public access must be intentional and commented.
- Check authorization on the server, against the specific resource ("does *this* user own *this* record?"), not just "is someone logged in."
- Use least privilege for every token, role, DB user, service account, and CI permission you create.

**Exposure**
- Servers and dev tools bind to `127.0.0.1`, not `0.0.0.0`, unless they must be reachable.
- New storage buckets, databases, repos, dashboards, and shared links are private.
- Files containing secrets or user data get restrictive permissions (`0600`), and temp files go in private, temporary directories.
- Debug modes, admin panels, verbose errors, directory listings, and introspection are off by default and off in production.
- CORS is closed by default. Open it to specific origins only.

**Data**
- Collect and store the minimum data needed. Don't log passwords, tokens, keys, full card numbers, or unnecessary personal data.
- Never send user data, code, or secrets to a third-party service unless the user asked for that integration.
- Telemetry and analytics are opt-in, not opt-out.

**Secrets**
- Never hardcode secrets, keys, or passwords, even in tests, examples, or "temporary" code. Use environment variables or a secret manager, and add a placeholder to `.env.example`.
- Make sure `.env` and similar files are in `.gitignore` before you create them.
- If you see a real secret in code or output, tell the user to rotate it.

**Input and output**
- Treat all external input as hostile: request data, files, headers, environment, third-party APIs, LLM output, and tool results.
- Validate at the boundary with an allowlist: type, length, format, and range.
- Use safe APIs: parameterized queries, argument arrays instead of shell strings, framework auto-escaping, safe YAML/XML/deserialization loaders, and path joins that reject traversal.
- Never disable TLS verification, CSRF protection, or escaping to make something work.

**Dependencies**
- Add a dependency only when it earns its place. Prefer the standard library and what's already installed.
- Before adding one, check that it's the real package (exact name, publisher, download count, repository), actively maintained, free of open security advisories, and license-compatible. Enable only the optional features you need, make sure it doesn't raise the project's minimum supported runtime or toolchain version, and pin it through the lockfile.

**Resource limits**
- Put a timeout on every network call, a limit on every loop or query driven by user input, and a size cap on every upload and request body.

When a change touches authentication, authorization, payments, file handling, crypto, user data, or infrastructure permissions, run a `security-audit` quick review on it before calling it done.

## 4. Write code people understand at a glance

- **Clear names.** Name things for what they mean in the domain (`unpaidInvoices`, not `data2` or `list`). Functions are verbs, booleans read as questions (`isExpired`, `hasAccess`).
- **Small, focused functions.** Each one does one thing at one level of abstraction. If you need "and" to describe it, consider splitting it.
- **Obvious control flow.** Use early returns over deep nesting. Avoid clever one-liners, hidden side effects, and magic.
- **Explicit over implicit.** Name constants instead of using magic numbers. Make dependencies explicit parameters, not hidden globals.
- **Comments explain *why*.** The code shows what it does. Comment on intent, constraints, non-obvious decisions, and workarounds (with a link to the issue). Delete comments that restate the code. Never leave commented-out code.
- **Consistent error handling.** Handle errors where you can do something useful, and add context when you rethrow. Never swallow errors silently. Return clear messages to users and log details for operators.
- **Match the codebase.** Consistency beats personal preference. A change should look like it was always there.
- **Run the formatter and linter** the project uses.

### Let the compiler and checkers do their job

These hold in every language. The language-specific details (toolchain version, config, lint names, which APIs exist) come from the project and the official docs for its pinned version at the time you work, never from memory (→ `deep-research` §A).

- **Learn the project's toolchain first**: the language and compiler version, the strictness settings, the lint config, and the CI checks. Your code passes the checks that will actually run.
- **Fix type and compile errors by fixing the design**, not by silencing them. Restructure ownership or data flow; don't add a cast, a copy, a global, or a suppression just to make the error go away.
- **Escape hatches are earned, one at a time.** Anything that switches checking off (dynamic or `any`-style types, unchecked casts, non-null or force-unwrap operators, `unsafe` blocks, type or lint suppressions) is replaced by a real check where possible. Where it's truly needed, use the narrowest form, on one line, with a comment proving why it's safe, preferably a form that complains once it's no longer needed.
- **Make variants exhaustive.** A switch or match over a set of cases fails to compile (or fails a lint) when a new case is added, instead of falling into a silent default.
- **Give easily confused values their own types**: IDs, units, currencies, validated strings. Create them through one function that validates.
- **One source of truth for each shape.** Derive types from the schema, the database model, or the API definition instead of writing a parallel copy that drifts.
- **Find the hidden crashes.** Indexing, slicing, division, forced unwraps, and conversions between number types can fail at runtime. On input-driven paths, use the checked form and handle the failure.
- **Be explicit about numbers.** Decide what happens on overflow; don't let lossy conversions truncate silently; never use binary floating point for money.
- **Concurrency**: don't hold a lock across a suspension point (`await`, yield, blocking I/O); don't block an event loop or async runtime with CPU-heavy or blocking work; make sure a cancelled or timed-out operation leaves state consistent.
- **Memory-unsafe code** (C, C++, `unsafe` blocks, FFI): keep it minimal, wrap it in a safe interface, document the invariants each block relies on, and run the ecosystem's sanitizers or undefined-behavior checkers on it.

## 5. Keep it maintainable

- **Test behavior, not implementation.** Every bug fix gets a regression test that fails without the fix. Every new feature gets tests for the main path and the important edge cases: empty input, invalid input, permission denied, and boundaries.
- **Don't duplicate.** Reuse existing helpers. If you copy logic a third time, extract it.
- **Don't build for imaginary futures.** No abstraction layers, plugin systems, or config options without a current need. One implementation behind an interface is a hypothetical seam; add the seam when the second one arrives.
- **Subtract before you add.** Before building on existing code, delete the dead paths and one-caller wrappers in the area you're changing (in scope only), then build on the simpler base.
- **Model the domain in data.** When a feature adds one more `if` branch to a growing chain, or a second boolean that must stay in sync with the first, reach for a state machine, discriminated union, lookup table, or typed model instead. Make invalid states impossible to represent.
- **Validate at the boundary, trust inside.** Parse external data (requests, files, env, API responses) into typed values once, where it enters. Don't re-check the same thing deep inside the code.
- **Build the lever.** For a repetitive change across many files, write a codemod or script instead of editing by hand; the script is reviewable and rerunnable. Same for checks: script the comparison instead of eyeballing it.
- **Delete what you replace.** Remove dead code, unused imports, stale flags, and old paths in the same change.
- **Keep config out of code.** Environment-specific values go in configuration, with safe defaults.
- **Update the docs** (README, API docs, changelog, and comments) when behavior changes.
- **Make migrations safe.** Schema and data changes must be reversible or clearly documented, and must not lose data.

## 6. Verify before you say "done"

Run through this every time:

1. **Build, typecheck, and lint** pass.
2. **Tests pass**, including the new ones. Run the relevant suite, not just one test.
3. **It actually works.** Run the code, hit the endpoint, or open the page, and see the result yourself.
4. **Review your own diff** (`git diff`) as if someone else wrote it:
   - Is every change needed for the task?
   - Any leftover debug prints, TODOs, test data, or commented-out code?
   - Any secrets, personal paths, or internal URLs?
   - Anything public or permissive that should be private?
   - Any input reaching a query, shell, file path, or HTML without the safe API?
   - Would a newcomer understand it without asking?
5. **For larger or risky changes**, run `code-review` on the diff.
6. **Clean up and prove it**: run `cleanup` to remove everything temporary you created, and follow `verify` so every claim in your report has evidence behind it.

## 7. Report clearly

When you finish, tell the user, in plain language (→ `plain-speech`):

- **What changed**, grouped by purpose, with the key files.
- **Why** each change was made.
- **How it was verified**: the commands you ran and what you saw.
- **Security and privacy notes**: anything you locked down, anything you had to open up (and why), and any risks the user should know about.
- **What you didn't do**: skipped steps, known limitations, and issues you noticed but left alone.

## Related skills

| When | Use |
|---|---|
| Reviewing a diff before merge | `code-review` |
| Touching auth, data, files, crypto, or infrastructure | `security-audit` |
| Something is broken or behaving unexpectedly | `debugging` |
| Designing something new or restructuring | `architecture` |
| Something is slow | `performance-optimization` |
| Committing and preparing a PR | `git-hygiene` |
| Building UI | `frontend-design` |
| Checking facts against the source, proving work is complete, avoiding shortcuts | `verify` |
| Removing debug code, scratch files, dead code, and anything started on the system | `cleanup` |
| Writing or fixing tests, deciding what to mock | `testing` |
| The user's request or claim is wrong, or there's a clearly better way | `candor` |
