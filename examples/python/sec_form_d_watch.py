"""Find companies in a sector that recently raised a private round.

A Form D is what a US company files after selling securities in a private
placement. Filing it is required, it is public, and it usually lands on EDGAR
before the funding announcement does — which makes it the earliest reliable
signal that a specific company just took money.

The interesting query is not "list every Form D" (there are thousands a month)
but "Form Ds that mention my sector". That is what full-text search over the
filing body gives you, and it is why this uses searchQuery rather than a list
of tickers: you do not know the company names in advance. That is the point.

    APIFY_TOKEN=apify_api_... python3 sec_form_d_watch.py "artificial intelligence"
"""

from __future__ import annotations

import datetime as dt
import sys

from client import run_sync, split_errors

ACTOR = "glitchbound~sec-filings-scraper"


def main() -> int:
    sector = sys.argv[1] if len(sys.argv) > 1 else "artificial intelligence"
    since = (dt.date.today() - dt.timedelta(days=90)).isoformat()

    print(f"Form D filings mentioning {sector!r}, filed since {since}\n")

    rows = run_sync(ACTOR, {
        # Quoting the phrase keeps EDGAR from matching the words separately.
        "searchQuery": f'"{sector}"',
        "formTypes": ["D"],
        "filedSince": since,
        "maxSearchResults": 50,
    }, max_charge_usd=0.50)

    good, failed = split_errors(rows)
    if failed:
        print(f"note: {len(failed)} target(s) came back as errors "
              f"(not charged): {failed[0].get('error')}\n")
    if not good:
        print("No Form D filings matched. Try a broader phrase or a longer "
              "window — full-text search covers filings since 2001.")
        return 0

    good.sort(key=lambda r: r.get("filingDate") or "", reverse=True)
    width = max(len(str(r.get("companyName") or "")) for r in good)
    for r in good:
        print(f"{r.get('filingDate','?'):10}  "
              f"{str(r.get('companyName') or '?'):{width}}  "
              f"{r.get('state') or '--':2}  {r.get('filingUrl') or ''}")

    print(f"\n{len(good)} filings. Each row is one charged result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
