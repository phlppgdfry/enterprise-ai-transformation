# Workshop series

Four workshops with the leadership team and the people who do the work. Each has one decision it must produce; if it does not produce it, the workshop failed, however good the energy was. Generic agendas for reuse are in the [playbook](../09-playbook/templates/workshop-agendas.md).

| # | Week | Who | Decision it must produce |
|---|---|---|---|
| W1 | 2 | Leadership team + 6 people from the floor | A long list of problems worth solving, clustered into candidate use cases |
| W2 | 3 | Leadership team | Agreed scoring criteria and weights; a scored, ranked portfolio |
| W3 | 6 | COO, doc desk lead, two clerks, IT, DPO | Success criteria and human-oversight rules for the pilot |
| W4 | 10 | Leadership team + works council chair (last hour) | Roadmap, owners, operating model |

## W1: Problems worth solving (3 hours)

| Time | Block | Method |
|---|---|---|
| 0:00 | What AI is good at and bad at today, with three live demos on Wendelkaai documents | Short talk, no slides of logos |
| 0:30 | The six themes from discovery, with the numbers | Read-out, questions only |
| 0:50 | "How might we...?" per theme | Silent writing, 6 minutes per theme |
| 1:40 | Cluster and name | Affinity mapping on the wall |
| 2:20 | Gut check: which clusters would you fund with your own budget? | 3 dots each |
| 2:40 | What we will not do (and why) | Open discussion |

**Output:** 31 ideas, 10 clusters (the use cases), one explicit "no": individual performance scoring of drivers and pickers was raised and parked in the room, with the reason (EU AI Act Annex III high-risk, works council, no owner). See [UC-08](../03-opportunity-discovery/use-case-catalog.md).

## W2: Scoring and ranking (2.5 hours)

| Time | Block | Method |
|---|---|---|
| 0:00 | Why criteria first, use cases second | Short talk |
| 0:15 | Agree criteria and weights | Each person splits 100 points over value / feasibility / risk; discuss outliers; settle |
| 0:45 | Score the 10 use cases, 1-5 per criterion | Pre-filled by us from interviews; challenged line by line |
| 1:45 | Look at the matrix | [Impact-feasibility matrix](../03-opportunity-discovery/impact-feasibility-matrix.md), live |
| 2:05 | Does the ranking survive if we change the weights? | Live sliders on the [opportunity page](../site/opportunities/index.html) |
| 2:20 | Pick the pilot | Decision |

**Output:** weights value 45% / feasibility 35% / risk 20%; ranked portfolio; UC-01 chosen as the pilot. It stayed first in <!--n:pf.UC-01.top1-->100%<!--/n--> of 2,000 random re-weightings, which ended a debate about whether customer e-mail should go first.

## W3: Pilot success criteria (2 hours)

| Time | Block | Method |
|---|---|---|
| 0:00 | What can go wrong when a machine reads a document? | Show 12 real failure examples from the mailbox sample |
| 0:20 | How many errors may reach the TMS unseen? | Discussion anchored on today's 2.1%; agree an error budget |
| 0:50 | What must a person always see? | List field types and situations; agree rules |
| 1:20 | What does the review screen need to show? | Paper prototype with the clerks (service designer) |
| 1:45 | What would make you stop the pilot? | Kill criteria |

**Decisions (these became the pilot's [thresholds file](../06-applied-ai/prototype/evals/thresholds.json)):**
1. **Error budget <!--n:pilot.error_budget-->1%<!--/n-->**: at most one document in a hundred may reach the TMS with an error nobody was asked to check. It must also stay below today's human rate of 2.1%.
2. **No silent guessing.** A field read with an assumption (a weight without a unit, a date that could be day-first or month-first) always goes to a person. This set the threshold floor at <!--n:pilot.threshold_floor-->0.75<!--/n-->.
3. **At least 50% straight-through**, or the review work eats the benefit and the clerks lose patience.
4. **Every flag has a reason a clerk understands**, in their words ("no unit, assumed kg"), not a score.
5. **Kill criterion:** if the error escape rate in shadow mode exceeds 2% for two weeks, go-live stops.

## W4: Roadmap and operating model (3 hours)

| Time | Block | Method |
|---|---|---|
| 0:00 | Pilot results | Live demo of the [review queue](../site/pilot/index.html) and the evaluation report |
| 0:30 | Business case, cash and capacity | Walk through, CFO challenges |
| 1:00 | Sequence: waves and dependencies | Sticky roadmap on the wall, using the [readiness gaps](../02-ai-readiness/gap-analysis.md) |
| 1:45 | Who owns what | RACI, filled in together |
| 2:15 | Works council chair joins | What changes for people; commitments; questions |
| 2:50 | What goes to the board | Agree the ask |

**Output:** the [12-month roadmap](../05-transformation-roadmap/12-month-roadmap.md), the [RACI](../05-transformation-roadmap/raci-matrix.md), the ask for the board, and the works council's agreement to the information and consultation calendar.
