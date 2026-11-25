# Untrusted input to dangerous sinks

For each entry point, follow the input through every transformation to where it's used. One row per sink class.

| Sink | Vulnerability | Look for |
|---|---|---|
| SQL / NoSQL queries | Injection | String building or interpolation into queries; raw query APIs; `$where`, `$regex` with user input; ORDER BY / column names from input |
| Shell / process exec | Command injection | `exec`, `system`, `subprocess(..., shell=True)`, backticks, argument injection (`--` options from user input) |
| File paths | Path traversal | User input in `open`, `readFile`, `send_file`; archive extraction (zip slip); symlink following |
| HTML / DOM | XSS | `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, `\|safe`, `document.write`, `javascript:` URLs, unescaped attributes, DOM sinks fed by `location` or `postMessage` |
| Outbound requests | SSRF | Server-side fetch of user URLs, webhooks, URL previews, PDF/image renderers; redirects to internal IPs; DNS rebinding; cloud metadata (`169.254.169.254`) |
| Deserializers | RCE | `pickle`, `yaml.load`, `marshal`, Java `ObjectInputStream`, PHP `unserialize`, .NET `BinaryFormatter`, `node-serialize` |
| Redirects | Open redirect | User input in `Location` headers or `next=` params without an allowlist |
| XML parsers | XXE | External entities or DTDs enabled; SVG and Office file uploads |
| Templates | SSTI | User input compiled as a template (Jinja, Twig, Handlebars, Velocity) |
| Regex | ReDoS | Nested quantifiers matched against user input |
| Object merging | Prototype pollution / mass assignment | Deep merge of user JSON; `__proto__`, `constructor`; binding request bodies straight to models |
| Headers / emails | Header and CRLF injection | User input in response headers, email headers, or log lines |
| Spreadsheet exports | CSV/formula injection | Cells starting with `=`, `+`, `-`, `@` |
| LDAP / XPath / GraphQL | Query injection | String-built filters and queries |
| LLM prompts | Prompt injection | Untrusted content (web pages, emails, files, tool output) placed in prompts of agents that have tools, data access, or the ability to send data out |
| Logs | Log injection, data leaks | Unsanitized newlines; secrets, tokens, or PII logged |

Also check **second-order** flows: data that's stored safely, then later read back and used unsafely, such as a username rendered unescaped in an admin panel.
