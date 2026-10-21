"""Static SVG charts for the Markdown deliverables (GitHub renders them inline).

The interactive versions live on the site; these are the print-and-slide
versions. Colours follow one palette (light and dark), text uses text inks,
never the series colour. Each chart answers one question in its title.
"""

from xml.sax.saxutils import escape

STYLE = """<style>
.bg{fill:#fcfcfb}.ink{fill:#0b0b0b}.ink2{fill:#52514e}.grid{stroke:#e4e3df}.axis{stroke:#a3a29c}
.s1{fill:#2a78d6;stroke:#2a78d6}.s2{fill:#eb6834;stroke:#eb6834}.s3{fill:#1baf7a;stroke:#1baf7a}
.s4{fill:#eda100;stroke:#eda100}.s5{fill:#e87ba4;stroke:#e87ba4}.muted{fill:#a3a29c;stroke:#a3a29c}
text{font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
@media (prefers-color-scheme: dark){.bg{fill:#1a1a19}.ink{fill:#f0efec}.ink2{fill:#c3c2b7}
.grid{stroke:#383835}.axis{stroke:#6b6a64}.s1{fill:#3987e5;stroke:#3987e5}.s2{fill:#d95926;stroke:#d95926}
.s3{fill:#199e70;stroke:#199e70}.s4{fill:#c98500;stroke:#c98500}.s5{fill:#d55181;stroke:#d55181}
.muted{fill:#6b6a64;stroke:#6b6a64}}
</style>"""


def _svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{escape(title)}">{STYLE}<rect class="bg" width="{w}" height="{h}" rx="8"/>'
            f'<text class="ink" x="24" y="34" font-size="17" font-weight="600">{escape(title)}</text>'
            + body + "</svg>\n")


def _t(x, y, s, cls="ink2", size=12, anchor="start", weight="400"):
    return (f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" '
            f'font-weight="{weight}">{escape(str(s))}</text>')


def radar(dimensions, overall, target):
    import math
    w, h, cx, cy, rmax = 640, 500, 320, 290, 160
    n = len(dimensions)
    body = []
    for level in range(1, 6):
        pts = []
        for i in range(n):
            a = -math.pi / 2 + 2 * math.pi * i / n
            pts.append(f"{cx + rmax * level / 5 * math.cos(a):.1f},{cy + rmax * level / 5 * math.sin(a):.1f}")
        body.append(f'<polygon points="{" ".join(pts)}" class="grid" fill="none" stroke-width="1"/>')
        body.append(_t(cx + 4, cy - rmax * level / 5 - 3, level, size=10))
    for key, cls, dash in (("target", "s2", ' stroke-dasharray="6 4"'), ("current", "s1", "")):
        pts = []
        for i, d in enumerate(dimensions):
            a = -math.pi / 2 + 2 * math.pi * i / n
            pts.append((cx + rmax * d[key] / 5 * math.cos(a), cy + rmax * d[key] / 5 * math.sin(a)))
        body.append(f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" class="{cls}" '
                    f'fill-opacity="{0.18 if key == "current" else 0.0}" stroke-width="2"{dash}/>')
        for x, y in pts:
            body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" class="{cls}"/>')
    for i, d in enumerate(dimensions):
        a = -math.pi / 2 + 2 * math.pi * i / n
        x, y = cx + (rmax + 26) * math.cos(a), cy + (rmax + 26) * math.sin(a)
        anchor = "middle" if abs(math.cos(a)) < 0.3 else ("start" if math.cos(a) > 0 else "end")
        body.append(_t(x, y, d["name"], "ink", 12, anchor, "600"))
        body.append(_t(x, y + 15, f"{d['current']:.1f} → {d['target']:.1f}", "ink2", 11, anchor))
    body.append(f'<line x1="24" y1="56" x2="44" y2="56" class="s1" stroke-width="3"/>' + _t(50, 60, f"Today (overall {overall:.1f})"))
    body.append(f'<line x1="220" y1="56" x2="240" y2="56" class="s2" stroke-width="3" stroke-dasharray="6 4"/>' + _t(246, 60, f"Target in 12 months (overall {target:.1f})"))
    return _svg(w, h, "".join(body), "AI readiness today and in 12 months (1-5)")


def matrix(ranking):
    w, h = 760, 540
    x0, y0, pw, ph = 80, 70, 620, 400

    def px(v):
        return x0 + (v - 1) / 4 * pw

    def py(v):
        return y0 + ph - (v - 1) / 4 * ph

    body = [f'<rect x="{px(3):.1f}" y="{y0}" width="{px(5) - px(3):.1f}" height="{py(3) - y0:.1f}" class="s1" fill-opacity="0.06" stroke="none"/>']
    for v in (1, 2, 3, 4, 5):
        body.append(f'<line x1="{px(v):.1f}" y1="{y0}" x2="{px(v):.1f}" y2="{y0 + ph}" class="grid"/>')
        body.append(f'<line x1="{x0}" y1="{py(v):.1f}" x2="{x0 + pw}" y2="{py(v):.1f}" class="grid"/>')
        body.append(_t(px(v), y0 + ph + 18, v, anchor="middle", size=11))
        body.append(_t(x0 - 10, py(v) + 4, v, anchor="end", size=11))
    body.append(_t(x0 + pw / 2, h - 22, "Feasibility (data, simplicity, integration, change)", "ink", 12, "middle", "600"))
    body.append(f'<text class="ink" font-size="12" font-weight="600" transform="translate(28 {y0 + ph / 2}) rotate(-90)" text-anchor="middle">Value (money and strategic fit)</text>')
    body.append(_t(px(5) - 6, y0 + 16, "Do now", "ink2", 11, "end", "600"))
    body.append(_t(px(1) + 6, y0 + 16, "Prepare (strategic bet)", "ink2", 11, "start", "600"))
    body.append(_t(px(5) - 6, y0 + ph - 8, "Fill-in", "ink2", 11, "end", "600"))
    body.append(_t(px(1) + 6, y0 + ph - 8, "Deprioritise", "ink2", 11, "start", "600"))
    short = {"UC-02": "E-mail triage and drafts", "UC-05": "ETA prediction", "UC-06": "Warehouse forecasting",
             "UC-08": "Driver and picker monitoring", "UC-04": "Knowledge assistant", "UC-03": "Customs classification",
             "UC-07": "Route and load optimisation", "UC-10": "Quote and tender assistant"}
    # label placement: (dx, dy, anchor) per use case, set by eye to avoid collisions
    place = {"UC-05": (-14, -10, "end"), "UC-06": (-12, 18, "end"), "UC-04": (0, 24, "middle"),
             "UC-09": (12, 4, "start"), "UC-10": (12, -2, "start")}
    for r in ranking:
        x, y = px(r["feasibility"]), py(r["value"])
        radius = 6 + 6 * (r["risk"] - 1) / 4
        cls = "muted" if r["parked"] else "s1"
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" class="{cls}" fill-opacity="0.85" stroke="#fcfcfb" stroke-width="2"/>')
        dx, dy, anchor = place.get(r["id"], (radius + 6, 4, "start"))
        label = f"{r['id']} {short.get(r['id'], r['name'])}" + (" (parked)" if r["parked"] else "")
        body.append(_t(x + dx, y + dy, label, "ink", 11, anchor))
    body.append(_t(24, 56, "Bubble size: risk score (bigger = lower risk). Grey: parked, high-risk under the EU AI Act.", size=11))
    return _svg(w, h, "".join(body), "Impact-feasibility matrix: ten use cases")


def tornado(rows, base, labels):
    w = 760
    rh, top = 30, 84
    h = top + rh * len(rows) + 64
    lo = min(min(r["low"], r["high"]) for r in rows + [{"low": base, "high": base}])
    hi = max(max(r["low"], r["high"]) for r in rows + [{"low": base, "high": base}])
    pad = (hi - lo) * 0.08
    lo, hi = lo - pad, hi + pad
    x0, pw = 350, 380

    def px(v):
        return x0 + (v - lo) / (hi - lo) * pw

    body = [f'<line x1="{px(base):.1f}" y1="{top - 6}" x2="{px(base):.1f}" y2="{top + rh * len(rows)}" class="axis" stroke-width="1.5"/>',
            _t(px(base), h - 12, f"Base NPV €{base / 1000:,.0f}k", "ink", 11, "middle", "600")]
    for i, r in enumerate(rows):
        y = top + i * rh
        body.append(_t(x0 - 10, y + 19, labels[r["key"]][:54], "ink", 11, "end"))
        for value, cls in ((r["low"], "s2"), (r["high"], "s1")):
            a, b = sorted((px(base), px(value)))
            if b - a < 1:
                continue
            body.append(f'<rect x="{a:.1f}" y="{y + 6}" width="{b - a:.1f}" height="{rh - 12}" rx="3" class="{cls}"/>')
    body.append('<rect x="24" y="52" width="14" height="10" rx="2" class="s2"/>' + _t(44, 61, "Driver at its low value"))
    body.append('<rect x="200" y="52" width="14" height="10" rx="2" class="s1"/>' + _t(220, 61, "Driver at its high value"))
    for v in range(int(lo // 50000 + 1) * 50000, int(hi), 50000):
        body.append(_t(px(v), h - 32, f"€{v / 1000:,.0f}k", size=10, anchor="middle"))
    return _svg(w, h, "".join(body), "What moves the 3-year NPV (cash view) most")


def roadmap(rm):
    streams = rm["streams"]
    cls = {s["id"]: f"s{i + 1}" for i, s in enumerate(streams)}
    w, top, rh = 1060, 90, 20
    h = top + rh * len(rm["items"]) + 70
    x0, pw = 400, 630

    def px(week):
        return x0 + (week - 1) / 52 * pw

    body = []
    for q in range(5):
        x = px(1 + q * 13)
        body.append(f'<line x1="{x:.1f}" y1="{top - 14}" x2="{x:.1f}" y2="{h - 50}" class="grid"/>')
        if q < 4:
            body.append(_t(x + 4, top - 18, f"Q{q + 1}", "ink2", 11, weight="600"))
    for g in rm["gates"]:
        x = px(g["week"] + 0.5)
        body.append(f'<line x1="{x:.1f}" y1="{top - 6}" x2="{x:.1f}" y2="{h - 50}" class="axis" stroke-dasharray="3 3"/>')
        body.append(_t(x, h - 34, g["id"], "ink", 11, "middle", "600"))
        body.append(_t(x, h - 20, f"wk {g['week']}", "ink2", 10, "middle"))
    for i, item in enumerate(rm["items"]):
        y = top + i * rh
        body.append(_t(x0 - 8, y + 14, f"{item['id']} {item['title']}"[:66], "ink", 10.5, "end"))
        x, x2 = px(item["start"]), px(item["end"] + 1)
        body.append(f'<rect x="{x:.1f}" y="{y + 4}" width="{max(4, x2 - x - 2):.1f}" height="{rh - 8}" rx="3" class="{cls[item["stream"]]}"/>')
    lx = 24
    for s in streams:
        body.append(f'<rect x="{lx}" y="50" width="12" height="10" rx="2" class="{cls[s["id"]]}"/>' + _t(lx + 17, 59, s["name"], size=11))
        lx += 22 + 7 * len(s["name"])
    return _svg(w, h, "".join(body), "12-month roadmap: five streams, five gates")


def ablation(rows):
    w, h = 720, 330
    x0, top, bw, gap = 70, 80, 110, 40
    maxv = max(r["escapes"] for r in rows) or 1
    ph = 180
    body = [f'<line x1="{x0}" y1="{top + ph}" x2="{x0 + 4 * (bw + gap)}" y2="{top + ph}" class="axis"/>']
    for i, r in enumerate(rows):
        x = x0 + 20 + i * (bw + gap)
        bh = ph * r["escapes"] / maxv
        body.append(f'<rect x="{x}" y="{top + ph - bh:.1f}" width="{bw}" height="{max(bh, 1.5):.1f}" rx="4" class="s1"/>')
        body.append(_t(x + bw / 2, top + ph - bh - 8, f"{r['escapes']} escapes", "ink", 12, "middle", "600"))
        body.append(_t(x + bw / 2, top + ph + 20, r["policy"].split(":")[0], "ink", 12, "middle", "600"))
        body.append(_t(x + bw / 2, top + ph + 36, r["policy"].split(": ")[1][:22], "ink2", 10.5, "middle"))
        body.append(_t(x + bw / 2, top + ph + 52, f"{100 * r['stp_rate']:.0f}% straight-through", "ink2", 10.5, "middle"))
    body.append(_t(24, 58, "Test set, 220 documents. An escape is a document that reached the TMS with an error nobody was asked to check.", size=11))
    return _svg(w, h, "".join(body), "Each safety layer removes errors that would reach the TMS")


def sweep(rows, chosen, floor, budget):
    w, h = 720, 300
    x0, top, pw, ph = 70, 70, 280, 160
    body = []
    panels = (("Straight-through rate", "stp_rate", 0, 1.0, "s1", 0), ("Error escape rate", "error_escape_rate", 0, 0.03, "s2", 340))
    for title, key, lo, hi, cls, dx in panels:
        ox = x0 + dx
        body.append(_t(ox, top - 10, title, "ink", 12, weight="600"))
        for frac in (0, 0.5, 1):
            y = top + ph - frac * ph
            body.append(f'<line x1="{ox}" y1="{y:.1f}" x2="{ox + pw}" y2="{y:.1f}" class="grid"/>')
            body.append(_t(ox - 6, y + 4, f"{100 * (lo + frac * (hi - lo)):.1f}%".replace(".0%", "%"), size=10, anchor="end"))

        def px(t):
            return ox + (t - 0.5) / 0.45 * pw

        def py(v):
            return top + ph - (v - lo) / (hi - lo) * ph

        if key == "error_escape_rate":
            body.append(f'<line x1="{ox}" y1="{py(budget):.1f}" x2="{ox + pw}" y2="{py(budget):.1f}" class="axis" stroke-dasharray="4 3"/>')
            body.append(_t(ox + pw, py(budget) - 5, f"error budget {100 * budget:.0f}%", size=10, anchor="end"))
        x_floor = px(floor)
        body.append(f'<rect x="{ox}" y="{top}" width="{x_floor - ox:.1f}" height="{ph}" class="muted" fill-opacity="0.12" stroke="none"/>')
        pts = " ".join(f"{px(r['threshold']):.1f},{py(r[key]):.1f}" for r in rows)
        body.append(f'<polyline points="{pts}" class="{cls}" style="fill:none" stroke-width="2"/>')
        for r in rows:
            rad = 5 if r["threshold"] == chosen else 3
            body.append(f'<circle cx="{px(r["threshold"]):.1f}" cy="{py(r[key]):.1f}" r="{rad}" class="{cls}"/>')
        for t in (0.5, 0.75, 0.95):
            body.append(_t(px(t), top + ph + 16, f"{t:.2f}", size=10, anchor="middle"))
        body.append(_t(ox + pw / 2, top + ph + 32, "confidence threshold", size=10.5, anchor="middle"))
    body.append(_t(24, h - 18, f"Dev set. Shaded: below the floor of {floor:.2f} (fields read with an assumption would pass unseen). Chosen: {chosen:.2f}.", size=11))
    return _svg(w, h, "".join(body), "Choosing the threshold on the dev set")
