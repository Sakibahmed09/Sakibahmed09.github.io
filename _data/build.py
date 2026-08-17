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
<meta property="og:image" content="https://sakib.lol/assets/og-v2.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#f7f4ec" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#17150f" media="(prefers-color-scheme: dark)">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%23bf3a2a'/%3E%3Ctext x='32' y='42' font-family='Georgia,serif' font-size='34' fill='%23faf7f0' text-anchor='middle'%3E%D8%B3%3C/text%3E%3C/svg%3E">
<script>(function(){{document.documentElement.classList.add("js");var q=new URLSearchParams(location.search).get("theme");var t=q||localStorage.getItem("theme");if(t==="dark"||t==="light")document.documentElement.dataset.theme=t;}})();</script>
<link rel="preload" href="../../assets/fonts/schibsted-grotesk-normal.woff2" as="font" type="font/woff2" crossorigin>
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
{clients}
  <p class="lede rise" style="--i:4">{lede}</p>
"""

LANE_HEAD = """
  <section class="section feed-wrap" data-feed="{feed}">
    <h2>Lately</h2>
    <p class="menu-note">{note}</p>
    <div class="feed">
"""

LANE_FOOT = """      <div class="feed-end"></div>
    </div>
  </section>
"""

TRACKLIST = """
  <section class="section tracks-wrap">
    <h2>Listen</h2>
    <p class="menu-note">{note}</p>
    <ol class="tracks">
{rows}
    </ol>
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


def client_block(v):
    """Named, checkable proof. Quotes and outcomes as published on draperhq.com."""
    rows = v.get("clients")
    if not rows:
        return ""
    li = "\n".join(
        '      <li>\n'
        '        <p class="cl-said">&#8220;%s&#8221;</p>\n'
        '        <p class="cl-who"><a class="u" data-out href="%s">%s</a>'
        '<span class="cl-at">%s</span><span class="cl-win">%s</span></p>\n'
        '      </li>' % (clean(r["said"]), r["url"], html.escape(r["who"]),
                         html.escape(r["at"]), html.escape(r["win"]))
        for r in rows)
    ask = '\n    <p class="cl-ask">%s</p>' % v["ask"] if v.get("ask") else ""
    return ('\n  <section class="clients rise" style="--i:3">\n'
            '    <h2 class="cl-head">Who says so</h2>\n'
            '    <ul>\n%s\n    </ul>%s\n  </section>\n' % (li, ask))


def drop_near_dupes(posts):
    """He reposts a tweet with a word changed and the archive keeps both.
    Printed side by side they read as a mistake, so keep the one that did
    better and drop the twin."""
    keep = []
    for p in sorted(posts, key=lambda x: -(x.get("fav") or 0)):
        words = set(flat(p["text"]).split())
        if not words:
            keep.append(p); continue
        twin = False
        for k in keep:
            kw = set(flat(k["text"]).split())
            if not kw: continue
            small = words if len(words) < len(kw) else kw
            if len(words & kw) / len(small) > 0.8:
                twin = True; break
        if not twin: keep.append(p)
    order = {id(x): i for i, x in enumerate(posts)}
    return sorted(keep, key=lambda x: order[id(x)])


def clean(t):
    """Strip the t.co noise, keep the line breaks."""
    t = re.sub(r"https://t\.co/\w+", "", t)
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r" *\n *", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def flat(t):
    """One-line version, for matching and for meta tags."""
    return re.sub(r"\s+", " ", clean(t)).strip()


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
    # The post used to be cut at 300 characters, which landed before the payoff
    # on most of them: the reader got the setup and had to leave to find out
    # what happened. Send the whole thing and let the page fold it instead.
    long_post = len(txt) > 320
    anchor = "p-" + re.sub(r"[^a-z0-9]+", "", (p.get("url") or "")[-14:].lower()) or "p"
    n = p.get("fav", 0)
    metric = "reactions" if src == "li" else "likes"
    bits = []
    if n:
        bits.append("%s %s" % ("{:,}".format(n), metric if n != 1 else metric[:-1]))
    if p.get("rt"):
        bits.append("%s repost%s" % ("{:,}".format(p["rt"]), "" if p["rt"] == 1 else "s"))
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
    if src == "x":
        name, handle, mark = "sakib", "@mertesakib", "\U0001D54F"
    else:
        # the same headline the venture cards and the scrolled-in cards use,
        # otherwise one feed shows two different handles
        name, handle, mark = "Sakib Ahmed", "Co-founder of Draper · Own your distribution", "in"
    return """    <article class="post {kind}" id="{anchor}">
      <img class="pfp" src="../../assets/media/avatar.jpg" alt="" loading="lazy" decoding="async">
      <div class="col">
        <header>
          <span class="name">{name}</span>
          <span class="handle">{handle}</span>
          <span class="sep">&#183;</span>
          <time>{date}</time>
          <span class="mark" aria-hidden="true">{mark}</span>
        </header>
        <div class="body{fold}">
          <p>{txt}</p>{shot}
        </div>
        <footer>
          <span class="stats">{num}</span>
          <a class="open" data-out href="{url}">Open</a>
        </footer>
      </div>
    </article>""".format(kind=src, anchor=anchor, fold=" folded" if long_post else "", name=name, handle=handle, mark=mark,
                         txt=html.escape(txt), shot=shot, date=pretty(p["date"]),
                         num=" &#183; ".join(bits), url=p.get("url", "#"))


def lane_row(p, label=None):
    """A compact row for the self-updating lane."""
    txt = flat(p["text"])
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
    words = re.sub(r"[^a-z0-9 ]", "", flat(p["text"]).lower()).split()
    return (p["date"], " ".join(words[:7]))


def dedupe(rows):
    """Collapse cross-posts, keeping whichever version travelled further."""
    best = {}
    for p in rows:
        k = crosspost_key(p)
        if k not in best or p.get("fav", 0) > best[k].get("fav", 0):
            best[k] = p
    return sorted(best.values(), key=lambda r: r["date"], reverse=True)


SEARCH = []


def find(bucket, needle):
    """Search the venture bucket first, then the whole corpus: some of the
    best posts never mention the venture by name."""
    key = flat(needle).lower()[:60]
    for pool in (bucket, BUCKETS.get("_all", [])):
        best = None
        for p in pool:
            if key in flat(p["text"]).lower():
                # prefer the version with more engagement (LI/X duplicates)
                if best is None or p.get("fav", 0) > best.get("fav", 0):
                    best = p
        if best:
            return best
    return None


def write_site_files(feed):
    """sitemap, robots and a real RSS feed — the marks of a site that is kept."""
    import xml.sax.saxutils as sx
    BASE = "https://sakib.lol"
    paths = ["/", "/chapters/", "/craft/", "/ventures/"]
    paths += ["/ventures/%s/" % k for k in SPEC.keys()]
    today = max(p["d"] for p in feed) if feed else "2026-08-16"

    open(os.path.join(ROOT, "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join('  <url><loc>%s%s</loc><lastmod>%s</lastmod></url>\n'
                  % (BASE, p, today) for p in paths)
        + "</urlset>\n")

    open(os.path.join(ROOT, "robots.txt"), "w").write(
        "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % BASE)

    MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    def rfc(d):
        y, m, dd = d.split("-")
        return "%s, %s %s %s 09:00:00 +0000" % ("Mon", dd, MON[int(m) - 1], y)

    items = []
    for p in feed[:40]:
        title = re.sub(r"\s+", " ", p["t"])[:90]
        if len(re.sub(r"\s+", " ", p["t"])) > 90:
            title += "\u2026"
        items.append(
            "  <item>\n"
            "    <title>%s</title>\n"
            "    <link>%s</link>\n"
            "    <guid isPermaLink=\"true\">%s</guid>\n"
            "    <pubDate>%s</pubDate>\n"
            "    <description>%s</description>\n"
            "  </item>\n" % (sx.escape(title), sx.escape(p["u"]),
                             sx.escape(p["u"]), rfc(p["d"]),
                             sx.escape(p["t"])))
    open(os.path.join(ROOT, "feed.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n<channel>\n'
        '  <title>Sakib Ahmed</title>\n'
        '  <link>%s/</link>\n'
        '  <atom:link href="%s/feed.xml" rel="self" type="application/rss+xml"/>\n'
        '  <description>Everything I post, in one place.</description>\n'
        '  <language>en-gb</language>\n%s</channel>\n</rss>\n'
        % (BASE, BASE, "".join(items)))
    print("wrote sitemap.xml, robots.txt and feed.xml (%d items)" % len(items))


def main():
    misses = []
    freshest = {}
    for slug, v in SPEC.items():
        bucket = BUCKETS.get(v.get("bucket") or BUCKET_ALIAS.get(slug, slug), [])
        bucket = drop_near_dupes(bucket)
        used = set()
        proof = "\n".join(
            '    <li><b>%s</b><span>%s</span></li>' % (a, b) for a, b in v["proof"])
        link = ""
        if v.get("link"):
            href, label = v["link"]
            link = ('\n    <p class="live"><a class="u" data-out href="%s">%s</a></p>'
                    % (href, label))
        has_posts = any(b.get("posts") for b in v["beats"])
        lede = ("What I say about it now, and what I was actually posting at the time."
                if has_posts else
                "No posts to show against this one, which is the whole point of it.")
        out = [HEAD.format(title=v["title"], years=v["years"], stand=v["stand"],
                           stand_plain=re.sub("<[^>]+>", "", v["stand"]),
                           proof=proof, link=link, lede=lede, clients=client_block(v))]
        i = 0
        for beat in v["beats"]:
            # a beat can carry a scribble in the margin. the whole beat is the
            # anchor so --pin can drop the note down beside a photo rather than
            # pinning it to the first line of prose.
            note = beat.get("note")
            out.append('\n  <div class="beat%s">' % (" anchored" if note else ""))
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
            if note:
                out.append(
                    '    <aside class="pen-note" style="--pin:%s">\n'
                    '      <svg class="stroke" width="52" height="30" viewBox="0 0 52 30" aria-hidden="true">'
                    '<path d="M50 25 C40 26, 16 24, 5 12"/><path d="M5 12 L14 13"/><path d="M5 12 L9 20"/></svg>\n'
                    '      <span class="txt">%s</span>\n'
                    '    </aside>' % (note.get("pin", "6rem"), clean(note["txt"])))
            out.append('  </div>')

        # index the curated clippings so the palette can search what he
        # actually wrote, not just the fourteen page titles
        for beat in v.get("beats", []):
            for entry in beat.get("posts", []):
                needle = entry["m"] if isinstance(entry, dict) else entry
                q = find(bucket, needle)
                if not q:
                    continue
                SEARCH.append({
                    # the whole post, so a search finds what he wrote in the
                    # middle of it and not only how it opened
                    "t": flat(q["text"]),
                    "v": v["title"],
                    "d": q["date"],
                    "u": "ventures/%s/#p-%s" % (
                        slug, re.sub(r"[^a-z0-9]+", "", (q.get("url") or "")[-14:].lower())),
                })

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
        # a music project whose page you cannot hear is a page that failed
        if v.get("tracks"):
            rows = []
            for t in v["tracks"]:
                art = ('<img class="art" src="../../assets/media/%s" alt="" loading="lazy">'
                       % t["art"]) if t.get("art") else '<span class="art no-art" aria-hidden="true"></span>'
                rows.append(
                    '      <li><button class="track" data-src="../../assets/audio/%s.mp3" '
                    'data-title="%s">%s<span class="meta"><span class="t">%s</span>'
                    '<span class="n">%s</span></span><span class="play" aria-hidden="true"></span>'
                    '</button></li>' % (t["f"], html.escape(t["t"]), art,
                                        html.escape(t["t"]), html.escape(t["n"])))
            extra = ""
            for href, label in v.get("extra_links", []):
                extra = ' There is <a class="u" data-out href="%s">%s</a>.' % (href, label)
            out.append(TRACKLIST.format(
                note="Vocals and daf only, no melodic instruments." + extra,
                rows="\n".join(rows)))

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
        if k in seen or not flat(r["text"]):
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
             '\n      <div class="feed-end"></div>\n    </div>\n  </section>\n')
    a, b_ = "<!-- LATELY:START -->", "<!-- LATELY:END -->"
    html_s = html_s[:html_s.index(a) + len(a)] + block + html_s[html_s.index(b_):]
    open(home, "w").write(html_s)
    with open(os.path.join(FEED_OUT, "search.json"), "w") as fh:
        json.dump(SEARCH, fh)
    print("search index: %d clippings" % len(SEARCH))
    print("front page feed: %d posts, newest %s" % (len(feed), feed[0]["d"]))
    write_site_files(feed)

    if misses:
        print("\n!! COULD NOT MATCH:")
        for s, n in misses:
            print("   [%s] %s" % (s, n[:70]))


main()
