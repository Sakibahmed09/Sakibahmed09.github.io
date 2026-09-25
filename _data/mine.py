#!/usr/bin/env python3
"""Mine the X archive + LinkedIn cache into per-venture candidate pools."""
import json, re, os, sqlite3, glob, html

OUT = os.path.dirname(os.path.abspath(__file__))
LI_DB = os.path.expanduser("~/.linkedin-cache/posts.db")

# The X archive is copied into _data/archive rather than read from ~/Downloads:
# macOS keeps Downloads off-limits to anything launchd starts, so the weekly
# job could never see it and failed every Monday. Downloads is only a fallback
# for a hand-run session.
ARCHIVE_DIR = os.path.join(OUT, "archive")
if not os.path.isdir(ARCHIVE_DIR):
    found = sorted(glob.glob(os.path.expanduser("~/Downloads/twitter-*/data")))
    ARCHIVE_DIR = found[-1] if found else None
# X splits a big archive into tweets.js plus tweets-part1.js and so on, and
# the parts barely overlap, so every part gets read.
ARCHIVE_FILES = sorted(glob.glob(os.path.join(ARCHIVE_DIR, "tweets*.js"))) if ARCHIVE_DIR else []

VENTURES = {
    "minideed":    [r"\bminideed\b", r"mini deed"],
    "simplysmashed": [r"simply\s*smashed", r"simply_smashed", r"burger joint",
                      r"\bsmashed\b"],
    "psk":         [r"peruvian", r"\bPSK\b", r"PSK_UKI", r"green sauce",
                    r"chicken and rice"],
    "draper":      [r"content is product", r"product is content",
                    r"founder.led growth", r"building in public",
                    r"ghostwrit", r"\bdraper\b", r"personal brand",
                    r"\bslop\b", r"distribution"],
    "simplyclo":   [r"simply\s*clo", r"simplyclo", r"liberation collection",
                    r"\bhoodie\b"],
    "vibenasheeds": [r"vibenasheed", r"\bnasheed"],
    "dhikry":      [r"\bdhikry\b", r"\bdhikr\b", r"\badhkar\b"],
    "bilal":       [r"\bbilal\b", r"masjid.{0,15}(time|display|tv)",
                    r"\bathan\b", r"\badhan\b"],
    "lofi":        [r"lofi muslim", r"lofimuslim", r"\blofi\b"],
    # huffadh and hifz alone pulled in Simply Smashed's Quran Revision Project
    # posts, and put a Barking family's sons on the school's page
    "foundation":  [r"simply foundation", r"simplyfoundatn",
                    r"boarding school", r"hifdh school"],
    "pouches":     [r"phone pouch", r"pouches", r"khutbah.{0,30}phone"],
}
# a 2016 tweet about someone else's boarding school is not the Foundation
SINCE = {"foundation": "2022-01-01"}


def tidy(t):
    """Collapse runs of spaces but KEEP the line breaks: the shape of a post
    is part of what he wrote."""
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r" *\n *", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def media_index():
    """tweet id -> its image files and its video files in the archive"""
    import collections
    d = os.path.join(ARCHIVE_DIR, "tweets_media") if ARCHIVE_DIR else ""
    images, videos = collections.defaultdict(list), collections.defaultdict(list)
    if os.path.isdir(d):
        for f in os.listdir(d):
            if f.lower().endswith((".jpg", ".png")):
                images[f.split("-")[0]].append(f)
            elif f.lower().endswith(".mp4"):
                videos[f.split("-")[0]].append(f)
    return images, videos


MEDIA, VIDEOS = media_index()


def media_for(tweet_id):
    """First photo if the post has one; otherwise its video, which build.py
    turns into a still."""
    if MEDIA.get(tweet_id):
        return sorted(MEDIA[tweet_id])[:1], False
    if VIDEOS.get(tweet_id):
        return sorted(VIDEOS[tweet_id])[:1], True
    return [], False


MONTHS = dict(Jan=1, Feb=2, Mar=3, Apr=4, May=5, Jun=6,
              Jul=7, Aug=8, Sep=9, Oct=10, Nov=11, Dec=12)


def iso(d):
    # "Tue Jan 30 18:11:23 +0000 2024"
    p = d.split()
    return "%s-%02d-%02d" % (p[5], MONTHS[p[1]], int(p[2]))


def deleted_ids():
    """Posts he has since deleted on X, which pull_tweets.py spots and flags."""
    live = os.path.join(OUT, "tweets_live.json")
    if not os.path.exists(live):
        return set()
    return {t["id"] for t in json.load(open(live)) if t.get("deleted")}


def load_tweets():
    gone = deleted_ids()
    data = []
    for f in ARCHIVE_FILES:
        raw = open(f, encoding="utf-8").read()
        data += json.loads(raw[raw.index("["):])
    out, seen = [], set()
    for row in data:
        t = row.get("tweet", row)
        if t["id_str"] in seen or t["id_str"] in gone:
            continue
        seen.add(t["id_str"])
        txt = html.unescape(t.get("full_text", ""))
        if txt.startswith("RT @"):
            continue
        if t.get("in_reply_to_status_id_str") and not txt.startswith("@mertesakib"):
            # keep self-threads only
            if t.get("in_reply_to_user_id_str") != "355236713":
                continue
        media, video = media_for(t["id_str"])
        out.append({
            "media": media,
            "video": video,
            "id": t["id_str"],
            "date": iso(t["created_at"]),
            "text": txt,
            "fav": int(t.get("favorite_count", 0)),
            "rt": int(t.get("retweet_count", 0)),
        })

    # The archive download stops where it was taken. tweets_live.json, kept fresh
    # by pull_tweets.py, carries the record forward.
    live = os.path.join(OUT, "tweets_live.json")
    if os.path.exists(live):
        have = {t["id"] for t in out}
        for t in json.load(open(live)):
            if t["id"] not in have and t["id"] not in gone:
                media, video = media_for(t["id"])
                out.append(dict(t, media=t.get("media") or media,
                                video=bool(t.get("video") or video)))
    return out


def main():
    tweets = load_tweets()
    print("tweets parsed:", len(tweets))

    li = []
    if os.path.exists(LI_DB):
        con = sqlite3.connect(LI_DB)
        con.row_factory = sqlite3.Row
        # He renamed his LinkedIn vanity to mertesakib in Aug 2026. Older rows
        # are still filed under the old handle, so read both and dedupe.
        for r in con.execute(
                "select posted_at, reactions, comments, reposts, url, text "
                "from posts where username in ('sakib-ahmed1','mertesakib') "
                "and author_name='Sakib Ahmed' and text != '' order by posted_at"):
            li.append({
                "date": r["posted_at"][:10],
                "text": tidy(r["text"] or ""),
                "fav": r["reactions"], "comments": r["comments"],
                "rt": r["reposts"], "url": r["url"], "src": "li",
            })
        con.close()
        seen, uniq = set(), []
        for p in li:
            k = p["url"] or (p["date"] + p["text"][:60])
            if k not in seen:
                seen.add(k)
                uniq.append(p)
        li = uniq
    print("linkedin posts:", len(li))

    buckets = {}
    for name, pats in VENTURES.items():
        rx = re.compile("|".join(pats), re.I)
        tw = [dict(t, src="x",
                   url="https://x.com/mertesakib/status/" + t["id"])
              for t in tweets if rx.search(t["text"])]
        lp = [p for p in li if rx.search(p["text"])]
        rows = sorted((r for r in tw + lp if r["date"] >= SINCE.get(name, "")),
                      key=lambda r: r["date"])
        buckets[name] = rows
        top = sorted(rows, key=lambda r: -r["fav"])[:6]
        print("\n=== %s: %d posts (%d x, %d li) ==="
              % (name, len(rows), len(tw), len(lp)))
        for r in top:
            print("  %s [%s] %4d  %s" % (r["date"], r["src"], r["fav"],
                                         r["text"][:95].replace("\n", " ")))

    # a searchable pool for posts that never name the venture
    pool = li + [dict(t, src="x",
                      url="https://x.com/mertesakib/status/" + t["id"])
                 for t in tweets if t["fav"] >= 5]
    buckets["_all"] = sorted(pool, key=lambda r: r["date"])

    with open(os.path.join(OUT, "buckets.json"), "w") as f:
        json.dump(buckets, f, indent=1)
    print("\nwrote buckets.json (pool: %d)" % len(buckets["_all"]))


main()
