---
name: performance-optimization
description: Diagnose and fix performance problems (slow requests, high latency, CPU or memory bloat, slow queries, slow builds or tests, large bundles, and poor web vitals) using measurement-driven optimization. Use when the user says something is slow, uses too much memory or CPU, times out, doesn't scale, or asks to make code faster or more efficient. Hands off to architecture, deep-research, math, code-review, security-audit, and debugging at specific points.
---

# Performance Optimization

Measure, don't guess. Most performance intuition is wrong, and most time is spent in a few places. Find those places with data, fix the biggest one, and measure again.

## How this skill connects to others

Performance work crosses into other skills at predictable points. Switch to the other skill at that point, then come back here to measure.

| When | Use | For |
|---|---|---|
| Setting targets, sizing capacity, reading benchmark results | `math` | Back-of-envelope estimates, Little's law, Amdahl's law, percentiles, variance, and significance |
| The cause is unfamiliar (a library, runtime, DB engine, or known issue) | `deep-research` | Known performance characteristics, upstream issues, benchmarks, and prior fixes |
| The bottleneck is structural (chatty services, shared DB, sync call chains, wrong data model) | `architecture` | Redesigning boundaries and data flow instead of patching symptoms |
| The optimization touches caching, validation, auth, limits, or shared state | `security-audit` | Checking that the speedup didn't open a hole |
| The optimization diff is ready | `code-review` | Catching correctness regressions before merge |
| Something broke or got slower, and the cause isn't obvious | `debugging` | Root cause, bisecting regressions, and fixing bugs the optimization introduced |

For a small, local fix (one query, one loop) most of these handoffs are unnecessary. Use them when the change is large, risky, or the cause is unclear.

## Workflow

### 1. Define the goal

- **Which metric?** p50/p95/p99 latency, throughput, CPU time, peak memory, bundle size, build time, LCP/INP/CLS, or cost.
- **Which scenario?** A specific endpoint, query, page, job, or input size. A vague "make it faster" request needs a concrete benchmark scenario.
- **What's the target?** "p95 under 200ms at 500 rps" is a goal you can finish. "Faster" never is.
- **Is the target realistic?** Do a quick estimate before you start (→ `math`). Count bytes moved, round trips, and rows touched against what the hardware and network can actually do. If one request needs 40 sequential DB round trips at 2ms each, 50ms is impossible without a design change (→ `architecture`).

### 2. Build a reliable benchmark

- Create a repeatable measurement with realistic data sizes and shapes. Toy inputs hide algorithmic problems.
- Warm up first (JIT, caches, connection pools), run several iterations, and report the spread, not just the mean.
- Control the noise: same machine, nothing else heavy running, and a fixed dataset.
- Record the baseline before changing anything.
- Decide in advance how big a difference counts as real. With noisy measurements, compare distributions rather than single runs (→ `math` for confidence intervals and the number of runs needed).

Tools by ecosystem: `hyperfine` (CLI), `pytest-benchmark` / `timeit`, `go test -bench` + `benchstat`, `cargo bench` / criterion, JMH, `vitest bench`, `k6` / `wrk` / `vegeta` (HTTP), Lighthouse / WebPageTest (web).

### 3. Profile to find the bottleneck

Find where time or memory actually goes.

| Problem | Tools |
|---|---|
| CPU hot spots | `perf`, `py-spy`, `pprof`, `async-profiler`, Chrome/Node `--cpu-prof`, flame graphs |
| Memory | heap snapshots, `memray`, `tracemalloc`, `pprof` heap, Valgrind massif |
| I/O and waiting | distributed tracing, APM, `strace`, timing logs around calls |
| Database | `EXPLAIN (ANALYZE, BUFFERS)`, slow query log, `pg_stat_statements` |
| Frontend | DevTools Performance panel, Lighthouse, bundle analyzers |
| Builds | build tool timing/trace output, `--profile` flags |

First, classify the bottleneck:
- **CPU-bound**: hot functions dominate the flame graph
- **I/O-bound**: time is spent waiting on network, disk, or DB
- **Memory-bound**: allocation, GC pauses, or cache misses
- **Contention**: locks, connection pool exhaustion, or queueing

Each one needs a different fix. If the profile points into a dependency or runtime you don't know well, research it before guessing (→ `deep-research`). If the time is spread across many hops between components, the problem is probably the design (→ `architecture`).

Use Amdahl's law to decide whether a hot spot is worth the effort. Making 10% of the runtime infinitely fast saves at most 10% (→ `math`).

### 4. Fix the biggest problem first

Work from the highest-leverage fixes down:

1. **Don't do the work at all.** Remove redundant calls, dead features, over-fetching, and unnecessary re-renders.
2. **Fix the algorithm.** Replace O(n²) with O(n log n), use a hash lookup instead of a linear scan, or batch work instead of looping. Confirm the complexity claim with real input sizes, not just theory (→ `math`).
3. **Fix I/O patterns.**
   - Eliminate N+1 queries (eager loading, joins, `IN` batches)
   - Add the right indexes, checked against `EXPLAIN`
   - Batch and pipeline network calls, and run independent calls concurrently
   - Paginate and stream instead of loading everything into memory
4. **Cache.** Do it only after the above, with a clear invalidation strategy, bounded size, and a measured hit rate.
5. **Reduce allocation and copying.** Reuse buffers, use streaming and generators, pick appropriate data structures.
6. **Parallelize.** Use concurrency for I/O and multiple cores for CPU-bound work, watching out for contention.
7. **Micro-optimize.** Only in a proven hot loop, and only with benchmark evidence.
8. **Change the design.** When the fixes above can't reach the target, the bottleneck is structural (→ `architecture`). Typical examples: synchronous fan-out across services, one database serving incompatible workloads, or a data model that forces joins on the hot path.

**Frontend specifics:** code-split by route, tree-shake, drop heavy dependencies, compress and size images, preload critical resources, avoid layout thrashing, virtualize long lists, memoize expensive renders (after profiling), and move heavy work off the main thread.

### 5. Check that the speedup is safe

Performance changes often weaken security without anyone noticing. Run the change past `security-audit` if it does any of the following:
- **Caches** responses or objects. Is the cache key scoped by user or tenant? Could one user see another's data? Could an attacker poison it?
- **Removes or skips validation**, authorization checks, or escaping on a "fast path"
- **Raises or removes limits**: timeouts, page sizes, request body sizes, rate limits, or recursion depth. Each one is DoS protection.
- **Moves work client-side** that used to be enforced on the server
- **Adds concurrency** around shared state, which creates race and TOCTOU risks
- **Changes comparisons of secrets** in ways that could create timing side channels

### 6. Verify

- Re-run the same benchmark and compare it against the baseline with the same methodology. Check that the difference is beyond the noise (→ `math`).
- **Explain the number before you trust it.** A speedup is a claim to check, not a result:
  - **What else could it be measuring?** Errors that return early, skipped or cached work, code that never ran, a smaller input, a warm cache on one side only, noise. Rule each out with evidence (error counts, output checksums, row counts, cache hit rates).
  - **Why not twice as fast?** Name what bounds the new number (CPU on a specific function, a lock, I/O, round trips), taken from a profile of the new run, not from reading the code.
  - Keep the run count, the spread, and the limiting factor next to the number when you report it.
- Confirm correctness: run the tests, and compare outputs before and after on real data.
- Check for regressions elsewhere: memory against CPU trade-offs, cold-start time, and tail latency.
- Send the diff through `code-review`. Optimizations are a common source of subtle bugs: stale caches, broken ordering, lost error handling, and races.
- If the tests fail, the numbers make no sense, or another path got slower, stop and find out why (→ `debugging`). Don't keep stacking changes on top.
- Report the result as numbers: "p95 840ms → 120ms (7×) on the 10k-row fixture; peak RSS unchanged."

### 7. Prevent regressions

- Add the benchmark to CI or a performance test suite where practical.
- Add guardrails: query count assertions in tests, bundle size budgets, and timeouts.
- When a performance regression lands anyway, bisect it against the benchmark (→ `debugging`).

## Rules

- Change one thing at a time and measure each change.
- Don't trade away correctness, security, or readability for unmeasured gains.
- Don't cache your way around a bug or a missing index.
- Big-O matters at scale, but constant factors and I/O dominate at small scale. Profile real workloads.
- Stop when you hit the target. Further optimization has a maintenance cost.
