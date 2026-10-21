"""AI readiness: dimension scores, overall level and the gaps that matter first.

A gap matters first when it is large and the top use cases depend on it, so
the gap list is weighted by how many of the top-five use cases name the item.
"""

LEVELS = ["Exploring", "Experimenting", "Formalising", "Scaling", "Transforming"]


def level(score):
    """Nearest level: 1.9 reads as Experimenting, 2.4 still as Experimenting."""
    return LEVELS[min(4, max(0, int(score + 0.5) - 1))]


def run(readiness, ranking):
    dims = []
    for d in readiness["dimensions"]:
        current = sum(i["score"] for i in d["items"]) / len(d["items"])
        target = sum(i["target"] for i in d["items"]) / len(d["items"])
        dims.append({"id": d["id"], "name": d["name"], "current": round(current, 2),
                     "target": round(target, 2), "level": level(current)})
    overall = sum(d["current"] for d in dims) / len(dims)
    top5 = [r for r in ranking if r["rank"] and r["rank"] <= 5]
    gaps = []
    for d in readiness["dimensions"]:
        for item in d["items"]:
            needed_by = [r["id"] for r in top5 if item["id"] in r["readiness_dependencies"]]
            gap = item["target"] - item["score"]
            gaps.append({"id": item["id"], "dimension": d["name"], "question": item["question"],
                         "current": item["score"], "target": item["target"], "gap": gap,
                         "needed_by": needed_by, "priority": gap * (1 + len(needed_by)),
                         "evidence": item["evidence"]})
    gaps.sort(key=lambda g: (-g["priority"], g["id"]))
    return {"dimensions": dims, "overall": round(overall, 2), "level": level(overall),
            "target_overall": round(sum(d["target"] for d in dims) / len(dims), 2),
            "gaps": gaps, "scale": readiness["scale"], "raw": readiness["dimensions"]}
