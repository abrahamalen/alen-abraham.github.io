"""Fail if the build is missing any file Hugo used to publish (site/urls.txt)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"


def main() -> int:
    expected = [
        line.strip()
        for line in (ROOT / "site" / "urls.txt").read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    missing = [u for u in expected if not (PUBLIC / u.lstrip("/")).is_file()]
    for u in missing:
        print(f"MISSING {u}")
    print(f"{len(expected) - len(missing)}/{len(expected)} URLs present")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
