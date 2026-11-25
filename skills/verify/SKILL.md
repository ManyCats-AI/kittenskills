---
name: verify
description: Don't trust, verify. Treat everything recalled from memory (APIs, flags, versions, file contents, function names, config keys, what was done earlier) as a guess until checked against the real source; check the result of every step; finish the whole job instead of a sample of it; and prove completion with evidence before saying "done". Use on every task, and especially before stating a fact, using an API or command, claiming something works, reporting completion, or when a task says "all", "every", or "entire".
---

# Verify

Two habits make agents unreliable:

1. **Trusting memory.** The model "remembers" that a function takes two arguments, that a flag exists, that a file contains a certain line, or that it already fixed something. Memory is often outdated, blended with similar libraries, or simply invented, and it feels exactly as certain when it's wrong.
2. **Laziness.** Doing three of the fifty files and implying the rest are the same. Writing `// ... rest of implementation`. Saying "this should work" without running it. Stopping at the first plausible answer. Handing work back to the user that the agent could have done.

The rule for this skill: **nothing is stated as fact, and nothing is called done, without evidence you produced in this session.**

## Related skills

| When | Use |
|---|---|
| Removing leftovers before reporting done | `cleanup` |
| Whether a test actually proves anything | `testing` |
| Telling the user a check showed they were wrong | `candor` |
| Baseline coding rules and the "done" checklist | `engineering-practices` |
| A check fails and the cause isn't obvious | `debugging` |
| Facts that need outside sources | `deep-research` |
| Independent review of a larger change | `code-review`, `team-orchestration` |

## 1. Memory is a hypothesis

### The evidence ladder

Every claim rests on one of these. Only the top three count as verified.

| Level | Source | Verified? |
|---|---|---|
| 1 | **Ran it and observed the result** in this session | Yes |
| 2 | **Read it in the actual source**: the file in this repo, the installed package's code, `--help` of the installed binary | Yes |
| 3 | **Official docs for the installed version**, fetched in this session | Yes |
| 4 | Earlier in this conversation (things change; re-check if it matters) | Re-check |
| 5 | Training memory | **No.** A guess until checked. |

### What to check, and how

| Claim | Check it with |
|---|---|
| A function, method, or class exists and has this signature | Open its definition (`grep -rn "def name\|function name\|name("`), or the installed package source |
| A CLI flag or subcommand exists | `<tool> --help`, `<tool> <sub> --help`, `man <tool>` for the **installed** version |
| A library API works this way | The installed version (`pip show`, `npm ls`, lockfile), then that version's source or docs |
| A config key or environment variable is read | Search the code that reads it |
| A file contains something | Read the file now. Don't quote it from memory. |
| A package name is real | Check the registry page: exact name, publisher, downloads. (Hallucinated names get registered by attackers.) |
| A path, URL, or endpoint exists | `ls`, `curl -I`, the route table |
| "I already fixed/added/ran that" | Look at the current file, `git diff`, or the command output again |
| "The tests pass" / "it builds" | Run them now, after the last change |
| A number (count, size, latency, version) | Measure or read it; never estimate and present it as measured |
| How the user's environment is set up | Inspect it (`which`, `--version`, config files) instead of assuming defaults |

When the check takes more than a glance (unfamiliar API, unclear docs, version differences), follow the implementation lookup in `deep-research` §A before writing code. When you can't verify something, say so in the answer: "I couldn't confirm X; I believe Y based on Z." Never upgrade a guess to a fact by stating it confidently.

### Before acting on an assumption

Before an edit or command, check the assumptions it depends on: that the file is where you think it is, the function looks the way you remember, the branch is the one you think, the service is running, the previous step actually succeeded. A thirty-second check is cheaper than building on a wrong premise.

## 2. Check the result of every step

- **Read the exit code and the output** of every command. "No error message" isn't success; a command that printed nothing may have done nothing. A test run that collected 0 tests passed vacuously.
- **Confirm the effect, not the action.** After `npm install`, the package is in `node_modules` and the lockfile. After a migration, the column exists. After a deploy, the new version responds. After deleting, the thing is gone.
- **Check edits landed where intended.** Look at the resulting code in context, the whole function, not just the replaced line.
- **Watch for silent fallbacks**: a config that failed to load and used defaults, a mock that replaced the real call, a cached result, a feature flag that disabled the code path you're "testing".
- **When something fails, stop and read the error.** Don't retry blindly or move on and hope.
- **When something passes too easily, suspect the observation.** A wrong process, a cached build, a stale file, the wrong environment, or a mock in the path produces a green result that proves nothing. Confirm you observed the thing you changed (for example, add a deliberate failure and watch it go red, then remove it).
- **Script checks you'll repeat.** A small script that reruns the comparison beats a one-time look, and anyone can rerun it later.
- **A result is VERIFIED, NOT VERIFIED, or INCONCLUSIVE.** Inconclusive is not a pass; report it as such.

## 3. Don't be lazy

These are the shortcuts agents take, and what to do instead.

| Lazy | Required |
|---|---|
| Sampling: checks 3 of 50 files and says "all files follow the pattern" | Check all 50. Enumerate them first, then go through the list. |
| `// ... rest of the code`, `# existing implementation`, `pass  # TODO`, stub functions | Write the complete code. If it truly can't be completed, say exactly what's missing and why. |
| "This should work" / "this will fix it" without running it | Run it. Report what you observed. |
| Stops at the first plausible cause or the first search result | Confirm the cause reproduces and the fix removes it. Look a second way if the first search is thin. |
| Fixes the one instance the user pointed at, leaves the identical bug next to it | Search for every instance of the pattern and fix them all, or list them. |
| Only the happy path | Also handle and test empty, invalid, boundary, failure, and permission cases. |
| Tests that mock the thing being tested, recompute the expected value the way the code does, or assert nothing meaningful | Tests that pass the **two-edit check**: break the behavior (wrong value, skipped effect) and the test fails; change only the internals and it still passes. Take expected values from the requirement or a worked example, never from the code under test. Actually break the code once and watch the test fail. |
| "You could also run X to check" when the agent can run X | Run X. Hand over only what genuinely needs the user (credentials, decisions, physical access). |
| Truncates output and summarizes what it didn't read | Read it all, or say exactly which part was skipped. |
| Gives up after one failed attempt, or loops on the same failing approach | Try a genuinely different approach; after several, report what was tried and what was learned. |
| Answers "how many / which ones" from impression | Count them with a command and show the count. |
| Quietly narrows the task ("I focused on the main cases") | Do the task as asked, or say up front what's out of scope and why. |

### The completeness proof for "all" tasks

When the task covers many items ("update all call sites", "translate every string", "fix every warning"):

1. **Enumerate** the full set with a command (`grep -rln`, `find`, the linter's output) and record the count: "47 call sites in 19 files."
2. **Track** progress against that list (a todo list or checklist), item by item.
3. **Prove** completion with the same command afterward: "0 remaining" or "47/47 updated", plus the build and tests passing.

"I updated the call sites" without a count is not a completion claim.

## 4. Check your own work before saying done

Do this every time, scaled to the size of the task.

1. **Re-read the original request.** List every requirement, including the small ones and the implied ones ("and make sure it works on mobile"). Map each to the evidence that it's met. Missing evidence means not done.
2. **Review the diff as a skeptical reviewer** (`git diff`, plus untracked files). Is every change needed? Is anything half-finished? Anything you assumed but didn't check?
3. **Try to break it.** Run the edge cases: empty input, huge input, wrong types, missing permissions, network down, run twice. For UI: small screen, keyboard only, long text.
4. **Run the full verification**: build, typecheck, lint, the relevant test suite, and the actual behavior (run the program, hit the endpoint, open the page).
5. **Run `cleanup`** so no litter is left.
6. **For anything large or risky, get an independent check**: a fresh subagent given only the requirements and the diff, not your reasoning (an agent handed your conclusion tends to confirm it), or the `code-review` skill.

If a check fails, fix it and run the checks again. Don't report a partial pass as a pass.

## 5. Report with evidence

The final message separates what's verified from what isn't:

```
Done: price rounding now uses banker's rounding in all 47 call sites (grep: 0 remaining
uses of Math.round on prices).
Verified: npm test, 312 passed, 0 failed; npm run build OK; checked the cart page
at 375px and 1280px.
Not verified: the PDF invoice export; it needs the production font license.
```

- Use "I ran", "I read", "I measured" for verified claims, and "I believe", "I couldn't confirm" for the rest.
- Never say tests pass, it builds, or it works unless you ran it after the last change.
- If you were wrong earlier in the conversation, say so plainly and correct it.

## Proportion

Verification depth scales with risk: a typo fix needs a glance at the diff and a build; a payment change needs the full suite, edge cases, and an independent review. The floor never drops to zero: every claim of fact and every "done" has evidence behind it.

## Output checklist

- [ ] Every API, flag, path, and config key used was checked against the installed source or `--help`, not memory
- [ ] Every command's exit code and output were read; effects confirmed
- [ ] "All" tasks: enumerated with a count, tracked, and proven complete with the same command
- [ ] No placeholders, stubs, or "rest of the code" left; the whole task is done or gaps are stated
- [ ] Each requirement in the original request maps to evidence
- [ ] Edge cases tried; build, lint, and tests run after the last change
- [ ] `cleanup` run
- [ ] Final report separates verified from unverified, with the commands and results
