# Use-case catalog

Ten use cases, clustered from 31 ideas in [workshop 1](../01-discovery/workshop-series.md). Each has an owner from the business, a problem in numbers and an honest kind of AI: three of them are not generative AI at all. The data lives in [model/use_cases.json](../model/use_cases.json); this page and the site are generated from it.

<!--table:use-case-catalog-->
| # | Use case | What it does | Kind of AI | Owner | Value / year | EU AI Act |
|---|---|---|---|---|---|---|
| UC-01 | Freight document intelligence | Read bills of lading, CMRs, invoices, packing lists and delivery orders; check them; post clean ones to the TMS and send the rest to a clerk with reasons. | Document AI (foundation model extraction + rules) | COO | €166k | minimal |
| UC-02 | Customer e-mail triage and draft replies | Classify incoming customer e-mails (status questions, changes, complaints), pull the shipment status from the TMS and draft a reply for the agent to send. | LLM classification and drafting | Customer service lead | €85k | limited |
| UC-03 | Customs classification assistant | Suggest HS codes for new products from invoice descriptions and past declarations, with the reasoning, for the customs declarant to confirm. | LLM with retrieval over tariff and past rulings | Customs lead | €130k | minimal |
| UC-04 | Internal knowledge assistant | Answer staff questions from work instructions, customer-specific procedures and SOPs, with links to the source. | Retrieval-augmented generation (RAG) | COO | €60k | minimal |
| UC-05 | ETA prediction and delay alerts | Predict arrival times for vessels and trucks from AIS, terminal and traffic data; alert customers and planners when a shipment will be late. | Machine learning (forecasting) on external data | Operations planning | €70k | minimal |
| UC-06 | Warehouse volume forecasting for staffing | Forecast inbound and outbound volumes per day and shift, so the warehouse plans temporary staff earlier. | Machine learning (time-series forecasting) | Warehouse manager | €55k | minimal |
| UC-07 | Route and load optimisation | Plan daily routes and loads for the 60 own trucks with an optimisation solver, replacing the planners' spreadsheet. | Operations research (optimisation), not generative AI | Transport manager | €160k | minimal |
| UC-08 | Driver and warehouse performance monitoring | Score individual drivers and pickers on speed and behaviour from telematics and scanner data. | Machine learning on employee data | None proposed | €40k | high |
| UC-09 | Carrier invoice audit | Check subcontractor freight invoices against agreed rates and the actual transport; flag overcharges before payment. | Document AI + rules (reuses UC-01) | CFO | €75k | minimal |
| UC-10 | Quote and tender assistant | Draft quotes and tender answers from rate cards, past quotes and capacity, for sales to check and send. | LLM drafting with retrieval over rate cards | Sales director | €65k | minimal |
<!--/table-->

## Scores per criterion (1-5, higher is better; for risk 5 = low risk)

<!--table:use-case-scores-->
| # | Fit | Data | Simplicity | Integration | Change | Regulatory | Error tolerance | Privacy | Value basis |
|---|---|---|---|---|---|---|---|---|---|
| UC-01 | 5 | 4 | 4 | 3 | 3 | 5 | 3 | 4 | Business case (04-business-case), capacity view, steady state. |
| UC-02 | 4 | 4 | 4 | 3 | 3 | 4 | 4 | 3 | 9,000 e-mails/month, 55% status questions, 3 minutes saved each at EUR 34/hour, 60% adoption. |
| UC-03 | 4 | 3 | 3 | 3 | 3 | 4 | 2 | 5 | 1,800 new classifications/year, 18 minutes saved each, plus avoided corrections (customs lead estimate, wide range). |
| UC-04 | 3 | 2 | 4 | 4 | 3 | 5 | 4 | 4 | Onboarding time and interruptions; soft value, HR and team leads' estimate. |
| UC-05 | 3 | 2 | 2 | 2 | 4 | 5 | 4 | 5 | Planner time and customer retention; requires data subscriptions not yet costed. |
| UC-06 | 3 | 2 | 3 | 3 | 2 | 4 | 3 | 4 | Fewer last-minute temp bookings (premium 18%). |
| UC-07 | 4 | 3 | 2 | 2 | 2 | 5 | 3 | 4 | 3 points fewer empty kilometres (fuel, tolls, driver hours), planner time. |
| UC-08 | 1 | 3 | 3 | 3 | 1 | 1 | 2 | 1 | Vendor claim, not validated. |
| UC-09 | 3 | 4 | 4 | 3 | 4 | 5 | 4 | 5 | 1.2% of EUR 7.5m subcontracted transport recovered, minus false positives handled by finance. |
| UC-10 | 4 | 3 | 3 | 4 | 3 | 5 | 3 | 4 | Sales time and a higher win rate on fast replies (sales director estimate). |
<!--/table-->

Scores were pre-filled from the interviews and challenged line by line in [workshop 2](../01-discovery/workshop-series.md). Spreadsheet version, with live weights: [use-case-scoring.xlsx](use-case-scoring.xlsx).

## Three use cases that need a sentence more

**UC-01 Freight document intelligence** is the pilot. Its value is not an estimate in this table: it is the steady-state value from the [business case](../04-business-case/cost-benefit-analysis.md) (<!--n:pf.UC-01.value-->€166k<!--/n--> a year in the capacity view), which in turn uses what the pilot measured.

**UC-07 Route and load optimisation** has high value but is an operations-research problem, solved by a planning solver, not by a language model. Calling it "AI" got it on the list; treating it as a *buy* decision between planning tools (not a build) keeps it honest. See [buy vs build](../04-business-case/buy-vs-build.md).

**UC-08 Driver and warehouse performance monitoring** is parked, not ranked. Scoring individual workers' performance and behaviour with AI is a **high-risk** use under Annex III point 4(b) of the EU AI Act, needs works-council consultation under Belgian collective agreements, and had no business owner. It stays on the list so the decision is visible: if the company ever wants it, it needs its own board decision, a conformity process and the works council at the table first.
