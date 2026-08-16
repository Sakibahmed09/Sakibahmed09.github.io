#!/usr/bin/env python3
"""Generate the venture pages: retrospective spine + pasted-in real posts."""
import json, os, re, html, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUCKETS = json.load(open(os.path.join(HERE, "buckets.json")))
SPEC = json.load(open(os.path.join(HERE, "ventures.json")))

BUCKET_ALIAS = {"simply-smashed": "simplysmashed", "psk": "psk",
                "minideed": "minideed", "draper": "draper"}

HEAD = """<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Sakib Ahmed</title>
<meta name="description" content="{stand_plain}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{stand_plain}">
<meta property="og:type" content="article">
<meta property="og:image" content="../../assets/og.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#f7f4ec" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#17150f" media="(prefers-color-scheme: dark)">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%23bf3a2a'/%3E%3Ctext x='32' y='42' font-family='Georgia,serif' font-size='34' fill='%23faf7f0' text-anchor='middle'%3E%D8%B3%3C/text%3E%3C/svg%3E">
<script>(function(){{document.documentElement.classList.add("js");var q=new URLSearchParams(location.search).get("theme");var t=q||localStorage.getItem("theme");if(t==="dark"||t==="light")document.documentElement.dataset.theme=t;}})();</script>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:ital,wght@0,400..700;1,400..600&family=Reenie+Beanie&display=swap" >
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Amiri&text=%20%D8%A3%D8%A7%D8%A8%D8%AD%D8%AF%D8%B1%D8%B3%D9%83%D9%84%D9%85%D9%86%D9%87&display=swap">
<link rel="stylesheet" href="../../assets/site.css">
</head>
<body>

<main class="page article venture">

  <a class="crumb rise" style="--i:0" href="../"><span class="back">←</span> Ventures</a>

  <header class="article-head rise" style="--i:1">
    <h1>{title}</h1>
    <p class="when">{years}</p>
    <p class="stand">{stand}</p>{link}
  </header>

  <ul class="proof rise" style="--i:2">
{proof}
  </ul>

  <p class="lede rise" style="--i:3">What I say about it now, and what I was actually posting at the time.</p>
"""

LANE_HEAD = """
  <section class="section feed-wrap" data-feed="{feed}">
    <h2>Lately</h2>
    <p class="menu-note">{note}</p>
    <div class="feed">
"""

LANE_FOOT = """    </div>
    <div class="feed-end" aria-hidden="true"></div>
  </section>
"""

PREVNEXT = """
  <nav class="prevnext" aria-label="Other ventures">
{links}
  </nav>
"""

FOOT = """
  <footer class="foot">
    <span class="clock" id="clock" title="Europe/London">&nbsp;</span>
    <nav class="links" aria-label="Elsewhere">
      <a class="u" href="../">Ventures</a>
      <a class="u" href="../../">Home</a>
    </nav>
    <button class="moon" id="moon" aria-pressed="false" aria-label="Toggle dark mode" title="Toggle dark mode">
      <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true">
        <g class="rays">
          <line class="ray" x1="11" y1="1.5" x2="11" y2="4"></line>
          <line class="ray" x1="11" y1="18" x2="11" y2="20.5"></line>
          <line class="ray" x1="1.5" y1="11" x2="4" y2="11"></line>
          <line class="ray" x1="18" y1="11" x2="20.5" y2="11"></line>
          <line class="ray" x1="4.3" y1="4.3" x2="6.1" y2="6.1"></line>
          <line class="ray" x1="15.9" y1="15.9" x2="17.7" y2="17.7"></line>
          <line class="ray" x1="4.3" y1="17.7" x2="6.1" y2="15.9"></line>
          <line class="ray" x1="15.9" y1="6.1" x2="17.7" y2="4.3"></line>
        </g>
        <mask id="bite-mask"><rect width="22" height="22" fill="white"></rect>
          <circle class="bite" cx="11" cy="11" r="5.5" fill="black"></circle></mask>
        <circle class="core" cx="11" cy="11" r="4.5" mask="url(#bite-mask)"></circle>
      </svg>
    </button>
    <div class="player" id="player" hidden>
      <button class="pp" id="pp" aria-label="Play the beats"><span class="tri" aria-hidden="true"></span></button>
      <span class="track" id="track">Lofi Muslim &#183; Open Road</span>
      <span class="bar" aria-hidden="true"><i id="bar"></i></span>
    </div>
  </footer>

</main>

<div class="veil" id="veil" hidden>
  <div class="palette" role="dialog" aria-label="Command palette">
    <input id="palette-input" type="text" placeholder="Where to?" autocomplete="off" spellcheck="false"
           role="combobox" aria-expanded="true" aria-controls="palette-list">
    <ul id="palette-list" role="listbox"></ul>
  </div>
</div>
<div class="toast" id="toast" role="status"></div>
<script src="../../assets/site.js" defer></script>
</body>
</html>
"""

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def pretty(d):
    y, m, dd = d.split("-")
    return "%d %s %s" % (int(dd), MONTHS[int(m) - 1], y)


def clean(t):
    t = re.sub(r"https://t\.co/\w+", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


MEDIA_SRC = glob.glob(os.path.expanduser(
    "~/Downloads/twitter-*/data/tweets_media"))
MEDIA_OUT = os.path.join(ROOT, "assets", "media")
FEED_OUT = os.path.join(ROOT, "assets", "feed")


def stage_image(fname):
    """Copy a photo out of the archive, downscaled for the web.
    Returns the site-relative filename, or None if it isn't there."""
    if not MEDIA_SRC:
        return None
    src = os.path.join(MEDIA_SRC[0], fname)
    if not os.path.exists(src):
        print("   !! missing photo: %s" % fname)
        return None
    os.makedirs(MEDIA_OUT, exist_ok=True)
    out_name = fname.split("-")[0] + ".jpg"
    dst = os.path.join(MEDIA_OUT, out_name)
    if not os.path.exists(dst):
        try:
            from PIL import Image
            im = Image.open(src)
            im = im.convert("RGB")
            w = 760
            if im.width > w:
                im = im.resize((w, round(im.height * w / im.width)),
                               Image.LANCZOS)
            im.save(dst, quality=82, optimize=True, progressive=True)
        except Exception as e:
            print("   !! could not stage %s (%s)" % (fname, e))
            return None
    return out_name


def card(p, i, img=None, alt=""):
    src = p.get("src", "x")
    glyph = "𝕏" if src == "x" else "in"
    where = "X" if src == "x" else "LinkedIn"
    txt = clean(p["text"])
    limit = 300
    clipped = len(txt) > limit
    if clipped:
        cut = txt[:limit]
        cut = cut[:cut.rfind(" ")]
        txt = cut + "…"
    n = p.get("fav", 0)
    metric = "reactions" if src == "li" else "likes"
    bits = []
    if n:
        bits.append("%s %s" % ("{:,}".format(n), metric))
    if p.get("rt"):
        bits.append("%s reposts" % "{:,}".format(p["rt"]))
    shot = ""
    if img:
        shot = ('\n        <img class="shot" src="../../assets/media/%s" alt="%s" '
                'loading="lazy" decoding="async">' % (img, html.escape(alt)))
    # a real post, wearing its own platform's clothes
    if src == "x":
        who = ('<span class="name">sakib</span>'
               '<span class="handle">@mertesakib</span>')
        mark = "𝕏"
    else:
        who = ('<span class="name">Sakib Ahmed</span>'
               '<span class="handle">Co-founder of Draper · Own your distribution</span>')
        mark = "in"
    return """    <article class="post {kind}">
      <header>
        <img class="pfp" src="../../assets/media/avatar.jpg" alt="" loading="lazy" decoding="async">
        <span class="who">{who}</span>
        <span class="mark" aria-hidden="true">{mark}</span>
      </header>
      <div class="body">
        <p>{txt}</p>{shot}
      </div>
      <footer>
        <time>{date}</time>
        <span class="stats">{num}</span>
        <a class="open" data-out href="{url}">{where}</a>
      </footer>
    </article>""".format(kind=src, who=who, mark=mark, txt=html.escape(txt),
                         shot=shot, date=pretty(p["date"]),
                         num=" · ".join(bits), url=p.get("url", "#"),
                         where="Open" if src == "x" else "Open")


def lane_row(p, label=None):
    """A compact row for the self-updating lane."""
    txt = clean(p["text"])
    if len(txt) > 132:
        cut = txt[:132]
        txt = cut[:cut.rfind(" ")] + "…"
    n = p.get("fav", 0)
    tag = ('<span class="tag">%s</span>' % label) if label else ""
    return ("""      <li>
        <a href="{url}" data-out>
          <span class="when"><span class="src" aria-hidden="true">{glyph}</span>{date}</span>
          <span class="txt">{txt}{tag}</span>
          <span class="num">{num}</span>
        </a>
      </li>""").format(
        url=p.get("url", "#"), glyph="𝕏" if p.get("src") == "x" else "in",
        date=pretty(p["date"]), txt=html.escape(txt), tag=tag,
        num="{:,}".format(n) if n else "")


def key_of(p):
    return p.get("url") or (p["date"] + p["text"][:50])


def crosspost_key(p):
    """He posts the same thing to X and LinkedIn. Same day, same opening
    words, means one story told twice."""
    words = re.sub(r"[^a-z0-9 ]", "", clean(p["text"]).lower()).split()
    return (p["date"], " ".join(words[:7]))


def dedupe(rows):
    """Collapse cross-posts, keeping whichever version travelled further."""
    best = {}
    for p in rows:
        k = crosspost_key(p)
        if k not in best or p.get("fav", 0) > best[k].get("fav", 0):
            best[k] = p
    return sorted(best.values(), key=lambda r: r["date"], reverse=True)


def find(bucket, needle):
    """Search the venture bucket first, then the whole corpus: some of the
    best posts never mention the venture by name."""
    key = clean(needle).lower()[:60]
    for pool in (bucket, BUCKETS.get("_all", [])):
        best = None
        for p in pool:
            if key in clean(p["text"]).lower():
                # prefer the version with more engagement (LI/X duplicates)
                if best is None or p.get("fav", 0) > best.get("fav", 0):
                    best = p
        if best:
            return best
    return None


def main():
    misses = []
    freshest = {}
    for slug, v in SPEC.items():
        bucket = BUCKETS.get(v.get("bucket") or BUCKET_ALIAS.get(slug, slug), [])
        used = set()
        proof = "\n".join(
            '    <li><b>%s</b><span>%s</span></li>' % (a, b) for a, b in v["proof"])
        link = ""
        if v.get("link"):
            href, label = v["link"]
            link = ('\n    <p class="live"><a class="u" data-out href="%s">%s</a></p>'
                    % (href, label))
        out = [HEAD.format(title=v["title"], years=v["years"], stand=v["stand"],
                           stand_plain=re.sub("<[^>]+>", "", v["stand"]),
                           proof=proof, link=link)]
        i = 0
        for beat in v["beats"]:
            out.append('\n  <div class="beat">')
            out.append('    <p class="say">%s</p>' % beat["say"])
            for entry in beat.get("posts", []):
                # a post is either a match string, or a dict that also opts
                # this one clipping into showing its photo
                if isinstance(entry, dict):
                    needle, img, alt = entry["m"], entry.get("img"), entry.get("alt", "")
                else:
                    needle, img, alt = entry, None, ""
                p = find(bucket, needle)
                if not p:
                    misses.append((slug, needle))
                    continue
                used.add(key_of(p))
                # if the post carried a photo, show it: an image-led post with
                # the image missing is just a headline with nothing under it
                if not img and p.get("media"):
                    img = p["media"][0]
                    alt = alt or "Photo from the post."
                out.append(card(p, i, stage_image(img) if img else None, alt))
                i += 1
            out.append('  </div>')

        # the self-updating lane: everything not already in the spine
        rest = dedupe([p for p in bucket if key_of(p) not in used])
        if rest:
            os.makedirs(FEED_OUT, exist_ok=True)
            feed = [{"d": r["date"], "t": clean(r["text"]), "s": r.get("src", "x"),
                     "u": r.get("url", ""), "f": r.get("fav", 0),
                     "r": r.get("rt", 0),
                     "m": stage_image(r["media"][0]) if r.get("media") else None}
                    for r in rest]
            with open(os.path.join(FEED_OUT, slug + ".json"), "w") as fh:
                json.dump(feed, fh)
            out.append(LANE_HEAD.format(
                feed="../../assets/feed/" + slug + ".json",
                note="Everything else I&#8217;ve posted about it, newest first. "
                     "Keeps going as you scroll."))
            for n, r in enumerate(rest[:6]):
                out.append(card(r, n,
                                stage_image(r["media"][0]) if r.get("media") else None,
                                "Photo from the post."))
            out.append(LANE_FOOT)
            freshest[slug] = (v["title"], rest[:6])
        # walkable in order, and the swipe uses these as its targets
        order = list(SPEC.keys())
        i_here = order.index(slug)
        pn = []
        if i_here > 0:
            prev = order[i_here - 1]
            pn.append('    <a class="prev" rel="prev" href="../%s/">'
                      '<span class="dir">Previous</span>'
                      '<span class="t">%s</span></a>'
                      % (prev, SPEC[prev]["title"]))
        if i_here < len(order) - 1:
            nxt = order[i_here + 1]
            pn.append('    <a class="next" rel="next" href="../%s/">'
                      '<span class="dir">Next</span>'
                      '<span class="t">%s</span></a>'
                      % (nxt, SPEC[nxt]["title"]))
        if pn:
            out.append(PREVNEXT.format(links="\n".join(pn)))
        out.append(FOOT)
        d = os.path.join(ROOT, "ventures", slug)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w").write("\n".join(out))
        print("built ventures/%s (%d clippings)" % (slug, i))

    # Front page: his own feed, newest first, streamed on scroll
    newest = dedupe(BUCKETS.get("_all", []))
    os.makedirs(FEED_OUT, exist_ok=True)
    seen, feed = set(), []
    for r in newest:
        k = key_of(r)
        if k in seen or not clean(r["text"]):
            continue
        seen.add(k)
        feed.append({"d": r["date"], "t": clean(r["text"]), "s": r.get("src", "x"),
                     "u": r.get("url", ""), "f": r.get("fav", 0),
                     "r": r.get("rt", 0),
                     "m": stage_image(r["media"][0]) if r.get("media") else None})
        if len(feed) >= 400:
            break
    with open(os.path.join(FEED_OUT, "all.json"), "w") as fh:
        json.dump(feed, fh)

    home = os.path.join(ROOT, "index.html")
    html_s = open(home).read()
    cards = []
    for n, r in enumerate(newest[:6]):
        cards.append(card(r, n,
                          stage_image(r["media"][0]) if r.get("media") else None,
                          "Photo from the post.")
                     .replace("../../assets/", "assets/"))
    block = ('\n  <section class="section feed-wrap" data-feed="assets/feed/all.json"'
             ' style="--i:11">\n    <h2>Lately</h2>\n'
             '    <p class="menu-note">Everything I post, in one place. Keeps going as you scroll.</p>\n'
             '    <div class="feed">\n' + "\n".join(cards) +
             '\n    </div>\n    <div class="feed-end" aria-hidden="true"></div>\n  </section>\n')
    a, b_ = "<!-- LATELY:START -->", "<!-- LATELY:END -->"
    html_s = html_s[:html_s.index(a) + len(a)] + block + html_s[html_s.index(b_):]
    open(home, "w").write(html_s)
    print("front page feed: %d posts, newest %s" % (len(feed), feed[0]["d"]))

    if misses:
        print("\n!! COULD NOT MATCH:")
        for s, n in misses:
            print("   [%s] %s" % (s, n[:70]))


main()
