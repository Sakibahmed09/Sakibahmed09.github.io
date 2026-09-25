#!/usr/bin/env python3
"""Top up tweets_live.json from Typefully's X analytics.

The analytics feed carries every post on the account (not just ones published
through Typefully), so this is the forward continuation of the X archive
download, which stops at 15 Apr 2026. Overlap is deduped by status id.
"""
import json, os, datetime, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tweets_live.json")
# beside the archive's own photos, so mine.py and build.py find them the same way
MEDIA_DIR = os.path.join(HERE, "archive", "tweets_media")
MEDIA_KEYS = ("media", "video", "media_checked", "deleted")


class Deleted(Exception):
    pass


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


def deleted_on_x(tweet_id):
    """Typefully keeps reporting a post after he deletes it; X's embed
    endpoint answers with a tombstone instead."""
    req = urllib.request.Request(
        "https://cdn.syndication.twimg.com/tweet-result?id=%s&token=a" % tweet_id,
        headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.load(r)
    return d.get("__typename") == "TweetTombstone"


def fetch_media(tweet_id):
    """Typefully's analytics carry no media, so ask fxtwitter (free, no key)
    for the post's first photo, or the still for a video, and keep a copy."""
    req = urllib.request.Request(
        "https://api.fxtwitter.com/mertesakib/status/" + tweet_id,
        headers={"User-Agent": "sakib.lol refresh"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            media = ((json.load(r).get("tweet") or {}).get("media") or {}).get("all") or []
    except urllib.error.HTTPError as e:
        if e.code == 404 and deleted_on_x(tweet_id):
            raise Deleted()
        raise
    if not media:
        return [], False
    first = media[0]
    video = first.get("type") in ("video", "gif")
    src = first.get("thumbnail_url") if video else first.get("url")
    if not src:
        return [], False
    name = "%s-%s" % (tweet_id, src.split("?")[0].rsplit("/", 1)[-1])
    if not name.lower().endswith((".jpg", ".png")):
        name += ".jpg"
    os.makedirs(MEDIA_DIR, exist_ok=True)
    dst = os.path.join(MEDIA_DIR, name)
    if not os.path.exists(dst):
        # pbs.twimg.com refuses Python's default user agent with a 403
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
        with open(dst, "wb") as f:
            f.write(body)
    return [name], video


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
            kept = {k: v for k, v in cache.get(r["post_id"], {}).items()
                    if k in MEDIA_KEYS}
            cache[r["post_id"]] = dict({
                "id": r["post_id"],
                "date": r["created_at"][:10],
                "text": txt,
                "fav": int(eng.get("likes") or 0),
                "rt": int(eng.get("shares") or 0),
                "url": r.get("url")
                or "https://x.com/mertesakib/status/" + r["post_id"],
            }, **kept)
        url = d.get("next")

    looked = 0
    recent = (datetime.date.today()
              - datetime.timedelta(days=REPULL_DAYS)).isoformat()
    for t in cache.values():
        if t.get("deleted"):
            continue
        if t.get("media_checked"):
            # he sometimes deletes a post days later, and Typefully keeps it
            if t["date"] >= recent:
                try:
                    if deleted_on_x(t["id"]):
                        t["deleted"] = True
                        print("tweets_live: %s was deleted on X, dropping it" % t["id"])
                except Exception:
                    pass
                time.sleep(0.2)
            continue
        try:
            t["media"], t["video"] = fetch_media(t["id"])
            t["media_checked"] = True
            looked += 1
        except Deleted:
            t["deleted"] = t["media_checked"] = True
            print("tweets_live: %s was deleted on X, dropping it" % t["id"])
        except Exception as e:
            # left unchecked, so the next run tries again
            print("warn: no media lookup for %s (%s)" % (t["id"], e))
        time.sleep(0.2)
    if looked:
        print("tweets_live: looked up media for %d posts" % looked)

    rows = sorted(cache.values(), key=lambda t: t["date"])
    with open(OUT, "w") as f:
        json.dump(rows, f, indent=1)
    print("tweets_live: %d cached (+%d new), through %s"
          % (len(rows), added, rows[-1]["date"] if rows else "-"))


main()
