# Apify data Actors: runnable examples

Working code for sixteen data-extraction Actors on the [Apify](https://apify.com) platform, published under [**glitchbound**](https://apify.com/glitchbound). Every Actor is built on an official or public API rather than on rendered HTML, so the shape of the output does not change when someone redesigns a page.

Each example in `examples/inputs/` is generated from the Actor's own input schema, so it is a valid input by construction, not a snippet that drifted out of date.

**Every Actor here is auto-tested daily** against the same check Apify runs on the Store: start with default input, require a non-empty dataset, five-minute limit. Results are per-row; a target that fails comes back as an `error` row and is not charged.

## The Actors

| Actor | What one result is |
|---|---|
| [SEC EDGAR Scraper](https://apify.com/glitchbound/sec-filings-scraper) | one filing, fiscal year of financials, or full-text hit |
| [Local Business Scraper](https://apify.com/glitchbound/places-scraper) | one business with phone and website |
| [Steam Scraper](https://apify.com/glitchbound/steam-scraper) | one game with price and metadata |
| [App Store & Google Play Scraper](https://apify.com/glitchbound/app-store-scraper) | one app listing |
| [App Store Top Charts Scraper](https://apify.com/glitchbound/app-charts-scraper) | one ranked chart entry |
| [App Developer Portfolio Scraper](https://apify.com/glitchbound/app-developer-scraper) | one app in a developer's portfolio |
| [Website Tech Stack & Contact Scraper](https://apify.com/glitchbound/website-scraper) | one website profiled: stack, contacts, socials |
| [Crypto Scraper](https://apify.com/glitchbound/crypto-scraper) | one coin, candle, or trending entry |
| [Job Board Scraper](https://apify.com/glitchbound/job-board-scraper) | one job posting |
| [Google Trends Scraper](https://apify.com/glitchbound/google-trends-scraper) | one trend series or trending query |
| [Podcast Scraper](https://apify.com/glitchbound/podcast-scraper) | one show or episode |
| [WHOIS Domain Lookup](https://apify.com/glitchbound/whois-domain-lookup) | one domain with WHOIS and DNS |
| [Shopify Scraper](https://apify.com/glitchbound/shopify-scraper) | one product variant or collection |
| [News Scraper](https://apify.com/glitchbound/news-scraper) | one article, after dedupe |
| [Remote Jobs Scraper](https://apify.com/glitchbound/remote-jobs-scraper) | one remote job, after dedupe |
| [App Reviews Scraper](https://apify.com/glitchbound/app-reviews-scraper) | one review |

Each Actor charges per result; the current rate for your plan is on its Store page.

## Job data

The job Actors have outgrown this list and live in their own repo:
[**job-board-apis**](https://github.com/danielhagever/job-board-apis) documents the public
job posting endpoint of 18 applicant tracking systems (Greenhouse, Lever, Ashby, Workday,
Oracle, SmartRecruiters and more), each with a `curl` tested live. The hosted versions:

- [Workday Jobs Scraper](https://apify.com/glitchbound/workday-jobs-scraper): any Workday careers site, by company name or URL.
- [Company Career Page Jobs Scraper](https://apify.com/glitchbound/ats-jobs-scraper): a company name or domain in, its open jobs out, across 24 systems.
- [Job Listings API](https://apify.com/glitchbound/ats-jobs-search): search one index of career-site jobs, refreshed daily.
- [Google Play Top Charts Scraper](https://apify.com/glitchbound/google-play-charts-scraper): top free, top grossing and trending apps by country.

## Quick start

One HTTP call runs an Actor and returns its rows. No SDK needed.

```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  -d @examples/inputs/sec-filings-scraper.json \
  "https://api.apify.com/v2/acts/glitchbound~sec-filings-scraper/run-sync-get-dataset-items?token=$APIFY_TOKEN"
```

Get a token from [console.apify.com/settings/integrations](https://console.apify.com/settings/integrations). The response is a JSON array of result rows.

For runs that take longer than the synchronous limit, start the run and poll instead. `examples/python/client.py` does both.

## Examples

```
examples/
  inputs/     one valid input per Actor, generated from its input schema
  python/     client.py + three end-to-end scripts
  node/       the same one-call pattern in JavaScript
```

Run any of them with your token in the environment:

```bash
export APIFY_TOKEN=apify_api_...
python3 examples/python/sec_form_d_watch.py
```

### Find startups that just raised money

`examples/python/sec_form_d_watch.py`

A Form D is what a US company files after selling securities in a private round. It is public, it is required, and it lands on EDGAR before the funding press release. The script pulls recent Form Ds and prints who filed.

### Track how a competitor's app is being reviewed

`examples/python/app_review_monitor.py`

Pulls the most recent reviews for a list of apps across both the App Store and Google Play, filters to the low ratings, and groups them so you can see what users are actually complaining about.

### Snapshot the crypto market

`examples/python/crypto_snapshot.py`

Top coins by market cap with price, 24h and 7d change, and Binance bid/ask, written to CSV.

## Notes on cost control

Every Actor honours the run's **maximum charge**, set in the run options or via `maxTotalChargeUsd` on the API call. When the limit is reached the Actor stops cleanly rather than being killed mid-write, so you never pay for a partial row.

Targets that cannot be resolved, such as a ticker that does not exist or a domain that does not resolve, come back as rows with an `error` field and are not charged.

## Write-ups

Some of these examples have a longer post behind them, each with the measurement
that made it worth writing:

- [Find startups the day they raise, before the press release](https://dev.to/glitchbound/find-startups-the-day-they-raise-before-the-press-release-with-30-lines-of-python-46o6). Form D hits EDGAR before the funding announcement. Includes the half-open date range EDGAR ignores in silence, which returned eleven years of filings outside the window and looked normal doing it.
- [The App Store top charts are a public API, and nobody archives them](https://dev.to/glitchbound/the-app-store-top-charts-are-a-public-api-and-nobody-archives-them-n7n). The feed shows today and nothing else, so the archive is worth more than the feed.
- [WHOIS is gone, RDAP replaced it, and a 404 does not mean what you think](https://dev.to/glitchbound/whois-is-gone-rdap-replaced-it-and-a-404-does-not-mean-what-you-think-3alh). RDAP's 404 is ambiguous: for the TLDs missing from IANA's bootstrap, including .io and .co, it means "nowhere to ask" rather than "available". That had this Actor reporting registered domains as free to buy.
- [Google's News API has been gone since 2016, and people still search for it](https://dev.to/glitchbound/googles-news-api-has-been-gone-since-2016-and-people-still-search-for-it-3544). The RSS endpoint that outlived it needs no key. Includes Bing's per-query XML namespace, which is the request URL itself, so no fixed namespace constant ever matches and the publisher field silently comes back null.
- [Workday Jobs Scraper: every posting from any Workday careers site, by company name](https://dev.to/glitchbound/workday-jobs-scraper-every-posting-from-any-workday-careers-site-by-company-name-8bd).
- [Company Career Page Scraper: every open job from any company, by name or domain](https://dev.to/glitchbound/company-career-page-scraper-every-open-job-from-any-company-by-name-or-domain-ede).
- [Google Play top charts API: top free, top grossing and trending apps in 130 countries](https://dev.to/glitchbound/google-play-top-charts-api-top-free-top-grossing-and-trending-apps-in-130-countries-31ac).

## License

MIT. See [LICENSE](LICENSE).
