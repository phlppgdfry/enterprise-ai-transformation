# Human oversight design (UC-01)

UC-01 is not high-risk under the EU AI Act, so Article 14 does not apply as a legal duty. We design to it anyway, because the risk it addresses (people trusting a machine they cannot check) is the one that sinks AI projects on the floor.

## The rules (from workshop 3)

| # | Rule | How the pilot enforces it |
|---|---|---|
| 1 | **No silent guessing.** A value read with an assumption always goes to a person. | Assumed units (0.60) and ambiguous dates (0.70) are below the threshold floor of <!--n:pilot.threshold_floor-->0.75<!--/n--> |
| 2 | **A flag has a reason in the clerk's words.** | Every review item lists reasons such as "gross_weight_kg: no unit, assumed kg" or "V11: packing list 6,943 kg vs B/L 7,466 kg" |
| 3 | **The clerk checks fields, not documents.** | Only flagged fields need a confirm or correct; the source document is shown next to them |
| 4 | **Accountability follows the task.** | A clerk answers for the fields they were asked to check. Straight-through documents are the pipeline's responsibility, measured by the audit |
| 5 | **Unsure what it is? A person handles it.** | Non-freight documents and uncertain types go to manual handling, as today |
| 6 | **Anyone can stop it.** | The doc desk lead can switch any document type back to manual from the queue; the stop rule (escape rate above 2% for two weeks) is automatic |
| 7 | **The machine's errors are measured, not assumed.** | 5% random audit of straight-through documents; every correction in review is logged and feeds the next golden set |

## Against automation bias

People who see "the system already checked this" approve faster and look less. Three counter-measures:

1. **Explicit action per flagged field.** No "approve all" button.
2. **Mixed audit.** The audit sample also includes reviewed documents, so a rubber-stamped review is found.
3. **Review speed is discussed, not punished.** An unusually fast reviewer gets a conversation at the Monday retro, not a performance note; the queue does not report individual speed to management (commitment 4 in the [change plan](../05-transformation-roadmap/change-and-adoption.md)).

## What the review screen shows

```
DOC-0084  Packing list  received 2026-09-08                     [ Source document ]
──────────────────────────────────────────────────────────────────────────────────
Why you see this
  • V11  packing list 6,943.0 kg vs B/L 7,465.6 kg
  • V13  container WKLU8492670 is not on the B/L (B/L BWAL78683871 also flagged)

Fields                     Read as               Confidence   Your action
  gross_weight_kg          6,943.0               0.95         [confirm] [correct]
  containers               WKLU8492670           0.95         [confirm] [correct]
  packages                 336                   0.95         ✓ not flagged
  ...
Linked documents: B/L BWAL78683871 (in review), 3 delivery orders
```

The live version on the 220 test documents is the [review queue demo](../site/pilot/index.html).
