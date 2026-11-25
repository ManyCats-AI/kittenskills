#!/usr/bin/env python3
"""Find the litter agents leave behind: narration comments, commented-out code,
debug statements, focused/skipped tests, stray scratch and backup files, AI
summary docs, empty files, and leftover git/system state.

Every hit is a candidate, not a verdict. Check each one before removing it.

Usage
  find_litter.py                 files changed vs HEAD, plus untracked files (default)
  find_litter.py --base main     files changed on this branch vs main, plus untracked
  find_litter.py --all           every tracked and untracked file in the repo
  find_litter.py --system        also report git worktrees/stashes/branches, listening
                                 ports, and running containers
  find_litter.py PATH ...        only these files/directories

Standard library only. Python 3.8+.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

CODE_EXT = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte", ".astro",
    ".go", ".rs", ".java", ".kt", ".swift", ".c", ".h", ".cc", ".cpp", ".hpp", ".cs",
    ".rb", ".php", ".sh", ".bash", ".zsh", ".lua", ".dart", ".scala", ".ex", ".exs",
    ".css", ".scss", ".sql", ".yaml", ".yml", ".toml", ".html",
}
SKIP_DIRS = {
    ".git", "node_modules", "dist", "build", ".next", ".nuxt", "out", "target", "vendor",
    ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".svelte-kit", ".turbo", "coverage", ".gradle", ".idea", ".vscode",
}

# ------------------------------------------------------------------ patterns

COMMENT = r"(?://|#|/\*+|\*|<!--|--)\s*"

LINE_RULES = [
    # Narration: comments that describe the edit history instead of the code.
    (
        "narration-comment",
        re.compile(
            COMMENT
            + r"(?i:(?:added|updated|changed|fixed|modified|removed|replaced|refactored|moved|renamed)\b"
            r"(?: (?:this|the|to|for|a|an|it|here|new|logic|code|function|line|check|import))|"
            r"new:|new (?:code|logic|function|helper|implementation)\b|"
            r"now (?:we|this|it|uses|returns|handles|correctly)\b|"
            r"this (?:now|was|is the (?:new|updated|fixed))\b|"
            r"(?:changed|updated|fixed) (?:from|per|as requested|based on)|"
            r"as (?:requested|per (?:the )?(?:user|your request))|"
            r"(?:here|now) we\b|let'?s\b|step \d+[:.)]|"
            r"(?:keep|keeping) (?:the )?(?:existing|original|rest of the) (?:code|implementation|logic) ?(?:as is|unchanged|here|the same)?\s*$|"
            r"\.\.\. ?(?:rest|existing|remaining|other) (?:of )?(?:the )?(?:code|implementation|logic|unchanged)|"
            r"(?:existing|rest of|remaining) code (?:here|unchanged|stays))"
        ),
        "comment narrates the edit or the conversation, not the code. Delete it, or rewrite it as a why-comment.",
    ),
    (
        "placeholder",
        re.compile(
            r"(?i)(?:"
            + COMMENT
            + r"(?:implement (?:this|me|later)|your code here|placeholder|stub|not implemented|fill (?:this )?in)|"
            r"raise NotImplementedError|throw new Error\(\s*['\"`](?:not implemented|todo)|unimplemented!\(|todo!\(|"
            r"^\s*pass\s*#)"
        ),
        "placeholder or unfinished implementation.",
    ),
    (
        "temporary-marker",
        re.compile(
            COMMENT
            + r"(?i:(?:temp(?:orary)?|for now|quick (?:fix|hack)|hack\b|debug(?:ging)?\b|testing\b|"
            r"remove (?:this|me|later|before)|delete (?:this|me|later)|xxx\b|wip\b))"
        ),
        "marked temporary or debug. Either it's needed (rewrite the comment) or it's litter (remove it).",
    ),
    (
        "todo-without-ticket",
        re.compile(COMMENT + r"(?:TODO|FIXME)\b(?!.*(?:#\d+|https?://|[A-Z][A-Z0-9]+-\d+))"),
        "TODO/FIXME with no issue link. Do it now, link an issue, or delete it.",
    ),
    (
        "debug-statement",
        re.compile(
            r"(?:^|[^\w.])(?:"
            r"console\.(?:log|debug|trace|dir|table)\(|debugger;|"
            r"(?:import pdb|pdb\.set_trace\(|breakpoint\(\)|ipdb\.set_trace|from icecream import|\bic\()|"
            r"print\(\s*f?['\"](?i:debug|here|xxx|test|>>>|---|===|\*\*\*)|"
            r"dbg!\(|eprintln!\(\s*\"(?:debug|here)|"
            r"fmt\.Print(?:ln|f)?\(\s*\"(?:DEBUG|debug|here)|"
            r"var_dump\(|print_r\(|\bdd\(|"
            r"System\.out\.println\(\s*\"(?:debug|here)|"
            r"set -x\b)"
        ),
        "debug output. Remove, or replace with the project's logger at the right level.",
    ),
    (
        "focused-or-skipped-test",
        re.compile(
            r"(?:\b(?:it|test|describe|context)\.(?:only|skip)\(|\b(?:xit|xdescribe|fit|fdescribe)\(|"
            r"@pytest\.mark\.skip\b|@unittest\.skip\b|\bt\.Skip\(|#\[ignore\]|@Disabled\b|\.todo\()"
        ),
        "focused or skipped test. .only silently disables the rest of the suite; skips hide failures.",
    ),
    (
        "lint-suppression",
        re.compile(
            r"(?:eslint-disable|@ts-ignore|@ts-nocheck|@ts-expect-error|# type: ignore|# noqa|"
            r"#\[allow\(|@SuppressWarnings|// nolint|# pylint: disable|#!\[allow\()"
        ),
        "suppression. Keep only with a specific rule and a reason; never to hide a real error.",
    ),
    (
        "emoji-in-code",
        re.compile(r"[\U0001F300-\U0001FAFF✅❌✨⚠⭐⚡✔✖]"),
        "emoji in code or comments (log decorations, ✅ markers). Usually litter.",
    ),
]

# Code-looking comment lines. Two or more in a row = commented-out code.
CODEISH = re.compile(
    r"^\s*(?://|#)\s*(?:"
    r"(?:import|from|export|return|const|let|var|def|class|function|fn|func|if|for|while|elif|else|try|except|catch|await|async|pub|use)\b.*|"
    r"[\w.$\[\]'\"]+\s*(?:=|\+=|-=)\s*[^=].*|"
    r"[\w.$]+\(.*\)\s*;?\s*|"
    r"[{}\])];?\s*|"
    r".*;\s*)$"
)
NOT_CODE_HINT = re.compile(r"^\s*(?://|#)\s*(?:!|type:|noqa|eslint|prettier|@|-\*-|SPDX|Copyright|\w+:\s*\w)")

ONE_OFF_SCRIPT = re.compile(r"(?i)^(?:test|check|verify|debug|repro|reproduce|try)_[\w-]+\.(?:py|js|ts|sh|mjs)$")
TEST_DIRS = {"test", "tests", "__tests__", "spec", "specs", "testing", "e2e"}

FILE_RULES = [
    (re.compile(r"(?:\.bak|\.orig|\.rej|\.swp|\.swo|\.tmp|~)$"), "backup/editor/patch leftover"),
    (re.compile(r"(?i)(?:^|[._-])(?:old|copy|backup|new\d*|v2|final|fixed|working)\.[a-z0-9]+$"), "copy/variant of another file"),
    (re.compile(r"(?i)^(?:scratch|tmp|temp|debug|playground|sandbox|try|experiment|foo|bar)(?:[_-][\w-]*)?\.[a-z0-9]+$"), "scratch/debug file name"),
    (ONE_OFF_SCRIPT, "one-off test/repro script outside the test suite"),
    (
        re.compile(
            r"(?i)^(?:.*summary.*|implementation[\w-]*|changes(?:_made)?|fix(?:es)?[\w-]*|"
            r"progress|status|notes|todo|plan|migration[\w-]*notes|refactor[\w-]*|analysis|report|"
            r".*_(?:fix|changes|summary|report|analysis|plan|notes))\.md$"
        ),
        "AI-style summary/notes doc. Was it requested? If not, its content belongs in the PR description or nowhere",
    ),
    (re.compile(r"\.(?:log|pid|prof|trace|heapsnapshot|cpuprofile|core)$"), "runtime artifact (log/profile/dump)"),
    (re.compile(r"^(?:out|output|result|results|dump|response)\d*\.(?:txt|json|html|csv|xml)$"), "captured output file"),
]

# ------------------------------------------------------------------ helpers


def git(*args, cwd=None):
    try:
        r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def repo_root():
    out = git("rev-parse", "--show-toplevel")
    return Path(out.strip()) if out else None


def collect(args, root):
    if args.paths:
        files = []
        for p in map(Path, args.paths):
            if p.is_file():
                files.append(p)
            elif p.is_dir():
                files += [f for f in p.rglob("*") if f.is_file() and not (set(f.parts) & SKIP_DIRS)]
        return files, "given paths"
    if root is None:
        sys.exit("not a git repository: pass paths explicitly, or run inside a repo")
    untracked = (git("ls-files", "--others", "--exclude-standard", cwd=root) or "").split("\n")
    if args.all:
        tracked = (git("ls-files", cwd=root) or "").split("\n")
        names, scope = tracked + untracked, "whole repository"
    elif args.base:
        mb = (git("merge-base", args.base, "HEAD", cwd=root) or "").strip()
        if not mb:
            sys.exit(f"can't find merge-base with {args.base}")
        changed = (git("diff", "--name-only", "--diff-filter=ACMR", mb, cwd=root) or "").split("\n")
        names, scope = changed + untracked, f"changes since {args.base} + untracked"
    else:
        changed = (git("diff", "--name-only", "--diff-filter=ACMR", "HEAD", cwd=root) or "").split("\n")
        names, scope = changed + untracked, "uncommitted changes + untracked"
    files = []
    for n in dict.fromkeys(x for x in names if x):
        f = root / n
        if f.is_file() and not (set(Path(n).parts) & SKIP_DIRS):
            files.append(f)
    return files, scope


def changed_lines(root, base, path):
    """Line numbers added/modified in this file, so a diff-scoped scan doesn't
    report pre-existing code the agent never touched."""
    rel = str(path.relative_to(root))
    ref = base or "HEAD"
    if base:
        ref = (git("merge-base", base, "HEAD", cwd=root) or "").strip() or base
    out = git("diff", "-U0", ref, "--", rel, cwd=root)
    if out is None:
        return None
    if not out.strip():
        # untracked or no diff: whole file is new
        tracked = git("ls-files", "--error-unmatch", rel, cwd=root)
        return None if tracked is None else set()
    lines = set()
    for m in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", out, re.M):
        start, count = int(m.group(1)), int(m.group(2) or 1)
        lines.update(range(start, start + count))
    return lines


# ------------------------------------------------------------------ scan


def scan(files, root, args):
    findings = []  # (kind, location, detail, source)
    for f in files:
        rel = f.relative_to(root) if root and f.is_absolute() and root in f.parents else f
        name = f.name
        in_test_dir = bool(set(p.lower() for p in Path(rel).parts[:-1]) & TEST_DIRS)
        for pat, why in FILE_RULES:
            if in_test_dir and pat is ONE_OFF_SCRIPT:
                continue
            if pat.search(name):
                findings.append(("suspicious-file", str(rel), why, ""))
                break
        try:
            size = f.stat().st_size
        except OSError:
            continue
        if size == 0 and name not in {"__init__.py", ".gitkeep", ".keep", "py.typed"}:
            findings.append(("empty-file", str(rel), "empty file", ""))
            continue
        if size > 2_000_000 or f.suffix.lower() not in CODE_EXT | {".md", ".txt"}:
            continue
        try:
            text = f.read_text(errors="ignore")
        except OSError:
            continue

        only = None
        if root and not args.all and not args.paths:
            only = changed_lines(root, args.base, f)  # None = whole file is new

        lines = text.splitlines()
        run = []

        def flush_run():
            if len(run) >= 2 and (only is None or any(n in only for n, _ in run)):
                n0 = run[0][0]
                findings.append(
                    (
                        "commented-out-code",
                        f"{rel}:{n0}-{run[-1][0]}",
                        f"{len(run)} lines of commented-out code. Version control remembers it; delete it.",
                        run[0][1].strip()[:100],
                    )
                )
            run.clear()

        is_doc = f.suffix.lower() in {".md", ".txt"}
        for i, line in enumerate(lines, 1):
            in_scope = only is None or i in only
            if not is_doc:
                if CODEISH.match(line) and not NOT_CODE_HINT.match(line):
                    run.append((i, line))
                else:
                    flush_run()
            if not in_scope:
                continue
            for kind, pat, why in LINE_RULES:
                if is_doc and kind != "placeholder":
                    continue
                if pat.search(line):
                    findings.append((kind, f"{rel}:{i}", why, line.strip()[:110]))
        flush_run()
    return findings


def run_quiet(cmd, timeout=20):
    """stdout of cmd, or None if it fails, hangs, or isn't usable."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def system_report(root):
    out = []
    if root:
        wt = git("worktree", "list", cwd=root) or ""
        extra = [l for l in wt.splitlines()[1:] if l.strip()]
        if extra:
            out.append(("git worktrees (besides the main one)", extra))
        st = (git("stash", "list", cwd=root) or "").splitlines()
        if st:
            out.append(("git stashes", st))
        cur = (git("branch", "--show-current", cwd=root) or "").strip()
        default = None
        for cand in ("main", "master", "trunk", "develop"):
            if git("rev-parse", "--verify", "--quiet", cand, cwd=root):
                default = cand
                break
        if default:
            merged = [
                b.strip().lstrip("* ").strip()
                for b in (git("branch", "--merged", default, cwd=root) or "").splitlines()
            ]
            merged = [b for b in merged if b and b not in {default, cur}]
            if merged:
                out.append((f"local branches already merged into {default}", merged))
        ign = (git("status", "--porcelain", "--ignored", cwd=root) or "").splitlines()
        ign = [l[3:] for l in ign if l.startswith("!! ")]
        ign = [p for p in ign if not (set(Path(p).parts) & SKIP_DIRS) and not p.endswith((".env", ".env.local"))]
        if ign:
            out.append(("ignored files present (are any of these your leftovers?)", ign[:40]))
    ports = None
    if shutil.which("ss"):
        r = run_quiet(["ss", "-ltnpH"])
        ports = [l for l in r.splitlines() if "users:" in l] if r else None
    elif shutil.which("lsof"):
        r = run_quiet(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"])
        ports = r.splitlines()[1:] if r else None
    if ports:
        out.append(("listening ports owned by your processes (dev servers you started?)", ports))
    for tool in ("docker", "podman"):
        if shutil.which(tool):
            r = run_quiet([tool, "ps", "--format", "{{.ID}} {{.Image}} {{.Status}} {{.Names}}"])
            if r and r.strip():
                out.append((f"running {tool} containers", r.strip().splitlines()))
    return out


TOOL_HINTS = {
    (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"): "unused files/exports/deps: npx knip   |   unused vars: eslint (no-unused-vars)",
    (".py",): "unused imports/vars: ruff check --select F401,F841   |   dead code: vulture .",
    (".go",): "unused code: staticcheck ./... (U1000)   |   go vet ./...",
    (".rs",): "unused code: cargo clippy -- -W dead_code   |   unused deps: cargo machete",
    (".java", ".kt"): "unused code: IDE inspection or PMD UnusedPrivateMethod",
    (".rb",): "dead code: debride   |   rubocop Lint/UselessAssignment",
    (".php",): "dead code: phpstan / psalm --find-dead-code",
    (".cs",): "unused code: dotnet build -warnaserror:CS0168,CS0219, IDE0051",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--all", action="store_true", help="scan the whole repository")
    g.add_argument("--base", help="scan changes since this branch/commit")
    ap.add_argument("--system", action="store_true", help="also report git/process/container leftovers")
    ap.add_argument("--limit", type=int, default=60, help="max findings to print per kind")
    a = ap.parse_args()

    root = repo_root()
    files, scope = collect(a, root)
    findings = scan(files, root, a)

    print(f"Scope: {scope} ({len(files)} files)")
    kinds = {}
    for k, loc, why, src in findings:
        kinds.setdefault(k, []).append((loc, why, src))
    order = [
        "suspicious-file", "empty-file", "placeholder", "debug-statement", "focused-or-skipped-test",
        "commented-out-code", "narration-comment", "temporary-marker", "todo-without-ticket",
        "lint-suppression", "emoji-in-code",
    ]
    for k in order:
        items = kinds.get(k)
        if not items:
            continue
        print(f"\n== {k} ({len(items)})")
        for loc, why, src in items[: a.limit]:
            print(f"  {loc}\n      {why}")
            if src:
                print(f"      > {src}")
        if len(items) > a.limit:
            print(f"  ... {len(items) - a.limit} more")

    if a.system:
        for title, rows in system_report(root):
            print(f"\n== {title} ({len(rows)})")
            for r in rows:
                print(f"  {r}")

    exts = {f.suffix.lower() for f in files}
    hints = [h for keys, h in TOOL_HINTS.items() if exts & set(keys)]
    if hints:
        print("\n== Also run the language's own dead-code tools (this script doesn't parse code):")
        for h in hints:
            print(f"  {h}")

    print(f"\nTotal candidates: {len(findings)}. Each one: verify, then remove or justify. Re-run until clean.")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
