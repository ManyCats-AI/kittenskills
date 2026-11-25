# Report template

Every finding is written for two readers: a plain-language explanation anyone can follow, then the technical detail. For a quick review, keep the structure and shorten it; the plain-language summary, the "In plain terms" line, and the "What we changed / Why this fixes it" lines are never optional.

## Writing the plain-language parts

- Explain it the way you'd explain it to a smart friend who doesn't write code. If you must use a term like "SQL injection", say what it means in one clause.
- Say **who** could do it (anyone on the internet, any logged-in user, only an admin), **what** they'd get or break, and **how likely** it is.
- Use an everyday analogy only when it helps, and keep it to one sentence.
- For changes, say **what's different now** from the user's or attacker's point of view, then why that closes the hole.

## Template

```markdown
# Security Audit: <scope>

## Plain-language summary
3–6 sentences for a non-technical reader: how secure this is overall, the most serious problems in everyday terms, what was fixed, and what still needs a decision or action from them.

## At a glance
| # | Severity | Problem (plain terms) | Status |
|---|---|---|---|
| 1 | High | Logged-in users could view other customers' invoices | Fixed |
| 2 | Medium | Login allowed unlimited password guesses | Fixed |
| 3 | Low | Error pages reveal server software versions | Open, recommended |

## Findings

### 1. [HIGH] Users can view other customers' invoices: `src/api/invoices.ts:88`

**In plain terms:** Anyone with an account could see any customer's invoice, including names, addresses, and amounts, just by changing the number at the end of the invoice link. It's like a hotel where every guest's key opens every room.

**Why it matters:** This exposes private customer data to every user of the app. It's easy to do, needs no special tools, and could be automated to download every invoice.

**What we changed:** The server now checks that an invoice belongs to the person asking before showing it. If it doesn't, they get a "not found" response, which also avoids confirming that the invoice exists.

**Why this fixes it:** Access is now decided by who you are, not by which number you type. Changing the link no longer gets you anything.

**Technical detail:**
- *Issue:* IDOR / broken object-level authorization (CWE-639). `GET /api/invoices/:id` loads by ID without an owner or tenant scope.
- *Evidence:* The route handler calls `Invoice.findById(req.params.id)`, with no ownership check in middleware or the model.
- *Fix:* Query scoped by `{ id, tenantId: req.user.tenantId }`; return 404 on a miss.
- *Variants:* The same pattern was found and fixed in `credit-notes.ts:41` and `exports.ts:112`.
- *Verification:* New tests in `invoices.authz.test.ts` show cross-tenant access returns 404. The full suite passes.
- *References:* OWASP API1:2023 (BOLA), CWE-639.

## Changes made
| What changed | Why | Files |
|---|---|---|
| Invoices, credit notes, and exports now check ownership | Stop users from seeing other customers' data | `invoices.ts`, `credit-notes.ts`, `exports.ts` |
| Login locks for 15 minutes after 5 failed attempts | Stop automated password guessing | `auth/login.ts`, migration `0042` |

## What still needs attention
Open findings, decisions only the owner can make (for example, rotating a leaked key, or accepting a risk), and recommended next steps, in priority order.

## Hardening recommendations
Defense-in-depth improvements that aren't vulnerabilities on their own, each with a one-line plain-language reason.

## Coverage
Audit depth, entry points reviewed vs. total, tools run, and areas not reviewed (and why). Be honest here: an audit that hides its gaps gives false confidence.
```
