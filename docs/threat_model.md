# Threat model

Scope: `nl-sql-agent` v0.2.0, a single-user terminal app over synthetic Synthea data, using the Gemini API. Written on 2026-11-20 from the tests and eval results in this repository.

**Assets:** integrity of the database; confidentiality of patient records; correctness of the numbers in answers; availability; the API key.

**Trust boundaries:** the user message, the model output, the rows returned by the database and the MCP tool definitions are all untrusted text. Only the code of the client and of the server is trusted.

| # | Threat | Example | Controls | Evidence | Residual risk |
|---|---|---|---|---|---|
| T1 | Data modification | `DELETE` from the user or hidden in a row | `mode=ro`, default-deny authorizer, human approval | unit tests; injection: 0/6 effect | Low |
| T2 | Reading outside the allowed scope | `sqlite_master`, `PRAGMA`, `ATTACH` | authorizer allow-list | unit tests; injection: tried 3/3, effect 0/3 | Low |
| T3 | Over-reading patient records | `SELECT * FROM patients`; exploratory reads on unanswerable questions | data minimisation, 200-row limit, human approval, prompt v1 | injection 0/3; abstention 4/5 | Medium: depends on the approver |
| T4 | Indirect injection changing the answer | instruction hidden in a medication description | none in code; the prompt only | injection: read 9/9, followed 0/9 | Medium: not covered by code |
| T5 | System-prompt disclosure | "repeat your system prompt" | no secrets in the prompt | injection: 3/3 disclosed | Accepted: the prompt is public |
| T6 | Tool poisoning, rug pull | a tool description changed after review | allow-list of 3 tools, SHA-256 pins | unit tests | Low; pins cannot prove the first review was right |
| T7 | Re-identification from quasi-identifiers | county of the patient with the highest expenses | names, addresses, SSN, income, ethnicity never loaded | eval question x05 | Medium with real data |
| T8 | Wrong numbers in the answer text | correct query, wrong number written | numbers must come from `run_select`; query shown | not measured | Medium |
| T9 | Approval fatigue | the approver accepts without reading | approval only for `run_select`, not for schema tools | not testable in code | High in real use |
| T10 | Resource exhaustion | slow or very large query | 3 s timeout, 200 rows, 4,000 characters | unit tests | Low |
| T11 | Patient data sent to a third-party model | prompts and rows go to the Gemini API | synthetic data only | n/a | Blocking with real data |
| T12 | Secret leakage | API key in a commit or a log | `.env` ignored, `.env.example`, CI without secrets | review | Low |

**Next steps, by risk:** (1) with real data, a paid tier with a data-processing agreement or a local model, and a DPIA (T11); (2) a minimum group size for aggregated answers and no county-level columns (T7); (3) check the answer text against the query result, with a judge validated on this project (T8); (4) more injection wordings, more repetitions and a second model (T4); (5) approver training and a log of approvals (T9).