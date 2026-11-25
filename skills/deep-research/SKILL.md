---
name: deep-research
description: Research a question thoroughly across many primary sources and deliver a cited answer in which every claim is traceable, actively challenged with counter-evidence, and labeled with its confidence. Also the lookup protocol for coding, covering unclear APIs, library behavior, versions, and standards, where the rule is to research and then implement, never guess. Use when the user asks to research, investigate, compare options, survey a field, or check a claim, when a question needs more than one or two lookups, or when implementation depends on behavior you aren't sure of.
---

# Deep Research

The output is a trustworthy answer, not a pile of links. Every claim in it traces to a source you opened and read in this session, every important conclusion has survived a deliberate attempt to disprove it, and the confidence you state matches the evidence.

**Never fill a gap with a plausible guess.** If something is unclear, research it. If research can't settle it, say so and say what would.

## Related skills

| When | Use |
|---|---|
| The evidence ladder and checking claims against installed code | `verify` |
| The answer is a design decision | `architecture` |
| Numbers, statistics, estimates | `math` |

## Two modes

| Mode | When | Depth |
|---|---|---|
| **Implementation lookup** | Mid-task: an API, flag, config key, library behavior, or standard you aren't sure of | Section A. Minutes. Stops when the behavior is confirmed for the installed version. |
| **Full research** | The user asks a question that needs a researched answer, comparison, or recommendation | Sections 1–8 |

## A. Implementation lookup: research, then implement

Use this every time you're about to write code against something you haven't confirmed in this session. Work down the list until the behavior is confirmed:

1. **Pin the version actually in use**: lockfile (`Cargo.lock`, `package-lock.json`, `pnpm-lock.yaml`, `poetry.lock`, `go.sum`), `--version` of the installed tool, or the runtime's version. Docs for a different version don't count.
2. **Read the docs for that version**: the official reference, docs.rs / pkg.go.dev / the package's versioned docs site, `--help` of the installed binary.
3. **Read the source** when docs are thin or ambiguous: the installed package (`node_modules/<pkg>`, `~/.cargo/registry/src/`, `site-packages/`, `go env GOMODCACHE`), or the repository at the matching tag.
4. **Read the changelog** between the version you know and the installed one, for renamed or removed APIs and changed defaults.
5. **Check the issue tracker** for the exact behavior ("<function> returns", "<error message>"), including closed issues, when the docs and observed behavior disagree.
6. **Probe it**: write a tiny throwaway program or test in your scratch directory that calls the API and prints what it does. Observed behavior beats any document.
7. **Search existing usage in this repo**: how does the project already call it? Match that unless it's wrong.

Then implement, and note the source in your report ("`retry` takes `max_elapsed_time` per the 0.4.2 docs: <url>"). If after all this the behavior is still unclear, stop and tell the user what you found and what's still uncertain. Don't paper over it with code that "probably works".

## 1. Frame the question

Write down before searching:

- **The core question** in one sentence, and the decision or understanding it serves.
- **Sub-questions** (3–8) that together answer it. These become the coverage table in step 6.
- **Scope**: time range, geography, versions, depth. Ask the user only if an ambiguity would change the research substantially; otherwise state your assumption and proceed.
- **What a good answer looks like**: a recommendation, comparison table, timeline, or explanation.
- **What would change the answer**: the facts that, if different, would flip the conclusion. Research those hardest.

## 2. Plan sources

| Need | Primary sources |
|---|---|
| How software behaves | Source code, official docs for the version, changelogs, issue trackers, the project's tests |
| Standards and specs | The spec itself (RFC, W3C, WHATWG, ECMA, ISO), errata, the working group's issues |
| Security | Vendor advisories, CVE/GHSA/RustSec/OSV entries, the fix commit |
| Scientific claims | Peer-reviewed papers, systematic reviews, meta-analyses; check retractions |
| Law and regulation | The legal text and the regulator's own guidance, not law-firm blog summaries |
| Current events, prices, availability | Official announcements and recent primary reporting, with dates |
| Practitioner experience | Engineering blogs, postmortems, talks; note the author's incentives |
| Statistics | The original dataset or publisher, not an article quoting it |

When the question concerns the local codebase, the code is a primary source. Read it.

## 3. Search wide, then deep

- **Wide**: several phrasings per sub-question, using the field's own vocabulary (learn it from the first results), synonyms, and the names of competing options. Use operators: `site:` for official domains and GitHub, quoted exact phrases for error messages, date filters for fast-moving topics.
- **Deep**: open and read the most authoritative sources in full. Search snippets and AI summaries are leads, not sources.
- **Follow citations back** to the original. Secondary sources routinely distort numbers and drop caveats.
- **Fan out for big questions**: give each sub-question to a parallel subagent with a precise brief and a fixed return format, so raw pages stay out of your context:

  ```
  For each finding: claim | exact quote or number | source URL | publication date |
  source type (primary/secondary) | counter-evidence found (or "searched: none found")
  ```

- **Keep a claims ledger** as you go: each claim, its sources, and its status. The report is built from the ledger, never from memory.

## 4. Challenge every conclusion

Before a conclusion goes in the report, try to break it. For each important claim or recommendation, run at least one adversarial search and record the result, including "none found":

- `"<X> problems"`, `"<X> limitations"`, `"<X> criticism"`, `"<X> postmortem"`, `"<X> incident"`
- `"migrated away from <X>"`, `"<X> vs <Y>"`, `"why not <X>"`
- For a statistic: who else measured it, and did they get the same number?
- For a technical claim: the issue tracker and the changelog of later versions.

A conclusion that you never tried to disprove is a hypothesis.

## 5. Evaluate evidence

For each significant claim:

- **Authority**: is the source in a position to know? Is it primary?
- **Recency**: current for this question? Check the date and the version it applies to.
- **Independence**: do the "confirming" sources all derive from one original? Five articles quoting one press release are one source.
- **Incentives**: is the source selling something or advocating?
- **Agreement**: what do the counter-searches from step 4 say?

**Source requirement:** each key claim needs one primary source read in full, or two independent secondary sources. Below that, it's labeled as weak or left out.

**Confidence labels**: **established** (primary source, or several independent strong sources), **likely** (good but limited evidence), **contested** (credible sources disagree; say who and why), **unknown** (searched and couldn't settle; say what you searched).

## 6. Check coverage and stop at saturation

Fill in the coverage table:

| Sub-question | Status (answered / partly / open) | Key sources | Confidence |
|---|---|---|---|

Keep searching while any sub-question that affects the answer is open. Stop when every sub-question has a status and two further search rounds produce no new claims that change the answer. "I ran out of patience" isn't a stopping point; saturation is. Say what stays open and why.

## 7. Verify citations

Before writing the report, re-open every source you cite and confirm it says what you attribute to it: the quote is exact, the number and its date are right, the context doesn't reverse it. Replace dead links with an archived copy (web.archive.org) or drop the claim. Never cite a source you didn't open; never construct a URL from memory.

## 8. Synthesize and report

Synthesis answers the question; it doesn't summarize each source in turn. Organize by sub-question or theme, reconcile conflicts explicitly, label your own inferences as inferences, and name the gaps.

```markdown
# <Question>

## Bottom line
3-5 sentences that directly answer the question, with confidence stated.

## Key findings
### <Theme / sub-question>
Findings with inline citations [1], [2]; confidence where it matters.

## Comparison (if applicable)
| Option | Criterion A | Criterion B | ... |

## What argues against this
The strongest counter-evidence found in step 4, and why the conclusion survives it (or doesn't).

## Disagreements and uncertainties
What's contested or unknown, and what evidence would settle it.

## Recommendation (if the user needs a decision)

## Coverage
The sub-question table from step 6, plus what was searched and not found.

## Sources
1. Title. Publisher or author, date. URL (accessed <date>)
```

## Rules

- Never fabricate a source, quote, statistic, version, API, or URL.
- Cite the source you read, not one you saw mentioned.
- Quote numbers with their date and context ("$4.2B revenue in FY2025, per the company's 10-K").
- Absence of evidence is reported as "I searched X, Y, Z and found nothing", not as evidence of absence.
- Prefer "I couldn't find reliable data on X" over a plausible guess.
- Tell the user when the evidence contradicts what they assumed (→ `candor`).

## Checklist

- [ ] Sub-questions written before searching; coverage table filled at the end
- [ ] Every claim in the report is in the ledger with a source opened this session
- [ ] Key claims: one primary source read in full, or two independent sources
- [ ] At least one adversarial search per important conclusion, results recorded
- [ ] Every citation re-opened and checked against the claim
- [ ] Confidence labeled; gaps and open questions stated
- [ ] For implementation lookups: version pinned, behavior confirmed in docs, source, or a probe before coding
