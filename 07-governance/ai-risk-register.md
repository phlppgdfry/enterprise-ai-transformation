# AI risk register

Fourteen risks for the roadmap's first year, sorted by score (likelihood × impact, 1-5 each; 12 and above is red). Owners are Wendelkaai managers, never the consultants. The register lives in [model/risks.json](../model/risks.json) and is reviewed at every gate.

<!--table:risks-->
| # | Risk | Category | L | I | Score | Owner | Mitigation | Controls |
|---|---|---|---|---|---|---|---|---|
| RK-01 | Clerks distrust the system and re-key documents anyway, or work around it | Adoption | 3 | 4 | 12 | Doc desk team lead | Co-designed review queue; pilot clerks as champions; written commitment on no redundancies; weekly numbers shared with the team. | ISO/IEC 42001 7.3 Awareness |
| RK-03 | TMS vendor delivers the document API late | Delivery | 4 | 3 | 12 | IT manager | Vendor engaged in week 1; file-drop import as fallback (already supported for bookings). | ISO/IEC 27001 A.5.20 Addressing information security within supplier agreements |
| RK-07 | Freed hours are absorbed without measurable value | Value | 3 | 4 | 12 | CFO | Cash view is the decision basis; attrition decision explicit and agreed; value tracked monthly per gate. | - |
| RK-08 | Staff keep pasting customer data into public chatbots (shadow AI) | Privacy & security | 4 | 3 | 12 | CEO | AI policy; one sanctioned assistant inside Microsoft 365; literacy training; DLP rules for known chatbot domains. | ISO/IEC 27001 A.5.10 Acceptable use of information; ISO/IEC 27001 A.8.12 Data leakage prevention; ISO/IEC 27001 A.6.3 Information security awareness, education and training |
| RK-12 | Pilot results do not hold on real documents | Quality | 3 | 4 | 12 | COO | Shadow mode on real volume before go-live; gate G2 measured on real documents, not on the pilot sets; real labelled set built during review. | ISO/IEC 42001 A.7 Data for AI systems |
| RK-09 | A use case drifts into a high-risk category (for example forecasting used to allocate work to individuals) | Compliance | 2 | 5 | 10 | DPO | AI inventory with a reclassification trigger on every scope change; UC-08 parked; works council informed of every new use case. | EU AI Act Art. 6 and Annex III; ISO/IEC 42001 6.1.4 AI system impact assessment |
| RK-04 | Model provider changes or retires the model; behaviour changes | Technology | 3 | 3 | 9 | IT manager | Provider behind the orchestration layer; pinned model version; evaluation gate runs before any switch; offline rules provider as degraded mode. | ISO/IEC 27001 A.8.32 Change management; ISO/IEC 42001 A.6 AI system life cycle |
| RK-11 | Dependency on one internal developer | Delivery | 3 | 3 | 9 | IT manager | Partner support during year 1; runbook; champion paired on every change. | - |
| RK-14 | Reviewers approve flagged fields without looking (automation bias) | Quality | 3 | 3 | 9 | Doc desk team lead | Flagged fields need an explicit confirm or correct; reasons shown; audit sample includes reviewed documents; review speed outliers discussed, not punished. | EU AI Act Art. 14 (human oversight, as good practice); ISO/IEC 42001 A.9 Use of AI systems |
| RK-02 | Wrong data reaches the TMS without a flag (error escape) | Quality | 2 | 4 | 8 | COO | Error budget of 1%; validation and cross-document rules; 5% random audit of straight-through documents; escape rate on the KPI dashboard; release gate before every change. | ISO/IEC 27001 A.8.16 Monitoring activities; ISO/IEC 42001 9.1 Monitoring, measurement, analysis and evaluation |
| RK-05 | Customer data is retained or used for training by the AI vendor, or processed outside agreed regions | Privacy & security | 2 | 4 | 8 | DPO | Commercial terms reviewed: no training on inputs, retention limits, processing region; vendor assessed in the ISMS supplier process; data minimised (OCR text only, no attachments beyond the document). | ISO/IEC 27001 A.5.23 Information security for use of cloud services; ISO/IEC 27001 A.5.34 Privacy and protection of PII; GDPR Art. 28 |
| RK-10 | Works council objects late and stops a roll-out | Adoption | 2 | 4 | 8 | HR | Information and consultation before go-live (week 1, 14, 30); no individual performance monitoring; jobs statement in writing. | Belgian collective agreement no. 39 (new technologies) |
| RK-06 | A document contains text that tries to steer the model (prompt injection) | Privacy & security | 2 | 3 | 6 | IT manager | The model only extracts: no tools, no actions; output constrained by a JSON schema; every value re-parsed and validated by code; prompt tells the model to ignore instructions in documents. | ISO/IEC 27001 A.8.26 Application security requirements; OWASP Top 10 for LLM Applications: LLM01 |
| RK-13 | Model usage costs more than planned | Value | 1 | 2 | 2 | IT manager | Cost per document tracked in the orchestration layer; budget alert at 150% of plan. | - |
<!--/table-->

## How the register is used

- **At every gate** steering reviews the red risks first, then anything whose score changed.
- **A new use case adds its risks** before its pilot starts; the DPO checks the EU AI Act class and the IT manager the ISMS impact.
- **Controls column** links each risk to the ISO/IEC 27001:2022 Annex A control or ISO/IEC 42001 clause that covers it, so the ISMS internal audit can test it (see [ISO mapping](iso-27001-and-42001.md)).
