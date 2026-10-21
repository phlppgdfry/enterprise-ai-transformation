"""Compute the transformation model and write it everywhere it is quoted.

One source of truth: model/*.json plus the pilot's evaluation report. From
those this script computes readiness, the ranked portfolio and the business
case, then writes:

  - every <!--n:key-->...<!--/n--> number in the Markdown and HTML files
  - every <!--table:name-->...<!--/table--> table in the Markdown files
  - site/data/*.json for the interactive pages
  - the Excel workbooks (readiness scorecard, use-case scoring, ROI calculator)

    python scripts/build.py           # write
    python scripts/build.py --check   # fail if anything is out of date (CI)
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / "06-applied-ai" / "prototype"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PROTO))
sys.path.insert(0, str(ROOT / "scripts"))

from engine import business_case, portfolio, readiness  # noqa: E402
import bpmn  # noqa: E402
import charts  # noqa: E402
from xlsx import Sheet, col_letter, workbook_bytes  # noqa: E402

SKIP_DIRS = {".git", "node_modules", "data", "__pycache__", ".github"}
NUMBER = re.compile(r"<!--n:([\w.\-]+)-->(.*?)<!--/n-->", re.S)
TABLE = re.compile(r"(<!--table:([\w\-]+)-->)(.*?)(<!--/table-->)", re.S)


def load(name):
    return json.loads((ROOT / "model" / f"{name}.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- model ----

def compute():
    report = json.loads((PROTO / "evals" / "report.json").read_text())
    client = load("client")
    bc = business_case.run(load("business_case"), report, client["doc_desk_fte"])
    uc01_value = int(round(bc["steady_state_value"], -3))
    pf = portfolio.run(load("use_cases"), uc01_value)
    rd = readiness.run(load("readiness"), pf["ranking"])
    return {"client": client, "report": report, "bc": bc, "bc_model": load("business_case"),
            "portfolio": pf, "readiness": rd, "roadmap": load("roadmap"),
            "risks": load("risks"), "raci": load("raci"),
            "stakeholders": load("stakeholders")["stakeholders"], "uc01_value": uc01_value}


# ------------------------------------------------------------ formatting ----

def eur(x):
    return ("-€" if x < 0 else "€") + f"{abs(round(x)):,}"


def keur(x):
    return ("-€" if x < 0 else "€") + f"{abs(x) / 1000:,.0f}k"


def pct(x, digits=1):
    return f"{100 * x:.{digits}f}%"


def months(x):
    return "not within 3 years" if x is None else f"{x:.0f} months"


def numbers(m):
    r, bc, rd, pf = m["report"], m["bc"], m["readiness"], m["portfolio"]
    t, base = r["test"], bc["base"]
    n = {
        "pilot.docs": str(t["documents"]),
        "pilot.stp": pct(t["stp_rate"]),
        "pilot.stp_ci_low": pct(t["stp_ci95"][0]),
        "pilot.stp_ci_high": pct(t["stp_ci95"][1]),
        "pilot.review": pct(t["review_rate"]),
        "pilot.manual": pct(t["manual_rate"]),
        "pilot.escapes": str(t["escapes"]),
        "pilot.escape_rate": pct(t["error_escape_rate"]),
        "pilot.escape_ci_high": pct(t["error_escape_ci95"][1]),
        "pilot.exceptions_caught": pct(t["exception_catch_rate"], 0),
        "pilot.exception_docs": str(t["exception_documents"]),
        "pilot.classification": pct(t["classification_accuracy"]),
        "pilot.field_accuracy": pct(t["field_accuracy"]),
        "pilot.review_useful": pct(t["review_usefulness"], 0),
        "pilot.threshold": f"{r['chosen_threshold']:.2f}",
        "pilot.threshold_floor": f"{r['thresholds']['min_threshold']:.2f}",
        "pilot.error_budget": pct(r["thresholds"]["error_budget"], 0),
        "pilot.human_error": pct(r["thresholds"]["human_error_rate"]),
        "pilot.dev_escapes": str(r["ablation_dev"]["D"]["escapes"]),
        "pilot.pooled_escapes": str(r["pooled_escapes"]),
        "pilot.pooled_docs": str(r["pooled_documents"]),
        "pilot.pooled_escape_rate": pct(r["pooled_escape_rate"], 2),
        "pilot.pooled_ci_high": pct(r["pooled_escape_ci95"][1]),
        "pilot.gate": "PASS" if r["gate"]["pass"] else "FAIL",
    }
    for k, row in r["test_ablation"].items():
        n[f"pilot.{k}.stp"] = pct(row["stp_rate"])
        n[f"pilot.{k}.escapes"] = str(row["escapes"])
        n[f"pilot.{k}.escape_rate"] = pct(row["error_escape_rate"])
    n["pilot.naive_factor"] = f"{r['test_ablation']['A']['escapes'] / max(1, r['test_ablation']['D']['escapes']):.0f}"

    years = base["years"]
    n.update({
        "bc.one_off": keur(base["one_off"]),
        "bc.saved_minutes": f"{base['saved_minutes_per_document']:.1f}",
        "bc.minutes_after": f"{base['minutes_after']:.1f}",
        "bc.model_cost_doc": f"€{base['model_cost_per_document_eur']:.3f}",
        "bc.model_cost_y1": eur(years[0]["model_cost"]),
        "bc.run_cost_y1": keur(years[0]["run_cost"]),
        "bc.hours_y2": f"{years[1]['hours_freed']:,}",
        "bc.fte_y2": f"{years[1]['fte_freed']:.1f}",
        "bc.cash_fte_y1": f"{years[0]['cash_fte']:.1f}",
        "bc.cash_fte_y2": f"{years[1]['cash_fte']:.1f}",
        "bc.errors_avoided_y2": f"{years[1]['errors_avoided']:,}",
        "bc.error_value_y2": keur(years[1]["error_value"]),
        "bc.capacity_value_y2": keur(years[1]["capacity_value"]),
        "bc.cash_labour_y2": keur(years[1]["cash_labour_value"]),
        "bc.error_rate_after": pct(base["error_rate_after"], 2),
        "bc.steady_value": keur(bc["steady_state_value"]),
        "bc.uc01_value": keur(m["uc01_value"]),
        "bc.noattr_npv": keur(bc["cash_if_all_leavers_replaced"]["npv"]),
        "bc.noattr_payback": months(bc["cash_if_all_leavers_replaced"]["payback_months"]),
        "bc.tornado_top": m["bc_label"][bc["tornado"]["rows"][0]["key"]],
        "bc.tornado_top2": m["bc_label"][bc["tornado"]["rows"][1]["key"]],
        "bc.stp_swing": keur(next(x["swing"] for x in bc["tornado"]["rows"] if x["key"] == "stp_rate")),
        "bc.top_swing": keur(bc["tornado"]["rows"][0]["swing"]),
    })
    for view in ("cash", "capacity"):
        n[f"bc.{view}.npv"] = keur(base[view]["npv"])
        n[f"bc.{view}.payback"] = months(base[view]["payback_months"])
        n[f"bc.{view}.roi"] = pct(base[view]["roi"], 0)
        for i, net in enumerate(base[view]["net_per_year"], 1):
            n[f"bc.{view}.net_y{i}"] = keur(net)
        for kind in ("pessimistic", "optimistic"):
            s = bc["scenarios"][kind][view]
            n[f"bc.{kind}.{view}.npv"] = keur(s["npv"])
            n[f"bc.{kind}.{view}.payback"] = months(s["payback_months"])

    # Dutch formatting for samenvatting.md
    n["nl.payback"] = f"{base['cash']['payback_months']:.0f} maanden"
    n["nl.stp"] = pct(t["stp_rate"]).replace(".", ",")
    n["nl.overall"] = f"{rd['overall']:.1f}".replace(".", ",")
    n.update({"rd.overall": f"{rd['overall']:.1f}", "rd.level": rd["level"],
              "rd.target": f"{rd['target_overall']:.1f}"})
    for d in rd["dimensions"]:
        n[f"rd.{d['id']}"] = f"{d['current']:.1f}"
        n[f"rd.{d['id']}.target"] = f"{d['target']:.1f}"
    for i, g in enumerate(rd["gaps"][:5], 1):
        n[f"rd.gap{i}"] = f"{g['id']} {g['question'].lower()}"
    lowest = min(rd["dimensions"], key=lambda d: d["current"])
    n["rd.lowest"] = f"{lowest['name']} ({lowest['current']:.1f})"

    for row in pf["ranking"]:
        key = row["id"]
        n[f"pf.{key}.score"] = f"{row['score']:.2f}"
        n[f"pf.{key}.rank"] = str(row["rank"]) if row["rank"] else "parked"
        n[f"pf.{key}.top3"] = pct(row["top3"], 0)
        n[f"pf.{key}.top1"] = pct(row["top1"], 0)
        n[f"pf.{key}.value"] = keur(row["annual_value_eur"])
    ranked = [r for r in pf["ranking"] if r["rank"]]
    for i in range(3):
        n[f"pf.rank{i + 1}"] = f"{ranked[i]['id']} {ranked[i]['name']}"
    n["pf.count"] = str(len(pf["ranking"]))
    return n


# ---------------------------------------------------------------- tables ----

def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in row) + " |")
    return "\n".join(out)


def tables(m):
    r, bc, rd, pf = m["report"], m["bc"], m["readiness"], m["portfolio"]
    uc = {u["id"]: u for u in pf["use_cases"]}
    t = {}
    t["readiness-dimensions"] = md_table(
        ["Dimension", "Today", "Level", "Target (12 months)"],
        [[d["name"], f"{d['current']:.1f}", d["level"], f"{d['target']:.1f}"] for d in rd["dimensions"]]
        + [["**Overall**", f"**{rd['overall']:.1f}**", f"**{rd['level']}**", f"**{rd['target_overall']:.1f}**"]])
    t["readiness-items"] = md_table(
        ["#", "Question", "Today", "Target", "Evidence"],
        [[i["id"], i["question"], i["score"], i["target"], i["evidence"]]
         for d in rd["raw"] for i in d["items"]])
    t["readiness-gaps"] = md_table(
        ["#", "Gap", "Today → target", "Needed by", "Priority"],
        [[g["id"], g["question"], f"{g['current']} → {g['target']}", ", ".join(g["needed_by"]) or "-", g["priority"]]
         for g in rd["gaps"][:10]])
    t["use-case-ranking"] = md_table(
        ["Rank", "Use case", "Value", "Feasibility", "Risk (5 = low)", "Score", "Quadrant", "Top 3 under re-weighting"],
        [[row["rank"] or "–", f"{row['id']} {row['name']}", f"{row['value']:.2f}", f"{row['feasibility']:.2f}",
          f"{row['risk']:.2f}", f"{row['score']:.2f}", row["quadrant"], pct(row["top3"], 0)]
         for row in pf["ranking"]])
    t["use-case-catalog"] = md_table(
        ["#", "Use case", "What it does", "Kind of AI", "Owner", "Value / year", "EU AI Act"],
        [[u["id"], u["name"], u["summary"], u["ai_type"], u["owner"], keur(u["annual_value_eur"]), u["ai_act"]["tier"]]
         for u in pf["use_cases"]])
    t["use-case-scores"] = md_table(
        ["#", "Fit", "Data", "Simplicity", "Integration", "Change", "Regulatory", "Error tolerance", "Privacy", "Value basis"],
        [[u["id"]] + [u["scores"][k] for k in ("strategic_fit", "data_readiness", "technical_simplicity",
                                                "integration_ease", "change_ease", "regulatory",
                                                "error_tolerance", "privacy")] + [u["value_basis"]]
         for u in pf["use_cases"]])
    t["ai-act"] = md_table(
        ["#", "Use case", "Tier", "Why"],
        [[u["id"], u["name"], u["ai_act"]["tier"], u["ai_act"]["basis"]] for u in pf["use_cases"]])
    vals = bc["values"]
    fmt_val = lambda a, v: (pct(v) if a["unit"] == "%" else f"{v:,}" if isinstance(v, int) else f"{v:g}")
    t["assumptions"] = md_table(
        ["#", "Assumption", "Base", "Low", "High", "Source", "Basis"],
        [[a["id"], a["name"] + (f" ({a['unit']})" if a["unit"] not in ("%",) else ""),
          fmt_val(a, vals[a["key"]]["base"]), fmt_val(a, vals[a["key"]]["low"]), fmt_val(a, vals[a["key"]]["high"]),
          a["source"], a["basis"]] for a in m["bc_model"]["assumptions"]])
    y = bc["base"]["years"]
    rows = [
        ("Documents", lambda i: f"{y[i]['documents']:,}"),
        ("Clerk hours freed", lambda i: f"{y[i]['hours_freed']:,}"),
        ("FTE freed", lambda i: f"{y[i]['fte_freed']:.2f}"),
        ("FTE that leave the cost base (cash view)", lambda i: f"{y[i]['cash_fte']:.2f}"),
        ("Errors avoided", lambda i: f"{y[i]['errors_avoided']:,}"),
        ("Capacity value", lambda i: eur(y[i]["capacity_value"])),
        ("Cash labour value", lambda i: eur(y[i]["cash_labour_value"])),
        ("Error cost avoided", lambda i: eur(y[i]["error_value"])),
        ("Model usage", lambda i: eur(-y[i]["model_cost"])),
        ("Run cost incl. model usage", lambda i: eur(-y[i]["run_cost"])),
        ("**Net, capacity view**", lambda i: f"**{eur(bc['base']['capacity']['net_per_year'][i])}**"),
        ("**Net, cash view**", lambda i: f"**{eur(bc['base']['cash']['net_per_year'][i])}**"),
    ]
    t["bc-years"] = md_table(["", "Year 1", "Year 2", "Year 3"], [[label] + [f(i) for i in range(3)] for label, f in rows])
    t["bc-scenarios"] = md_table(
        ["Scenario", "NPV cash view", "Payback cash view", "NPV capacity view", "Payback capacity view"],
        [[name.capitalize(), keur(s["cash"]["npv"]), months(s["cash"]["payback_months"]),
          keur(s["capacity"]["npv"]), months(s["capacity"]["payback_months"])]
         for name, s in (("pessimistic", bc["scenarios"]["pessimistic"]), ("base", bc["base"]),
                         ("optimistic", bc["scenarios"]["optimistic"]))]
        + [["Base, but every leaver replaced", keur(bc["cash_if_all_leavers_replaced"]["npv"]),
            months(bc["cash_if_all_leavers_replaced"]["payback_months"]), "–", "–"]])
    t["tornado"] = md_table(
        ["Driver", "NPV at low value", "NPV at high value", "Swing"],
        [[m["bc_label"][row["key"]], keur(row["low"]), keur(row["high"]), keur(row["swing"])]
         for row in bc["tornado"]["rows"]])
    rm = m["roadmap"]
    streams = {s["id"]: s["name"] for s in rm["streams"]}
    t["roadmap-items"] = md_table(
        ["#", "Stream", "What", "Weeks", "Owner", "Deliverable"],
        [[i["id"], streams[i["stream"]], i["title"], f"{i['start']}–{i['end']}", i["owner"], i["deliverable"]]
         for i in rm["items"]])
    phases = [("Days 1–30 (weeks 1–4)", 1, 4), ("Days 31–60 (weeks 5–9)", 5, 9), ("Days 61–90 (weeks 10–13)", 10, 13)]
    blocks = []
    for label, a, b in phases:
        items = [i for i in rm["items"] if a <= i["start"] <= b]
        blocks.append(f"**{label}**\n\n" + md_table(
            ["#", "Start", "What", "Owner", "Done when"],
            [[i["id"], f"week {i['start']}", i["title"], i["owner"], i["deliverable"]] for i in items]))
    t["90-day"] = "\n\n".join(blocks)
    t["gates"] = md_table(["Gate", "Week", "Name", "Pass criteria"],
                          [[g["id"], g["week"], g["name"], "; ".join(g["criteria"])] for g in rm["gates"]])
    t["waves"] = md_table(["Wave", "Use cases"],
                          [[w, ", ".join(f"{i} {uc[i]['name']}" for i in ids)] for w, ids in rm["waves"].items()])
    roles = m["raci"]["roles"]
    t["raci"] = md_table(["Activity"] + roles,
                         [[a["activity"]] + [a.get(role, "") for role in roles] for a in m["raci"]["activities"]])
    risks = sorted(m["risks"]["risks"], key=lambda x: -x["likelihood"] * x["impact"])
    t["risks"] = md_table(
        ["#", "Risk", "Category", "L", "I", "Score", "Owner", "Mitigation", "Controls"],
        [[x["id"], x["risk"], x["category"], x["likelihood"], x["impact"], x["likelihood"] * x["impact"],
          x["owner"], x["mitigation"], "; ".join(x["controls"]) or "-"] for x in risks])
    t["stakeholders"] = md_table(
        ["Who", "Role", "Influence", "Interest", "Stance", "Concern", "What they need", "How we engage"],
        [[s["name"], s["role"], s["influence"], s["interest"], s["stance"], s["concern"], s["needs"], s["engagement"]]
         for s in m["stakeholders"]])
    t["pilot-gate"] = md_table(
        ["Check", "Result", "Target", ""],
        [[c["check"], pct(c["value"]) if isinstance(c["value"], float) and "threshold" not in c["check"] else c["value"],
          f"{c['op']} " + (pct(c["target"]) if isinstance(c["target"], float) and "threshold" not in c["check"] else str(c["target"])),
          "pass" if c["pass"] else "**FAIL**"] for c in r["gate"]["checks"]])
    t["pilot-ablation"] = md_table(
        ["Configuration", "Straight-through", "Error escapes", "Escape rate", "Review"],
        [[row["policy"], pct(row["stp_rate"]), row["escapes"], pct(row["error_escape_rate"]), pct(row["review_rate"])]
         for row in r["test_ablation"].values()])
    t["pilot-sweep"] = md_table(
        ["Threshold", "Straight-through", "Escape rate", "Review"],
        [[f"{row['threshold']:.2f}" + (" ← chosen" if row["threshold"] == r["chosen_threshold"] else ""),
          pct(row["stp_rate"]), pct(row["error_escape_rate"]), pct(row["review_rate"])] for row in r["sweep_dev"]])
    t["pilot-faults"] = md_table(
        ["Fault injected", "Documents", "Went straight through", "Reached the TMS wrong"],
        [[k, v["documents"], v["auto"], v["escaped"]] for k, v in r["test_noise"].items()])
    return t


# ------------------------------------------------------------- workbooks ----

def readiness_workbook(m):
    rd = m["readiness"]
    s = Sheet("Scorecard")
    s.widths = {1: 6, 2: 26, 3: 58, 4: 9, 5: 9, 6: 8, 7: 90}
    s.set(1, 1, "AI readiness scorecard: Wendelkaai Logistics (fictional)", "title")
    s.set(2, 1, "Yellow cells are inputs (1-5). Gap and summary update automatically.")
    s.row(4, ["#", "Dimension", "Question", "Today", "Target", "Gap", "Evidence"], "header")
    r = 5
    for d in rd["raw"]:
        for i in d["items"]:
            s.row(r, [i["id"], d["name"], i["question"]])
            s.set(r, 4, i["score"], "input")
            s.set(r, 5, i["target"], "input")
            s.set(r, 6, f"=E{r}-D{r}")
            s.set(r, 7, i["evidence"], "wrap")
            r += 1
    last = r - 1
    summary = Sheet("Summary")
    summary.widths = {1: 30, 2: 10, 3: 10, 4: 10}
    summary.row(1, ["Dimension", "Today", "Target", "Gap"], "header")
    for k, d in enumerate(rd["dimensions"], 2):
        summary.set(k, 1, d["name"])
        summary.set(k, 2, f"=ROUND(AVERAGEIF(Scorecard!$B$5:$B${last},A{k},Scorecard!$D$5:$D${last}),2)", "dec")
        summary.set(k, 3, f"=ROUND(AVERAGEIF(Scorecard!$B$5:$B${last},A{k},Scorecard!$E$5:$E${last}),2)", "dec")
        summary.set(k, 4, f"=C{k}-B{k}", "dec")
    k = len(rd["dimensions"]) + 2
    summary.set(k, 1, "Overall", "header")
    summary.set(k, 2, f"=ROUND(AVERAGE(B2:B{k - 1}),2)", "dec")
    summary.set(k, 3, f"=ROUND(AVERAGE(C2:C{k - 1}),2)", "dec")
    summary.set(k, 4, f"=C{k}-B{k}", "dec")
    return workbook_bytes([s, summary])


def scoring_workbook(m):
    pf = m["portfolio"]
    crit = pf["criteria"]
    s = Sheet("Scoring")
    keys = ["strategic_fit", "data_readiness", "technical_simplicity", "integration_ease", "change_ease",
            "regulatory", "error_tolerance", "privacy"]
    s.widths = {1: 8, 2: 40, 3: 12}
    s.set(1, 1, "Use-case scoring: change the yellow weights and scores; the ranking follows.", "title")
    s.row(3, ["Group weights", "Value", "Feasibility", "Risk"], "header")
    s.set(4, 2, crit["value"]["weight"], "input")
    s.set(4, 3, crit["feasibility"]["weight"], "input")
    s.set(4, 4, crit["risk"]["weight"], "input")
    s.set(4, 1, "weight")
    subw = {**crit["value"]["sub"], **crit["feasibility"]["sub"], **crit["risk"]["sub"]}
    header = ["#", "Use case", "Value / year (EUR)", "Value score"] + keys + ["Value", "Feasibility", "Risk", "Score", "Rank"]
    s.row(6, ["Sub-weights", None, None, subw["annual_value"]] + [subw[k] for k in keys], "input")
    s.set(6, 1, "Sub-weights", "header")
    s.row(7, header, "header")
    first = 8
    for idx, u in enumerate(pf["use_cases"]):
        r = first + idx
        s.set(r, 1, u["id"])
        s.set(r, 2, u["name"])
        s.set(r, 3, u["annual_value_eur"], "input")
        s.set(r, 4, f"=1+4*MIN(C{r},{pf['value_scale_eur']})/{pf['value_scale_eur']}", "dec")
        for j, k in enumerate(keys):
            s.set(r, 5 + j, u["scores"][k], "input")
        c = {k: col_letter(5 + j) for j, k in enumerate(keys)}
        v = f"=D{r}*$D$6+{c['strategic_fit']}{r}*${c['strategic_fit']}$6"
        f = "=" + "+".join(f"{c[k]}{r}*${c[k]}$6" for k in ("data_readiness", "technical_simplicity", "integration_ease", "change_ease"))
        rk = "=" + "+".join(f"{c[k]}{r}*${c[k]}$6" for k in ("regulatory", "error_tolerance", "privacy"))
        base = 5 + len(keys)
        s.set(r, base, v, "dec")
        s.set(r, base + 1, f, "dec")
        s.set(r, base + 2, rk, "dec")
        V, F, R = (col_letter(base + i) for i in range(3))
        s.set(r, base + 3, f"=IF({c['regulatory']}{r}=1,\"parked\",({V}{r}*$B$4+{F}{r}*$C$4+{R}{r}*$D$4)/($B$4+$C$4+$D$4))", "dec")
    last = first + len(pf["use_cases"]) - 1
    S = col_letter(5 + len(keys) + 3)
    for r in range(first, last + 1):
        s.set(r, 5 + len(keys) + 4, f"=IF(ISNUMBER({S}{r}),RANK({S}{r},${S}${first}:${S}${last}),\"-\")")
    s.set(last + 2, 1, "Score 1-5 per criterion, 5 is best (for risk criteria 5 = low risk). A regulatory score of 1 parks the use case.")
    return workbook_bytes([s])


def roi_workbook(m):
    bc, model = m["bc"], m["bc_model"]
    inputs = Sheet("Inputs")
    inputs.widths = {1: 6, 2: 56, 3: 12, 4: 12, 5: 12, 6: 22, 7: 16, 8: 80}
    inputs.set(1, 1, "ROI calculator, UC-01 freight document intelligence (fictional client)", "title")
    inputs.set(2, 1, "Change the yellow Base column. Low and high are the scenario bounds used in the business case.")
    inputs.row(4, ["#", "Assumption", "Base", "Low", "High", "Unit", "Source", "Basis"], "header")
    ref = {}
    for i, a in enumerate(model["assumptions"]):
        r = 5 + i
        v = bc["values"][a["key"]]
        style = "input_pct" if a["unit"] == "%" else "input"
        inputs.row(r, [a["id"], a["name"]])
        inputs.set(r, 3, v["base"], style)
        inputs.set(r, 4, v["low"], "pct" if a["unit"] == "%" else "default")
        inputs.set(r, 5, v["high"], "pct" if a["unit"] == "%" else "default")
        inputs.row(r, [a["unit"], a["source"], a["basis"]], start=6)
        ref[a["key"]] = f"Inputs!$C${r}"
    fte_row = 5 + len(model["assumptions"]) + 1
    inputs.set(fte_row, 2, "Doc desk headcount (FTE)")
    inputs.set(fte_row, 3, m["client"]["doc_desk_fte"], "input")
    ref["doc_desk_fte"] = f"Inputs!$C${fte_row}"

    s = Sheet("Model")
    s.widths = {1: 48, 2: 14, 3: 14, 4: 14}
    s.set(1, 1, "Calculation (do not edit; change Inputs)", "title")
    s.row(3, ["", "Year 1", "Year 2", "Year 3"], "header")
    s.set(4, 1, "Year")
    for y in range(3):
        s.set(4, 2 + y, y + 1)
    R = ref
    lines = [
        ("Review rate", f"=1-{R['stp_rate']}-{R['manual_rate']}", "pct", True),
        ("Minutes per document after", f"={R['stp_rate']}*{R['stp_minutes']}+B5*{R['review_minutes']}+{R['manual_rate']}*{R['manual_minutes']}", "dec", True),
        ("Minutes saved per document", f"={R['manual_minutes']}-B6", "dec", True),
        ("Error rate after", f"={R['pilot_escape_rate']}+B5*{R['human_error_rate']}*{R['review_error_factor']}+{R['manual_rate']}*{R['human_error_rate']}", "pct", True),
        ("Model cost per document (EUR)", f"=({R['tokens_in']}*{R['price_in_usd_per_mtok']}+{R['tokens_out']}*{R['price_out_usd_per_mtok']})/1000000*{R['eur_per_usd']}", "dec", True),
        ("Documents", "=12*{docs}*(1+{g})^({c}4-1)", "num", False),
        ("Ramp", "=IF({c}4=1,{ramp},1)", "pct", False),
        ("Clerk hours freed", "={c}10*$B$7/60*{c}11", "num", False),
        ("FTE freed", "={c}12/{fte_hours}", "dec", False),
        ("Hires avoided (growth + leavers not replaced)", "={fte}*((1+{g})^{c}4-1)+{attr}*{c}4", "dec", False),
        ("FTE leaving the cost base (cash view)", "=MIN({c}13,{c}14)", "dec", False),
        ("Errors avoided", "={c}10*({herr}-$B$8)*{c}11", "num", False),
        ("Capacity value", "={c}12*{hourly}", "eur", False),
        ("Cash labour value", "={c}15*{ftecost}", "eur", False),
        ("Error cost avoided", "={c}16*{errcost}", "eur", False),
        ("Run cost incl. model usage", "={run}+{c}10*$B$9", "eur", False),
        ("Net, capacity view", "={c}17+{c}19-{c}20", "bold_eur", False),
        ("Net, cash view", "={c}18+{c}19-{c}20", "bold_eur", False),
    ]
    fill = {"docs": R["documents_per_month"], "g": R["volume_growth"], "ramp": R["ramp_year1"],
            "fte_hours": R["fte_hours"], "fte": R["doc_desk_fte"], "attr": R["attrition_fte"],
            "herr": R["human_error_rate"], "hourly": R["hourly_cost"], "ftecost": R["fte_cost"],
            "errcost": R["error_cost"], "run": R["run_cost"]}
    for i, (label, formula, style, single) in enumerate(lines):
        r = 5 + i
        s.set(r, 1, label)
        if single:
            s.set(r, 2, formula, style)
        else:
            for y in range(3):
                c = col_letter(2 + y)
                s.set(r, 2 + y, formula.format(c=c, **fill), style)
    s.set(24, 1, "One-off cost", "header")
    s.set(24, 2, f"={R['one_off_cost']}", "eur")
    s.set(25, 1, "NPV, capacity view", "header")
    s.set(25, 2, f"=-B24+NPV({R['discount_rate']},B21:D21)", "bold_eur")
    s.set(26, 1, "NPV, cash view", "header")
    s.set(26, 2, f"=-B24+NPV({R['discount_rate']},B22:D22)", "bold_eur")
    s.set(27, 1, "3-year ROI, cash view")
    s.set(27, 2, "=(SUM(B22:D22)-B24)/B24", "pct")
    s.set(29, 1, f"Reference values from the Python model: NPV cash {eur(bc['base']['cash']['npv'])}, "
                 f"NPV capacity {eur(bc['base']['capacity']['npv'])}. With the base inputs Excel shows the same, give or take rounding.")
    return workbook_bytes([inputs, s])


# ------------------------------------------------------------- site data ----

def pilot_demo():
    from evals.run import load as load_set, score_document
    from freightdoc.pipeline import process
    from freightdoc.validate import CROSS_DOC, RULES
    docs, truth = load_set("test")
    results = process(docs)
    text = {d["id"]: d["text"] for d in docs}
    out = []
    for r in sorted(results, key=lambda x: x.id):
        s = score_document(r, truth)
        d = r.as_dict()
        t = truth[r.id]
        for name, f in d["fields"].items():
            f["truth"] = t["fields"].get(name)
            f["correct"] = name in s["correct"]
        out.append({
            "id": r.id, "received": r.received, "text": text[r.id], "type": r.doc_type,
            "truth_type": t["type"], "route": r.route, "reasons": r.reasons, "fields": d["fields"],
            "checks": d["checks"], "tms_record": d["tms_record"], "clean": s["clean"],
            "exceptions": t["exceptions"], "noise": t["noise"],
            "min_conf": min((f.confidence for f in r.fields.values()), default=1.0),
            "rule_fail_single": any(not c.ok for c in r.checks if c.rule not in CROSS_DOC),
            "rule_fail_cross": any(not c.ok for c in r.checks if c.rule in CROSS_DOC),
            "missing_truth": s["missing"], "wrong": s["wrong"],
        })
    return {"documents": out, "rules": RULES}


def site_data(m):
    bc = m["bc"]
    model = {
        "client": m["client"],
        "readiness": {k: m["readiness"][k] for k in ("dimensions", "overall", "level", "target_overall", "gaps", "scale", "raw")},
        "portfolio": m["portfolio"],
        "business_case": {"assumptions": m["bc_model"]["assumptions"], "values": bc["values"],
                          "base": bc["base"], "scenarios": bc["scenarios"], "tornado": bc["tornado"],
                          "labels": m["bc_label"], "noattr": bc["cash_if_all_leavers_replaced"],
                          "doc_desk_fte": m["client"]["doc_desk_fte"]},
        "roadmap": m["roadmap"], "risks": m["risks"], "raci": m["raci"], "stakeholders": m["stakeholders"],
        "pilot": {k: m["report"][k] for k in ("test", "test_ablation", "sweep_dev", "chosen_threshold",
                                              "thresholds", "gate", "pooled_escape_rate", "test_noise")},
    }
    return {
        "site/data/model.json": json.dumps(model, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        "site/data/pilot.json": json.dumps(pilot_demo(), ensure_ascii=False, sort_keys=True) + "\n",
    }


# ----------------------------------------------------------------- write ----

def text_files():
    for path in sorted(ROOT.rglob("*")):
        if path.suffix not in (".md", ".html") or not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        yield path


def render(text, nums, tabs, where):
    def num(mt):
        key = mt.group(1)
        if key not in nums:
            raise KeyError(f"{where}: unknown number key '{key}'")
        return f"<!--n:{key}-->{nums[key]}<!--/n-->"

    def tab(mt):
        key = mt.group(2)
        if key not in tabs:
            raise KeyError(f"{where}: unknown table '{key}'")
        return f"{mt.group(1)}\n{tabs[key]}\n{mt.group(4)}"

    return TABLE.sub(tab, NUMBER.sub(num, text))


def outputs():
    m = compute()
    m["bc_label"] = {a["key"]: a["name"] for a in m["bc_model"]["assumptions"]}
    nums, tabs = numbers(m), tables(m)
    files = {}
    for path in text_files():
        old = path.read_text(encoding="utf-8")
        files[str(path.relative_to(ROOT))] = render(old, nums, tabs, path.relative_to(ROOT))
    files.update(site_data(m))
    files["02-ai-readiness/readiness-scorecard.xlsx"] = readiness_workbook(m)
    files["03-opportunity-discovery/use-case-scoring.xlsx"] = scoring_workbook(m)
    files["04-business-case/roi-calculator.xlsx"] = roi_workbook(m)
    rd, bc, r = m["readiness"], m["bc"], m["report"]
    files["02-ai-readiness/readiness-radar.svg"] = charts.radar(rd["dimensions"], rd["overall"], rd["target_overall"])
    files["03-opportunity-discovery/impact-feasibility-matrix.svg"] = charts.matrix(m["portfolio"]["ranking"])
    files["04-business-case/tornado.svg"] = charts.tornado(bc["tornado"]["rows"], bc["tornado"]["base"], m["bc_label"])
    files["05-transformation-roadmap/roadmap.svg"] = charts.roadmap(m["roadmap"])
    files["06-applied-ai/ablation.svg"] = charts.ablation(list(r["test_ablation"].values()))
    files["06-applied-ai/threshold-sweep.svg"] = charts.sweep(r["sweep_dev"], r["chosen_threshold"],
                                                               r["thresholds"]["min_threshold"],
                                                               r["thresholds"]["error_budget"])
    for src in ("02-ai-readiness/readiness-radar.svg", "03-opportunity-discovery/impact-feasibility-matrix.svg",
                "04-business-case/tornado.svg", "05-transformation-roadmap/roadmap.svg",
                "06-applied-ai/ablation.svg", "06-applied-ai/threshold-sweep.svg"):
        files["site/media/" + src.split("/")[1]] = files[src]  # the site deploys site/ only
    files["01-discovery/current-state.bpmn"] = bpmn.as_is()
    files["01-discovery/future-state.bpmn"] = bpmn.to_be()
    files["site/data/numbers.json"] = json.dumps(nums, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    return files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = []
    for rel, content in outputs().items():
        path = ROOT / rel
        data = content if isinstance(content, bytes) else content.encode("utf-8")
        if path.exists() and path.read_bytes() == data:
            continue
        if args.check:
            stale.append(rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            print("wrote", rel)
    if stale:
        print("Out of date (run python scripts/build.py):", *stale, sep="\n  ")
        return 1
    if args.check:
        print("all generated content is up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
