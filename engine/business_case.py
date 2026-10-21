"""Business case for UC-01, freight document intelligence.

Two views, because freed hours are not saved euros:
  capacity view  every freed clerk hour valued at its loaded cost
  cash view      only what leaves the cost base: hires avoided because volume
                 grows and leavers are not replaced, capped at the hours freed

The board decides on the cash view; the capacity view shows the room the doc
desk gets for customs files and exceptions.
"""

GOOD_WHEN_HIGH = {"documents_per_month", "volume_growth", "manual_minutes", "stp_rate",
                  "hourly_cost", "human_error_rate", "error_cost", "ramp_year1", "attrition_fte"}


def _lookup(report, path):
    node = report
    for part in path.split("."):
        node = node[int(part)] if isinstance(node, list) else node[part]
    return node


def resolve(model, report):
    """-> {key: {"base", "low", "high"}} with pilot values filled in from the report."""
    values = {}
    for a in model["assumptions"]:
        row = {}
        for side in ("base", "low", "high"):
            v = a[side]
            row[side] = _lookup(report, v[len("pilot:"):]) if isinstance(v, str) else v
        values[a["key"]] = row
    return values


def pick(values, side="base", **overrides):
    out = {k: v[side] for k, v in values.items()}
    out.update(overrides)
    return out


def scenario(values, kind):
    """Pessimistic: every driver on its bad side; optimistic: every driver on its good side."""
    out = {}
    for key, v in values.items():
        good = v["high"] if key in GOOD_WHEN_HIGH else v["low"]
        bad = v["low"] if key in GOOD_WHEN_HIGH else v["high"]
        out[key] = {"base": v["base"], "pessimistic": bad, "optimistic": good}[kind]
    return out


def compute(v, horizon=3, doc_desk_fte=11):
    review_rate = max(0.0, 1 - v["stp_rate"] - v["manual_rate"])
    minutes_after = (v["stp_rate"] * v["stp_minutes"] + review_rate * v["review_minutes"]
                     + v["manual_rate"] * v["manual_minutes"])
    saved_minutes = v["manual_minutes"] - minutes_after
    error_after = (v["pilot_escape_rate"] + review_rate * v["human_error_rate"] * v["review_error_factor"]
                   + v["manual_rate"] * v["human_error_rate"])
    model_cost_per_doc = ((v["tokens_in"] * v["price_in_usd_per_mtok"]
                           + v["tokens_out"] * v["price_out_usd_per_mtok"]) / 1e6 * v["eur_per_usd"])
    years = []
    for t in range(1, horizon + 1):
        volume = v["documents_per_month"] * 12 * (1 + v["volume_growth"]) ** (t - 1)
        ramp = v["ramp_year1"] if t == 1 else 1.0
        hours = volume * saved_minutes / 60 * ramp
        fte_freed = hours / v["fte_hours"]
        hires_avoided = doc_desk_fte * ((1 + v["volume_growth"]) ** t - 1) + v["attrition_fte"] * t
        cash_fte = min(fte_freed, hires_avoided)
        errors_avoided = volume * (v["human_error_rate"] - error_after) * ramp
        error_value = errors_avoided * v["error_cost"]
        model_cost = volume * model_cost_per_doc
        run = v["run_cost"] + model_cost
        years.append({
            "year": t, "documents": round(volume), "hours_freed": round(hours),
            "fte_freed": round(fte_freed, 2), "cash_fte": round(cash_fte, 2),
            "errors_avoided": round(errors_avoided),
            "capacity_value": round(hours * v["hourly_cost"]),
            "cash_labour_value": round(cash_fte * v["fte_cost"]),
            "error_value": round(error_value), "model_cost": round(model_cost),
            "run_cost": round(run),
        })
    out = {
        "review_rate": round(review_rate, 4),
        "minutes_after": round(minutes_after, 3),
        "saved_minutes_per_document": round(saved_minutes, 3),
        "error_rate_after": round(error_after, 4),
        "model_cost_per_document_eur": round(model_cost_per_doc, 4),
        "one_off": v["one_off_cost"],
        "years": years,
    }
    for view, labour in (("capacity", "capacity_value"), ("cash", "cash_labour_value")):
        nets = [y[labour] + y["error_value"] - y["run_cost"] for y in years]
        npv = -v["one_off_cost"] + sum(n / (1 + v["discount_rate"]) ** (i + 1) for i, n in enumerate(nets))
        out[view] = {
            "net_per_year": nets,
            "npv": round(npv),
            "roi": round((sum(nets) - v["one_off_cost"]) / v["one_off_cost"], 3),
            "payback_months": payback_months(nets, v["one_off_cost"]),
        }
    return out


def payback_months(nets, one_off):
    """Months until the cumulative net covers the one-off cost (None if not within horizon)."""
    cumulative = 0.0
    for i, net in enumerate(nets):
        monthly = net / 12
        if monthly <= 0:
            continue
        if cumulative + net >= one_off:
            return round(i * 12 + (one_off - cumulative) / monthly, 1)
        cumulative += net
    return None


def tornado(values, drivers, view="cash"):
    base = compute(pick(values))[view]["npv"]
    rows = []
    for key in drivers:
        low = compute(pick(values, **{key: values[key]["low"]}))[view]["npv"]
        high = compute(pick(values, **{key: values[key]["high"]}))[view]["npv"]
        rows.append({"key": key, "low": low, "high": high, "swing": abs(high - low)})
    rows.sort(key=lambda r: -r["swing"])
    return {"base": base, "rows": rows}


def run(model, report, doc_desk_fte=11):
    values = resolve(model, report)
    result = {
        "values": values,
        "base": compute(pick(values), model["horizon_years"], doc_desk_fte),
        "scenarios": {k: compute(scenario(values, k), model["horizon_years"], doc_desk_fte)
                      for k in ("pessimistic", "optimistic")},
        # The cash case rests on a people decision more than on model accuracy,
        # so show what happens when every leaver is replaced after all.
        "cash_if_all_leavers_replaced": compute(pick(values, attrition_fte=0.0),
                                                model["horizon_years"], doc_desk_fte)["cash"],
        "tornado": tornado(values, model["tornado_drivers"]),
    }
    y2 = result["base"]["years"][1]
    result["steady_state_value"] = y2["capacity_value"] + y2["error_value"]
    return result
