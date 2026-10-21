# 90-day plan

The first 13 weeks after the board decision. The aim: UC-01 live for the first two document types, governance basics in place, and nobody in the company surprised.

<!--table:90-day-->
**Days 1–30 (weeks 1–4)**

| # | Start | What | Owner | Done when |
|---|---|---|---|---|
| R01 | week 1 | Production build and TMS integration | IT manager | Pipeline posting to the TMS import API, with retries and an audit log |
| R02 | week 3 | Review queue in the doc desk's tooling | Doc desk team lead | Queue that shows flagged fields, reasons and the source document side by side |
| R06 | week 2 | Business KPI dashboard | CFO | Straight-through rate, escapes from the audit sample, review time, value realised |
| R12 | week 1 | AI orchestration layer v1 | IT manager | Model gateway, prompt registry, logging, evaluation harness, cost tracking |
| R13 | week 1 | TMS document API agreed with the vendor | IT manager | Documented endpoint for document records; file-drop fallback |
| R14 | week 2 | Data owners for customer, location and document data | COO | Named owners, change process, monthly quality report |
| R16 | week 1 | AI policy and acceptable use | CEO | One-page policy, approved tools list, rules for customer data |
| R17 | week 2 | AI inventory and EU AI Act classification | DPO | Register of AI systems with risk tier, owner and review date; quarterly refresh |
| R18 | week 4 | AI in the ISO/IEC 27001 ISMS | IT manager | AI suppliers assessed, risk register and Statement of Applicability updated |
| R20 | week 3 | AI literacy programme (three tiers) | HR | All staff 90 minutes; users half a day; builders two days |
| R21 | week 1 | Works council information and consultation | HR | Plan presented before go-live; agreement on no redundancies and attrition |

**Days 31–60 (weeks 5–9)**

| # | Start | What | Owner | Done when |
|---|---|---|---|---|
| R03 | week 7 | Shadow mode on real documents | Doc desk team lead | Pipeline runs next to the clerks; differences labelled; first real evaluation set |
| R15 | week 8 | Labelled evaluation sets per use case | Doc desk team lead | Real documents, labelled during review, refreshed quarterly |
| R22 | week 8 | Sanctioned AI assistant for all office staff | IT manager | One approved assistant inside Microsoft 365; covers drafting and knowledge needs (UC-04, UC-10) without custom builds |
| R23 | week 6 | AI champions network | COO | Eight champions, two hours a week, monthly show-and-tell |

**Days 61–90 (weeks 10–13)**

| # | Start | What | Owner | Done when |
|---|---|---|---|---|
| R04 | week 12 | Go-live: bills of lading and packing lists | COO | Two document types straight-through within the error budget |
<!--/table-->

## What "done" looks like on day 90

- [ ] Bills of lading and packing lists go straight to the TMS when they pass, within the 1% error budget, measured on real documents (gate G2)
- [ ] Clerks work from the review queue every day; review time per document is measured
- [ ] KPI dashboard live: straight-through rate, escapes from the 5% audit, review time, value realised against plan
- [ ] AI policy approved and published; approved tools list in place
- [ ] AI inventory complete, every system classified under the EU AI Act, owners named
- [ ] Works council informed and consulted; commitments in writing
- [ ] All staff invited to the 90-minute AI literacy session; doc desk trained on the review queue
- [ ] Orchestration layer v1 running: model gateway, prompt registry, logging, evaluation harness, cost per document

## Weekly rhythm

| When | What | Who |
|---|---|---|
| Monday 30 min | Review queue retro: which flags were useful, which were noise | Doc desk lead, two clerks, AI engineer |
| Wednesday 45 min | Delivery stand-up across streams | Partner lead, IT manager, doc desk lead |
| Every 4 weeks | Steering: gate decisions, risks, value | CEO, CFO, COO, IT manager, partner lead |
