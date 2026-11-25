---
name: testing
description: Write tests that fail when the code is wrong and survive refactors, test-first where a cheap test path exists: pick the seam, work in vertical red-green slices, mock only true external dependencies, and prove each test can fail. Use when writing or fixing tests, adding a regression test, doing TDD or "test-first", reviewing test quality, deciding what to mock, or when tests pass but bugs still ship.
---

# Testing

A test is worth keeping only if it **fails when the behavior breaks** and **keeps passing when only the internals change**. Tests that do neither are worse than no tests: they cost time and give false confidence.

## Related skills

| When | Use |
|---|---|
| A bug: build the failing repro first | `debugging` |
| Proving the work is done | `verify` |

## 1. Pick the seam

A **seam** is the public interface where you observe behavior: a function's return value, an HTTP response, a CLI's output, a rendered screen, a row another service can read. Tests go at seams, never against private helpers or internal call order.

- Prefer the **highest seam that's still fast and deterministic**. A test through the HTTP handler with a real database in a container catches more than five unit tests of the helpers behind it.
- Use existing seams and the project's existing test patterns before inventing new ones. Find a similar test in the repo and follow it.
- For a large feature, list the seams you plan to test, each with one line on what it catches and what it misses, and show the user before writing them. For a small change, just pick the seam and go.
- If the only place you could test a behavior is too shallow to reproduce it (the bug needs two callers, the unit test has one), say so. That's a design finding, not a reason to write a test that proves nothing.

## 2. Work in vertical slices: red, then green

One behavior at a time:

1. Write **one** test for the next behavior, at the chosen seam.
2. **Run it and watch it fail for the right reason** (the assertion about the behavior, not an import error or a typo).
3. Write the minimum code to make it pass.
4. Run it and watch it pass; run the neighbouring tests.
5. Next behavior.

Don't write all the tests first and then all the code. Bulk-written tests describe imagined behavior, lock in a structure before you understand the problem, and tend to test shapes instead of outcomes. Refactor after green, as its own step, with the tests unchanged.

Skip strict test-first when there's no cheap test path (the test would need heavy infrastructure, production-only state, or brittle mocks). Use the closest executable check instead (a script, a `curl`, a browser automation run) and say so. No test is better than a bad test.

## 3. What to mock

Decide by what kind of dependency it is:

| Dependency | Treatment |
|---|---|
| Your own code in the same process (helpers, services, classes) | **Don't mock.** Run the real thing. Mocking your own collaborators tests the mock. |
| Local and substitutable (database, filesystem, queue, cache) | **Use a real one**: a container (testcontainers), SQLite/in-memory engine if the project supports it, a temp directory. |
| Your own remote service | A fake behind the same interface (port/adapter), shared by tests, or a contract test. |
| A true third party (payment provider, email, external API) | Mock at the edge of your code, using recorded real responses where possible. Assert on what you sent them; that's behavior. |
| Time and randomness | Inject a clock and a seeded random source; never `sleep` in tests. |

## 4. Make every assertion able to fail

- **Expected values come from the requirement**, a worked example, or a known-good literal, never recomputed the way the code computes them. `expect(total(cart)).toBe(cart.items.reduce(...))` passes by construction.
- **Assert outcomes, not calls.** "The order is saved with status `paid`" beats "`repository.save` was called once".
- **Assert the specific symptom.** "Doesn't throw" and `toBeTruthy()` rarely prove anything.
- **Errors**: assert the error type or code callers branch on, not the message text.
- **Pair "never happens" with "does happen"**: a test that a forbidden user gets 403 needs a sibling where the allowed user gets 200, or the 403 could come from a broken route.
- **Snapshot tests** only for output that is the product (a rendered email, a CLI help screen), kept small and reviewed on change.

## 5. Prove the test can fail

After writing a test, break the code it covers (flip a condition, return early, delete the line), run the test, watch it fail, and restore the code (`git diff` shows nothing left over). For important logic, run a mutation tester if the project has one (look up the current one for the ecosystem) and look at the mutants that survived.

A test that still passes with the behavior broken is deleted or rewritten, not kept for coverage numbers.

## 6. Match the test technique to the risk

| Code | Technique |
|---|---|
| Parsers, encoders, serializers, anything with a round-trip or ordering invariant | Property-based tests: generate many inputs and assert the invariant |
| Anything that parses untrusted input | A fuzzer, run long enough to matter |
| Locks, lock-free structures, custom synchronization | A tool that explores thread interleavings, or a stress loop with a measured failure rate |
| Memory-unsafe code | Sanitizers or an undefined-behavior checker on the test suite |
| Code with feature flags or build options | Test the flag combinations that ship |
| Test data for typed code | Complete fixtures from factory functions, not casts that hide missing fields |

Use the tools the project already has. If it has none, look up the ecosystem's current, maintained option and propose it rather than assuming a name from memory.

## 7. Keep the suite trustworthy

- **Deterministic**: no real network, no wall-clock time, no unseeded randomness, no dependence on test order or shared state. Each test sets up and cleans up its own data.
- **Fast**: the tests you run while working finish in seconds.
- **Flaky tests are bugs.** Find the cause (→ `debugging`); don't add retries or sleeps, and don't skip them without a linked issue.
- **Never weaken a test to make it pass**: no loosened assertions, no deleted cases, no `.skip`, no updated snapshots you didn't read, unless the expected behavior genuinely changed and you say so.

## 8. Report

Name each new test, the seam it runs at, and show it failing before the fix or with the behavior broken, then passing after. Include the suite command and result. If a behavior couldn't be tested, say why and what you checked instead.

## Checklist

- [ ] Tests run at public seams, following the repo's existing test patterns
- [ ] Each test was seen failing for the right reason before it passed
- [ ] Only true external dependencies are mocked; time and randomness are injected
- [ ] Expected values come from the requirement, not from the code
- [ ] Each test checked by breaking the code (or a mutation run)
- [ ] No sleeps, retries, skips, or weakened assertions added
- [ ] Full relevant suite run after the last change
