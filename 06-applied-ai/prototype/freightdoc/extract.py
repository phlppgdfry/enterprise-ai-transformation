"""Deterministic stand-in for the document model: classify, then extract.

It does what the production model has to do (find the document type, find
each field, normalise it, and say how sure it is), with rules instead of a
neural network, so that the evaluation runs offline and gives the same result
every time. The Claude provider (providers/claude.py) has the same interface.

Confidence is the extractor's own estimate. It is not a probability: the
evaluation calibrates the routing threshold against it (evals/run.py).
"""

import datetime as dt
import re
from functools import lru_cache

from .reference import (CURRENCIES, DOC_TYPES, FIELDS, INCOTERMS, LABELS, LOCODES, TITLES,
                        iso6346_valid)

ILLEGIBLE = ("[illegible]", "###", "smudged")
LOOKALIKE_TO_DIGIT = {"O": "0", "Q": "0", "D": "0", "I": "1", "L": "1", "S": "5", "B": "8",
                      "Z": "2", "G": "6"}
MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
LINE = re.compile(r"^(.*?)\s*(?::|\.{3,}|\s{2,})\s*(.+)$")
LBS = 0.45359237


class Field:
    __slots__ = ("value", "confidence", "raw", "note")

    def __init__(self, value, confidence, raw, note=""):
        self.value, self.confidence, self.raw, self.note = value, confidence, raw, note

    def as_dict(self):
        return {"value": self.value, "confidence": round(self.confidence, 2),
                "raw": self.raw, "note": self.note}


def _norm_label(label):
    return re.sub(r"\s+", " ", label.strip().lower()).rstrip(" .:")


def _distance(a, b):
    """Levenshtein distance, small strings only."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def split_lines(text):
    """(label, value) pairs for every line that looks like `label: value`."""
    pairs = []
    for line in text.splitlines():
        m = LINE.match(line.strip())
        if m and m.group(1):
            pairs.append((m.group(1), m.group(2).strip()))
    return pairs


def match_label(label, candidates):
    """Best field for a label among `candidates` -> (field, exact) or (None, False)."""
    return _match_label(_norm_label(label), tuple(candidates))


@lru_cache(maxsize=4096)
def _match_label(norm, candidates):
    for field in candidates:
        if norm in LABELS[field]:
            return field, True
    best, best_d = None, 99
    for field in candidates:
        for syn in LABELS[field]:
            if len(syn) < 6:
                continue
            d = _distance(norm, syn)
            limit = 2 if len(syn) >= 12 else 1
            if d <= limit and d < best_d:
                best, best_d = field, d
    return (best, False) if best else (None, False)


# ----------------------------------------------------------- classify ----

def classify(text):
    """-> (doc_type or 'other', confidence, scores)."""
    head = " ".join(text.lower().splitlines()[:2])
    pairs = split_lines(text)
    scores = {}
    for doc_type in DOC_TYPES:
        score = 4 if any(t in head for t in TITLES[doc_type]) else 0
        hits = {match_label(label, FIELDS[doc_type])[0] for label, _ in pairs}
        hits.discard(None)
        scores[doc_type] = score + len(hits)
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    (best, top), (_, second) = ranked[0], ranked[1]
    if top < 6:
        return "other", 0.9 if top < 3 else 0.6, scores
    return best, round(top / (top + second), 2) if top + second else 0.0, scores


# ------------------------------------------------------------- parsers ----

def parse_number(text):
    """Number from European (1.234,5) or English (1,234.5) notation, or None.

    With one kind of separator, groups of exactly three digits mean thousands
    ("18.443" is 18443, as Belgian shippers write it); anything else is a
    decimal mark ("6392.5", "850,3").
    """
    m = re.search(r"\d[\d.,]*", text)
    if not m:
        return None
    s = m.group(0).rstrip(".,")
    if "." in s and "," in s:
        dec = "." if s.rfind(".") > s.rfind(",") else ","
        thou = "," if dec == "." else "."
        return float(s.replace(thou, "").replace(dec, "."))
    for sep in (",", "."):
        if sep in s:
            parts = s.split(sep)
            if len(parts[0]) <= 3 and all(len(p) == 3 for p in parts[1:]):
                return float("".join(parts))
            if len(parts) == 2:
                return float(parts[0] + "." + parts[1])
            return float("".join(parts))
    return float(s)


def locale_hint(text):
    """+ means US conventions are likely, - means European. Used for dates."""
    score = 0
    low = text.lower()
    score += 2 * ("lbs" in low) + 2 * bool(re.search(r"\b(inc|llc)\b", low))
    score += 1 * ("usd" in low) + 1 * bool(re.search(r"\bus[a-z]{3}\b", low))
    score -= 1 * bool(re.search(r"\bkg\b", low)) + 1 * ("eur" in low)
    score -= 1 * bool(re.search(r"\b(nv|bv|gmbh|sas|spa|oy|ab|sa)\b", low))
    return score


def parse_date(raw, hint):
    s = raw.strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if m:
        return _date(int(m[1]), int(m[2]), int(m[3])), 0.95, ""
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", s)
    if m:
        return _date(int(m[3]), int(m[2]), int(m[1])), 0.95, ""
    m = re.match(r"^(\d{1,2}) ([A-Za-z]{3})[a-z]* (\d{4})$", s)
    if m and m[2].lower() in MONTHS:
        return _date(int(m[3]), MONTHS[m[2].lower()], int(m[1])), 0.95, ""
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s)
    if m:
        a, b, y = int(m[1]), int(m[2]), int(m[3])
        if a > 12:
            return _date(y, b, a), 0.95, ""
        if b > 12:
            return _date(y, a, b), 0.85, "month-first date (US style)"
        if a == b:
            return _date(y, a, b), 0.95, ""
        if hint >= 2:
            return _date(y, a, b), 0.85, "ambiguous date, read month-first from US signals"
        if hint <= -2:
            return _date(y, b, a), 0.85, "ambiguous date, read day-first from EU signals"
        return _date(y, b, a), 0.7, "ambiguous date, assumed day-first"
    return None, 0.3, "unrecognised date format"


def _date(y, mth, d):
    try:
        return dt.date(y, mth, d).isoformat()
    except ValueError:
        return None


def parse_containers(raw):
    tokens = [t for t in re.split(r"[,;\s]+", raw.upper()) if t]
    values, conf, notes = [], 0.95, []
    for tok in tokens:
        if iso6346_valid(tok):
            values.append(tok)
            continue
        repaired = _repair_container(tok)
        if repaired:
            values.append(repaired)
            conf = min(conf, 0.75)
            notes.append(f"{tok} read as {repaired} (OCR look-alike)")
        else:
            values.append(tok)
            conf = min(conf, 0.5)
            notes.append(f"{tok} fails the ISO 6346 check")
    return values, conf, "; ".join(notes)


def _repair_container(tok):
    if len(tok) != 11:
        return None
    head, tail = tok[:4], tok[4:]
    fixed = "".join(LOOKALIKE_TO_DIGIT.get(c, c) for c in tail)
    candidate = head + fixed
    return candidate if candidate != tok and iso6346_valid(candidate) else None


def parse_value(kind, raw, hint):
    """-> Field for one raw value of the given kind."""
    if any(mark in raw.lower() for mark in ILLEGIBLE):
        return Field(None, 0.0, raw, "unreadable")
    if kind in ("ref", "text"):
        return Field(raw.strip(), 0.95, raw)
    if kind == "locode":
        code = raw.strip().upper()[:5]
        return Field(code, 0.95 if code in LOCODES else 0.6, raw,
                     "" if code in LOCODES else "unknown UN/LOCODE")
    if kind == "containers":
        values, conf, note = parse_containers(raw)
        return Field(values, conf, raw, note)
    if kind == "list":
        return Field([t for t in re.split(r"[,;\s]+", raw.strip()) if t], 0.95, raw)
    if kind == "hs_list":
        codes = [t for t in re.split(r"[,;\s]+", raw.strip()) if t]
        return Field(codes, 0.95, raw)
    if kind == "int":
        m = re.search(r"\d+", raw.replace(".", "").replace(",", ""))
        return Field(int(m.group(0)), 0.95, raw) if m else Field(None, 0.2, raw, "no number")
    if kind == "weight":
        parsed = parse_number(raw)
        if parsed is None:
            return Field(None, 0.2, raw, "no number")
        number = parsed
        low = raw.lower()
        if "lb" in low:
            return Field(round(number * LBS, 1), 0.9, raw, "converted from lbs")
        if "kg" in low:
            return Field(round(number, 1), 0.95, raw)
        return Field(round(number, 1), 0.6, raw, "no unit, assumed kg")
    if kind == "amount":
        parsed = parse_number(raw)
        return Field(round(parsed, 2), 0.95, raw) if parsed is not None else Field(None, 0.2, raw, "no number")
    if kind == "amount_list":
        parts = [parse_number(p) for p in raw.split(";")]
        if not parts or any(p is None for p in parts):
            return Field(None, 0.3, raw, "could not read all line amounts")
        return Field([round(p, 2) for p in parts], 0.95, raw)
    if kind == "date":
        value, conf, note = parse_date(raw, hint)
        return Field(value, conf if value else 0.3, raw, note)
    if kind == "currency":
        code = raw.strip().upper()[:3]
        return Field(code, 0.95 if code in CURRENCIES else 0.5, raw)
    if kind == "incoterm":
        code = raw.strip().upper().split()[0] if raw.strip() else ""
        return Field(code, 0.95 if code in INCOTERMS else 0.5, raw)
    if kind == "plate":
        plate = raw.strip().upper()
        ok = re.match(r"^[A-Z0-9]{1,3}([ -]?[A-Z0-9]{1,5}){1,3}$", plate) and \
            re.search(r"\d", plate) and re.search(r"[A-Z]", plate)
        return Field(plate, 0.9 if ok else 0.5, raw)
    raise ValueError(kind)


# ------------------------------------------------------------- extract ----

def extract(text, doc_type):
    """-> {field: Field} for the fields of `doc_type`."""
    spec = FIELDS[doc_type]
    hint = locale_hint(text)
    found = {}
    for label, raw in split_lines(text):
        field, exact = match_label(label, spec)
        if not field:
            continue
        parsed = parse_value(spec[field][0], raw, hint)
        if not exact:
            parsed.confidence = round(parsed.confidence * 0.85, 3)
            parsed.note = "; ".join(x for x in (parsed.note, f"label read as '{label}'") if x)
        if field in found and found[field].value != parsed.value:
            found[field].confidence = min(found[field].confidence, 0.5)
            found[field].note = "conflicting values on the document"
            continue
        found.setdefault(field, parsed)
    return found


class RulesProvider:
    """Offline provider: the deterministic extractor above."""

    name = "rules"

    def read(self, text):
        doc_type, conf, _ = classify(text)
        fields = extract(text, doc_type) if doc_type != "other" else {}
        return doc_type, conf, fields
