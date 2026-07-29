"""Minimal Apify client: run an Actor, get its rows back.

Two ways to run an Actor over the API, and the choice matters:

  run_sync()   one call, blocks until the run finishes, returns the rows.
               Apify caps synchronous calls, so this is for runs that finish
               in well under five minutes.

  run_async()  start the run, poll until it finishes, then read the dataset.
               Use this for anything large: a hundred companies, a full
               historical series, an entire top-chart sweep.

Only the standard library is used, so these scripts run on a clean Python 3.9+
with no pip install.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

API = "https://api.apify.com/v2"


class ApifyError(RuntimeError):
    pass


def _token() -> str:
    tok = os.environ.get("APIFY_TOKEN", "").strip()
    if not tok:
        raise ApifyError(
            "Set APIFY_TOKEN first. Create one at "
            "https://console.apify.com/settings/integrations")
    return tok


def _request(method: str, url: str, body: dict | None = None,
             timeout: int = 300) -> object:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {_token()}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        raise ApifyError(f"HTTP {e.code} from {url}\n{detail}") from None


def run_sync(actor: str, actor_input: dict, *,
             max_charge_usd: float | None = None) -> list[dict]:
    """Run an Actor and return its dataset rows in one call.

    max_charge_usd is a hard ceiling the platform enforces: the Actor stops
    cleanly when charges reach it, so it cannot overspend a budget you set.
    """
    url = f"{API}/acts/{actor}/run-sync-get-dataset-items"
    if max_charge_usd is not None:
        url += f"?maxTotalChargeUsd={max_charge_usd}"
    rows = _request("POST", url, actor_input)
    if not isinstance(rows, list):
        raise ApifyError(f"expected a list of rows, got {type(rows).__name__}")
    return rows


def run_async(actor: str, actor_input: dict, *,
              max_charge_usd: float | None = None,
              poll_secs: int = 5, timeout_secs: int = 3600) -> list[dict]:
    """Start a run, wait for it, then read its dataset. For long runs."""
    url = f"{API}/acts/{actor}/runs"
    if max_charge_usd is not None:
        url += f"?maxTotalChargeUsd={max_charge_usd}"
    started = _request("POST", url, actor_input)
    run = (started or {}).get("data") or {}
    run_id, dataset_id = run.get("id"), run.get("defaultDatasetId")
    if not run_id:
        raise ApifyError(f"run did not start: {json.dumps(started)[:300]}")

    deadline = time.time() + timeout_secs
    while time.time() < deadline:
        time.sleep(poll_secs)
        current = ((_request("GET", f"{API}/actor-runs/{run_id}") or {})
                   .get("data") or {})
        status = current.get("status")
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            if status != "SUCCEEDED":
                raise ApifyError(
                    f"run {run_id} finished as {status}. Logs: "
                    f"https://console.apify.com/actors/runs/{run_id}")
            break
    else:
        raise ApifyError(f"run {run_id} still going after {timeout_secs}s")

    rows = _request("GET", f"{API}/datasets/{dataset_id}/items?clean=true")
    return rows if isinstance(rows, list) else []


def split_errors(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Separate real results from per-target error rows.

    These Actors report a failed target as a row carrying an `error` field
    rather than aborting the whole run, and those rows are not charged. Any
    code that counts results should split them out — otherwise a run that
    failed on every target still looks like it returned data.
    """
    good = [r for r in rows if not r.get("error")]
    bad = [r for r in rows if r.get("error")]
    return good, bad
