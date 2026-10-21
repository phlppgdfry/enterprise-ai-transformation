"""Fail when a relative link in a Markdown file points to a file that does not exist.

    python scripts/check_links.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\]\(([^)\s]+)\)")


def main():
    broken = []
    for md in sorted(ROOT.rglob("*.md")):
        if ".git" in md.parts or "data" in md.relative_to(ROOT).parts[:-1]:
            continue
        text = re.sub(r"```.*?```", "", md.read_text(encoding="utf-8"), flags=re.S)
        for target in LINK.findall(text):
            if re.match(r"^(https?:|mailto:|#)", target) or target.startswith("../../actions"):
                continue
            path = target.split("#")[0].split("?")[0]
            if path and not (md.parent / path).exists():
                broken.append(f"{md.relative_to(ROOT)} -> {target}")
    if broken:
        print("Broken links:", *broken, sep="\n  ")
        return 1
    print("all relative links resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
