---
name: cleanup
description: Leave no trace. Remove everything an agent left behind (narration comments, commented-out code, debug prints, placeholder stubs, focused or skipped tests, scratch and repro scripts, backup files, unrequested summary docs, unused code and dependencies) and everything it started outside the repo (dev servers, containers, temp directories, worktrees, stashes, branches, installed tools), fully and verifiably. Use at the end of every coding task before reporting done, when the user says the repo is messy, sloppy, or full of leftovers, or asks to clean up, tidy, remove dead code, or remove test or debug artifacts.
---

# Cleanup

Agents litter. They add a debug print to check a value, write `test_fix.py` to reproduce a bug, start a dev server to look at a page, comment out the old version "just in case", write `IMPLEMENTATION_SUMMARY.md` nobody asked for, and narrate their edits in comments (`// Added this to fix the bug`). Then they report "done" and leave all of it behind.

The standard: **when the task is finished, the repo and the machine look as if a careful engineer did the work.** Every remaining line is there on purpose. Everything temporary is gone, from the repo and from the system.

## Related skills and files

| What | Where |
|---|---|
| Litter scanner: narration, placeholders, debug output, commented-out code, skipped tests, suppressions, stray files, system leftovers | `scripts/find_litter.py` |
| Prove the cleanup is complete and nothing broke | `verify` |
| Comment and code-quality rules | `engineering-practices` §4–5 |
| Commit the cleanup cleanly | `git-hygiene` |

## Two modes

| Mode | When | Scope |
|---|---|---|
| **After yourself** (default) | End of every task | Only what *you* created or changed in this task, plus anything you started on the system |
| **Repo sweep** | The user asks to clean up the repo | The whole repo, but every removal is verified and the list is shown to the user first |

Never turn "clean up after yourself" into a repo-wide refactor. Pre-existing code you didn't touch is out of scope unless the user asks for a sweep.

## 1. Keep a litter ledger while you work

Cleanup fails because by the end nobody remembers what was created. So write it down as you go. Every time you create something temporary, add a line to your task notes or todo list:

```
LEDGER
- file   scripts/repro_issue_42.py        (repro, delete at end)
- edit   src/cart.ts:88 console.log        (debug, remove)
- proc   npm run dev, pid 48211, port 5173 (stop at end)
- dir    /tmp/claude-xyz/fixtures          (delete at end)
- pkg    pip install --user httpie         (uninstall unless the user wants it)
- git    branch spike/try-redis            (delete)
- cfg    added DEBUG=1 to .env.local       (revert)
```

Things that belong on the ledger: scratch and repro scripts, fixture and output files, debug statements, feature flags and config toggles you flipped, background processes, ports, containers and volumes, temp directories, installed packages and global tools, git branches, worktrees, and stashes, files written outside the repo, browser profiles, and anything you `chmod`ed or moved.

Tag every temporary debug statement with one unique prefix per task, such as `[DEBUG-a4f2]`, so a single `grep -rn "DEBUG-a4f2"` finds them all at the end.

Prefer putting temporary files where they clean themselves up: the session scratch directory or a `mktemp -d` directory, never the repo root.

## 2. Scan for litter

Paths are relative to this skill's directory; run the script by its full path from the repo you're cleaning.

```bash
python3 <skill-dir>/scripts/find_litter.py --system        # your uncommitted changes + untracked files
python3 <skill-dir>/scripts/find_litter.py --base main     # everything on this branch
python3 <skill-dir>/scripts/find_litter.py --all           # repo sweep
```

The scanner checks only the lines you added or changed (in the default and `--base` modes), so pre-existing code doesn't drown out your own litter. It reports candidates, not verdicts. It also prints the right dead-code tool for each language present: run those too, since the scanner doesn't parse code.

| Tool | Finds |
|---|---|
| `npx knip` | Unused files, exports, dependencies (JS/TS) |
| `ruff check --select F401,F841`, `vulture` | Unused imports, variables, dead code (Python) |
| `staticcheck`, `go vet` | Unused code (Go) |
| `cargo clippy`, `cargo machete` | Dead code, unused deps (Rust) |
| The project's linter with unused-code rules on | Everything else |

Then **read your own diff** top to bottom (`git diff`, `git status`, and untracked files), because no scanner catches everything.

## 3. What counts as litter

### In code

- **Narration comments**: comments about the edit or the conversation instead of the code. `// Added error handling`, `# Fixed the bug`, `// Updated to use the new API`, `// Now correctly handles null`, `// As requested`, `// Step 3: ...`. Delete them. If there's a real *why* behind the change, rewrite it as a why-comment: `// Retries once: the payment API returns 409 on a cold cache (PAY-1123)`.
- **Comments that restate the code**: `// increment i` above `i++`, `# return the result`. Delete.
- **Commented-out code**: delete it. Git remembers it.
- **Placeholder code**: `// ... rest of the code`, `pass  # TODO`, `raise NotImplementedError`, `throw new Error("not implemented")`, empty function bodies. These aren't litter to delete; they're **unfinished work**. Finish it, or tell the user plainly what's missing.
- **Debug output**: `console.log`, `print("here")`, `dbg!`, `debugger`, `breakpoint()`, `set -x`. Remove them, or convert to the project's logger at the right level if the information is genuinely useful.
- **Focused and skipped tests**: `.only` silently disables the rest of the suite; `.skip`, `xit`, `@pytest.mark.skip` hide failures. Remove them, unless the skip predates you and has a linked reason.
- **Suppressions you added**: `@ts-ignore`, `# type: ignore`, `eslint-disable`, `# noqa`. Each one either gets fixed properly or stays with the specific rule and a reason.
- **Dead code you made dead**: the old function you replaced, the import it used, the helper only it called, the config key only it read, the dependency only it needed. Follow the chain all the way out.
- **TODOs you wrote**: do it now, link an issue, or delete it. No anonymous "TODO: handle this later".
- **Emoji and decoration**: `✅ Success!` in logs, 🚀 in comments.
- **Defensive clutter**: try/except wrappers, null checks, and fallbacks added "just in case" for cases that can't happen. Each one must correspond to a real failure mode.

### Files

- **Scratch and repro scripts**: `test_fix.py`, `repro.js`, `debug.sh`, `scratch.ts`, `try_*.py`. If it reproduces a real bug, turn it into a proper regression test in the test suite; then delete the script.
- **Backups and variants**: `*.bak`, `*.orig`, `*.rej`, `*_old.*`, `*_copy.*`, `*_v2.*`, `*_fixed.*`, `*~`.
- **Unrequested documents**: `IMPLEMENTATION_SUMMARY.md`, `CHANGES.md`, `FIX_NOTES.md`, `PLAN.md`, `ANALYSIS.md`. Summaries go in your final message or the PR description. Keep a doc only if the user asked for it or the project clearly keeps that kind of doc.
- **Runtime artifacts**: logs, `out.json`, profiles, coverage reports, screenshots, downloaded files, generated fixtures.
- **Empty files and directories** you created.
- **Accidental files**: `nul`, files named like a flag (`-rf`), files created by a mistyped redirect.

### Outside the repo ("fully remove it from the system")

- **Processes**: dev servers, watchers, background jobs, tunnels. Stop the ones *you* started (match on the PID you recorded, never `pkill -f <pattern>`, which can kill unrelated processes, including your own shell).
- **Containers, images, volumes, networks** you created.
- **Temp directories and files** outside the repo.
- **Packages and tools** you installed (pip/npm global, `cargo install`, `go install`, system packages). Remove them unless the user wants to keep them; ask if unsure.
- **Git state**: branches, worktrees, and stashes you made.
- **Config you changed**: shell rc files, git config, editor settings, environment files, OS settings. Revert to exactly what was there.
- **Credentials** you created for testing: revoke or delete them, and tell the user.

The scanner's `--system` flag lists worktrees, stashes, merged branches, ignored files, listening ports, and running containers. Compare that list against your ledger.

## 4. Verify before removing anything

Deleting something that's in use is worse than leaving litter. For every candidate:

1. **Did you create it, or did it exist before you started?** Check `git log`, `git blame`, `git status`, and your ledger. Pre-existing things are out of scope in "after yourself" mode. In a sweep, list them for the user rather than deleting them silently.
2. **Is it referenced?** Search the *whole* repo for the name: imports, string references, config files, build scripts, CI workflows, Dockerfiles, docs, dynamic imports, reflection, routes, CLI entry points, package.json `bin`/`scripts`, framework conventions (files loaded by naming convention, such as Next.js pages, Django migrations, pytest `conftest.py`).
3. **Is it public API?** Exported symbols in a library may be used by other repos. Don't remove them in a cleanup; deprecate them through the normal process.
4. **Is it something a user wants?** A file in `.gitignore` might be their local config (`.env`, `*.local.*`, IDE settings). Never delete secrets or local config files, even if they look unused.

Delete what is provably yours and provably unused. List what's uncertain and ask.

## 5. Remove fully, then prove it

- **Remove completely**, not partially: the file *and* its import, the export, the test, the fixture, the doc reference, the CI step, the dependency in the manifest and lockfile, the env var in `.env.example`, the route registration.
- **Don't leave tombstones**: no `// removed X` comments, no empty stub files, no `_unused` renames, no re-exports kept "for compatibility" that nothing needs.
- **Then prove it**:
  1. Re-run `find_litter.py` until it's clean, or every remaining hit has a reason.
  2. Search for every name you removed: zero hits left (except changelog entries).
  3. Build, typecheck, lint, and run the test suite. A cleanup that breaks the build isn't a cleanup.
  4. `git status` shows only intended changes; no untracked files left behind.
  5. Confirm processes, ports, containers, and temp paths from the ledger are gone (`ps -p <pid>`, `ss -ltnp`, `docker ps -a`, `ls <path>`).

## 6. Repo sweep mode

When the user asks for a whole-repo cleanup:

1. Run the scanner with `--all --system` and the language's dead-code tools.
2. Group the candidates: certain (provably unused, clearly litter), likely, and uncertain. For each, note the evidence ("no references in src/, tests/, CI, or docs").
3. **Show the user the list before deleting**, with counts and the uncertain items called out. A sweep touches code the user may care about.
4. Remove in small, reviewable commits by category (debug output, dead code, stray files, unused deps), running the tests between each, so any mistake is easy to revert.
5. Report what was removed, what was kept and why, and the verification results.

## Report

Close every task with a cleanup line in your final message:

```
Cleanup: removed repro_issue_42.py, 3 debug logs, and the old parsePrice(); stopped
the dev server on :5173; deleted /tmp/fixtures. find_litter.py clean; tests 212/212 pass.
Kept: none.
```

If you deliberately left something (a dev server the user wants running, a tool they want installed), say so explicitly.

## Notes on the scanner

- It's pattern-based and will produce some false positives. Read each hit; don't delete blindly.
- When you run it on files that *define* litter patterns (linters, this skill's own scripts), those definitions match themselves. That's expected.
- Exit code is 1 when anything is found, so it can be used as a pre-commit or CI check.

## Output checklist

- [ ] Ledger kept during the task, and every entry resolved
- [ ] `find_litter.py` clean, or each remaining hit justified
- [ ] Language dead-code tools run on the changed area
- [ ] Every removal verified as yours and unreferenced; uncertain items asked about
- [ ] Removals complete: imports, exports, deps, config, docs, CI all updated
- [ ] No narration, commented-out code, placeholders, debug output, or skipped tests left
- [ ] Processes, containers, temp files, packages, branches, and config changes cleaned up
- [ ] Build, lint, and tests pass after cleanup
- [ ] Final message states what was removed, what was kept, and why
