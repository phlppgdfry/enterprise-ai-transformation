"""Just enough of an Excel formula evaluator to check the generated workbooks.

Supports what scripts/build.py writes: cell and cross-sheet references,
ranges, + - * / ^, comparisons, and MIN, MAX, IF, SUM, NPV, ROUND, AVERAGE,
AVERAGEIF, ISNUMBER, RANK. Not a general spreadsheet engine.
"""

import re
import zipfile
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


def _cells(xml):
    out = {}
    for c in ET.fromstring(xml).iter(f"{{{NS['m']}}}c"):
        ref = c.get("r")
        f = c.find("m:f", NS)
        v = c.find("m:v", NS)
        t = c.find("m:is/m:t", NS)
        if f is not None:
            out[ref] = "=" + f.text
        elif v is not None:
            out[ref] = float(v.text)
        elif t is not None:
            out[ref] = t.text
    return out


def load(path):
    with zipfile.ZipFile(path) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        names = [s.get("name") for s in wb.iter(f"{{{NS['m']}}}sheet")]
        return {name: _cells(z.read(f"xl/worksheets/sheet{i}.xml")) for i, name in enumerate(names, 1)}


def _split(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref.replace("$", ""))
    col = 0
    for ch in m.group(1):
        col = col * 26 + ord(ch) - 64
    return col, int(m.group(2))


def _name(col, row):
    s = ""
    while col:
        col, r = divmod(col - 1, 26)
        s = chr(65 + r) + s
    return f"{s}{row}"


class Workbook:
    def __init__(self, path):
        self.sheets = load(path)
        self.cache = {}

    def value(self, sheet, ref):
        key = (sheet, ref.replace("$", ""))
        if key not in self.cache:
            raw = self.sheets[sheet].get(key[1])
            self.cache[key] = self._eval(sheet, raw[1:]) if isinstance(raw, str) and raw.startswith("=") else raw
        return self.cache[key]

    def range(self, sheet, a, b):
        (c1, r1), (c2, r2) = _split(a), _split(b)
        return [self.value(sheet, _name(c, r)) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]

    def _eval(self, sheet, formula):
        py = formula
        py = re.sub(r"(\w+)!(\$?[A-Z]+\$?\d+):(\$?[A-Z]+\$?\d+)", r'RNG("\1","\2","\3")', py)
        py = re.sub(r"(\w+)!(\$?[A-Z]+\$?\d+)", r'REF("\1","\2")', py)
        py = re.sub(r'(?<!["\w$])(\$?[A-Z]+\$?\d+):(\$?[A-Z]+\$?\d+)', rf'RNG("{sheet}","\1","\2")', py)
        py = re.sub(r'(?<!["\w$])(\$?[A-Z]{1,2}\$?\d+)(?![\w"(])', rf'REF("{sheet}","\1")', py)
        py = py.replace("^", "**").replace("<>", "!=")
        py = re.sub(r"(?<![<>!=])=(?!=)", "==", py)
        env = {
            "REF": lambda s, r: self.value(s, r), "RNG": lambda s, a, b: self.range(s, a, b),
            "MIN": lambda *a: min(a), "MAX": lambda *a: max(a), "IF": lambda c, x, y: x if c else y,
            "SUM": lambda *a: sum(sum(x) if isinstance(x, list) else x for x in a),
            "NPV": lambda rate, vals: sum(v / (1 + rate) ** (i + 1) for i, v in enumerate(vals)),
            "ISNUMBER": lambda x: isinstance(x, (int, float)),
            "RANK": lambda x, vals: None if isinstance(x, str) else 1 + sum(1 for v in vals if isinstance(v, (int, float)) and v > x),  # IF is eager here
            "ROUND": lambda x, d=0: round(x, int(d)), "AVERAGE": lambda vals: sum(vals) / len(vals),
            "AVERAGEIF": lambda crit, val, values: (lambda xs: sum(xs) / len(xs))(
                [v for c, v in zip(crit, values) if c == val]),
        }
        return eval(py, {"__builtins__": {}}, env)  # noqa: S307 - formulas come from our own build
