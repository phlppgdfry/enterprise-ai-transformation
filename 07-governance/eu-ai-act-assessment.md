# EU AI Act assessment

*Working analysis against the AI Act (Regulation (EU) 2024/1689) as amended by the Digital Omnibus on AI (Regulation (EU) 2026/1744, published in the Official Journal on 24 July 2026, in force since 27 July 2026), checked on 21 October 2026. It is a consultant's analysis for the DPO and legal counsel, not legal advice. Dates and wording must be confirmed against the Official Journal text before a decision depends on them.*

## Wendelkaai's role

- **Deployer** of every AI system it uses under its own authority (Art. 3(4)).
- **Provider** of UC-01 as well, if it puts the pipeline into service under its own name, which it will (built to its specification by a partner). For a system that is not high-risk, provider obligations are light: mainly transparency where applicable and general product and data law.
- The **foundation model vendor** is a provider of a general-purpose AI model, with its own obligations since 2 August 2025. Wendelkaai relies on the vendor's documentation and terms.

## Classification of the ten use cases

<!--table:ai-act-->
| # | Use case | Tier | Why |
|---|---|---|---|
| UC-01 | Freight document intelligence | minimal | Not in Annex III; does not interact with people or make decisions about them. |
| UC-02 | Customer e-mail triage and draft replies | limited | Art. 50(1) applies if customers interact with an AI system directly; with an agent reviewing every draft, transparency is still good practice. |
| UC-03 | Customs classification assistant | minimal | Not in Annex III. The declarant stays legally responsible for the declaration; financial error impact is the real risk. |
| UC-04 | Internal knowledge assistant | minimal | Internal use; staff are told they use an AI tool (AI literacy). |
| UC-05 | ETA prediction and delay alerts | minimal | No personal data, no decisions about people. |
| UC-06 | Warehouse volume forecasting for staffing | minimal | Forecasts volumes, not individuals. Would become high-risk if extended to allocating work to individuals (Annex III 4(b)). |
| UC-07 | Route and load optimisation | minimal | Plans vehicles and loads. Must not be used to evaluate drivers (that would be UC-08). |
| UC-08 | Driver and warehouse performance monitoring | high | Annex III point 4(b): AI to monitor and evaluate the performance and behaviour of persons in work relationships. Also needs works-council consultation under Belgian collective agreements on new technology and monitoring. |
| UC-09 | Carrier invoice audit | minimal | Business documents between companies; no decisions about people. |
| UC-10 | Quote and tender assistant | minimal | Business-to-business drafting reviewed by sales. |
<!--/table-->

**Method per use case:** (1) is it a prohibited practice under Art. 5? (2) is it listed in Annex III, or a safety component of a product under Annex I? (3) if Annex III, does the Art. 6(3) exception apply (narrow procedural task, no profiling)? (4) does Art. 50 transparency apply? (5) what does AI literacy require for the people using it?

## UC-01 in detail

| Question | Answer |
|---|---|
| Prohibited practice (Art. 5)? | No |
| Annex III? | No. Reading business documents between companies is not in any Annex III area. It does not decide about people. |
| Art. 50 transparency? | No direct interaction with natural persons and no content published to the public. Clerks know they work with an AI system (training, labelled in the queue). |
| AI literacy (Art. 4)? | Yes: clerks, their lead and the IT team are trained on what it does, its limits and how to override it. |
| GDPR? | Freight documents contain names of contact persons and drivers. Lawful basis: contract and legitimate interest; minimised to the fields needed; covered by the existing processing register. No DPIA required for UC-01 in the DPO's view; one is required for UC-02 (customer e-mails). |

We still apply practices the Act requires only of high-risk systems, because they are cheap and reduce real risk: human oversight by design ([human-oversight.md](human-oversight.md)), logging, accuracy measurement with a release gate ([evaluation framework](../06-applied-ai/evaluation-framework.md)) and technical documentation (this repository).

## UC-08: why it is parked

Annex III point 4(b) lists AI systems intended to make decisions affecting work-related relationships, to allocate tasks based on individual behaviour or personal traits, or **to monitor and evaluate the performance and behaviour of persons** in such relationships. Scoring drivers and pickers from telematics and scanner data falls squarely in it. As a deployer of a high-risk system Wendelkaai would need, among other things, human oversight by trained people, input-data control, monitoring, log retention, informing workers' representatives and affected workers before use (Art. 26(7)), and a GDPR DPIA. Belgian collective agreements on new technologies and on monitoring add a works-council track. With no business owner and a value claim from a vendor only, the leadership team parked it. If it comes back, it starts with this paragraph.

## Watch list: use cases that can drift into high-risk

| Use case | Drift that would change the class | Trigger in the inventory |
|---|---|---|
| UC-06 volume forecasting | Using forecasts to allocate shifts or tasks to named individuals | Any change of output from "volume per shift" to "who works when" |
| UC-07 route optimisation | Using planning data to evaluate individual drivers | Any report per driver |
| UC-02 e-mail triage | Sending replies without an agent (then Art. 50(1) applies: tell customers they deal with AI) | Any change to auto-send |

## Dates that matter (after the Digital Omnibus)

| Date | What applies |
|---|---|
| 2 February 2025 | Prohibited practices; AI literacy (Art. 4) |
| 2 August 2025 | Obligations for providers of general-purpose AI models |
| 2 August 2026 | Transparency obligations (Art. 50) and most remaining provisions; national supervision and enforcement |
| 2 December 2027 | High-risk obligations for Annex III systems (moved from 2 August 2026 by the Omnibus) |
| 2 August 2028 | High-risk obligations for AI in products under Annex I (moved from 2 August 2027) |

**AI literacy after the Omnibus.** The amended Art. 4 asks providers and deployers to *take measures to support* the development of AI literacy among their staff, and states that this does not require them to guarantee a specific level for any individual. A new paragraph has the Commission and Member States support operators, in particular SMEs. The obligation was softened, not removed; the [literacy plan](ai-literacy-plan.md) is how Wendelkaai meets it, and it is worth doing for adoption reasons anyway.

*Sources for the Omnibus changes: law-firm and specialist summaries (White & Case, nicfab.eu, aiacto.eu, July-August 2026). Legal must confirm against the Official Journal.*
