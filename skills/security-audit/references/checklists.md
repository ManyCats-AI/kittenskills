# Area checklists

Read only the sections that match the stack and features found in recon. Each item is a question to answer against the code, with `file:line` evidence.

## Authentication

- **Passwords**: hashed with argon2id, bcrypt, or scrypt with sane parameters; length minimums; breached-password checks where appropriate.
- **Brute force**: rate limiting and lockout on login, password reset, MFA, and any endpoint that checks a secret or code.
- **Enumeration**: login, signup, and reset return the same response and timing whether or not the account exists.
- **Password reset**: tokens random, single-use, short-lived, and bound to the account; no host-header injection in reset links.
- **MFA**: can't be bypassed by skipping a step, replaying codes, or changing the flow order.
- **Sessions**: `Secure`, `HttpOnly`, and `SameSite` cookies; session ID rotated at login and privilege change (no fixation); server-side invalidation at logout and password change; sensible idle and absolute timeouts.
- **JWTs**: signature verified with a pinned algorithm (no `none`, no RS/HS confusion); `exp`, `aud`, and `iss` checked; keys rotated; nothing sensitive in the payload; a revocation story for long-lived tokens.
- **OAuth / OIDC / SAML**: `state` and PKCE used, redirect URIs matched exactly, ID tokens validated, account linking safe against email-based takeover, SAML signatures verified on the right element.
- **API keys and service tokens**: scoped, revocable, stored hashed, and never sent in URLs.

## Business logic and race conditions

Scanners can't find these. Read the flows and ask "what if I do this out of order, twice, or with weird values?"

- **Workflow bypass**: skipping steps (payment, email verification, approval) by calling a later endpoint directly.
- **Numeric abuse**: negative quantities, zero prices, integer overflow, float rounding in money (use integer cents or decimals), currency mismatch.
- **Limits and quotas**: coupons, trials, invites, and rate-limited actions that can be reused, stacked, or reset.
- **Race conditions and TOCTOU**: double-spend, double-redeem, or over-withdraw by sending parallel requests. Look for check-then-act without locking, transactions, unique constraints, or idempotency keys.
- **State machines**: transitions that should be impossible (refund after refund, cancel after shipment).
- **Replay**: signed requests, webhooks, and one-time links that can be reused. Check nonces, timestamps, and signature verification.

## Files and uploads

- Content type validated server-side by content, not by extension or the client's `Content-Type`.
- Size limits, and protection against decompression bombs.
- Stored outside the web root, with random names, and served with `Content-Disposition: attachment` and a safe `Content-Type`.
- No path traversal in names; no zip slip on extraction.
- Image, PDF, and Office processing (ImageMagick, Ghostscript, LibreOffice) sandboxed and kept up to date.
- SVG and HTML uploads never served inline from the main origin.

## Cryptography and secrets

- **Secrets in code**: `git grep -nE '(api[_-]?key|secret|passw(or)?d|token|BEGIN [A-Z ]*PRIVATE KEY)'` plus the history scan from step 2. Check `.env` files, config, test fixtures, Dockerfiles, CI configs, and client bundles.
- **Algorithms**: no MD5 or SHA-1 for security purposes, no DES/3DES/RC4, no ECB mode, no unauthenticated encryption (use AES-GCM or ChaCha20-Poly1305), and no homemade crypto.
- **Randomness**: a CSPRNG for tokens, IDs that must be unguessable, salts, and nonces. Never `Math.random`, `random.random`, or a time-based seed. Check token entropy (→ `math`).
- **Nonces and IVs**: never reused with the same key.
- **Comparisons**: constant-time comparison for MACs, tokens, and signatures.
- **Key management**: keys in a KMS or secret manager, rotated, scoped per environment, and never logged.
- **Data at rest**: sensitive fields encrypted where required, backups protected, and PII minimized.
- **Transport**: TLS enforced everywhere including internal traffic where required, HSTS set, and certificate verification never disabled (`verify=False`, `rejectUnauthorized: false`, `InsecureSkipVerify`).

## Web and API configuration

- **Headers**: Content-Security-Policy (no `unsafe-inline` or `unsafe-eval` where avoidable), `X-Content-Type-Options: nosniff`, `frame-ancestors` or `X-Frame-Options`, Referrer-Policy, and Permissions-Policy.
- **CORS**: no reflected origins combined with credentials, no `null` origin, and no `*` on authenticated APIs.
- **CSRF**: protection on every state-changing, cookie-authenticated request, including JSON endpoints and GraphQL.
- **GraphQL**: query depth and complexity limits, introspection off in production if the schema is sensitive, batching limits, and authorization in resolvers.
- **WebSockets**: origin checked at handshake, and authentication and authorization enforced per message.
- **Errors and debug**: no stack traces, SQL errors, or internal paths in responses; debug modes and admin consoles off in production.
- **HTTP layer**: request smuggling risks behind proxies, web cache poisoning through unkeyed headers, and host-header trust.
- **`postMessage`**: the origin is checked on receive, and the target origin is set on send.

## Denial of service and resource limits

- Rate limits on expensive and sensitive endpoints, per user and per IP.
- Limits on request body size, upload size, page size, batch size, nesting depth, and regex input length.
- Timeouts on every outbound call and every query.
- No unbounded loops, recursion, or allocation driven by user input.
- Costly operations (exports, report generation, image processing) queued and limited.
- See `performance-optimization` for measuring the real cost of an endpoint under load.

## Supply chain and build

- Dependency advisories triaged by **reachability**: is the vulnerable function actually called?
- Lockfiles committed and used in CI (`npm ci`, `pip install --require-hashes`, `cargo --locked`).
- Watch for typosquatted, abandoned, or newly ownership-transferred packages, and for install scripts from untrusted packages.
- CI/CD: third-party actions pinned to a commit SHA, minimal `GITHUB_TOKEN` permissions, no secrets exposed to fork PRs, no `pull_request_target` checkouts of untrusted code, and no script injection from issue or PR titles.
- Build artifacts and container images signed or produced reproducibly where practical; base images current.

## Infrastructure and cloud

- Containers run as non-root with read-only filesystems where possible, no privileged mode, and dropped capabilities.
- Kubernetes: network policies, RBAC least privilege, no default service account tokens mounted unnecessarily, and secrets not stored in plain ConfigMaps.
- Cloud IAM least privilege, with no wildcard actions or resources on sensitive services.
- No public storage buckets, snapshots, or databases unless intended; security groups don't open admin ports to the internet.
- The metadata service is protected (IMDSv2 on AWS).
- Separate environments with separate credentials.

## Memory safety (C, C++, unsafe Rust, cgo, native extensions)

- Buffer overflows, off-by-one errors in bounds checks, and unchecked `memcpy`/`strcpy`/`sprintf`
- Use-after-free, double free, and uninitialized memory
- Integer overflow in size calculations before allocation
- Format string vulnerabilities
- `unsafe` blocks: check that every invariant they rely on actually holds
- Build hardening: ASLR, stack protector, FORTIFY_SOURCE, RELRO; run sanitizers (ASan, UBSan) and fuzzers where possible

## Logging, monitoring, and privacy

- Security-relevant events are logged with the actor: logins, failures, permission denials, admin actions, and key changes.
- Logs never contain passwords, tokens, full card numbers, or unnecessary PII.
- Alerts exist for brute force, unusual admin activity, and spikes in authorization failures.
- Data retention and deletion work as promised, including in backups, logs, and analytics.

## Client apps (mobile, desktop, browser extensions)

- Never trust the client. Every check that matters is repeated on the server.
- No API keys, secrets, or privileged endpoints shipped in the app bundle. Assume the app is decompiled.
- Tokens stored in the platform's secure storage (Keychain, Keystore, OS credential vault), not plain files or `localStorage` when avoidable.
- Deep links, custom URL schemes, and intents validated as untrusted input.
- Electron and similar: `contextIsolation` on, `nodeIntegration` off, a strict CSP, a minimal preload API, and no `shell.openExternal` on untrusted URLs.
- Browser extensions: minimal permissions and host access, no remote code, and content-script messages treated as untrusted.
- Auto-updates signed and fetched over TLS.

## AI features and agents

- **Prompt injection**: any untrusted text the model reads (web pages, documents, emails, tickets, tool results) can contain instructions. Assume it will.
- **Tool permissions**: what can the model do if it's tricked? Agents that read untrusted content shouldn't also have unrestricted write, delete, payment, or outbound network tools without human approval.
- **Data exfiltration**: check for ways to leak data through rendered links, images, markdown, or tool calls that reach attacker-controlled URLs.
- **Output handling**: model output is untrusted input. Never pass it to `eval`, shells, SQL, or HTML without the same safeguards as user input.
- **Data scope**: the model sees only data the current user is allowed to see. Retrieval and RAG indexes respect per-user and per-tenant permissions.
- **Secrets**: no API keys or secrets in system prompts, which can be extracted.
- **Cost and abuse**: rate limits and token caps per user.

## Secure-by-default review

Check what happens when someone deploys with **default settings** and changes nothing:
- Is anything public, listening on all interfaces, or reachable without authentication?
- Are debug modes, sample accounts, default passwords, or test endpoints active?
- Are new resources (buckets, repos, links, records) private by default?
- Does the app fail closed (deny access) when config is missing or an auth service is down, rather than fail open?
- Is telemetry opt-in, and is data collection minimal?

Any "yes" to an insecure default is a finding, even if the docs tell people to change it.
