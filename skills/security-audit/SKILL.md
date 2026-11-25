---
name: security-audit
description: Find, prove, and fix security vulnerabilities in code, configuration, infrastructure, and dependencies (injection, broken access control, business logic flaws, races, secrets, SSRF, XSS, crypto, supply chain, cloud, client apps, LLM prompt injection), with every entry point accounted for and every serious finding backed by a test or a traced path. Reports in plain language with technical detail underneath. Use when the user asks for a security review or audit, asks whether something is secure, changes authentication, authorization, payments, or cryptography, or prepares for a release, compliance review, or pentest. For defensive and authorized use only.
---

# Security Audit

Think like an attacker, report like an engineer. A useful audit covers every way in, proves each finding is reachable, and fixes the whole class of bug. Scanner output isn't an audit. Neither is a checklist ticked without reading the code.

## Scope and ethics

- Audit only code and systems the user owns or is authorized to test.
- Describe vulnerabilities and fixes. Don't produce weaponized exploits for third-party systems.
- If you find a live secret, tell the user to rotate it immediately. Don't use it.
- Don't run active attacks (fuzzing, load tests, exploit attempts) against production or shared environments without explicit permission.

## Files and related skills

| What | Where |
|---|---|
| Sink table: untrusted input → SQL, shell, paths, HTML, SSRF, deserializers, templates, regex, prompts | `references/sinks.md` |
| Area checklists: authentication, business logic, uploads, crypto, web/API config, DoS, supply chain, cloud, memory safety, logging, client apps, AI agents, secure defaults | `references/checklists.md` |
| Report template with plain-language and technical layers | `references/report-template.md` |
| Structural findings (no trust boundary, no tenant isolation) | `architecture` |
| CVEs, library security history, current protocol guidance | `deep-research` |
| Reproducing a suspected issue | `debugging` |
| Reviewing the fix diff | `code-review` |
| Proving each claim and that coverage is complete | `verify` |

## Audit depth

State the depth in the report.

- **Quick review** (one change or feature): steps 1–4 and 6–8 for the touched entry points only, plus secrets and dependency checks.
- **Standard audit** (a service or app): every step.
- **Deep audit** (pre-release, high-risk, compliance): every step, the full authorization matrix, variant analysis for every finding, and a scan of the whole git history.

## Workflow

### 1. Recon: enumerate every way in

- **Stack**: languages, frameworks, ORM, template engine, auth library, build, deploy, and hosting. This decides which sections of `references/checklists.md` apply.
- **Entry points, with a command.** List every HTTP route, GraphQL resolver, RPC handler, WebSocket handler, message consumer, webhook, scheduled job, CLI argument, file upload, and anything else that parses outside input. Use the framework's route table or a search (`grep -rnE "@(app|router)\.(get|post|put|patch|delete)"`, `rails routes`, `php artisan route:list`), not memory. Write the list to a coverage file in your scratch directory with its count: "63 entry points".
- **Trust boundaries**: where untrusted data enters and where privilege changes (anonymous → user → admin → system, tenant A → tenant B, client → server, service → service).
- **Assets**: credentials, tokens, PII, payment and health data, admin functions, availability.
- **Threat model**: apply STRIDE at each boundary and audit the threats that matter for this system first.
- **Prior art**: past advisories and pentest reports for this codebase and its main dependencies.

**Done when** the coverage file lists every entry point with a count, produced by a command you can rerun.

### 2. Run automated tools as a starting point

Tools find candidates, not findings. Each result still needs reading and proof.

| Purpose | Tools |
|---|---|
| Static analysis | `semgrep` with security rulesets, CodeQL, `bandit`, `gosec`, `brakeman`, `eslint-plugin-security`, FindSecBugs |
| Secrets | `gitleaks detect` or `trufflehog git file://.` across the **full history** |
| Dependencies | `npm audit`, `pip-audit`, `cargo audit`, `govulncheck`, `osv-scanner`, triaged by whether the vulnerable function is actually called |
| Containers and IaC | `trivy`, `grype`, `checkov`, `tfsec`, `hadolint` |
| CI workflows | `zizmor`, `actionlint` |

Check which tools are installed before running them. Say which ones you couldn't run.

### 3. Walk every entry point

For each entry point in the coverage file, mark it done only after answering:

1. **Who can call it?** Unauthenticated, any user, a role, another service.
2. **Where does each input go?** Follow it through every transformation to every sink, using `references/sinks.md`. Include second-order flows: data stored safely, then read back and used unsafely later.
3. **Is access checked on the server, against this specific object?** (Step 4.)
4. **What happens out of order, twice, in parallel, or with odd values?** (Business logic and races in `references/checklists.md`.)

Then apply the checklist sections that match the stack and features from recon. Skip sections that don't apply and say so in the coverage notes.

### 4. Authorization: the highest-yield step

Most serious real-world findings are here. Check every entry point, not a sample.

- **Missing checks**: every route and action enforces authentication and authorization on the server. Look hardest at new, "internal", admin, export, and bulk endpoints.
- **IDOR / BOLA**: can user A read or change user B's object by changing an ID in the path, body, query, or a nested field? Queries are scoped by owner or tenant, not just by ID.
- **Function-level access**: can a regular user call admin operations directly?
- **Mass assignment**: can a request set `role`, `isAdmin`, `ownerId`, `tenantId`, `price`, or `verified`?
- **Tenant isolation**: every query, cache key, file path, search index, and background job is scoped by tenant.
- **Indirect access**: exports, reports, search, webhooks, notifications, and GraphQL nested resolvers that return objects the caller can't access directly.
- **Client-side trust**: permissions, prices, or flags decided by the client and accepted by the server.
- **Consistency**: the same resource is enforced the same way across REST, GraphQL, WebSocket, and background paths.
- **Authorization matrix** (standard and deep): a table of role × resource × action (read, create, update, delete, list, export), each cell checked against the code. Empty cells are where bugs hide.
- **Negative tests**: tests exist proving users *can't* do what they shouldn't. Most suites only test the happy path.

### 5. Coverage gate

Before writing findings up, rerun the step 1 command and compare against the coverage file: **reviewed N of N**. Any entry point not reviewed is listed in the report's Coverage section with the reason. "Reviewed the main routes" is not coverage.

### 6. Prove each finding

A finding's severity depends on proof, not on how bad it sounds.

- **Medium and above need one of:** a failing test or script against a local or test environment that demonstrates the issue, or a traced path from attacker-controlled input to impact with `file:line` at every hop (entry → transformations → sink) and the preconditions (auth required, specific config, role). Without either, report it as **unconfirmed** and say what would confirm it.
- **Check the mitigations** in the path: framework auto-escaping, ORM parameterization, middleware, WAF rules, network isolation. Don't report what's already handled; do note when one mitigation is the only thing between the input and the sink.
- **Variant analysis**: for every confirmed finding, search the whole codebase for the same pattern. One instance usually means more. Report the count: "same unscoped `findById` in 4 of 31 handlers".
- **Attack chains**: several low-severity issues can combine into a critical one (open redirect + token in URL → account takeover; verbose error + IDOR → full data dump). Rate a chain by its combined impact.
- **Abuse cases**: for each major feature, ask how a malicious user, a curious user, a competitor, or a compromised account would misuse it.
- **Severity** = impact × exploitability: who can do it, how hard it is, what they gain. Use CVSS if the team does.

| Severity | Typical examples |
|---|---|
| Critical | Unauthenticated RCE, auth bypass, cross-tenant data access, leaked production credentials |
| High | Authenticated RCE, IDOR on sensitive data, stored XSS in admin views, SSRF to internal services |
| Medium | Reflected XSS, CSRF on important actions, no rate limit on login, verbose errors leaking internals |
| Low | Missing hardening headers, minor information disclosure |
| Informational | Defense-in-depth suggestions with no direct exploit |

### 7. Fix and re-attack (when asked to fix)

- **Fix the root cause and every variant**, following the fix principles below.
- **Regression test per fix** that fails before and passes after. For authorization bugs, the test proves the forbidden action is now denied.
- **Re-attack the fix.** Try to get around it with encoding tricks, alternate endpoints, other HTTP methods, case changes, and parallel requests. A fix that blocks one payload but not the class isn't a fix.
- **Prevent the class**: where possible, add a lint rule, a type, a shared helper, or a test that makes the vulnerable pattern fail the build (for example, a semgrep rule for unscoped queries).
- Rerun the tools from step 2 and the full test suite, and check legitimate use still works and nothing now fails open.

### 8. Report

Use `references/report-template.md`. Every finding is written for two readers: a plain-language explanation (who could do it, what they'd get, how likely; → `plain-speech`), then the technical detail with evidence, fix, variants, and verification. Be calm and specific about risk; don't hype it or downplay it.

The **Coverage** section is mandatory: depth, entry points reviewed out of the total, tools run and not run, checklist sections skipped and why. An audit that hides its gaps gives false confidence.

Send fixes through `code-review` before merging. Structural findings belong in an `architecture` discussion, not only a patch.

## Fix principles

- Parameterized queries and safe APIs, not hand-written sanitizing.
- Allowlists over denylists.
- Validate input at the boundary; encode output for its context.
- Deny by default; require explicit grants.
- Least privilege for users, services, tokens, and containers.
- Fail closed when config is missing or a dependency is down.
- Never ship a "temporary" bypass of a security control.

## Output checklist

- [ ] Entry points enumerated by command, with a count; coverage N/N or gaps listed with reasons
- [ ] Checklist sections chosen from the stack; skipped sections named
- [ ] Every Medium+ finding has a failing test or a `file:line` traced path; the rest marked unconfirmed
- [ ] Variant analysis run for every confirmed finding, with counts
- [ ] Fixes re-attacked and covered by regression tests; tools and suite rerun
- [ ] Report has the plain-language layer for every finding and an honest Coverage section
