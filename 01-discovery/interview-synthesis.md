# Interview synthesis

**Inputs (weeks 1-2):** 14 interviews (12 stakeholders, two clerks), two half-day floor observations at the doc desk and in customer service, a staff survey (148 of 250 responded), a two-week mailbox sample and a time study at the doc desk. Names are fictional; quotes are paraphrased from interview notes and approved by the people quoted.

## The numbers we measured (they did not exist before)

| What | How we measured it | Result | Used in |
|---|---|---|---|
| Documents to key | Counted all inbound freight documents in the doc desk mailboxes, 31 Aug - 11 Sep 2026 | 1,846 in two weeks, about **4,000 a month** | Business case A01 |
| Time to key a document | Time study: 60 documents, two clerks, stopwatch from opening the e-mail to saving in the TMS | **5.5 minutes** on average (B/L 7.1, CMR 4.2, invoice 6.0, packing list 4.4, DO 3.8) | Business case A03 |
| Keying error rate | Team lead double-checked 480 documents keyed in August against the source | 10 documents with at least one error: **<!--n:pilot.human_error-->2.1%<!--/n-->** | Error budget, pilot gate, business case A11 |
| What goes wrong in documents | Classified every problem found in the mailbox sample | See table below | Pilot data recipe |
| Shadow AI | Staff survey | 38% use public chatbots for work; 11% admit pasting customer data | Readiness T2, G1; risk RK-08 |
| Attitude | Staff survey | 61% expect AI to "replace jobs at the desk"; 22% feel confident using it | Readiness P1; change plan |

### What goes wrong in documents (mailbox sample, 1,846 documents)

| Problem | Share | Example |
|---|---|---|
| A label garbled by the scan or OCR | 12% | "Gr0ss weight", "Consignce" |
| A container number with a look-alike character (O for 0, I for 1) | 10% of documents with containers | NSXU4O17282 |
| A field that cannot be read (smudged, stamped over) | 7% | "[illegible]" in the weight box |
| Packing list weight disagrees with the B/L by more than 1% | 8% of packing lists | 6,943 kg vs 7,466 kg |
| Invoice lines do not add up to the total | 6% of invoices | — |
| Container number mistyped by the shipper (check digit wrong) | 6% of B/Ls | — |
| Weight without a unit | 5% | "18,443.4" |
| A digit misread with nothing to check it against | 4% | 27 packages instead of 21 |
| Seal number missing on a B/L | 5% of B/Ls | — |
| Not a freight document at all (newsletters, invites, arrival notices) | ~5% | — |

These rates are the recipe for the pilot's synthetic test data ([make_data.py](../06-applied-ai/prototype/scripts/make_data.py)), so the pilot was tested on the problems the desk actually sees.

**One practice that mattered for the design:** the doc desk waits until a shipment's set (B/L, invoice, packing list) is complete before keying it, because the documents correct each other. The pilot does the same, which is what makes the cross-document checks possible.

## Six themes

### 1. Skilled people retype documents
> *"We hired people who know customs and shipping, and they spend half the day typing what is already in a PDF."* — COO

11 clerks, about 4,000 documents a month, two vacancies open for eight months. The work is repetitive but not trivial: the clerks know which shipper writes dates the American way, which agent never sends a seal number. That knowledge is what an AI solution has to capture in rules and in the review flow.

### 2. Errors are found late and cost money downstream
> *"Nobody knows what an error costs because nobody sees it. It shows up three days later as a customs amendment or a truck waiting at the terminal."* — Customs lead

The 2.1% error rate surprised the leadership team. The cost per error is an estimate (€35-110, depending on whether it causes rework only or a customs amendment and demurrage), which is why the business case shows it as a range.

### 3. Knowledge lives in people and in 340 Word files
> *"New people ask Bart. If Bart is on holiday, they ask whoever is nearest, and sometimes that is wrong."* — Doc desk clerk

Customer-specific instructions are in Word files, a third older than three years. This is a data problem before it is an AI problem (readiness D1, O1).

### 4. AI is already used, without rules
> *"I paste the customer's e-mail into ChatGPT to write a polite answer. Is that not allowed?"* — Customer service agent

38% use public chatbots for work. No policy, no approved tool. This is the fastest risk to close and the cheapest: a policy and one sanctioned assistant ([R16, R22](../05-transformation-roadmap/12-month-roadmap.md)).

### 5. Fear of jobs and of blame
> *"If the system makes a mistake and I approved it, whose fault is that?"* — Doc desk clerk
> *"We heard about the truck tracking from the drivers, not from management."* — Works council member

Two separate fears: losing the job, and being blamed for a machine's error. The first is answered by a written commitment (no redundancies; capacity goes to customs files and exceptions; attrition handled case by case). The second by the design: the pilot shows *why* a field is flagged, and a person is accountable only for what they were asked to check ([human oversight](../07-governance/human-oversight.md)).

### 6. Data quality is uneven
14% duplicate customer records; no data owners. Fine for the document pilot (it reads documents, not master data), a blocker for forecasting and route optimisation (UC-05, UC-06, UC-07). That shaped the roadmap order.

## From themes to ideas

The themes went into [workshop 1](workshop-series.md) as problem statements, not as solutions. The workshop produced 31 ideas, clustered into the [10 use cases](../03-opportunity-discovery/use-case-catalog.md).
