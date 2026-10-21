# Stop counting pilots. Start counting errors that reach your systems.

*A short piece for a company blog or a talk, based on this case. About 900 words.*

Most AI programmes I see are measured by how many pilots they have running. It is the wrong number. A pilot that never reaches production costs money and teaches the organisation that AI is a demo. The number that matters is less exciting and much more useful: **how many wrong records does the AI put into your systems without anyone being asked to look?**

Here is why, from a document-automation pilot at a mid-sized logistics company in Zeebrugge (the company is fictional; the problems are not).

## "Let AI read the documents" is the easy part

Eleven clerks retyped about 4,000 freight documents a month: bills of lading, CMRs, invoices, packing lists. We measured it before anyone touched a model: 5.5 minutes per document, and 2.1% of documents had at least one keying error. Nobody in the company knew either number. Measuring them was the first useful thing the project did.

Getting a model to read those documents is not hard any more. In our evaluation, extraction alone pushed 95% of documents straight through. It also put 36 out of 220 into the TMS with an error. A digit misread by the scanner looks perfectly normal; a confidence score does not catch it. Neither does "accuracy": field accuracy was high, and the share of documents with an error (16%) was still several times worse than the humans it was meant to help (2.1%).

## What made it safe was not AI

What brought those 36 errors down to zero on the test set was something the clerks already did in their heads: comparing documents. The packing list says 6,943 kilos; the bill of lading says 7,466. The package count differs between the invoice and the B/L. A container number fails its check digit. We wrote fourteen of those rules down and made them run. Three of them compare documents of the same shipment, and those three caught most of the remaining errors.

The first version still failed its gate. A third of the packing lists did not mention their bill of lading, so the pipeline never compared them. That is not a model problem; it is business logic. Linking documents by container number fixed it.

## Agree the error budget before you build

The single most useful meeting in the project took two hours. The COO, the doc desk lead, two clerks, IT and the DPO agreed, before any code was written:

- **At most 1 in 100** documents may reach the system with an error nobody was asked to check. (Today, by hand, it is 2 in 100.)
- **No silent guessing:** a weight without a unit or a date that could be day-first or month-first always goes to a person.
- **Every flag has a reason** in the clerk's words.

Those three sentences became the release gate. The pilot was judged against them, not against a vendor's benchmark. The threshold was chosen on one data set and reported on another, so nobody could tune it until it looked good.

## Count the euros the way the CFO does

Freed hours are not saved euros. The pilot frees about 2.4 FTE of clerk time in year 2. That only becomes cash if someone decides what happens with it. In this case the company, HR and the works council agreed: no redundancies, freed time goes to customs files and exceptions, and while the solution scales every second leaver is not replaced.

When we ran the sensitivity analysis, the biggest driver of the business case was not the model's straight-through rate. It was that attrition decision, followed by the real cost of an error. The straight-through rate barely moved the result, because documents that are not straight-through still arrive pre-filled and checked. That changes where management should spend its attention: on the people decision and on measuring error costs, not on squeezing the last percent out of the model.

## Governance is a delivery item

The same company had no AI policy, and 38% of staff used public chatbots for work, some with customer data. Two pharma customers had asked about AI governance in their supplier audits. The roadmap put an AI policy, an AI inventory with EU AI Act classification, supplier assessment inside the existing ISO/IEC 27001 system and literacy training in the first 90 days, before go-live, each with an owner. One idea from a vendor (scoring drivers' and pickers' performance with AI) was parked in writing: high-risk under the AI Act, no business owner, and a works council that had been told about the last tracking system after the fact.

None of that slowed the project down. It is what made the board comfortable saying yes.

## What to count instead

If you run an AI programme, try reporting these four numbers instead of "pilots running":

1. **Use cases in production**, with a named business owner.
2. **Error escape rate** per use case, against a budget the business set.
3. **Value realised**, on the cash view, against the business case.
4. **AI systems in the inventory**, each with a risk class and a review date.

They are harder to make look good. That is the point.
