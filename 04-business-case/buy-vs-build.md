# Buy vs build

Three ways to put document AI into the doc desk, compared on the criteria the leadership team cared about. Vendors are described by category, not named: the point is the decision logic, and a real selection would run a short RFP with two vendors per category.

## Options

| | A. Buy: document-AI SaaS for logistics | B. Buy: TMS vendor's add-on | C. Build on a foundation model, behind our own orchestration layer |
|---|---|---|---|
| What it is | Specialised SaaS that reads freight documents and exports data | Module offered by the existing TMS vendor | Pipeline like the pilot: foundation model reads, our rules check, our queue routes |
| Time to first value | Fast (weeks), if their templates fit our documents | Depends on the vendor roadmap (announced for 2027) | Pilot exists; production in about 12 weeks |
| Fit with our documents and rules | Good for standard documents; our cross-document checks and customer rules need custom work or are not possible | Unknown; not demonstrated on our documents | Full: rules V01-V14 and the review flow are ours |
| Cost profile | Per-page licence; grows with volume | Licence on top of the TMS contract | Build cost up front; low run cost (model usage about €0.02 per document) |
| Lock-in | Medium: data export usually possible, rules live in their tool | High: tied to the TMS | Low: provider behind a gateway; the offline provider proves the switch |
| Governance and evaluation | Vendor's metrics; our own evaluation requires their cooperation | Vendor's metrics | Our own evaluation and release gate on our documents |
| Reuse for UC-09 and UC-03 | Partly (UC-09 if invoices are supported) | No | Yes, same platform |
| Skills needed in house | Low | Low | Medium: one developer plus partner support in year 1 |

## Decision

**C, with a market check.** The deciding factors were the cross-document checks (where most of the error value is), reuse for UC-09 and UC-03, and owning the evaluation. Cost was not decisive: at about 50,000 documents a year, a per-page licence and the build land in the same range over three years at typical per-page prices, so the market check asks vendors for a price on our volumes rather than a list price.

The market check is part of gate G1: two document-AI SaaS vendors run our 220-document test set (the same one the pilot was measured on). If one of them beats the pilot's error escape rate at a comparable straight-through rate and allows our cross-document rules, we switch to A before the production build starts. The evaluation harness makes that comparison cheap, which is one of the reasons to have it.

## The general rule we apply

| Buy when | Build when |
|---|---|
| The problem is common and the vendor's template fits | The value sits in company-specific rules or data |
| Speed matters more than control | Evaluation and governance must be in your hands |
| You cannot staff ongoing ownership | You will reuse the capability for several use cases |
| The vendor can be evaluated on your data | The run cost of a licence grows faster than the build cost |

UC-07 (route optimisation) lands on the other side of this rule: planning solvers are mature products, and Wendelkaai's routing problem is not unusual. It is a **buy**.
