"""See what people are actually complaining about in an app's recent reviews.

Both stores are queried in one run — the Actor normalises App Store and Google
Play into the same row shape, which is the whole reason to use it rather than
two separate scrapers whose fields disagree.

The filter that matters is `maxRating`. Pulling every review and grepping
locally means paying for the four- and five-star ones you are going to throw
away; asking the Actor for 1-2 stars only is the same answer for a fraction of
the cost.

Note which identifier each store wants, because getting it wrong returns an
empty half rather than an error: Google Play takes the package name
(`com.spotify.music`), the App Store takes the numeric app id (`324684580`) or
an iOS bundle id. Passing an Android package and expecting iOS reviews back
gets you exactly zero iOS rows.

A store can also come back empty for an honest reason: the App Store exposes
only a recent slice of reviews, so a popular, well-liked app may have no 1-2
star reviews in that window at all. The platform breakdown printed below is
there so an empty half is visible rather than assumed away.

    APIFY_TOKEN=apify_api_... python3 app_review_monitor.py 324684580 com.spotify.music
"""

from __future__ import annotations

import collections
import re
import sys

from client import run_sync, split_errors

ACTOR = "glitchbound~app-reviews-scraper"

# Words that carry no signal in a complaint, so they would otherwise top every
# frequency count.
STOP = set("""a an the and or but if then than that this these those is are was
were be been being do does did doing have has had having i me my we our you
your it its of to in on for with at by from as so not no just now very really
too also can cannot cant will wont would could should app apps get got make
made use used using thing things time""".split())


def main() -> int:
    # Spotify on both stores: numeric id for the App Store, package for Play.
    app_ids = sys.argv[1:] or ["324684580", "com.spotify.music"]
    print(f"Recent 1-2 star reviews for: {', '.join(app_ids)}\n")

    rows = run_sync(ACTOR, {
        "appIds": app_ids,
        "platform": "both",
        "maxReviewsPerApp": 200,
        "sortBy": "mostrecent",
        "minRating": 1,
        "maxRating": 2,
    }, max_charge_usd=0.20)

    good, failed = split_errors(rows)
    for f in failed:
        print(f"could not resolve {f.get('target') or f.get('appId')}: "
              f"{f.get('error')}")
    if not good:
        print("\nNo 1-2 star reviews came back — which is its own answer.")
        return 0

    by_platform = collections.Counter(r.get("platform") or "?" for r in good)
    print(f"{len(good)} negative reviews  ({dict(by_platform)})\n")

    words = collections.Counter()
    for r in good:
        text = f"{r.get('title') or ''} {r.get('text') or ''}".lower()
        for w in re.findall(r"[a-z']{4,}", text):
            if w not in STOP:
                words[w] += 1

    print("Most common words in the complaints:")
    for word, n in words.most_common(15):
        print(f"  {n:4}  {word}")

    print("\nMost recent, verbatim:")
    # The timestamp field is `reviewedAt`, and `title` is always null on Google
    # Play because Play reviews have no titles — so the text is the only line
    # guaranteed to carry content.
    good.sort(key=lambda r: r.get("reviewedAt") or "", reverse=True)
    for r in good[:5]:
        stars = "★" * int(r.get("rating") or 0)
        when = (r.get("reviewedAt") or "")[:10] or "date unknown"
        print(f"\n  [{r.get('platform')}] {stars}  {when}  "
              f"v{r.get('appVersion') or '?'}")
        title = (r.get("title") or "").strip()
        if title:
            print(f"  {title}")
        body = " ".join((r.get("text") or "").split())
        print(f"  {body[:240]}{'...' if len(body) > 240 else ''}" if body
              else "  (no text)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
