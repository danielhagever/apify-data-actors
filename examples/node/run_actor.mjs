// Run any of the Actors and print its rows. Node 18+, no dependencies.
//
//   APIFY_TOKEN=apify_api_... node run_actor.mjs sec-filings-scraper '{"companies":["AAPL"]}'
//
// The synchronous endpoint used here returns the dataset directly, which is the
// shortest path from "I have a token" to "I have rows". For runs that take
// longer than Apify's synchronous limit, start the run at POST /acts/<id>/runs
// and poll GET /actor-runs/<runId> instead — examples/python/client.py shows
// both paths.

const API = "https://api.apify.com/v2";

const token = process.env.APIFY_TOKEN?.trim();
if (!token) {
  console.error("Set APIFY_TOKEN. Create one at https://console.apify.com/settings/integrations");
  process.exit(1);
}

const actor = process.argv[2];
if (!actor) {
  console.error("usage: node run_actor.mjs <actor-name> ['<json input>']");
  process.exit(1);
}

let input = {};
if (process.argv[3]) {
  try {
    input = JSON.parse(process.argv[3]);
  } catch (e) {
    console.error(`input is not valid JSON: ${e.message}`);
    process.exit(1);
  }
}

const name = actor.includes("/") || actor.includes("~")
  ? actor.replace("/", "~")
  : `glitchbound~${actor}`;

const res = await fetch(
  `${API}/acts/${name}/run-sync-get-dataset-items?maxTotalChargeUsd=0.50`,
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(input),
  },
);

if (!res.ok) {
  console.error(`HTTP ${res.status}\n${(await res.text()).slice(0, 500)}`);
  process.exit(1);
}

const rows = await res.json();

// A target that could not be resolved comes back as a row with an `error`
// field rather than failing the run, and those rows are not charged. Counting
// them as results is how a run that fetched nothing still looks successful.
const failed = rows.filter((r) => r.error);
const good = rows.filter((r) => !r.error);

for (const r of failed) console.error(`error row: ${r.error}`);
console.log(JSON.stringify(good, null, 2));
console.error(`${good.length} results, ${failed.length} error rows`);
