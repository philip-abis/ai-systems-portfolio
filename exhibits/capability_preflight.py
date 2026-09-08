"""Which fetch path can this run actually use? Decide once, say it out loud.

Excerpted from a prospecting pipeline built to run in two environments.

WHY THIS EXISTS
===============
The same skill runs on a laptop, where a Python script can open a socket, and in
a hosted agent sandbox, where it cannot but where the agent's own tool calls run
server-side and reach the web fine. Tools fetch, scripts compute.

The wrong way to handle that is to ask "which environment am I in". That is a
label, and labels are guesses. The right question is "can a script in THIS
process open a socket to the API", which is the thing that actually decides and
the thing that silently breaks.

Two further rules, both learned the hard way:

DECIDE ONCE, BEFORE ANY URL IS FETCHED. Not per-URL with a fallback. A run that
fetched half one way and half the other cannot be read afterwards, because
nothing in the output says which half is which.

ANNOUNCE THE PATH. One sentence, before anything is fetched, including whether
the chosen path is slower or costs more per item, and what it cannot do at all.
Otherwise the operator cannot tell a thin result from an honest empty one.

WHAT IT IS EVIDENCE OF
======================
Branching on a measured capability rather than an assumed environment, and
failing at the start of an expensive operation rather than the end. This probe
is the cheapest step in the pipeline and it prevents the most expensive failure:
discovering after a full sweep that nothing was ever read.
"""
import json
import os
import time
import urllib.error
import urllib.request

TIMEOUT = 5.0

# Any HTTP answer proves egress, INCLUDING 401 and 404. The question is whether
# the host is reachable from this process, not whether the key is good. Treating
# a 401 as failure here would report "no network" on a bad key, which sends you
# looking in entirely the wrong place.
PROBES = {
    "firecrawl":   "https://api.firecrawl.dev/",
    "perplexity":  "https://api.perplexity.ai/",
    "usaspending": "https://api.usaspending.gov/",
    "notion":      "https://api.notion.com/",
}
KEYS = {
    "firecrawl": "FIRECRAWL_API_KEY",
    "perplexity": "PERPLEXITY_API_KEY",
    "usaspending": None,          # public, no key
    "notion": "NOTION_API_KEY",
}


def find_key(name, env_files=(".env", "../.env")):
    """(value, where). Project .env first, then the environment.

    Deliberately the SAME order the fetching code uses, so preflight can never
    report a key that the fetcher would not find. A preflight that checks
    somewhere different from the thing it is clearing is worse than none.
    """
    for p in env_files:
        if os.path.exists(p):
            for line in open(p):
                if line.startswith(name):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v:
                        return v, p
    v = os.environ.get(name)
    return (v, "environment") if v else (None, None)


def reachable(url, timeout=TIMEOUT):
    """(bool, detail, seconds). Only a TRANSPORT failure means blocked."""
    t0 = time.time()
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True, "ok", round(time.time() - t0, 2)
    except urllib.error.HTTPError as e:
        return True, f"http {e.code}", round(time.time() - t0, 2)   # reachable
    except Exception as e:
        return False, type(e).__name__, round(time.time() - t0, 2)  # blocked


def decide(services):
    """Returns the path this run will take, plus why, for announcing."""
    report = {}
    for s in services:
        key, where = find_key(KEYS[s]) if KEYS[s] else ("n/a", "public")
        ok, detail, secs = reachable(PROBES[s])
        report[s] = {"egress": ok, "detail": detail, "seconds": secs,
                     "key": bool(key), "key_from": where}
    script_path = all(r["egress"] for r in report.values())
    return {
        "path": "script-fetch" if script_path else "tool-fetch",
        "why": ("scripts can reach every API directly"
                if script_path else
                "this process has no outbound network; fetching moves to tool calls, "
                "which cost a model turn per call and are slower per item"),
        "services": report,
    }


if __name__ == "__main__":
    print(json.dumps(decide(["firecrawl", "notion"]), indent=2))
