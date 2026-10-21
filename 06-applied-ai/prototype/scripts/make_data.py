"""Generate the synthetic document sets for the pilot.

Two sets with the same recipe and different seeds:
  data/dev   tune thresholds here
  data/test  report results here (never tuned on)

Each set holds documents.jsonl (what the pipeline sees: OCR text) and
truth.json (what a careful clerk would key in, plus the genuine exceptions a
person has to handle). Noise is injected on purpose, with the kinds of faults
the Wendelkaai doc desk sees: OCR look-alikes, unreadable fields, US date
formats, missing units, shipper typos and documents that disagree.

    python scripts/make_data.py          # write both sets
    python scripts/make_data.py --check  # fail if files differ from the recipe
"""

import argparse
import datetime as dt
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from freightdoc.reference import LABELS, iso6346_check_digit  # noqa: E402

SETS = {"dev": 20260901, "test": 20260915}
SHIPMENTS = 40      # B/L + invoice + packing list each
CMRS = 60
DELIVERY_ORDERS = 30
OTHERS = 10
LBS = 0.45359237

COMPANIES = [
    ("Brugland Foods BV", "NL"), ("Nordhavn Steel AB", "SE"), ("Calderwick Paper Ltd", "GB"),
    ("Maison Vérane SAS", "FR"), ("Kestrel Pharma GmbH", "DE"), ("Oostveld Machinery NV", "BE"),
    ("Lanterra Ceramics SpA", "IT"), ("Haldor Timber Oy", "FI"), ("Wexmoor Retail Ltd", "GB"),
    ("Peloria Chemicals SA", "ES"), ("Thistlebank Distillers Ltd", "GB"),
    ("Riverside Agri Inc", "US"), ("Bayline Industrial LLC", "US"),
    ("Sundra Textiles Pvt Ltd", "IN"), ("Huaxin Components Co Ltd", "CN"),
    ("Vlaskamp Bakeries NV", "BE"), ("Grevenor Plastics GmbH", "DE"),
]
VESSELS = ["MV Noordster", "Celtic Mariner", "Baltic Wren", "Hollandia Bay", "Atlantic Merel",
           "Wielingen Express", "Scaldis Trader", "North Sea Kestrel"]
OWNERS = ["WKL", "NSX", "BRT", "HLD", "OST", "CMV", "TGH"]
CARRIERS = ["NSLU", "BWAL", "CMVE", "OSTL"]
PORTS_EU = ["BEZEE"]
PORTS_FAR = ["GBFXT", "GBTIL", "GBPME", "IEDUB", "IEORK", "ESBIO", "PTLIS", "SEGOT", "FIHEL",
             "USBAL", "USSAV", "CNSHA", "CNNGB", "SGSIN", "INNSA", "MAPTM"]
PLACES = ["Zeebrugge, BE", "Brugge, BE", "Gent, BE", "Lille, FR", "Roubaix, FR", "Venlo, NL",
          "Tilburg, NL", "Duisburg, DE", "Köln, DE", "Poznań, PL", "Lyon, FR", "Liège, BE"]
TERMINALS = ["Zeebrugge Terminal A", "Zeebrugge Terminal B", "Zeebrugge Ro-Ro Quay 2"]
CURRENCY_BY_COUNTRY = {"US": "USD", "GB": "GBP", "SE": "SEK", "CN": "USD", "IN": "USD"}
INCOTERMS = ["FOB", "CIF", "CFR", "FCA", "DAP", "EXW", "DDP"]
LANGS = ["en", "en", "nl", "fr", "de"]
TITLE_BY_LANG = {
    "bill_of_lading": {"en": "BILL OF LADING", "nl": "CONNAISSEMENT / COGNOSSEMENT",
                       "fr": "CONNAISSEMENT", "de": "KONNOSSEMENT"},
    "cmr": {"en": "CMR CONSIGNMENT NOTE", "nl": "CMR — INTERNATIONALE VRACHTBRIEF",
            "fr": "CMR — LETTRE DE VOITURE INTERNATIONALE", "de": "CMR-FRACHTBRIEF"},
    "commercial_invoice": {"en": "COMMERCIAL INVOICE", "nl": "HANDELSFACTUUR",
                           "fr": "FACTURE COMMERCIALE", "de": "HANDELSRECHNUNG"},
    "packing_list": {"en": "PACKING LIST", "nl": "PAKLIJST", "fr": "LISTE DE COLISAGE",
                     "de": "PACKLISTE"},
    "delivery_order": {"en": "DELIVERY ORDER", "nl": "VRIJGAVE / DELIVERY ORDER",
                       "fr": "BON DE LIVRAISON", "de": "FREISTELLUNG"},
}
LANG_INDEX = {"en": 0, "nl": 1, "fr": 2, "de": 3}
OCR_LOOKALIKE = {"0": "O", "1": "I", "5": "S", "8": "B"}
SILENT_DIGIT = {"3": "8", "8": "3", "1": "7", "7": "1", "6": "8", "5": "6", "4": "9"}
OTHER_DOCS = [
    "ARRIVAL NOTICE\nVessel: {vessel}\nETA Zeebrugge: {date}\nPlease arrange customs clearance.\n"
    "Containers will be available after discharge.",
    "PORT NEWSLETTER\nZeebrugge container volumes rose this quarter.\nNew rail shuttle to Duisburg.",
    "MEETING INVITE\nSubject: quarterly service review\nDate: {date}\nLocation: Brugge office",
    "PROOF OF DELIVERY\nDelivered in good order. Signature: [illegible]\nPhoto attached.",
    "RATE REQUEST\nCould you quote 2x40HC Zeebrugge to Dublin, weekly, from next month?",
]


class Doc:
    def __init__(self, doc_id, doc_type, lang, received):
        self.id = doc_id
        self.type = doc_type
        self.lang = lang
        self.received = received
        self.lines = []           # (field or None, label, value text)
        self.fields = {}          # truth
        self.exceptions = []
        self.noise = []
        self.shipment = None


def container_number(rng):
    owner = rng.choice(OWNERS) + "U"
    serial = "".join(rng.choice("0123456789") for _ in range(6))
    return owner + serial + str(iso6346_check_digit(owner + serial))


def label_for(rng, field, lang):
    options = LABELS[field]
    if lang in LANG_INDEX and LANG_INDEX[lang] < len(options) and rng.random() < 0.7:
        return options[LANG_INDEX[lang]]
    return rng.choice(options)


def fmt_date(rng, date, us):
    if us:
        return date.strftime("%m/%d/%Y")
    return date.strftime(rng.choice(["%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d", "%d %b %Y"]))


def fmt_weight(rng, kg, us):
    if us:
        lbs = round(kg / LBS)
        return f"{lbs:,} lbs", round(lbs * LBS, 1)
    style = rng.choice(["eu", "en", "plain"])
    if style == "eu":
        whole, dec = f"{kg:.1f}".split(".")
        text = f"{int(whole):,}".replace(",", ".") + ("," + dec if dec != "0" else "") + " kg"
    elif style == "en":
        text = f"{kg:,.1f} KG"
    else:
        text = f"{kg:.1f} kg"
    return text, kg


def fmt_amount(rng, amount, us):
    if us or rng.random() < 0.5:
        return f"{amount:,.2f}"
    whole, dec = f"{amount:.2f}".split(".")
    return f"{int(whole):,}".replace(",", ".") + "," + dec


def add(doc, rng, field, value_text, truth):
    doc.lines.append((field, label_for(rng, field, doc.lang), value_text))
    doc.fields[field] = truth


def make_bl(rng, doc, shipment):
    doc.shipment = shipment["id"]
    us = shipment["us"]
    add(doc, rng, "bl_number", shipment["bl"], shipment["bl"])
    add(doc, rng, "shipper", shipment["seller"], shipment["seller"])
    add(doc, rng, "consignee", shipment["buyer"], shipment["buyer"])
    add(doc, rng, "vessel", shipment["vessel"], shipment["vessel"])
    add(doc, rng, "port_of_loading", shipment["pol"], shipment["pol"])
    add(doc, rng, "port_of_discharge", shipment["pod"], shipment["pod"])
    add(doc, rng, "containers", ", ".join(shipment["containers"]), list(shipment["containers"]))
    add(doc, rng, "seal_numbers", ", ".join(shipment["seals"]), list(shipment["seals"]))
    add(doc, rng, "packages", f"{shipment['packages']} {rng.choice(['PKGS', 'pallets', 'colli'])}",
        shipment["packages"])
    text, kg = fmt_weight(rng, shipment["gross"], us)
    add(doc, rng, "gross_weight_kg", text, kg)
    add(doc, rng, "issue_date", fmt_date(rng, shipment["date"], us), shipment["date"].isoformat())


def make_invoice(rng, doc, shipment):
    doc.shipment = shipment["id"]
    us = shipment["us"]
    add(doc, rng, "invoice_number", shipment["invoice"], shipment["invoice"])
    add(doc, rng, "invoice_date", fmt_date(rng, shipment["date"], us), shipment["date"].isoformat())
    add(doc, rng, "seller", shipment["seller"], shipment["seller"])
    add(doc, rng, "buyer", shipment["buyer"], shipment["buyer"])
    add(doc, rng, "currency", shipment["currency"], shipment["currency"])
    add(doc, rng, "incoterm", f"{shipment['incoterm']} {rng.choice(['Zeebrugge', 'Incoterms 2020', ''])}".strip(),
        shipment["incoterm"])
    add(doc, rng, "hs_codes", ", ".join(shipment["hs"]), list(shipment["hs"]))
    lines = shipment["lines"]
    add(doc, rng, "line_amounts", " ; ".join(fmt_amount(rng, a, us) for a in lines), list(lines))
    total = round(sum(lines), 2)
    add(doc, rng, "total_amount", fmt_amount(rng, total, us), total)
    add(doc, rng, "packages", str(shipment["packages"]), shipment["packages"])
    if rng.random() < 0.6:
        add(doc, rng, "bl_reference", shipment["bl"], shipment["bl"])


def make_packing_list(rng, doc, shipment):
    doc.shipment = shipment["id"]
    us = shipment["us"]
    add(doc, rng, "reference", shipment["pl"], shipment["pl"])
    add(doc, rng, "containers", ", ".join(shipment["containers"]), list(shipment["containers"]))
    add(doc, rng, "packages", str(shipment["packages"]), shipment["packages"])
    text, kg = fmt_weight(rng, shipment["gross"], us)
    add(doc, rng, "gross_weight_kg", text, kg)
    text, kg = fmt_weight(rng, shipment["net"], us)
    add(doc, rng, "net_weight_kg", text, kg)
    if rng.random() < 0.7:
        add(doc, rng, "bl_reference", shipment["bl"], shipment["bl"])


def make_do(rng, doc, shipment):
    doc.shipment = shipment["id"]
    add(doc, rng, "do_number", "DO" + "".join(rng.choice("0123456789") for _ in range(7)), None)
    doc.fields["do_number"] = doc.lines[-1][2]
    add(doc, rng, "bl_reference", shipment["bl"], shipment["bl"])
    k = rng.randint(1, len(shipment["containers"]))
    picked = sorted(rng.sample(shipment["containers"], k))
    add(doc, rng, "containers", ", ".join(picked), picked)
    add(doc, rng, "terminal", rng.choice(TERMINALS), None)
    doc.fields["terminal"] = doc.lines[-1][2]
    until = doc.received + dt.timedelta(days=rng.randint(3, 10))
    add(doc, rng, "valid_until", fmt_date(rng, until, False), until.isoformat())
    pin = "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
    add(doc, rng, "pickup_reference", pin, pin)


def make_cmr(rng, doc):
    sender, s_country = rng.choice(COMPANIES[:11] + COMPANIES[15:])
    consignee, _ = rng.choice([c for c in COMPANIES if c[0] != sender])
    add(doc, rng, "cmr_number", "CMR" + "".join(rng.choice("0123456789") for _ in range(8)), None)
    doc.fields["cmr_number"] = doc.lines[-1][2]
    add(doc, rng, "sender", sender, sender)
    add(doc, rng, "consignee", consignee, consignee)
    a, b = rng.sample(PLACES, 2)
    add(doc, rng, "place_of_taking_over", a, a)
    add(doc, rng, "place_of_delivery", b, b)
    date = doc.received - dt.timedelta(days=rng.randint(0, 6))
    add(doc, rng, "date_of_taking_over", fmt_date(rng, date, False), date.isoformat())
    plate = rng.choice([
        lambda: f"1-{rng.choice('ABCDEFGHJKLMNPRSTVWXYZ')}{rng.choice('ABCDEFGHJKLMNPRSTVWXYZ')}{rng.choice('ABCDEFGHJKLMNPRSTVWXYZ')}-{rng.randint(100, 999)}",
        lambda: f"{rng.choice(['AB', 'GH', 'LM'])}-{rng.randint(100, 999)}-{rng.choice(['CD', 'XY', 'TR'])}",
        lambda: f"WZ {rng.randint(10000, 99999)}",
        lambda: f"DU-{rng.choice(['KR', 'AB'])} {rng.randint(1000, 9999)}",
    ])()
    add(doc, rng, "vehicle_plate", plate, plate)
    packages = rng.randint(4, 66)
    add(doc, rng, "packages", f"{packages} {rng.choice(['pallets', 'colli', 'PKGS'])}", packages)
    kg = round(rng.uniform(800, 24000), 1)
    text, kg = fmt_weight(rng, kg, False)
    add(doc, rng, "gross_weight_kg", text, kg)


def new_shipment(rng, i, received):
    seller, country = rng.choice(COMPANIES)
    buyer, _ = rng.choice([c for c in COMPANIES if c[1] in ("BE", "NL", "FR", "DE")
                           and c[0] != seller])
    us = country == "US"
    n_cont = rng.choice([1, 1, 1, 2, 2, 3])
    containers = [container_number(rng) for _ in range(n_cont)]
    gross = round(sum(rng.uniform(4000, 24000) for _ in containers), 1)
    lines = [round(rng.uniform(1500, 48000), 2) for _ in range(rng.randint(1, 4))]
    far = rng.choice(PORTS_FAR)
    inbound = rng.random() < 0.6
    return {
        "id": f"SHP-{i:03d}",
        "us": us,
        "seller": seller,
        "buyer": buyer,
        "bl": rng.choice(CARRIERS) + "".join(rng.choice("0123456789") for _ in range(8)),
        "invoice": f"INV-{rng.randint(2026000, 2026999)}",
        "pl": f"PL-{rng.randint(10000, 99999)}",
        "vessel": rng.choice(VESSELS),
        "pol": far if inbound else "BEZEE",
        "pod": "BEZEE" if inbound else far,
        "containers": containers,
        "seals": [f"{rng.choice(['SL', 'ML', ''])}{rng.randint(1000000, 9999999)}" for _ in containers],
        "packages": rng.randint(10, 1200),
        "gross": gross,
        "net": round(gross * rng.uniform(0.84, 0.95), 1),
        "date": received - dt.timedelta(days=rng.randint(1, 20)),
        "currency": CURRENCY_BY_COUNTRY.get(country, "EUR"),
        "incoterm": rng.choice(INCOTERMS),
        "hs": sorted({"".join(rng.choice("0123456789") for _ in range(rng.choice([6, 8, 8, 10])))
                      for _ in range(rng.randint(1, 3))}),
        "lines": lines,
    }


# ---------------------------------------------------------------- noise ----

def line_index(doc, field):
    for i, (f, _, _) in enumerate(doc.lines):
        if f == field:
            return i
    return None


def set_value(doc, i, value):
    f, label, _ = doc.lines[i]
    doc.lines[i] = (f, label, value)


def noise_ocr_container(rng, doc):
    i = line_index(doc, "containers")
    if i is None:
        return
    value = doc.lines[i][2]
    first = value.split(", ")[0]
    positions = [p for p in range(4, 10) if first[p] in OCR_LOOKALIKE]
    if not positions:
        return
    p = rng.choice(positions)
    bad = first[:p] + OCR_LOOKALIKE[first[p]] + first[p + 1:]
    set_value(doc, i, value.replace(first, bad, 1))
    doc.noise.append("ocr_container")


def noise_source_typo(rng, doc):
    """The shipper typed the container number wrong: the document itself is wrong."""
    i = line_index(doc, "containers")
    if i is None:
        return
    value = doc.lines[i][2]
    first = value.split(", ")[0]
    check = int(first[10])
    bad = first[:10] + str((check + rng.randint(1, 9)) % 10)
    set_value(doc, i, value.replace(first, bad, 1))
    doc.fields["containers"] = [bad if c == first else c for c in doc.fields["containers"]]
    doc.exceptions.append("container_check_digit")
    doc.noise.append("source_typo")


def noise_illegible(rng, doc):
    candidates = [k for k, (f, _, _) in enumerate(doc.lines)
                  if f in ("packages", "gross_weight_kg", "consignee", "vehicle_plate",
                           "total_amount", "valid_until", "seal_numbers")]
    if not candidates:
        return
    i = rng.choice(candidates)
    set_value(doc, i, rng.choice(["[illegible]", "###", "~~ smudged ~~"]))
    doc.noise.append("illegible")


def noise_silent_digit(rng, doc):
    """An OCR misread in a field with no checksum: the kind that slips through."""
    options = [f for f in ("packages", "gross_weight_kg") if line_index(doc, f) is not None]
    if not options:
        return
    field = rng.choice(options)
    i = line_index(doc, field)
    value = doc.lines[i][2]
    digits = [p for p, ch in enumerate(value) if ch in SILENT_DIGIT]
    if not digits:
        return
    p = digits[0] if field == "packages" else rng.choice(digits[:2])
    set_value(doc, i, value[:p] + SILENT_DIGIT[value[p]] + value[p + 1:])
    doc.noise.append("silent_digit")


def noise_no_unit(rng, doc):
    i = line_index(doc, "gross_weight_kg")
    if i is None:
        return
    value = doc.lines[i][2]
    for unit in (" lbs", " KG", " kg"):
        value = value.replace(unit, "")
    set_value(doc, i, value)
    doc.noise.append("no_unit")


def noise_label_ocr(rng, doc):
    k = rng.randrange(len(doc.lines))
    f, label, value = doc.lines[k]
    if len(label) < 6:
        return
    swaps = {"o": "0", "e": "c", "l": "1", "i": "l", "a": "o"}
    positions = [p for p, ch in enumerate(label) if ch in swaps]
    if not positions:
        return
    p = rng.choice(positions)
    doc.lines[k] = (f, label[:p] + swaps[label[p]] + label[p + 1:], value)
    doc.noise.append("label_ocr")


def noise_weight_mismatch(rng, doc):
    i = line_index(doc, "gross_weight_kg")
    if i is None:
        return
    kg = doc.fields["gross_weight_kg"]
    new = round(kg * rng.choice([0.9, 0.93, 1.06, 1.12]), 1)
    text, new = fmt_weight(rng, new, False)
    set_value(doc, i, text)
    doc.fields["gross_weight_kg"] = new
    net_i = line_index(doc, "net_weight_kg")
    if net_i is not None and doc.fields["net_weight_kg"] > new:
        net = round(new * 0.9, 1)
        text, net = fmt_weight(rng, net, False)
        set_value(doc, net_i, text)
        doc.fields["net_weight_kg"] = net
    doc.exceptions.append("weight_mismatch")
    doc.noise.append("weight_mismatch")


def noise_sum_mismatch(rng, doc):
    i = line_index(doc, "total_amount")
    if i is None:
        return
    total = round(doc.fields["total_amount"] + rng.choice([-100, 250, 1000, -0.5]), 2)
    set_value(doc, i, f"{total:,.2f}")
    doc.fields["total_amount"] = total
    doc.exceptions.append("invoice_total_mismatch")
    doc.noise.append("sum_mismatch")


def noise_missing_seal(rng, doc):
    i = line_index(doc, "seal_numbers")
    if i is None:
        return
    del doc.lines[i]
    del doc.fields["seal_numbers"]
    doc.exceptions.append("missing_required")
    doc.noise.append("missing_seal")


def render(rng, doc):
    title = TITLE_BY_LANG[doc.type][doc.lang]
    out = [title]
    if rng.random() < 0.4:
        out.append(rng.choice(["Original", "Copy non-negotiable", "Page 1/1", "Wendelkaai ref pending"]))
    sep = rng.choice([": ", " : ", ":  ", "  ", " ..... "])
    for _, label, value in doc.lines:
        pretty = label.upper() if rng.random() < 0.3 else label[:1].upper() + label[1:]
        out.append(f"{pretty}{sep}{value}")
    if rng.random() < 0.3:
        out.append(rng.choice(["Signature: ____________", "Stamp", "Terms overleaf apply."]))
    return "\n".join(out)


def generate(seed):
    rng = random.Random(seed)
    start = dt.date(2026, 9, 1)
    docs = []
    n = 0

    def new(doc_type, after=None):
        nonlocal n
        n += 1
        if after is None:
            received = start + dt.timedelta(days=rng.randint(0, 27))
        else:
            received = after + dt.timedelta(days=rng.randint(1, 6))
        return Doc(f"DOC-{n:04d}", doc_type, rng.choice(LANGS), received)

    shipments = [new_shipment(rng, i + 1, start + dt.timedelta(days=21)) for i in range(SHIPMENTS)]
    for shipment in shipments:
        for kind, maker in (("bill_of_lading", make_bl), ("commercial_invoice", make_invoice),
                            ("packing_list", make_packing_list)):
            doc = new(kind, after=shipment["date"])
            maker(rng, doc, shipment)
            docs.append(doc)
    for _ in range(DELIVERY_ORDERS):
        shipment = rng.choice(shipments)
        doc = new("delivery_order", after=shipment["date"])
        make_do(rng, doc, shipment)
        docs.append(doc)
    for _ in range(CMRS):
        doc = new("cmr")
        make_cmr(rng, doc)
        docs.append(doc)

    # Noise, per document, independent draws. Rates come from the 2-week
    # mailbox sample in discovery (01-discovery/interview-synthesis.md).
    for doc in docs:
        if rng.random() < 0.10:
            noise_ocr_container(rng, doc)
        if doc.type == "bill_of_lading" and rng.random() < 0.06:
            noise_source_typo(rng, doc)
        if rng.random() < 0.07:
            noise_illegible(rng, doc)
        if rng.random() < 0.04:
            noise_silent_digit(rng, doc)
        if rng.random() < 0.05:
            noise_no_unit(rng, doc)
        if rng.random() < 0.12:
            noise_label_ocr(rng, doc)
        if doc.type == "packing_list" and rng.random() < 0.08:
            noise_weight_mismatch(rng, doc)
        if doc.type == "commercial_invoice" and rng.random() < 0.06:
            noise_sum_mismatch(rng, doc)
        if doc.type == "bill_of_lading" and rng.random() < 0.05:
            noise_missing_seal(rng, doc)

    documents, truth = [], {}
    for doc in docs:
        documents.append({"id": doc.id, "received": doc.received.isoformat(),
                          "text": render(rng, doc)})
        truth[doc.id] = {"type": doc.type, "lang": doc.lang, "shipment": doc.shipment,
                         "fields": doc.fields, "exceptions": doc.exceptions, "noise": doc.noise}
    for _ in range(OTHERS):
        n += 1
        doc_id = f"DOC-{n:04d}"
        received = start + dt.timedelta(days=rng.randint(0, 27))
        text = rng.choice(OTHER_DOCS).format(vessel=rng.choice(VESSELS),
                                             date=received.strftime("%d/%m/%Y"))
        documents.append({"id": doc_id, "received": received.isoformat(), "text": text})
        truth[doc_id] = {"type": "other", "lang": "en", "shipment": None, "fields": {},
                         "exceptions": [], "noise": []}

    order = list(range(len(documents)))
    rng.shuffle(order)
    documents = [documents[i] for i in order]
    return documents, truth


def serialise(documents, truth):
    jsonl = "".join(json.dumps(d, ensure_ascii=False) + "\n" for d in documents)
    return jsonl, json.dumps(truth, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = []
    for name, seed in SETS.items():
        jsonl, truth = serialise(*generate(seed))
        folder = ROOT / "data" / name
        targets = {folder / "documents.jsonl": jsonl, folder / "truth.json": truth}
        for path, content in targets.items():
            if args.check:
                if not path.exists() or path.read_text(encoding="utf-8") != content:
                    stale.append(str(path.relative_to(ROOT)))
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
    if stale:
        print("Out of date (run python scripts/make_data.py):", *stale, sep="\n  ")
        return 1
    print("data is up to date" if args.check else "wrote data/dev and data/test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
