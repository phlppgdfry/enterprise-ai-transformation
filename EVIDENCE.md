# Evidence

What in this repository was executed, what was simulated, and what was not done. Read this before quoting anything from the case.

## Executed (runs in CI on every push)

| What | How to check |
|---|---|
| Synthetic document sets are reproducible from their recipe | `python scripts/make_data.py --check` |
| Pilot unit tests: parsing, ISO 6346, rules, routing, linking, Claude request shape (fake client) | `python -m unittest discover -s tests -t .` in `06-applied-ai/prototype` |
| Evaluation: ablation A-D, threshold sweep on dev, results on test, release gate | `python -m evals.run --gate` |
| Readiness, portfolio (incl. 2,000-sample robustness) and business case computed from `model/` | `python scripts/build.py --check` |
| Every number and generated table in the Markdown and HTML matches the model | `python scripts/build.py --check` |
| Non-generated claims in the prose hold | `tests/test_model.py::ClaimsTest` |
| ROI, readiness and scoring workbooks compute the same results as the Python model | `tests/test_model.py::WorkbookTest` (own formula evaluator) |
| Browser model on the site matches the Python model | `node scripts/check_js.js` |
| Relative links resolve | `python scripts/check_links.py` |

## Rendered locally (committed output)

| What | How |
|---|---|
| Board deck PDF, social card, pilot GIF | `python scripts/render_media.py` (Playwright + local Chrome + ffmpeg) |
| Screen recording of the 5-minute walkthrough, with subtitles | `python scripts/record_walkthrough.py OUT_DIR [--captions]`; not committed |
| BPMN files checked in bpmn-js | Opened in the bpmn.io viewer during development; not part of CI |

## Simulated

| What | Reality |
|---|---|
| Client, people, interviews, survey, time study, mailbox sample | Fictional, written to be plausible for a Zeebrugge forwarder |
| Documents | Synthetic OCR text, 2 × 220, with faults injected at the rates in the interview synthesis |
| Document model | Deterministic offline provider; Claude provider not run against the API |
| Workshops, steering, board meeting | Agendas, decisions and outputs written as they would be produced |

## Not done

- No real client data, no real documents, no shadow mode.
- No call to the Claude API (it costs money per document and needs credentials).
- No production build: mailbox connector, OCR hand-off, TMS integration, review UI beyond the demo, monitoring.
- No legal review of the EU AI Act, GDPR and labour-law statements.
- The five-minute CEO walkthrough has a generated screen recording, but no voice-over by the presenter yet.

## Iterations that are part of the record

The pilot failed its gate twice before passing; the [pilot results](06-applied-ai/pilot-results.md) list the three runs and what changed. Those first two runs are documented from the development log, not reproducible from the current code, which contains the fix.
