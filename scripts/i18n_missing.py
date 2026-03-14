from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iograph.services.i18n import I18nService


def main() -> int:
    parser = argparse.ArgumentParser(description="Report missing i18n id translations")
    parser.add_argument("--strict", action="store_true", help="exit with code 1 if any language has missing keys")
    args = parser.parse_args()

    report = I18nService.translation_coverage_report()
    has_missing = False
    for lang in I18nService.SUPPORTED_LANGUAGES:
        row = report[lang]
        print(f"{lang:8} translated={row['translated']:3}/{row['total']:3} missing={row['missing']:3}")
        if row["missing"] > 0:
            has_missing = True
    if args.strict and has_missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
