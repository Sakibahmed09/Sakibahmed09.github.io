#!/usr/bin/env python3
"""Top up tweets_live.json from @mertesakib's timeline on fxtwitter.

This is the forward continuation of the X archive download, which stops at
15 Apr 2026. Overlap is deduped by status id. Typefully's analytics feed did
this job until it was dropped from their public API in Sep 2026.
"""
import json, os, datetime, time, urllib.error, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tweets_live.json")
# beside the archive's own photos, so mine.py and build.py find them the same way
MEDIA_DIR = os.path.join(HERE, "archive", "tweets_media")
MEDIA_KEYS = ("media", "video", "media_checked", "deleted")


class Deleted(Exception):
    pass


HANDLE = "mertesakib"
FLOOR = "2026-04-01"
REPULL_DAYS = 30  # re-read a trailing window so engagement counts settle
MAX_PAGES = 60
BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/130 Safari/537.36")


def timeline_page(cursor=None):
    """fxtwitter answers about one call in three with an empty 404, so retry."""
    url = ("https://api.fxtwitter.com/2/profile/%s/statuses?count=50" % HANDLE)
    if cursor:
        url += "&cursor=" + urllib.parse.quote(cursor)
    req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
    for attempt in range(8):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)
        except urllib.error.HTTPError as e:
            d = json.load(e)
        if d.get("results"):
            return d
        time.sleep(2 + 2 * attempt)
    raise RuntimeError("fxtwitter timeline kept coming back empty")


def own_post(r):
    author = ((r.get("author") or {}).get("screen_name") or "").lower()
    if author != HANDLE or r.get("reposted_by"):
        return False
    to = ((r.get("replying_to") or {}).get("screen_name") or HANDLE).lower()
    return to == HANDLE


def deleted_on_x(tweet_id):
    """A cached post stays here after he deletes it; X's embed endpoint
    answers with a tombstone instead."""
    req = urllib.request.Request(
        "https://cdn.syndication.twimg.com/tweet-result?id=%s&token=a" % tweet_id,
        headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.load(r)
    return d.get("__typename") == "TweetTombstone"


def fetch_media(tweet_id):
    """Ask fxtwitter (free, no key) for the post's first photo, or the still
    for a video, and keep a copy."""
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
    cache = {}
    if os.path.exists(OUT):
        cache = {t["id"]: t for t in json.load(open(OUT))}

    start = FLOOR
    if cache:
        newest = max(t["date"] for t in cache.values())
        start = max(FLOOR, (datetime.date.fromisoformat(newest)
                            - datetime.timedelta(days=REPULL_DAYS)).isoformat())

    added = 0
    cursor = None
    for _ in range(MAX_PAGES):
        d = timeline_page(cursor)
        dates = []
        for r in d["results"]:
            date = datetime.datetime.utcfromtimestamp(
                r["created_timestamp"]).date().isoformat()
            dates.append(date)
            txt = (r.get("text") or "").strip()
            if not txt or not own_post(r) or date < start:
                continue
            if r["id"] not in cache:
                added += 1
            kept = {k: v for k, v in cache.get(r["id"], {}).items()
                    if k in MEDIA_KEYS}
            cache[r["id"]] = dict({
                "id": r["id"],
                "date": date,
                "text": txt,
                "fav": int(r.get("likes") or 0),
                "rt": int(r.get("reposts") or 0),
                "url": "https://x.com/%s/status/%s" % (HANDLE, r["id"]),
            }, **kept)
        cursor = (d.get("cursor") or {}).get("bottom")
        # reposts and the pinned post carry old dates, so stop only once the
        # newest post on a page is already older than the window
        if not cursor or max(dates) < start:
            break
        time.sleep(1)

    looked = 0
    recent = (datetime.date.today()
              - datetime.timedelta(days=REPULL_DAYS)).isoformat()
    for t in cache.values():
        if t.get("deleted"):
            continue
        if t.get("media_checked"):
            # he sometimes deletes a post days later, after it was cached
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
