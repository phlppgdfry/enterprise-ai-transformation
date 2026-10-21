"""Evaluate the pilot against the truth files and apply the release gate.

What it measures (definitions in 06-applied-ai/evaluation-framework.md):
  straight-through rate   documents that go to the TMS with no person
  error escape rate       documents that went straight through with a wrong or
                          missing field, the wrong type, or a genuine exception
  exception catch rate    genuine exceptions that reached a person
  review usefulness       reviews that found a real problem

How it decides:
  1. Ablation on dev: layers A-D switched on one by one.
  2. Threshold sweep on dev: pick the threshold with the most straight-through
     documents while the escape rate stays within the error budget, and never
     at or below the confidence of fields read with an assumption.
  3. Report on test, with that threshold, untouched until now.
  4. Gate: the test results must meet evals/thresholds.json, and the pipeline's
     configured threshold must be the one the sweep picked.

    python -m evals.run           # write evals/report.json and evals/report.md
    python -m evals.run --gate    # also exit 1 when the gate fails
    python -m evals.run --provider claude --set test   # real model, costs money
"""

import argparse
import copy
import json
import math
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from freightdoc.pipeline import POLICIES, process  # noqa: E402

EVALS = Path(__file__).resolve().parent
THRESHOLDS = json.loads((EVALS / "thresholds.json").read_text())
SWEEP = [round(0.5 + 0.05 * i, 2) for i in range(10)]


def load(name):
    folder = ROOT / "data" / name
    documents = [json.loads(line) for line in (folder / "documents.jsonl").read_text().splitlines()]
    truth = json.loads((folder / "truth.json").read_text())
    return documents, truth


def same(name, got, want):
    if got is None:
        return False
    if name.endswith("_kg"):
        return abs(got - want) <= 0.5
    if name in ("total_amount",):
        return abs(got - want) < 0.005
    if name == "line_amounts":
        return len(got) == len(want) and all(abs(a - b) < 0.005 for a, b in zip(got, want))
    if isinstance(want, list):
        return sorted(str(x).upper() for x in got) == sorted(str(x).upper() for x in want)
    if isinstance(want, str):
        return " ".join(str(got).split()).casefold() == " ".join(want.split()).casefold()
    return got == want


def score_document(result, truth):
    t = truth[result.id]
    outcome = {"correct": [], "wrong": [], "missing": []}
    if result.doc_type == t["type"]:
        for name, want in t["fields"].items():
            f = result.fields.get(name)
            if f is None or f.value in (None, []):
                outcome["missing"].append(name)
            elif same(name, f.value, want):
                outcome["correct"].append(name)
            else:
                outcome["wrong"].append(name)
    clean = (result.doc_type == t["type"] and not outcome["wrong"] and not outcome["missing"]
             and not t["exceptions"])
    return {
        "id": result.id, "type": t["type"], "predicted_type": result.doc_type,
        "route": result.route, "clean": clean, "exceptions": t["exceptions"],
        "noise": t["noise"], **outcome,
    }


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4))


def metrics(scored):
    n = len(scored)
    auto = [s for s in scored if s["route"] == "auto"]
    review = [s for s in scored if s["route"] == "review"]
    escapes = [s for s in auto if not s["clean"]]
    exceptions = [s for s in scored if s["exceptions"]]
    caught = [s for s in exceptions if s["route"] != "auto"]
    correct = sum(len(s["correct"]) for s in scored)
    wrong = sum(len(s["wrong"]) for s in scored)
    missing = sum(len(s["missing"]) for s in scored)
    return {
        "documents": n,
        "classification_accuracy": round(sum(s["type"] == s["predicted_type"] for s in scored) / n, 4),
        "field_accuracy": round(correct / (correct + wrong), 4) if correct + wrong else 0.0,
        "field_coverage": round((correct + wrong) / (correct + wrong + missing), 4),
        "stp_rate": round(len(auto) / n, 4),
        "stp_ci95": wilson(len(auto), n),
        "review_rate": round(len(review) / n, 4),
        "manual_rate": round(sum(s["route"] == "manual" for s in scored) / n, 4),
        "error_escape_rate": round(len(escapes) / n, 4),
        "error_escape_ci95": wilson(len(escapes), n),
        "escapes": len(escapes),
        "exception_documents": len(exceptions),
        "exception_catch_rate": round(len(caught) / len(exceptions), 4) if exceptions else 1.0,
        "review_usefulness": round(sum(not s["clean"] for s in review) / len(review), 4) if review else 0.0,
        "escape_details": [{"id": s["id"], "type": s["type"], "wrong": s["wrong"],
                            "missing": s["missing"], "exceptions": s["exceptions"],
                            "noise": s["noise"]} for s in escapes],
    }


class Cached:
    """Reads each document once per run: the read does not depend on the policy,
    so the ablation and the sweep cost no extra model calls."""

    def __init__(self, provider):
        self.provider, self.name, self.memo = provider, getattr(provider, "name", "rules"), {}

    def read(self, text):
        if text not in self.memo:
            self.memo[text] = self.provider.read(text)
        doc_type, conf, fields = self.memo[text]
        return doc_type, conf, {k: copy.copy(v) for k, v in fields.items()}


def evaluate(documents, truth, policy, provider=None):
    results = process(documents, provider=provider, policy=policy)
    scored = [score_document(r, truth) for r in results]
    return results, scored, metrics(scored)


def pick_threshold(sweep_rows, budget, floor=0.0):
    """Most straight-through documents within the error budget, never below the
    floor; ties -> higher threshold."""
    ok = [r for r in sweep_rows if r["error_escape_rate"] <= budget and r["threshold"] >= floor]
    if not ok:
        return max(r["threshold"] for r in sweep_rows)
    best = max(r["stp_rate"] for r in ok)
    return max(r["threshold"] for r in ok if r["stp_rate"] == best)


def noise_breakdown(scored):
    """For each kind of injected fault: how often it ended up wrong in the TMS."""
    rows = {}
    for s in scored:
        for kind in s["noise"]:
            row = rows.setdefault(kind, {"documents": 0, "auto": 0, "escaped": 0})
            row["documents"] += 1
            row["auto"] += s["route"] == "auto"
            row["escaped"] += s["route"] == "auto" and not s["clean"]
    return dict(sorted(rows.items()))


def run(provider=None, sets=("dev", "test")):
    from freightdoc.extract import RulesProvider
    provider = Cached(provider or RulesProvider())
    dev_docs, dev_truth = load("dev")
    test_docs, test_truth = load("test")
    report = {"provider": getattr(provider, "name", "rules"), "thresholds": THRESHOLDS}

    report["ablation_dev"] = {}
    for key, policy in POLICIES.items():
        _, _, m = evaluate(dev_docs, dev_truth, policy, provider)
        m.pop("escape_details")
        report["ablation_dev"][key] = {"policy": policy.name, **m}

    sweep = []
    for t in SWEEP:
        _, _, m = evaluate(dev_docs, dev_truth, replace(POLICIES["D"], confidence_threshold=t), provider)
        sweep.append({"threshold": t, "stp_rate": m["stp_rate"],
                      "error_escape_rate": m["error_escape_rate"], "review_rate": m["review_rate"]})
    report["sweep_dev"] = sweep
    chosen = pick_threshold(sweep, THRESHOLDS["error_budget"], THRESHOLDS["min_threshold"])
    report["chosen_threshold"] = chosen
    report["configured_threshold"] = POLICIES["D"].confidence_threshold

    policy = replace(POLICIES["D"], confidence_threshold=chosen)
    results, scored, test = evaluate(test_docs, test_truth, policy, provider)
    report["test"] = test
    report["test_noise"] = noise_breakdown(scored)
    report["test_ablation"] = {}
    for key, pol in POLICIES.items():
        _, _, m = evaluate(test_docs, test_truth, replace(pol, confidence_threshold=chosen if pol.confidence_threshold else None), provider)
        report["test_ablation"][key] = {"policy": pol.name, "stp_rate": m["stp_rate"],
                                        "error_escape_rate": m["error_escape_rate"],
                                        "escapes": m["escapes"], "review_rate": m["review_rate"]}
    dev_escapes = report["ablation_dev"]["D"]["escapes"]
    pooled_n = report["ablation_dev"]["D"]["documents"] + test["documents"]
    pooled_k = dev_escapes + test["escapes"]
    report["pooled_escape_rate"] = round(pooled_k / pooled_n, 4)
    report["pooled_escape_ci95"] = wilson(pooled_k, pooled_n)
    report["pooled_escapes"] = pooled_k
    report["pooled_documents"] = pooled_n
    report["gate"] = gate(report)
    return report, results, scored


def gate(report):
    t, th = report["test"], THRESHOLDS
    checks = [
        ("classification accuracy", t["classification_accuracy"], ">=", th["min_classification_accuracy"]),
        ("error escape rate", t["error_escape_rate"], "<=", th["error_budget"]),
        ("error escape rate below human keying error rate", t["error_escape_rate"], "<", th["human_error_rate"]),
        ("straight-through rate", t["stp_rate"], ">=", th["min_stp_rate"]),
        ("exception catch rate", t["exception_catch_rate"], ">=", th["min_exception_catch_rate"]),
        ("configured threshold = threshold picked on dev", report["configured_threshold"], "==", report["chosen_threshold"]),
    ]
    ops = {">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b, "<": lambda a, b: a < b,
           "==": lambda a, b: a == b}
    rows = [{"check": name, "value": value, "op": op, "target": target, "pass": ops[op](value, target)}
            for name, value, op, target in checks]
    return {"pass": all(r["pass"] for r in rows), "checks": rows}


def pct(x):
    return f"{100 * x:.1f}%"


def markdown(report):
    t = report["test"]
    lines = [
        "# Pilot evaluation report",
        "",
        "*Generated by `python -m evals.run` (provider: `%s`). Do not edit by hand.*" % report["provider"],
        "",
        "## Release gate (test set)",
        "",
        "| Check | Value | Target | Result |",
        "|---|---|---|---|",
    ]
    for r in report["gate"]["checks"]:
        fmt = (lambda v: pct(v)) if isinstance(r["value"], float) and r["value"] <= 1 and "threshold" not in r["check"] else str
        lines.append(f"| {r['check']} | {fmt(r['value'])} | {r['op']} {fmt(r['target'])} | {'pass' if r['pass'] else '**FAIL**'} |")
    lines += [
        "",
        f"**Gate: {'PASS' if report['gate']['pass'] else 'FAIL'}**",
        "",
        "## Test set results",
        "",
        f"- Documents: {t['documents']}",
        f"- Straight-through: {pct(t['stp_rate'])} (95% CI {pct(t['stp_ci95'][0])}–{pct(t['stp_ci95'][1])})",
        f"- Review: {pct(t['review_rate'])}, manual: {pct(t['manual_rate'])}",
        f"- Error escapes: {t['escapes']} ({pct(t['error_escape_rate'])}, 95% CI {pct(t['error_escape_ci95'][0])}–{pct(t['error_escape_ci95'][1])})",
        f"- Exception catch rate: {pct(t['exception_catch_rate'])} of {t['exception_documents']} documents with a genuine problem",
        f"- Classification accuracy: {pct(t['classification_accuracy'])}; field accuracy {pct(t['field_accuracy'])}, coverage {pct(t['field_coverage'])}",
        f"- Reviews that found a real problem: {pct(t['review_usefulness'])}",
        "",
        "## Ablation (test set, threshold %.2f)" % report["chosen_threshold"],
        "",
        "| Configuration | Straight-through | Escapes | Escape rate | Review |",
        "|---|---|---|---|---|",
    ]
    for row in report["test_ablation"].values():
        lines.append(f"| {row['policy']} | {pct(row['stp_rate'])} | {row['escapes']} | {pct(row['error_escape_rate'])} | {pct(row['review_rate'])} |")
    lines += ["", "## Threshold sweep (dev set, configuration D)", "",
              "| Threshold | Straight-through | Escape rate | Review |", "|---|---|---|---|"]
    for row in report["sweep_dev"]:
        mark = " ← chosen" if row["threshold"] == report["chosen_threshold"] else ""
        lines.append(f"| {row['threshold']:.2f}{mark} | {pct(row['stp_rate'])} | {pct(row['error_escape_rate'])} | {pct(row['review_rate'])} |")
    lines += ["", "## Where the faults went (test set)", "",
              "| Injected fault | Documents | Went straight through | Escaped with an error |", "|---|---|---|---|"]
    for kind, row in report["test_noise"].items():
        lines.append(f"| {kind} | {row['documents']} | {row['auto']} | {row['escaped']} |")
    lines += ["", "## Escapes (test set)", ""]
    if not t["escape_details"]:
        lines.append("None.")
    for e in t["escape_details"]:
        lines.append(f"- `{e['id']}` ({e['type']}): wrong {e['wrong'] or '-'}, missing {e['missing'] or '-'}, "
                     f"exceptions {e['exceptions'] or '-'}, injected {e['noise'] or '-'}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", action="store_true")
    parser.add_argument("--provider", default="rules", choices=["rules", "claude"])
    args = parser.parse_args()
    provider = None
    if args.provider == "claude":
        from freightdoc.providers.claude import ClaudeProvider
        provider = ClaudeProvider()
    report, _, _ = run(provider)
    suffix = "" if args.provider == "rules" else f"-{args.provider}"
    (EVALS / f"report{suffix}.json").write_text(json.dumps(report, indent=1) + "\n")
    (EVALS / f"report{suffix}.md").write_text(markdown(report))
    t = report["test"]
    print(f"test: STP {pct(t['stp_rate'])}, escapes {t['escapes']} ({pct(t['error_escape_rate'])}), "
          f"exceptions caught {pct(t['exception_catch_rate'])}, threshold {report['chosen_threshold']}")
    for r in report["gate"]["checks"]:
        print(f"  [{'x' if r['pass'] else ' '}] {r['check']}: {r['value']} {r['op']} {r['target']}")
    if args.gate and not report["gate"]["pass"]:
        print("GATE FAILED")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
