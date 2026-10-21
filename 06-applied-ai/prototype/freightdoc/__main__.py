"""Command line for the pilot.

    python -m freightdoc read DOC-0042            # one document from the test set
    python -m freightdoc read path/to/scan.txt    # any OCR text file
    python -m freightdoc batch --set test         # route counts for a whole set
    python -m freightdoc queue --set test         # the review queue a clerk would see
    python -m freightdoc rules                    # the validation rules

Add --provider claude to read with Claude instead of the offline rules.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from .pipeline import process
from .validate import RULES

ROOT = Path(__file__).resolve().parents[1]


def load_set(name):
    path = ROOT / "data" / name / "documents.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def provider_for(name):
    if name == "claude":
        from .providers.claude import ClaudeProvider
        return ClaudeProvider()
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(prog="freightdoc")
    parser.add_argument("--provider", default="rules", choices=["rules", "claude"])
    sub = parser.add_subparsers(dest="cmd", required=True)
    read = sub.add_parser("read")
    read.add_argument("target")
    read.add_argument("--set", default="test")
    for name in ("batch", "queue"):
        p = sub.add_parser(name)
        p.add_argument("--set", default="test")
    sub.add_parser("rules")
    args = parser.parse_args(argv)

    if args.cmd == "rules":
        for code, text in RULES.items():
            print(f"{code}  {text}")
        return 0

    provider = provider_for(args.provider)
    if args.cmd == "read":
        path = Path(args.target)
        if path.exists():
            docs = [{"id": path.stem, "received": "2026-09-20", "text": path.read_text(encoding="utf-8")}]
            target = path.stem
        else:
            docs, target = load_set(args.set), args.target
        results = {r.id: r for r in process(docs, provider=provider)}
        if target not in results:
            print(f"no document {target}", file=sys.stderr)
            return 1
        print(json.dumps(results[target].as_dict(), indent=2, ensure_ascii=False))
        return 0

    results = process(load_set(args.set), provider=provider)
    if args.cmd == "batch":
        counts = Counter(r.route for r in results)
        total = len(results)
        for route in ("auto", "review", "manual"):
            print(f"{route:7} {counts[route]:4}  {100 * counts[route] / total:5.1f}%")
        return 0
    for r in results:
        if r.route == "review":
            print(f"{r.id}  {r.doc_type:18}  " + " | ".join(r.reasons))
    return 0


if __name__ == "__main__":
    sys.exit(main())
