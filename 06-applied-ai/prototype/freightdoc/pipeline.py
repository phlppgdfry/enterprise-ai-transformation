"""The pilot pipeline: read -> validate -> route -> TMS record.

    classify + extract   (provider: offline rules, or Claude)
    validate             (V01-V14, freightdoc/validate.py)
    route                auto  -> straight into the TMS
                         review -> a clerk checks the flagged fields only
                         manual -> not a freight document, or unsure what it is

The routing policy is configuration, not code, so the evaluation can switch
layers on and off and measure what each one buys (evals/run.py).
"""

from collections import defaultdict
from dataclasses import dataclass, field

from .extract import RulesProvider
from .validate import CROSS_DOC, check_document, check_shipment, shipment_key

PIPELINE_VERSION = "0.4.0"


@dataclass(frozen=True)
class Policy:
    """Which safety layers are on, and where the threshold sits."""
    name: str = "full"
    confidence_threshold: float | None = 0.75
    single_doc_rules: bool = True
    cross_doc_rules: bool = True
    class_threshold: float = 0.75


# The four configurations the evaluation compares (the ablation).
POLICIES = {
    "A": Policy("A: extraction only", None, False, False),
    "B": Policy("B: + confidence threshold", 0.75, False, False),
    "C": Policy("C: + single-document rules", 0.75, True, False),
    "D": Policy("D: + cross-document rules", 0.75, True, True),
}


@dataclass
class Result:
    id: str
    received: str
    doc_type: str
    type_confidence: float
    fields: dict
    checks: list = field(default_factory=list)
    route: str = "auto"
    reasons: list = field(default_factory=list)

    def as_dict(self):
        return {
            "id": self.id, "received": self.received, "doc_type": self.doc_type,
            "type_confidence": self.type_confidence,
            "fields": {k: v.as_dict() for k, v in self.fields.items()},
            "checks": [c.as_dict() for c in self.checks],
            "route": self.route, "reasons": self.reasons,
            "tms_record": tms_record(self) if self.route == "auto" else None,
        }


def route(result, policy):
    reasons = []
    if result.doc_type == "other" or result.type_confidence < policy.class_threshold:
        result.route = "manual"
        result.reasons = ["not recognised as a freight document" if result.doc_type == "other"
                          else f"document type unsure ({result.type_confidence:.2f})"]
        return result
    if policy.confidence_threshold is not None:
        for name, f in result.fields.items():
            if f.confidence < policy.confidence_threshold:
                why = f.note or "low confidence"
                reasons.append(f"{name}: {why} ({f.confidence:.2f})")
    for check in result.checks:
        if check.ok:
            continue
        if check.rule in CROSS_DOC and not policy.cross_doc_rules:
            continue
        if check.rule not in CROSS_DOC and not policy.single_doc_rules:
            continue
        reasons.append(f"{check.rule}: {check.message}")
    result.route = "review" if reasons else "auto"
    result.reasons = reasons
    return result


def process(documents, provider=None, policy=POLICIES["D"]):
    """Run the pipeline over a batch. `documents` = [{id, received, text}]."""
    provider = provider or RulesProvider()
    results = []
    for doc in documents:
        doc_type, conf, fields = provider.read(doc["text"])
        results.append(Result(doc["id"], doc["received"], doc_type, conf, fields))

    keys = link_shipments(results)
    by_shipment = defaultdict(list)
    for r in results:
        if keys.get(r.id):
            by_shipment[keys[r.id]].append(r)

    for r in results:
        r.checks = check_document(r.doc_type, r.fields, r.received)
        key = keys.get(r.id)
        if key:
            siblings = [(s.doc_type, s.fields) for s in by_shipment[key] if s is not r]
            r.checks += check_shipment(r.doc_type, r.fields, siblings)
        route(r, policy)
    return results


def link_shipments(results):
    """Document id -> shipment key (the B/L number).

    Documents name their B/L, or don't: 30-40% of packing lists and invoices
    carry no B/L reference. Those are linked through a container number that
    appears on exactly one B/L (added in v0.4 after the first evaluation run
    let weight mismatches through, see 06-applied-ai/pilot-results.md). The
    match ignores the check digit, so a B/L with a mistyped container number
    still finds its packing list.
    """
    keys = {}
    by_container = defaultdict(set)
    for r in results:
        if r.doc_type == "bill_of_lading":
            for c in (r.fields.get("containers").value if r.fields.get("containers") else None) or []:
                by_container[c[:10]].add(shipment_key(r.doc_type, r.fields))
    for r in results:
        if r.doc_type == "other":
            continue
        key = shipment_key(r.doc_type, r.fields)
        if not key and r.fields.get("containers") and r.fields["containers"].value:
            candidates = set().union(*(by_container.get(c[:10], set()) for c in r.fields["containers"].value))
            candidates.discard(None)
            if len(candidates) == 1:
                key = candidates.pop()
        keys[r.id] = key
    return keys


def tms_record(result):
    """The JSON the TMS import endpoint accepts (schema: schema/tms-record.schema.json)."""
    values = {k: v.value for k, v in result.fields.items()}
    return {
        "documentType": result.doc_type,
        "reference": next((values[k] for k in ("bl_number", "cmr_number", "invoice_number",
                                               "reference", "do_number") if values.get(k)), None),
        "shipmentKey": values.get("bl_number") or values.get("bl_reference"),
        "fields": values,
        "source": {
            "documentId": result.id,
            "receivedOn": result.received,
            "pipelineVersion": PIPELINE_VERSION,
            "minFieldConfidence": round(min((v.confidence for v in result.fields.values()),
                                            default=1.0), 2),
        },
    }
