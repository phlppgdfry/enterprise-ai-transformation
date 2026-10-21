# Gap analysis

A gap is the distance between today's score and the 12-month target. It matters first when it is large **and** the top-ranked use cases depend on it, so the priority is `gap x (1 + number of top-5 use cases that need it)`. Computed by [engine/readiness.py](../engine/readiness.py) from [model/readiness.json](../model/readiness.json) and the [ranked portfolio](../03-opportunity-discovery/prioritization.md).

## The ten gaps that matter first

<!--table:readiness-gaps-->
| # | Gap | Today → target | Needed by | Priority |
|---|---|---|---|---|
| G1 | An AI policy says what is allowed | 1 → 4 | UC-01, UC-02, UC-03 | 12 |
| D5 | Core systems can be reached through APIs | 2 → 4 | UC-01, UC-09, UC-02, UC-07 | 10 |
| T3 | An AI orchestration layer exists (model access, prompts, logging, evaluation) | 1 → 3 | UC-01, UC-09, UC-02, UC-03 | 10 |
| D4 | Labelled historical data exists to evaluate AI | 1 → 3 | UC-01, UC-03 | 6 |
| G3 | Human oversight and accountability are designed in | 2 → 4 | UC-01, UC-03 | 6 |
| P1 | Staff understand what AI can and cannot do (AI literacy) | 1 → 3 | UC-02 | 4 |
| P2 | There are internal AI champions | 1 → 3 | UC-03 | 4 |
| T2 | Staff have sanctioned AI tools | 2 → 4 | UC-02 | 4 |
| G2 | AI systems are inventoried and classified (EU AI Act) | 1 → 4 | - | 3 |
| D1 | Data domains have named owners | 1 → 3 | - | 2 |
<!--/table-->

## How each top gap is closed

| Gap | Closed by | Roadmap | Owner |
|---|---|---|---|
| G1 No AI policy | One-page policy, approved tools list, rules for customer data | R16, weeks 1-4 | CEO |
| D5 Systems not reachable by API | TMS document endpoint agreed with the vendor; file-drop fallback | R13, weeks 1-6 | IT manager |
| T3 No orchestration layer | Model gateway, prompt registry, logging, evaluation harness, cost tracking | R12, weeks 1-12 | IT manager |
| D4 No labelled data | Labels created as a by-product of the review queue; refreshed quarterly | R15, weeks 8-40 | Doc desk lead |
| G3 No human-oversight rules | Rules from workshop 3, built into the review queue | R02, weeks 3-10 | Doc desk lead |
| P1 Low AI literacy | Three-tier programme: all staff, users, builders | R20, weeks 3-20 | HR |
| G2 No AI inventory | Register with risk tier, owner and review date; quarterly refresh | R17, weeks 2-6 | DPO |
| T2 No sanctioned tools | One approved assistant inside Microsoft 365 | R22, weeks 8-24 | IT manager |
| P2 No champions | Eight champions, two hours a week | R23, weeks 6-52 | COO |
| S3 No portfolio management | Scoring method and annual refresh (this repository's method) | R24, weeks 48-52 | CEO |

## What we deliberately do not fix in year 1

- **Master data quality beyond ownership (D2).** Named owners and a monthly quality report, yes; a master data management programme, no. It only pays off when forecasting and route optimisation start (UC-05/06/07).
- **Full process documentation (O1).** The 340 work instructions are cleaned only for the doc desk, as part of the pilot. The rest waits for the knowledge use case, which the sanctioned assistant partly covers.
