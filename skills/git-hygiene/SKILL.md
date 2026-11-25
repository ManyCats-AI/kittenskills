---
name: git-hygiene
description: Keep git history clean, reviewable, and safe: well-scoped commits, clear messages, sensible branching, clean rebases, conflict resolution, and recovery from mistakes. Use when committing, writing commit messages, preparing a branch or PR, rebasing, squashing, resolving merge conflicts, cleaning up history, or undoing a git mistake.
---

# Git Hygiene

History is documentation. Each commit should be a coherent, buildable step with a message that explains *why*. Above all, never destroy work that might be needed.

## Safety rules (always)

- **Look before you act.** Run `git status`, `git diff`, `git log --oneline -n 20`, and `git branch -vv` before any history-changing operation.
- **Never force-push shared branches** (`main`, `master`, release branches, or anyone else's branch). On your own feature branch, use `git push --force-with-lease`, never bare `--force`.
- **Don't rewrite published history** unless the branch is yours alone and the user agreed.
- **Back up before risky operations**: `git branch backup/<name>-$(date +%s)` before a rebase, reset, or filter.
- **Don't run destructive commands** (`reset --hard`, `clean -fd`, `checkout -- .`, `branch -D`, `stash drop`) without confirming that the changes they discard are unwanted.
- **Don't commit secrets** (`.env`, keys, credentials, tokens). If one was committed, removing it from history is not enough. It must be rotated.
- **Don't skip hooks** (`--no-verify`) unless asked. Fix what the hook reports instead.
- **Commit and push only when asked.** Don't commit directly to the default branch; create a branch first.

## Commits

**Scope:** one logical change per commit.
- Don't mix refactoring with behavior changes, or formatting with logic.
- Every commit should build and pass tests, because that keeps `git bisect` useful.
- Stage deliberately: name the files (`git add src/a.ts src/b.ts`), then `git diff --staged` to review exactly what's going in. Avoid `git add -A` or `git add .` without checking `git status` first. Interactive commands (`git add -p`, `git rebase -i`, `git commit` without `-m`) hang in agent shells; to stage part of a file, write a patch and `git apply --cached`.

**Messages:** follow the repo's existing convention (check `git log`). Without one, use:

```
<type>(<scope>): <imperative summary, ≤ 72 chars>

Why this change is needed: the problem or motivation.
What changed at a high level, if not obvious from the diff.
Any consequences: migrations, breaking changes, follow-ups.

Refs: #123
```

- Write the summary in the imperative mood ("Add retry to webhook sender", not "Added" or "Adds").
- Common types: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `build`, `ci`, `chore`.
- The body explains **why**; the diff already shows **what**.
- Avoid messages like "fix", "wip", "updates", or "address review comments" in final history.

## Branches

- Use short-lived branches off the latest default branch: `git switch -c feat/short-description origin/main`.
- Use descriptive names: `fix/login-redirect-loop`, `feat/csv-export`.
- Stay current with the base branch by rebasing (for private branches) or merging (for shared branches), following team convention.
- Delete branches after they merge.

## Cleaning up before a PR

```bash
git fetch origin
git rebase -i origin/main      # reorder, squash fixups, reword messages
```

- Squash "fix typo" and "review feedback" commits into the commits they fix.
- During development, use `git commit --fixup=<sha>` and later `git rebase -i --autosquash origin/main`.
- Note: interactive rebase requires an editor. In non-interactive environments, use `GIT_SEQUENCE_EDITOR` scripts, `--autosquash` with fixup commits, or `git reset --soft origin/main` followed by deliberate recommits.
- Verify afterward: `git log --oneline origin/main..HEAD` and `git diff origin/main...HEAD` should show exactly what you intend.
- After a rebase, compare the old and new commit series with `git range-diff <old-base>..<old-head> origin/main..HEAD`. Confirm no intended change disappeared and no change already on main came back.
- When pushing a rebased branch, pin the lease to the head you observed before rebasing: `git push --force-with-lease=<branch>:<observed-sha>`. If the lease fails, someone pushed in the meantime; fetch and look before trying again.
- A clean rebase only means there are no textual conflicts. Check whether main has since changed the APIs, types, or behavior this branch relies on, or already solved the same problem.

## Resolving conflicts

1. Understand both sides before editing: `git diff`, `git log --merge -p`, and `git show :1:<file> :2:<file> :3:<file>` for base, ours, and theirs.
2. Resolve by intent, not by picking a side. Often the correct result combines both changes.
3. Remove all conflict markers, then build and run tests before continuing.
4. During a rebase, "ours" is the branch you're rebasing **onto** and "theirs" is your commit. This is the reverse of a merge.
5. If it goes wrong, use `git rebase --abort` or `git merge --abort` to return to the starting state.
6. Consider `git config rerere.enabled true` for recurring conflicts.

## Recovery

Almost nothing in git is truly lost once it's been committed.

| Situation | Fix |
|---|---|
| Wrong last commit message | `git commit --amend` (only if not pushed) |
| Forgot a file in the last commit | `git add <file>; git commit --amend --no-edit` |
| Committed to the wrong branch | `git branch <new>; git reset --keep HEAD~1; git switch <new>` |
| Undo a pushed commit | `git revert <sha>` (doesn't rewrite history) |
| Lost commits after reset or rebase | `git reflog` → `git branch rescue <sha>` |
| Deleted a branch | `git reflog` or the SHA from the deletion message → `git branch <name> <sha>` |
| Unstage a file | `git restore --staged <file>` |
| Dropped a stash | `git fsck --lost-found`, then look for dangling commits |
| Secret committed | Rotate the secret immediately, then purge it with `git filter-repo` and coordinate a force-push |

## Repo hygiene

- Keep a `.gitignore` covering build output, dependencies, local env files, editor and OS files, and logs.
- Don't commit generated files, large binaries (use Git LFS), or lockfile churn that isn't part of the change.
- Normalize line endings with `.gitattributes` when the team works across operating systems.
- Tag releases with annotated tags: `git tag -a v1.2.0 -m "..."`.
