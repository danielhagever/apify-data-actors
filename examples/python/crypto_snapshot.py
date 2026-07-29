"""Write a CSV snapshot of the top coins by market cap.

Two things worth pointing out, because they are the reason to use this rather
than hitting a public price endpoint yourself:

  * `includeBinance` adds live bid/ask alongside the market-cap-weighted price.
    Those two numbers disagree, and the spread between them is often the thing
    you actually wanted.
  * The whole snapshot is one run and one charge per coin, not one request per
    coin, so a 250-coin sweep costs 250 results rather than 250 round trips.

    APIFY_TOKEN=apify_api_... python3 crypto_snapshot.py 100 > snapshot.csv
"""

from __future__ import annotations

import csv
import sys

from client import run_sync, split_errors

ACTOR = "glitchbound~crypto-scraper"

FIELDS = ["symbol", "name", "price", "marketCapRank", "marketCap", "volume24h",
          "priceChangePct24h", "priceChangePct7d", "binanceBidPrice",
          "binanceAskPrice", "circulatingSupply", "ath", "athChangePct"]


def main() -> int:
    top = int(sys.argv[1]) if len(sys.argv) > 1 else 100

    rows = run_sync(ACTOR, {
        "topCoins": top,
        "vsCurrency": "usd",
        "includeBinance": True,
        "includeTrending": False,
    }, max_charge_usd=1.00)

    good, failed = split_errors(rows)
    for f in failed:
        print(f"# error row: {f.get('error')}", file=sys.stderr)
    if not good:
        print("# nothing returned", file=sys.stderr)
        return 1

    good.sort(key=lambda r: r.get("marketCapRank") or 10**9)

    writer = csv.DictWriter(sys.stdout, fieldnames=FIELDS, extrasaction="ignore")
    writer.writeheader()
    for r in good:
        writer.writerow(r)

    print(f"# {len(good)} coins", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
