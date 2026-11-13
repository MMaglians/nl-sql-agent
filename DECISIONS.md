# Decisions

**MCP instead of calling SQLite directly from the agent.** The database is behind a server with a fixed, reviewable set of tools. The same server can be used by any MCP client, and the agent only sees what the server declares.

**Three tools, schema from code.** `list_tables` and `describe_table` read `schema.py`, not the SQLite catalog, so the model sees curated descriptions and the catalog stays blocked by the authorizer.

**Default-deny authorizer instead of a keyword blacklist.** SQLite asks the authorizer about each operation after parsing the query, so the check is on what the query does, not on how it is written. Allowed: reading the four tables and a closed list of functions. The `SELECT`/`WITH` prefix check only gives a clearer error.

**`mode=ro` as a separate layer.** Writes are blocked by the connection even if the authorizer had a bug. It has its own test, which fails if `mode=ro` is removed.

**Pinned tool definitions.** The client stores a SHA-256 of name, description and input schema of each reviewed tool and stops if anything differs. This catches tool poisoning and later changes (rug pull); it cannot prove that the first reviewed version was safe.

**Approval only for `run_select`, in code.** Approval is enforced by the client, not requested in the prompt, so it does not depend on the model obeying. Schema tools do not need approval: asking for everything leads to approving without reading. A rejection is returned to the model as an error, so it can ask what to change.

**No agent framework.** Same loop as my `nihongo-agent` v0: the model proposes, the code executes, the result goes back, with a 6-step limit. For three tools a framework adds more than it saves.

**Synthetic data and the free tier.** Synthea data is public domain and contains no personal data, which is what makes the Gemini free tier acceptable here.

**Execution accuracy as the first metric.** Comparing query results with gold queries is automatic and order-insensitive, and tolerates rounding and extra columns. It measures the SQL, not the prose; checking answers is the next step.