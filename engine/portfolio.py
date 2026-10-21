"""Score, gate and rank the use-case portfolio, and test how robust the ranking is.

A ranking that flips when someone nudges a weight is an opinion, not a
priority. `robustness` re-ranks the portfolio under 2,000 random weightings
(each top-level weight between 0.5x and 1.5x of the agreed weight) and counts
how often each use case stays in the top three.
"""

import random

QUADRANTS = {
    (True, True): "Do now",
    (True, False): "Prepare (strategic bet)",
    (False, True): "Fill-in",
    (False, False): "Deprioritise",
}


def value_score(eur, scale):
    return 1 + 4 * min(eur, scale) / scale


def score(uc, criteria, scale, weights=None):
    s = dict(uc["scores"])
    s["annual_value"] = value_score(uc["annual_value_eur"], scale)
    parts = {}
    for group, spec in criteria.items():
        parts[group] = sum(s[k] * w for k, w in spec["sub"].items())
    weights = weights or {g: spec["weight"] for g, spec in criteria.items()}
    total = sum(parts[g] * weights[g] for g in parts) / sum(weights.values())
    return parts, total


def rank(portfolio, weights=None):
    criteria, scale = portfolio["criteria"], portfolio["value_scale_eur"]
    rows = []
    for uc in portfolio["use_cases"]:
        parts, total = score(uc, criteria, scale, weights)
        parked = uc["scores"]["regulatory"] == 1
        rows.append({
            "id": uc["id"], "name": uc["name"], "annual_value_eur": uc["annual_value_eur"],
            "value": round(parts["value"], 2), "feasibility": round(parts["feasibility"], 2),
            "risk": round(parts["risk"], 2), "score": round(total, 3), "parked": parked,
            "quadrant": "Parked (high-risk)" if parked else
            QUADRANTS[(parts["value"] >= 3, parts["feasibility"] >= 3)],
            "ai_act": uc["ai_act"]["tier"], "depends_on": uc["depends_on"],
            "readiness_dependencies": uc["readiness_dependencies"],
        })
    ranked = sorted((r for r in rows if not r["parked"]), key=lambda r: -r["score"])
    for i, r in enumerate(ranked, 1):
        r["rank"] = i
    for r in rows:
        r.setdefault("rank", None)
    return sorted(rows, key=lambda r: (r["rank"] is None, r["rank"] or 0))


def robustness(portfolio, samples=2000, seed=42):
    base = {g: spec["weight"] for g, spec in portfolio["criteria"].items()}
    rng = random.Random(seed)
    top1, top3 = {}, {}
    for _ in range(samples):
        weights = {g: w * (0.5 + rng.random()) for g, w in base.items()}
        ranked = [r for r in rank(portfolio, weights) if r["rank"]]
        top1[ranked[0]["id"]] = top1.get(ranked[0]["id"], 0) + 1
        for r in ranked[:3]:
            top3[r["id"]] = top3.get(r["id"], 0) + 1
    ids = [uc["id"] for uc in portfolio["use_cases"]]
    return {i: {"top1": round(top1.get(i, 0) / samples, 3), "top3": round(top3.get(i, 0) / samples, 3)}
            for i in ids}


def run(portfolio, uc01_value):
    portfolio = {**portfolio, "use_cases": [
        {**uc, "annual_value_eur": uc01_value if uc["annual_value_eur"] == "business_case"
         else uc["annual_value_eur"]} for uc in portfolio["use_cases"]]}
    rows = rank(portfolio)
    robust = robustness(portfolio)
    for r in rows:
        r.update(robust[r["id"]])
    return {"criteria": portfolio["criteria"], "value_scale_eur": portfolio["value_scale_eur"],
            "ranking": rows, "use_cases": portfolio["use_cases"]}
