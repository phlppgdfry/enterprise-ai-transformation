"""Business rules that check extracted data before it reaches the TMS.

Single-document rules (V01-V10, V14) need only the document itself. Cross-
document rules (V11-V13) compare documents of the same shipment, linked by
B/L number. The doc desk already waits for a complete set before keying a
shipment (01-discovery/interview-synthesis.md), so the pilot does the same.

Every rule returns a Check; a failed check sends the document to a person
with the rule's message as the reason.
"""

import datetime as dt
import re

from .reference import CURRENCIES, FIELDS, INCOTERMS, LOCODES, iso6346_valid

RULES = {
    "V01": "Container numbers pass the ISO 6346 check digit",
    "V02": "Ports are known UN/LOCODEs",
    "V03": "All required fields are present",
    "V04": "Dates are plausible for the day the document arrived",
    "V05": "Net weight does not exceed gross weight",
    "V06": "Gross weight per container is physically possible",
    "V07": "HS codes have 6, 8 or 10 digits",
    "V08": "Incoterm is a valid Incoterms 2020 rule",
    "V09": "Currency is one finance accepts",
    "V10": "Invoice lines add up to the invoice total",
    "V11": "Gross weight agrees between B/L and packing list (within 1%)",
    "V12": "Package count agrees across the shipment's documents",
    "V13": "Containers on packing list / delivery order appear on the B/L",
    "V14": "Vehicle registration looks like a registration",
}
CROSS_DOC = {"V11", "V12", "V13"}
MAX_GROSS_PER_CONTAINER_KG = 30000


class Check:
    __slots__ = ("rule", "ok", "message")

    def __init__(self, rule, ok, message=""):
        self.rule, self.ok, self.message = rule, ok, message

    def as_dict(self):
        return {"rule": self.rule, "ok": self.ok, "message": self.message}


def _v(fields, name):
    f = fields.get(name)
    return f.value if f is not None else None


def check_document(doc_type, fields, received):
    """Single-document rules. `fields` maps name -> Field."""
    checks = []
    if doc_type == "other":
        return checks
    missing = [n for n, (_, required) in FIELDS[doc_type].items()
               if required and _v(fields, n) in (None, [], "")]
    checks.append(Check("V03", not missing, "missing: " + ", ".join(missing) if missing else ""))

    containers = _v(fields, "containers")
    if containers:
        bad = [c for c in containers if not iso6346_valid(c)]
        checks.append(Check("V01", not bad, "check digit fails: " + ", ".join(bad) if bad else ""))

    for port in ("port_of_loading", "port_of_discharge"):
        code = _v(fields, port)
        if code:
            checks.append(Check("V02", code in LOCODES, f"unknown port {code}" if code not in LOCODES else ""))

    received_date = dt.date.fromisoformat(received)
    for name in ("issue_date", "invoice_date", "date_of_taking_over"):
        value = _v(fields, name)
        if value:
            delta = (dt.date.fromisoformat(value) - received_date).days
            ok = -120 <= delta <= 1
            checks.append(Check("V04", ok, f"{name} {value} is {delta:+d} days from arrival" if not ok else ""))
    until = _v(fields, "valid_until")
    if until:
        delta = (dt.date.fromisoformat(until) - received_date).days
        ok = 0 <= delta <= 30
        checks.append(Check("V04", ok, f"valid_until {until} is {delta:+d} days from arrival" if not ok else ""))

    gross, net = _v(fields, "gross_weight_kg"), _v(fields, "net_weight_kg")
    if gross is not None and net is not None:
        checks.append(Check("V05", net <= gross, f"net {net} kg > gross {gross} kg" if net > gross else ""))
    if gross is not None and containers:
        per = gross / len(containers)
        ok = 0 < per <= MAX_GROSS_PER_CONTAINER_KG
        checks.append(Check("V06", ok, f"{per:,.0f} kg per container" if not ok else ""))

    hs = _v(fields, "hs_codes")
    if hs:
        bad = [c for c in hs if not (c.isdigit() and len(c) in (6, 8, 10))]
        checks.append(Check("V07", not bad, "bad HS code: " + ", ".join(bad) if bad else ""))
    incoterm = _v(fields, "incoterm")
    if incoterm:
        checks.append(Check("V08", incoterm in INCOTERMS, f"unknown incoterm {incoterm}" if incoterm not in INCOTERMS else ""))
    currency = _v(fields, "currency")
    if currency:
        checks.append(Check("V09", currency in CURRENCIES, f"currency {currency} not accepted" if currency not in CURRENCIES else ""))
    lines, total = _v(fields, "line_amounts"), _v(fields, "total_amount")
    if lines and total is not None:
        diff = round(sum(lines) - total, 2)
        checks.append(Check("V10", abs(diff) < 0.01, f"lines add up to {sum(lines):,.2f}, total says {total:,.2f}" if abs(diff) >= 0.01 else ""))
    plate = _v(fields, "vehicle_plate")
    if plate:
        ok = bool(re.match(r"^[A-Z0-9]{1,3}([ -]?[A-Z0-9]{1,5}){1,3}$", plate))
        checks.append(Check("V14", ok, f"registration '{plate}' looks wrong" if not ok else ""))
    return checks


def shipment_key(doc_type, fields):
    if doc_type == "bill_of_lading":
        return _v(fields, "bl_number")
    return _v(fields, "bl_reference")


def check_shipment(doc_type, fields, siblings):
    """Cross-document rules. `siblings` = [(doc_type, fields)] with the same B/L."""
    checks = []
    bls = [f for t, f in siblings if t == "bill_of_lading"]
    pls = [f for t, f in siblings if t == "packing_list"]
    gross = _v(fields, "gross_weight_kg")
    if doc_type == "packing_list" and gross is not None:
        for bl in bls:
            other = _v(bl, "gross_weight_kg")
            if other:
                ok = abs(gross - other) <= 0.01 * other
                checks.append(Check("V11", ok, f"packing list {gross:,.1f} kg vs B/L {other:,.1f} kg" if not ok else ""))
    if doc_type == "bill_of_lading" and gross is not None:
        for pl in pls:
            other = _v(pl, "gross_weight_kg")
            if other:
                ok = abs(gross - other) <= 0.01 * gross
                checks.append(Check("V11", ok, f"B/L {gross:,.1f} kg vs packing list {other:,.1f} kg" if not ok else ""))

    packages = _v(fields, "packages")
    if packages is not None:
        others = {_v(f, "packages") for t, f in siblings
                  if t in ("bill_of_lading", "commercial_invoice", "packing_list")} - {None}
        if others:
            ok = others == {packages}
            checks.append(Check("V12", ok, f"{packages} packages here, {sorted(others)} on the other documents" if not ok else ""))

    containers = _v(fields, "containers")
    if doc_type in ("packing_list", "delivery_order") and containers:
        for bl in bls:
            on_bl = set(_v(bl, "containers") or [])
            extra = [c for c in containers if c not in on_bl]
            checks.append(Check("V13", not extra, "not on the B/L: " + ", ".join(extra) if extra else ""))
    return checks
