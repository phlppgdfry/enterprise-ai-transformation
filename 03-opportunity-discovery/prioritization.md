# Prioritization

## Method

1. **Criteria and weights first.** In [workshop 2](../01-discovery/workshop-series.md) each leadership-team member split 100 points over value, feasibility and risk; the team settled on **value 45%, feasibility 35%, risk 20%**.
2. **Score each use case 1-5 per sub-criterion** (8 scores plus annual value), pre-filled from interviews and challenged in the room.
3. **Gate before ranking.** A regulatory score of 1 (high-risk under the EU AI Act or against a works-council agreement) parks the use case: it needs its own decision, not a place in a list.
4. **Rank by weighted score.**
5. **Test robustness.** Re-rank under 2,000 random weightings (each group weight between half and one-and-a-half times the agreed weight) and count how often each use case stays in the top three. A ranking that flips when someone nudges a weight is an opinion, not a priority.

Implemented in [engine/portfolio.py](../engine/portfolio.py); the spreadsheet version is [use-case-scoring.xlsx](use-case-scoring.xlsx).

## Result

<!--table:use-case-ranking-->
| Rank | Use case | Value | Feasibility | Risk (5 = low) | Score | Quadrant | Top 3 under re-weighting |
|---|---|---|---|---|---|---|---|
| 1 | UC-01 Freight document intelligence | 4.06 | 3.60 | 4.00 | 3.89 | Do now | 100% |
| 2 | UC-09 Carrier invoice audit | 2.44 | 3.75 | 4.60 | 3.33 | Fill-in | 65% |
| 3 | UC-02 Customer e-mail triage and draft replies | 2.85 | 3.60 | 3.80 | 3.30 | Fill-in | 56% |
| 4 | UC-07 Route and load optimisation | 3.69 | 2.35 | 4.00 | 3.28 | Prepare (strategic bet) | 50% |
| 5 | UC-03 Customs classification assistant | 3.36 | 3.00 | 3.40 | 3.24 | Do now | 29% |
| 6 | UC-10 Quote and tender assistant | 2.63 | 3.25 | 4.00 | 3.12 | Fill-in | 0% |
| 7 | UC-04 Internal knowledge assistant | 2.27 | 3.15 | 4.40 | 3.00 | Fill-in | 0% |
| 8 | UC-05 ETA prediction and delay alerts | 2.38 | 2.30 | 4.60 | 2.80 | Deprioritise | 0% |
| 9 | UC-06 Warehouse volume forecasting for staffing | 2.22 | 2.50 | 3.60 | 2.59 | Deprioritise | 0% |
| – | UC-08 Driver and warehouse performance monitoring | 1.45 | 2.70 | 1.40 | 1.88 | Parked (high-risk) | 0% |
<!--/table-->

**What is robust and what is not**

- **UC-01 is first in <!--n:pf.UC-01.top1-->100%<!--/n--> of the re-weightings.** The choice of pilot does not depend on the weights.
- **Places 2 to 5 are close** (scores within about 0.1). UC-09 is in the top three in <!--n:pf.UC-09.top3-->65%<!--/n--> of re-weightings, UC-02 in <!--n:pf.UC-02.top3-->56%<!--/n-->, UC-07 in <!--n:pf.UC-07.top3-->50%<!--/n-->. The order between them is a judgement call, so the roadmap uses dependencies and readiness to break the tie, not the third decimal.
- **The bottom of the list is robust.** UC-05 and UC-06 never reach the top three: their problem is data, not weighting.

## From ranking to waves

| Wave | Use cases | Why in this order |
|---|---|---|
| 1 (weeks 1-20) | UC-01 | Ranked first under every weighting; builds the platform the next ones reuse |
| 2 (weeks 15-39) | UC-09, UC-02 | UC-09 reuses the pipeline almost as is; UC-02 needs a DPIA first (customer e-mails hold personal data) |
| 3 (weeks 30-52) | UC-03, UC-07 | UC-03 needs labelled past classifications and the declarant-in-the-loop design proven in UC-01; UC-07 needs clean location data and is a buy decision |
| Covered by the sanctioned assistant | UC-04, UC-10 | A general assistant inside Microsoft 365 covers most drafting and knowledge needs; revisit custom builds only if usage data shows a gap |
| After data foundations | UC-05, UC-06 | Data owners and quality first |
| Parked | UC-08 | High-risk; no owner |

The full plan is in the [12-month roadmap](../05-transformation-roadmap/12-month-roadmap.md).
