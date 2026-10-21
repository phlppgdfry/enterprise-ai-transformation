# Business case assumptions

Every input of the business case, with its source. Values marked **pilot** are read from the pilot's evaluation report, so when the pilot results change, the business case changes in the same build. Edit [model/business_case.json](../model/business_case.json), then run `python scripts/build.py`.

<!--table:assumptions-->
| # | Assumption | Base | Low | High | Source | Basis |
|---|---|---|---|---|---|---|
| A01 | Documents keyed per month (documents) | 4,000 | 3,600 | 4,400 | measured | Two-week mailbox count, September 2026, extrapolated. |
| A02 | Annual volume growth | 4.0% | 2.0% | 6.0% | client plan | CFO's 2027-2029 plan. |
| A03 | Minutes to key one document today (minutes) | 5.5 | 4.5 | 6.5 | measured | Discovery time study, 60 documents, two clerks. |
| A04 | Minutes to review a flagged document (minutes) | 2.5 | 2 | 3.5 | estimate | Clerk checks only the flagged fields; to be measured in the first production month. |
| A05 | Minutes per straight-through document (sample audit) (minutes) | 0.3 | 0.2 | 0.5 | design | 5% random audit of straight-through documents at 6 minutes each. |
| A06 | Straight-through rate | 70.0% | 63.6% | 75.7% | pilot | Test set result; low and high are the 95% confidence interval. |
| A07 | Share of documents handled fully by hand | 4.5% | 4.5% | 4.5% | pilot | Not freight documents or type unsure. |
| A08 | Loaded cost per clerk hour (EUR) | 34 | 31 | 37 | client finance | EUR 52,000 loaded cost per clerk / 1,530 productive hours. |
| A09 | Loaded cost per clerk per year (EUR) | 52,000 | 52,000 | 52,000 | client finance | HR, 2026 salary scales plus employer costs. |
| A10 | Productive hours per FTE per year (hours) | 1,530 | 1,530 | 1,530 | client finance | HR. |
| A11 | Documents with a keying error today | 2.1% | 1.5% | 2.8% | measured | Time study: 60 documents double-checked. |
| A12 | Cost of one error that reaches operations (EUR) | 60 | 35 | 110 | estimate | Operations and customs leads: rework, customs amendment, share of demurrage. Wide range on purpose. |
| A13 | Documents posted with an unflagged error (pilot) | 0.4% | 0.4% | 1.6% | pilot | Dev and test sets pooled (440 documents); high is the upper 95% bound. |
| A14 | Error rate on reviewed documents, relative to keying (x) | 0.3 | 0.2 | 0.5 | estimate | Clerks check a few flagged fields instead of keying all; fewer chances to slip. |
| A15 | One-off cost: production build, TMS integration, change and training (EUR) | 85,000 | 70,000 | 115,000 | estimate | Partner quote range for 10 weeks build and integration plus internal time; pilot cost (EUR 38,000) is sunk and excluded. |
| A16 | Run cost per year excluding model usage (EUR) | 19,000 | 15,000 | 26,000 | estimate | Hosting and monitoring EUR 7,000; support and model upkeep (0.1 FTE engineer) EUR 12,000. |
| A17 | Input tokens per document (tokens) | 2,500 | 2,000 | 4,000 | estimate | Prompt plus OCR text of a one-page document. |
| A18 | Output tokens per document (tokens) | 600 | 400 | 1,000 | estimate | Structured JSON with 6-11 fields. |
| A19 | Model price, input (claude-opus-5-5) (USD per million tokens) | 4 | 4 | 4 | vendor price list | Anthropic list price, October 2026. |
| A20 | Model price, output (claude-opus-5-5) (USD per million tokens) | 20 | 20 | 20 | vendor price list | Anthropic list price, October 2026. |
| A21 | Exchange rate (EUR per USD) | 0.9 | 0.85 | 0.95 | assumption | Rounded. |
| A22 | Share of steady-state benefit reached in year 1 | 60.0% | 40.0% | 75.0% | assumption | Go-live in month 5 of the roadmap, document types switched on one by one. |
| A23 | Doc desk leavers per year not replaced (FTE) | 0.5 | 0 | 1 | client HR | Average 1.4 leavers a year over 2023-2025. Agreed with HR and the works council: no redundancies; every second leaver is not replaced while the pilot scales. |
| A24 | Discount rate | 8.0% | 8.0% | 8.0% | client finance | CFO's hurdle rate. |
<!--/table-->

## Source labels

| Label | Meaning | Confidence |
|---|---|---|
| measured | Counted or timed during discovery | High, but small samples |
| pilot | Measured by the pilot's evaluation on synthetic documents | Medium: real documents in shadow mode (gate G2) must confirm it |
| client finance / client HR / client plan | Provided by the client's finance or HR team | High |
| estimate | Our estimate or an interviewee's, with a deliberately wide range | Low: tracked on the KPI dashboard from week 2 |
| design | Follows from how we designed the process (e.g. the 5% audit) | High, as long as the design holds |
| vendor price list | Public list price at the time of writing | High, changes yearly |
| assumption | Rounded or conventional value | — |
