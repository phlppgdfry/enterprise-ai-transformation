# Executive summary

**Client:** Wendelkaai Logistics NV (fictional), Zeebrugge, 250 employees · **Engagement:** 12 weeks, discovery to board decision · **Ask:** *"Where do we start with AI, what is it worth, and how do we do it without getting into trouble?"*

## Three answers

**1. Start with the documents.** Eleven clerks retype about 4,000 freight documents a month: 5.5 minutes each, and 2.1% carry an error that costs money later. Of ten use cases scored with the leadership team, *freight document intelligence* ranks first in <!--n:pf.UC-01.top1-->100%<!--/n--> of 2,000 re-weightings of the criteria. Performance scoring of workers, raised by a vendor, is parked: high-risk under the EU AI Act and without an owner.

**2. It is worth <!--n:bc.cash.npv-->€189k<!--/n--> over three years on the cash view** (payback <!--n:bc.cash.payback-->15 months<!--/n-->, one-off <!--n:bc.one_off-->€85k<!--/n-->). The pilot, measured on 220 documents it never saw during tuning, sends <!--n:pilot.stp-->70.0%<!--/n--> straight to the TMS with <!--n:pilot.escapes-->0<!--/n--> unflagged errors and catches <!--n:pilot.exceptions_caught-->100%<!--/n--> of genuine document problems. The biggest lever on the value is not the model: it is the decision not to replace every second leaver, and the real cost of an error.

**3. Do it with governance from week one.** Readiness is <!--n:rd.overall-->1.9<!--/n--> of 5: ready to use AI, not to govern it (no policy, no inventory, 38% shadow AI). The roadmap puts an AI policy, an AI inventory with EU AI Act classification, ISO/IEC 27001 supplier assessment, literacy training and the works council before go-live, and keeps a person in charge of every document the pilot is unsure about.

## The decision

Approve UC-01 production and the year-1 foundations (<!--n:bc.one_off-->€85k<!--/n--> one-off, about <!--n:bc.run_cost_y1-->€20k<!--/n--> a year), released at gate G2 in week 13 only if shadow mode on real documents reaches ≥ 60% straight-through within the 1% error budget. Wave 2 (carrier invoice audit, customer e-mail triage) comes back at week 26 with its own case.

## What the board should know

- Extraction alone would have put <!--n:pilot.A.escapes-->36<!--/n--> of 220 documents into the TMS with an error. The business rules, written down and automated, make it safe.
- If every driver of the business case went wrong at once, it would lose money (NPV <!--n:bc.pessimistic.cash.npv-->-€142k<!--/n-->). The gates and the KPI dashboard watch exactly those drivers.
- The pilot ran on synthetic documents built from a real mailbox sample, with an offline stand-in for the model. Go-live depends on the same gate passing on real documents.

[Proposal](08-executive-presentation/proposal.md) · [Board deck](08-executive-presentation/board-presentation.pdf) · [Samenvatting (NL)](samenvatting.md)
