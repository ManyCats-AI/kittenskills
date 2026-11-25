---
name: debugging
description: Find and fix the root cause of bugs, crashes, failing tests, flaky behavior, regressions, and wrong output, starting from a fast command that reproduces the failure. Use when the user reports something broken, pastes an error or stack trace, says "debug this" or "why does this fail", or when a fix you already tried didn't work.
---

# Debugging

Debugging is the scientific method applied to code. The single biggest predictor of success is having a **red loop**: one command that runs the broken code path and fails on *this* bug. With a red loop, bisection, hypotheses, and instrumentation are mechanical. Without one, reading code and guessing is how agents ship wrong fixes.

## Related skills

| When | Use |
|---|---|
| The bug is "it's slow" | `performance-optimization` |
| Removing the debug logs and repro scripts afterwards | `cleanup` |
| Proving the fix with evidence | `verify` |

## 1. Build the red loop first

Spend most of your effort here. Construct the loop in roughly this order of preference:

1. A **failing test** at whatever level reaches the bug (unit, integration, e2e).
2. A **script or `curl`** against the running program, asserting on the wrong output.
3. A **CLI run with a fixture input**, diffed against known-good output.
4. A **headless browser script** (Playwright) asserting on DOM, console, or network.
5. A **replayed capture**: save the real request, payload, or event log, and feed it through the code path in isolation.
6. A **minimal harness**: boot only the subsystem involved and call the failing function directly.
7. A **fuzz loop**: for "sometimes wrong", run 1000 random inputs and catch the bad one.
8. A **differential run**: same input through the old and new version (or two configs), diff the outputs.
9. A **bisection script** for regressions: `git bisect run <loop-command>`.

Then tighten it. Make it faster (skip unrelated setup, narrow the test), sharper (assert on the exact symptom, not "didn't crash"), and deterministic (pin time, seed randomness, isolate the filesystem and network).

**Flaky bugs:** the goal is a higher failure rate, not a perfect repro. Loop the trigger 100 times, add parallelism or load, and narrow timing windows until it fails often enough to debug against. Measure the rate: `for i in $(seq 100); do <cmd> >/dev/null 2>&1 || echo fail; done | wc -l`.

**Done when** you can name one command that you have already run, with its output shown, and that is:

- [ ] **Red on the user's symptom**: it drives the real code path and fails with the exact error or wrong value the user reported, not a different nearby failure
- [ ] **Deterministic**: same verdict every run, or a measured, high failure rate for flaky bugs
- [ ] **Fast**: seconds, not minutes
- [ ] **Unattended**: you can rerun it without a human

If you notice yourself reading code to build a theory before this command exists, stop and build the command. If you truly can't build one, say so, list what you tried, and ask the user for what would unlock it: access to the environment, a captured artifact (log, HAR file, core dump, recording), or permission to add instrumentation.

## 2. Minimise

Shrink the repro to the smallest case that still fails. Remove one input, caller, config value, or step at a time and rerun the loop after each cut. **Done when** every remaining element is load-bearing: removing any one makes the loop pass. A minimal repro shrinks the search space and becomes the regression test later.

## 3. Read the evidence

- Read the **whole** error and stack trace, including "caused by" sections. The first frame in your own code usually matters most.
- Read the code at each frame and work out which values can reach that line.
- Check recent changes: `git log -p --since=...`, `git diff <last-good>`. Regressions usually live in a recent diff.
- Check the environment: installed dependency versions, config, env vars, OS, data shape. Inspect them; don't assume them (→ `verify`).

## 4. Hypothesise: several, ranked, falsifiable

Write **3 to 5 hypotheses** before testing any. Stopping at one anchors you on the first plausible idea.

Each one states a prediction: "If the cache key ignores case, then requesting `ABC` after `abc` returns stale data, and lowercasing the key makes the loop pass." A hypothesis without a prediction is a hunch; sharpen it or drop it.

Rank by likelihood and cost to check. Show the ranked list to the user in one short message (they often know "we changed #3 yesterday"), then keep going without waiting for a reply.

## 5. Test one hypothesis at a time

- **Change one variable per run.** Several changes at once tell you nothing.
- Prefer a **debugger or REPL** over logs. Otherwise add **targeted logs** at the boundaries that separate your hypotheses. Never "log everything and grep".
- **Tag every temporary log** with a unique prefix, such as `[DEBUG-a4f2]`, so removing them later is one search.
- Use `git bisect run` when there's a known good commit, and binary search over data or config when the trigger is buried.
- When a check passes suspiciously easily, suspect your observation (wrong process, cached build, stale file, mock in the way) before you trust it.

## 6. Find the root cause

Keep asking "why" until you reach a wrong decision in the code, not just the line where it surfaced: crash at line 80 → `x` is null → the cache returned a stale entry → **the invalidation skips keys with uppercase letters**. You're done when you can explain every link from trigger to symptom.

Then ask: **is the state that triggered the failure legitimate?**

- If yes (null really can happen there), handle it where the code broke.
- If no (it should never exist), a guard at the crash site hides the bug. Find and fix whatever produced the bad state.

Guards, retries, sleeps, swallowed exceptions, clamped values, and default fallbacks are the usual ways a symptom gets hidden instead of fixed.

**Fix the pattern, not the instance.** Search for the same defect in other call sites, sibling functions, and copied code, and fix or list every one.

## 7. When fixes keep failing, attack the premise

If two fixes that rest on the same assumption have both failed, the assumption is probably wrong, not the fixes.

1. Write the premise down as one sentence: the thing every failed fix assumed ("the request reaches the handler", "this runs after the config loads").
2. Find an observation that would come out differently if the premise were false, and make it.
3. Don't write another fix until that observation is in.

## 8. Fix with a regression test

1. Turn the minimised repro into a test at a level that exercises the real bug pattern. If the only available test level is too shallow to reproduce it (a unit test that can't recreate the chain that triggered the bug), say so: that's an architecture finding, not a reason to write a test that proves nothing.
2. **Watch the test fail** for the right reason.
3. Make the smallest fix at the right layer. Keep refactors for a separate change.
4. Watch the test pass, rerun the original un-minimised loop from step 1, and run the broader suite.

## 9. Clean up and report

- Remove every tagged debug log (`grep -rn "DEBUG-a4f2"` returns nothing), repro script, and throwaway harness (→ `cleanup`).
- Report: the symptom, the root cause and the full causal chain, the hypothesis that turned out right, the fix, and the commands that prove it (loop red before, green after; suite results).
- If finding the cause took a long dig, propose the cheap, always-on signal that would have shown it at a glance (a log line with context, an assertion, a metric, a clearer error message).
- Mention similar code you noticed but didn't change.

## Anti-patterns

- **Theorising without a red loop.** The most common failure. No loop, no hypotheses.
- **Shotgun debugging**: changing several things until it works, without knowing why.
- **Symptom patching**: try/except, retries, sleeps, or null checks that hide an illegitimate state.
- **Fixing a neighbouring bug**: the loop fails, but not with the user's symptom.
- **Blaming the platform early**: compiler, framework, and OS bugs exist but are rare. Rule out your own code first.
- **Weakening the test** to make it pass.

## Special cases

- **Flaky tests**: suspect shared state between tests, test order, real clocks, unawaited async work, network calls, unseeded randomness, and resource limits. Report the failure rate before and after the fix.
- **Works locally, fails in CI or prod**: diff the environments: versions, env vars, filesystem case sensitivity, time zone, locale, CPU count, memory limits, network access, data.
- **Heisenbugs** that vanish when observed: suspect races. Logging changes timing, so use lightweight tracing or record-and-replay (`rr`).
- **Performance bugs**: logs are the wrong tool. Measure a baseline and profile (→ `performance-optimization`).
