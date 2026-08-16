#!/usr/bin/env python3
"""Generate the venture pages: retrospective spine + pasted-in real posts."""
import json, os, re, html, datetime

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
<script>(function(){{var q=new URLSearchParams(location.search).get("theme");var t=q||localStorage.getItem("theme");if(t==="dark"||t==="light")document.documentElement.dataset.theme=t;}})();</script>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:ital,wght@0,400..700;1,400..700&family=EB+Garamond:ital,wght@1,400..600&family=Reenie+Beanie&family=Amiri&display=swap">
<link rel="stylesheet" href="../../assets/site.css">
</head>
<body>

<main class="page article venture">

  <a class="crumb rise" style="--i:0" href="../"><span class="back">←</span> Ventures</a>

  <header class="article-head rise" style="--i:1">
    <h1>{title}</h1>
    <p class="when">{years}</p>
    <p class="stand">{stand}</p>
  </header>

  <ul class="proof rise" style="--i:2">
{proof}
  </ul>

  <p class="lede rise" style="--i:3">What I say about it now, and what I was actually posting at the time.</p>
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


def card(p, i):
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
    tilt = (i % 3) - 1  # -1, 0, 1
    return """    <figure class="clip" style="--tilt:{tilt}">
      <figcaption>
        <span class="src" aria-hidden="true">{glyph}</span>
        <time>{date}</time>
        <span class="num">{num}</span>
      </figcaption>
      <p>{txt}</p>
      <a class="u out" data-out href="{url}">Read on {where}</a>
    </figure>""".format(tilt=tilt * 0.35, glyph=glyph, date=pretty(p["date"]),
                        num=" · ".join(bits), txt=html.escape(txt),
                        url=p.get("url", "#"), where=where)


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
    for slug, v in SPEC.items():
        bucket = BUCKETS[BUCKET_ALIAS.get(slug, slug)]
        proof = "\n".join(
            '    <li><b>%s</b><span>%s</span></li>' % (a, b) for a, b in v["proof"])
        out = [HEAD.format(title=v["title"], years=v["years"], stand=v["stand"],
                           stand_plain=re.sub("<[^>]+>", "", v["stand"]),
                           proof=proof)]
        i = 0
        for beat in v["beats"]:
            out.append('\n  <div class="beat">')
            out.append('    <p class="say">%s</p>' % beat["say"])
            for needle in beat.get("posts", []):
                p = find(bucket, needle)
                if not p:
                    misses.append((slug, needle))
                    continue
                out.append(card(p, i))
                i += 1
            out.append('  </div>')
        out.append(FOOT)
        d = os.path.join(ROOT, "ventures", slug)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w").write("\n".join(out))
        print("built ventures/%s (%d clippings)" % (slug, i))

    if misses:
        print("\n!! COULD NOT MATCH:")
        for s, n in misses:
            print("   [%s] %s" % (s, n[:70]))


main()
