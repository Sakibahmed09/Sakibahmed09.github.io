#!/usr/bin/env python3
"""Top up tweets_live.json from Typefully's X analytics.

The analytics feed carries every post on the account (not just ones published
through Typefully), so this is the forward continuation of the X archive
download, which stops at 15 Apr 2026. Overlap is deduped by status id.
"""
import json, os, datetime, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tweets_live.json")
SOCIAL_SET = 209256  # @mertesakib
FLOOR = "2026-04-01"
REPULL_DAYS = 30  # re-read a trailing window so engagement counts settle


def api_key():
    v = os.environ.get("TYPEFULLY_API_KEY", "").strip()
    if v:
        return v
    p = os.path.expanduser("~/.config/typefully/api_key")
    if os.path.exists(p):
        return open(p).read().strip()
    cfg = os.path.expanduser(
        "~/claude-draper/datstra-slack-watcher/config.json")
    return json.load(open(cfg))["typefully_api_key"]


def fetch(url, key):
    req = urllib.request.Request(
        url, headers={"Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    key = api_key()
    cache = {}
    if os.path.exists(OUT):
        cache = {t["id"]: t for t in json.load(open(OUT))}

    start = FLOOR
    if cache:
        newest = max(t["date"] for t in cache.values())
        start = max(FLOOR, (datetime.date.fromisoformat(newest)
                            - datetime.timedelta(days=REPULL_DAYS)).isoformat())
    end = datetime.date.today().isoformat()

    url = ("https://api.typefully.com/v2/social-sets/%d/analytics/x/posts"
           "?start_date=%s&end_date=%s&limit=100" % (SOCIAL_SET, start, end))
    added = 0
    while url:
        d = fetch(url, key)
        for r in d["results"]:
            txt = (r.get("preview_text") or "").strip()
            if not txt or txt.startswith("RT @"):
                continue
            eng = (r.get("metrics") or {}).get("engagement") or {}
            if r["post_id"] not in cache:
                added += 1
            cache[r["post_id"]] = {
                "id": r["post_id"],
                "date": r["created_at"][:10],
                "text": txt,
                "fav": int(eng.get("likes") or 0),
                "rt": int(eng.get("shares") or 0),
                "url": r.get("url")
                or "https://x.com/mertesakib/status/" + r["post_id"],
            }
        url = d.get("next")

    rows = sorted(cache.values(), key=lambda t: t["date"])
    with open(OUT, "w") as f:
        json.dump(rows, f, indent=1)
    print("tweets_live: %d cached (+%d new), through %s"
          % (len(rows), added, rows[-1]["date"] if rows else "-"))


main()
