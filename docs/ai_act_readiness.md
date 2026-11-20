# AI Act readiness: nl-sql-agent

Self-assessment written on 2026-11-20 against Regulation (EU) 2024/1689 as amended by the Digital Omnibus on AI, Regulation (EU) 2026/1744 (in force since 27 July 2026). A structured exercise for a portfolio project, **not legal advice**.

## 1. System and intended purpose
- **What it does:** turns questions in Italian into SQL `SELECT` queries on a healthcare database and answers with the numbers and the query used.
- **Intended purpose:** aggregate descriptive statistics for analysts (counts, averages, costs, durations). **Not** for decisions about individual patients: no diagnosis, treatment, triage, prioritisation or eligibility for care.
- **Users:** analysts who can read SQL and approve every query. **Affected persons:** the patients whose records are queried.
- **Model and data:** a general-purpose model through an API (Gemini); synthetic data (Synthea), no personal data.

## 2. Roles
| Party | Role | Main consequence |
|---|---|---|
| Me | Provider of the AI system (I build it and publish it under my name, open source) | Classification, transparency, documentation |
| An organisation using it | Deployer | Use within the intended purpose, human oversight, AI literacy of staff |
| Google | Provider of the general-purpose model | Its own obligations (Chapter V), not mine |

A deployer who changes the intended purpose, for example to decide on individual patients, can become the provider of a new high-risk system (Art. 25).

## 3. Classification
| Step | Answer | Reason |
|---|---|---|
| AI system (Art. 3(1))? | Yes | an LLM infers queries and answers from the input |
| Prohibited practice (Art. 5)? | No | no manipulation, social scoring or biometrics |
| High-risk through Annex I (medical device)? | No, with this intended purpose (my assessment) | descriptive statistics on aggregated data, no medical purpose for individual patients |
| High-risk through Annex III? | No | not used by a public authority to assess eligibility for healthcare (point 5(a)), nor for emergency triage (point 5(d)) |
| Transparency (Art. 50)? | Yes, Art. 50(1) | people must be told they are dealing with an AI system unless it is obvious |
| **Result** | **Not high-risk; transparency obligations apply** | |

## 4. Obligations and status
| Obligation | Applies from | Status |
|---|---|---|
| Art. 50(1): tell users they are interacting with AI | 2 August 2026 | **Done in v0.2.0:** notice at the start of the chat |
| Art. 50(2): machine-readable marking of generated text | 2 December 2026 for systems already on the market | **Open:** applicability to internal analytical answers to be assessed with a legal advisor |
| Art. 4: measures to support AI literacy | in force (amended by the Omnibus) | README states limits and that the approver must read SQL; a deployer would need short training |
| GDPR (not AI Act): health data are a special category (Art. 9), DPIA (Art. 35) | already applicable | Not triggered: synthetic data. Blocking before any real data |

## 5. Voluntary alignment with high-risk requirements
Not required for this class, but the design already covers the same ground:
| Requirement for high-risk systems | In this project |
|---|---|
| Risk management (Art. 9) | [threat model](threat_model.md) with residual risks |
| Data governance (Art. 10) | data minimisation: identifying columns never loaded; synthetic data |
| Record-keeping (Art. 12) | JSONL traces of every question, tool call and refused query |
| Information to deployers (Art. 13) | README: intended use, results with intervals, limits |
| Human oversight (Art. 14) | every query approved in code before it runs |
| Accuracy, robustness, cybersecurity (Art. 15) | eval with pre-registered criteria; prompt-injection tests; read-only connection and default-deny authorizer |

## 6. What would change the classification
- Supporting decisions on individual patients (diagnosis, treatment, prioritisation): likely medical-device software, so high-risk through Annex I (obligations from 2 August 2028).
- Use by a public authority to assess eligibility for healthcare services, or for emergency triage: high-risk through Annex III point 5 (obligations from 2 December 2027).
- Real patient data: the GDPR obligations above, whatever the AI Act class.

## 7. Recommendations
1. Keep the intended purpose and the excluded uses in the README and in any contract with a deployer.
2. Assess Art. 50(2) with a legal advisor before any distribution after 2 December 2026.
3. Before real data: DPIA, a data-processing agreement or a local model, and a minimum group size for answers (threat model T7, T11).
4. Train approvers to read SQL, and log approvals (T9).