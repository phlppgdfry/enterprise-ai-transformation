# Applied AI: the freight document pilot

The pilot reads freight documents, checks them and decides who needs to look at them. It runs end to end on synthetic documents built from what the discovery found in Wendelkaai's mailboxes, and it reports how well it does against criteria the business agreed before the build.

| | |
|---|---|
| **Result on the held-out test set** | <!--n:pilot.stp-->70.0%<!--/n--> straight-through, <!--n:pilot.escapes-->0<!--/n--> documents reached the TMS with an unflagged error, <!--n:pilot.exceptions_caught-->100%<!--/n--> of genuine document problems sent to a person. Gate: **<!--n:pilot.gate-->PASS<!--/n-->** |
| **Without the safety layers** | Extraction alone would send <!--n:pilot.A.escapes-->36<!--/n--> of 220 documents into the TMS with an error |
| **Honest caveat** | Synthetic documents, and the dev set shows a residual failure mode (<!--n:pilot.dev_escapes-->2<!--/n--> escapes: misread digits on stand-alone CMRs). Real documents in shadow mode decide go-live (gate G2). |

| Read | What it covers |
|---|---|
| [architecture.md](architecture.md) | Components, data flow, what the model does and what code does, provider choice |
| [evaluation-framework.md](evaluation-framework.md) | Metrics, data sets, ablation, threshold selection, release gate |
| [pilot-results.md](pilot-results.md) | Results, the three evaluation runs that shaped the design, failure analysis, residual risk |
| [prototype/](prototype/) | The code: `python -m evals.run --gate` runs everything offline in under a second |
| [site/pilot](../site/pilot/index.html) | Interactive review queue on the 220 test documents, with a threshold slider |
