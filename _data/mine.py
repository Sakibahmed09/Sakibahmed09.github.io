#!/usr/bin/env python3
"""Mine the X archive + LinkedIn cache into per-venture candidate pools."""
import json, re, os, sqlite3, glob, html

ARCHIVE = glob.glob(os.path.expanduser(
    "~/Downloads/twitter-*/data/tweets.js"))[0]
LI_DB = os.path.expanduser("~/.linkedin-cache/posts.db")
OUT = os.path.dirname(os.path.abspath(__file__))

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
    "dhikry":      [r"\bdhikry\b", r"\bdhikr\b"],
    "bilal":       [r"\bbilal\b", r"masjid.{0,15}(time|display|tv)",
                    r"\bathan\b", r"\badhan\b"],
    "lofi":        [r"lofi muslim", r"lofimuslim", r"\blofi\b"],
    "foundation":  [r"simply foundation", r"simplyfoundatn", r"\bhuffadh\b",
                    r"\bhifz\b", r"boarding school"],
    "pouches":     [r"phone pouch", r"pouches", r"khutbah.{0,30}phone"],
}


def media_index():
    """tweet id -> its image files in the archive"""
    import collections
    dirs = glob.glob(os.path.expanduser("~/Downloads/twitter-*/data/tweets_media"))
    idx = collections.defaultdict(list)
    if dirs:
        for f in os.listdir(dirs[0]):
            if f.lower().endswith((".jpg", ".png")):
                idx[f.split("-")[0]].append(f)
    return idx


MEDIA = media_index()


def load_tweets():
    raw = open(ARCHIVE, encoding="utf-8").read()
    raw = raw[raw.index("["):]
    data = json.loads(raw)
    out = []
    for row in data:
        t = row.get("tweet", row)
        txt = html.unescape(t.get("full_text", ""))
        if txt.startswith("RT @"):
            continue
        if t.get("in_reply_to_status_id_str") and not txt.startswith("@mertesakib"):
            # keep self-threads only
            if t.get("in_reply_to_user_id_str") != "355236713":
                continue
        out.append({
            "media": sorted(MEDIA.get(t["id_str"], []))[:1],
            "id": t["id_str"],
            "date": t["created_at"],
            "text": txt,
            "fav": int(t.get("favorite_count", 0)),
            "rt": int(t.get("retweet_count", 0)),
        })
    return out


MONTHS = dict(Jan=1, Feb=2, Mar=3, Apr=4, May=5, Jun=6,
              Jul=7, Aug=8, Sep=9, Oct=10, Nov=11, Dec=12)


def iso(d):
    # "Tue Jan 30 18:11:23 +0000 2024"
    p = d.split()
    return "%s-%02d-%02d" % (p[5], MONTHS[p[1]], int(p[2]))


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
                "text": " ".join((r["text"] or "").split()),
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
        tw = [dict(t, date=iso(t["date"]), src="x",
                   url="https://x.com/mertesakib/status/" + t["id"])
              for t in tweets if rx.search(t["text"])]
        lp = [p for p in li if rx.search(p["text"])]
        rows = sorted(tw + lp, key=lambda r: r["date"])
        buckets[name] = rows
        top = sorted(rows, key=lambda r: -r["fav"])[:6]
        print("\n=== %s: %d posts (%d x, %d li) ==="
              % (name, len(rows), len(tw), len(lp)))
        for r in top:
            print("  %s [%s] %4d  %s" % (r["date"], r["src"], r["fav"],
                                         r["text"][:95].replace("\n", " ")))

    # a searchable pool for posts that never name the venture
    pool = li + [dict(t, date=iso(t["date"]), src="x",
                      url="https://x.com/mertesakib/status/" + t["id"])
                 for t in tweets if t["fav"] >= 5]
    buckets["_all"] = sorted(pool, key=lambda r: r["date"])

    with open(os.path.join(OUT, "buckets.json"), "w") as f:
        json.dump(buckets, f, indent=1)
    print("\nwrote buckets.json (pool: %d)" % len(buckets["_all"]))


main()
