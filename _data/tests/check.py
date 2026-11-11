#!/usr/bin/env python3
"""Site test suite. Start `python3 -m http.server 5177` in the site root first,
then run: python3 _data/tests/check.py

Covers: structural audit, no-JS, reduced motion, tasbih, theme persistence,
mobile overflow, and command-palette navigation by mouse and keyboard.
"""
from playwright.sync_api import sync_playwright
import collections, sys

import os
BASE = os.environ.get("SITE_BASE", "http://localhost:5177")
PAGES = ["/", "/chapters/", "/craft/", "/manifesto/",
         "/ventures/minideed/", "/ventures/simply-smashed/",
         "/ventures/draper/", "/ventures/bilal/",
         "/404.html"]

results = []


def check(name, ok, note=""):
    results.append((name, ok, note))


with sync_playwright() as pw:
    # Playwright's own browsers are not installed on this Mac; Chrome is
    b = pw.chromium.launch(channel=os.environ.get("SITE_BROWSER", "chrome"))

    # ---- structural ----
    issues = collections.defaultdict(list)
    for path in PAGES:
        pg = b.new_page()
        pg.on("pageerror", lambda e: issues[path].append("JS " + str(e)[:80]))
        pg.on("response", lambda r: issues[path].append(
            "%s %s" % (r.status, r.url.replace(BASE, ""))) if r.status >= 400 else None)
        pg.goto(BASE + path, wait_until="networkidle")
        pg.wait_for_timeout(250)
        d = pg.evaluate("""() => {
          const ids = [...document.querySelectorAll('[id]')].map(e => e.id);
          return {
            dup: ids.filter((v, i) => ids.indexOf(v) !== i),
            noAlt: [...document.querySelectorAll('img')]
                     .filter(i => i.getAttribute('alt') === null).length,
            h1: document.querySelectorAll('h1').length,
            hScroll: document.documentElement.scrollWidth >
                     document.documentElement.clientWidth,
          };
        }""")
        if d["dup"]:
            issues[path].append("dup ids %s" % set(d["dup"]))
        if d["noAlt"]:
            issues[path].append("%d img without alt" % d["noAlt"])
        if d["h1"] != 1:
            issues[path].append("%d h1 tags" % d["h1"])
        if d["hScroll"]:
            issues[path].append("horizontal overflow")
        pg.close()
        check("structure %s" % path, not issues[path], "; ".join(issues[path])[:90])

    # ---- ledger rows must not squash (a nested grid once ate the link) ----
    pg = b.new_page()
    pg.goto(BASE + "/", wait_until="networkidle")
    pg.wait_for_timeout(300)
    squash = pg.evaluate("""() => {
        const bad = [];
        document.querySelectorAll('.ledger li').forEach(li => {
            const w = li.querySelector('.what');
            if (!w) return;
            const share = w.getBoundingClientRect().width /
                          li.getBoundingClientRect().width;
            if (share < 0.35) bad.push(w.textContent.trim().slice(0, 18)
                                       + ' @' + Math.round(share * 100) + '%');
        });
        return bad;
    }""")
    check("no ledger row squash", not squash, ", ".join(squash)[:80])
    pg.close()

    # ---- no JS: content must still be readable ----
    ctx = b.new_context(java_script_enabled=False)
    pg = ctx.new_page()
    pg.goto(BASE + "/chapters/", wait_until="load")
    n = pg.evaluate("""() => [...document.querySelectorAll('.receipt q')]
        .filter(q => q.getBoundingClientRect().height > 8 &&
                     getComputedStyle(q).opacity !== '0').length""")
    check("no-JS receipts readable", n >= 25, "%s visible" % n)
    ctx.close()

    # ---- receipts: every red number has a post, and none sit on each other ----
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.goto(BASE + "/chapters/", wait_until="networkidle")
    pg.wait_for_timeout(400)
    r = pg.evaluate("""() => {
      const refs = [...document.querySelectorAll('.ref a')];
      const orphans = refs.filter(a => !document.querySelector(a.getAttribute('href'))).length;
      const dead = [...document.querySelectorAll('.receipt .src')]
        .filter(a => !/^https:\\/\\/(x\\.com|www\\.linkedin\\.com)\\//.test(a.href)).length;
      const boxes = [...document.querySelectorAll('.receipts')].map(e => e.getBoundingClientRect());
      let overlap = 0;
      for (let i = 1; i < boxes.length; i++) if (boxes[i].top < boxes[i - 1].bottom - 1) overlap++;
      const margin = boxes.filter(b => b.left > 800).length;
      return {refs: refs.length, orphans, dead, overlap, margin, boxes: boxes.length};
    }""")
    check("every receipt number has its post", r["refs"] >= 25 and r["orphans"] == 0 and r["dead"] == 0, str(r))
    check("receipts sit in the margin on a wide screen", r["margin"] == r["boxes"], str(r))
    check("no two receipts overlap", r["overlap"] == 0, str(r))
    pg.close()

    # ---- doors: one per chapter, drawn on arrival, and the big arch at the end ----
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.goto(BASE + "/chapters/", wait_until="networkidle")
    d = pg.evaluate("""() => ({
        heads: document.querySelectorAll('.article h2').length,
        doors: document.querySelectorAll('.article h2 .door').length,
        shut: document.querySelectorAll('.article h2 .door.shut').length,
        last: document.querySelectorAll('.last-door a.door.masjid').length,
        firstSeen: document.querySelector('.article h2 .door').classList.contains('seen')})""")
    check("every chapter ends at a door", d["heads"] == 11 and d["doors"] == 11 and d["last"] == 1, str(d))
    pg.wait_for_timeout(600)
    check("a door is drawn when you reach it",
          pg.evaluate("document.querySelector('.article h2 .door').classList.contains('seen')"), "")
    pg.click(".article h2 .door.ajar")
    pg.wait_for_timeout(250)
    op = pg.eval_on_selector(".article h2 .door.ajar .says", "e => getComputedStyle(e).opacity")
    check("a door says which door it is", float(op) > 0.9, "opacity=%s" % op)
    sits = pg.evaluate("""() => { const h = document.querySelector('.article h2'), dr = h.querySelector('.door');
        const hr = h.getBoundingClientRect(), r = dr.getBoundingClientRect();
        return Math.abs(r.bottom - (hr.top + hr.height / 2)); }""")
    check("the door stands on the rule", sits < 3, "%.1fpx off" % sits)
    pg.close()

    ctx = b.new_context(java_script_enabled=False)
    pg = ctx.new_page()
    pg.goto(BASE + "/chapters/", wait_until="load")
    off = pg.eval_on_selector(".article h2 .door .line", "e => getComputedStyle(e).strokeDashoffset")
    check("no-JS doors are still drawn", off in ("0", "0px"), off)
    ctx.close()

    # ---- pages that were cut still get you somewhere ----
    pg = b.new_page()
    landed = []
    for old in ("/ventures/", "/ventures/psk/", "/ventures/simply-clo/", "/ventures/dhikry/", "/ventures/lofi-muslim/"):
        pg.goto(BASE + old, wait_until="networkidle")
        pg.wait_for_timeout(500)
        landed.append(pg.url.replace(BASE, ""))
    check("old addresses forward", landed == ["/#built", "/chapters/#smashed", "/chapters/#hoodie", "/", "/"], str(landed))
    pg.goto(BASE + "/", wait_until="networkidle")
    pg.wait_for_timeout(600)
    quiet = pg.evaluate("({feed: document.querySelectorAll('.feed-wrap').length, player: document.querySelectorAll('#player').length, clock: document.querySelector('#clock').textContent.trim()})")
    check("front page has no feed, player or prayer times", quiet == {"feed": 0, "player": 0, "clock": ""}, str(quiet))
    pg.goto(BASE + "/ventures/bilal/", wait_until="networkidle")
    pg.wait_for_timeout(600)
    bc = pg.text_content("#clock").strip()
    check("Bilal's page keeps the prayer clock", len(bc) > 5, bc)
    pg.close()

    # ---- card and icon ----
    pg = b.new_page()
    pg.goto(BASE + "/", wait_until="networkidle")
    meta = pg.evaluate("""async () => {
      const og = document.querySelector('meta[property="og:image"]').content.replace('https://sakib.lol', '');
      const r = await fetch(og);
      const t = await fetch(document.querySelector('link[rel="apple-touch-icon"]').href);
      return {og, ok: r.ok, touch: t.ok, icon: document.querySelector('link[rel="icon"]').href.includes('efc96a')};
    }""")
    check("social card and icons are in place", meta["ok"] and meta["touch"] and meta["icon"] and "og-v3" in meta["og"], str(meta))
    pg.close()

    # ---- one path through the site ----
    pg = b.new_page()
    hops = []
    pg.goto(BASE + "/chapters/", wait_until="networkidle")
    for _ in range(3):
        nxt = pg.get_attribute(".prevnext .next", "href")
        pg.goto(pg.evaluate("(h) => new URL(h, location.href).href", nxt), wait_until="networkidle")
        hops.append(pg.url.replace(BASE, ""))
    check("the story hands you on", hops[:2] == ["/manifesto/", "/ventures/draper/"], str(hops))
    pg.close()

    # ---- the memo: addressed on open, and the footer keeps count ----
    pg = b.new_page()
    pg.goto(BASE + "/", wait_until="networkidle")
    pg.wait_for_timeout(1300)
    to = pg.text_content("#memo-to")
    stay = pg.text_content("#stay")
    check("memo is addressed to whoever opened it", " at " in to, to)
    check("footer counts the visit", "been here" in stay and "second" in stay, stay)
    dated = pg.text_content("#memo-date")
    check("memo is dated today", str(__import__("datetime").date.today().year) in dated, dated)
    said = pg.text_content(".memo-head .from")
    check("the first line says what I do", "Draper" in said, said)
    order = pg.evaluate("[...document.querySelectorAll('.section .ledger .what')].map(e => e.firstChild.textContent.trim())")
    check("Draper leads the projects", "Draper" in order and order.index("Draper") < order.index("Simply Smashed"), str(order))
    paper = pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--sun-paper')")
    check("the paper takes its warmth from the sun", paper.strip().startswith("oklch(97.4%"), paper)
    check("the footer has its door", pg.evaluate("document.querySelectorAll('.foot .stay-door').length") == 1, "")
    pg.goto(BASE + "/ventures/bilal/", wait_until="networkidle")
    pg.wait_for_timeout(300)
    check("the count carries to other pages", "been here" in (pg.text_content("#stay") or ""), "")
    pg.close()

    # ---- reduced motion ----
    ctx = b.new_context(reduced_motion="reduce")
    pg = ctx.new_page()
    pg.goto(BASE + "/", wait_until="networkidle")
    pg.wait_for_timeout(200)
    op = pg.eval_on_selector(".memo p", "e => getComputedStyle(e).opacity")
    check("reduced-motion content visible", op == "1", "opacity=%s" % op)
    ctx.close()

    # ---- tasbih + theme ----
    pg = b.new_page()
    pg.goto(BASE + "/", wait_until="networkidle")
    pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    pg.wait_for_timeout(400)
    hidden = pg.eval_on_selector("#tasbih", "e => getComputedStyle(e).display")
    check("tasbih stays out of the way until found", hidden == "none", hidden)
    for _ in range(5):
        pg.keyboard.press("t")
    check("tasbih counts", pg.text_content("#tasbih-count").startswith("5/33"))
    pg.click("#moon")
    pg.wait_for_timeout(150)
    t1 = pg.evaluate("document.documentElement.dataset.theme")
    pg.goto(BASE + "/ventures/bilal/", wait_until="networkidle")
    t2 = pg.evaluate("document.documentElement.dataset.theme")
    check("theme persists across pages", t1 == t2, "%s -> %s" % (t1, t2))
    pg.close()

    # ---- palette: hover must not rebuild the list, clicks must navigate ----
    pg = b.new_page()
    pg.goto(BASE + "/", wait_until="networkidle")
    pg.evaluate("""() => { window.__r = 0;
        new MutationObserver(() => window.__r++)
          .observe(document.getElementById('palette-list'), {childList: true}); }""")
    pg.keyboard.press("Meta+k")
    pg.wait_for_timeout(200)
    # opening the palette legitimately builds the list once; only count what
    # the hover itself causes
    opened_at = pg.evaluate("window.__r")
    box = pg.eval_on_selector("#palette-list li:nth-child(3)",
                              "e => {const r = e.getBoundingClientRect();"
                              "return {x: r.x + r.width / 2, y: r.y + r.height / 2};}")
    pg.mouse.move(box["x"], box["y"])
    pg.wait_for_timeout(500)
    rebuilds = pg.evaluate("window.__r") - opened_at
    check("palette hover does not rebuild list", rebuilds == 0,
          "%d rebuilds" % rebuilds)
    pg.close()

    # select by what the item says, the way a person does, not by position
    for path, query, want in [("/", "minideed", "/ventures/minideed/"),
                              ("/", "chapters", "/chapters/"),
                              ("/", "bilal", "/ventures/bilal/"),
                              ("/ventures/bilal/", "draper", "/ventures/draper/")]:
        p2 = b.new_page()
        p2.goto(BASE + path, wait_until="networkidle")
        p2.keyboard.press("Meta+k")
        p2.wait_for_timeout(200)
        p2.keyboard.type(query, delay=10)
        p2.wait_for_timeout(200)
        try:
            p2.click("#palette-list li:first-child", timeout=4000)
            p2.wait_for_timeout(700)
            got = p2.url.replace(BASE, "") or "/"
        except Exception:
            got = "CLICK FAILED"
        check("palette click %r -> %s" % (query, want), got == want, got)
        p2.close()

    # ---- mobile ----
    ctx = b.new_context(viewport={"width": 390, "height": 844})
    for path in PAGES:
        m = ctx.new_page()
        m.goto(BASE + path, wait_until="networkidle")
        m.wait_for_timeout(200)
        ov = m.evaluate("""() => ({s: document.documentElement.scrollWidth,
                                   c: document.documentElement.clientWidth})""")
        check("mobile no overflow %s" % path, ov["s"] <= ov["c"] + 1,
              "%s>%s" % (ov["s"], ov["c"]))
        m.close()
    ctx.close()

    # ---- the footer furniture actually renders ----
    # a bare .track rule written for the Lofi Muslim list also matched the
    # player's own label, turned it into a grid and squashed it to five lines
    # inside a 41px column on all fourteen pages. nothing caught it, so:
    for path in PAGES:
        f = b.new_page(viewport={"width": 1200, "height": 900})
        f.goto(BASE + path, wait_until="networkidle")
        f.wait_for_timeout(150)
        r = f.evaluate("""() => {
          const pl = document.getElementById('player');
          if (!pl) return null;
          pl.hidden = false;
          const t = pl.querySelector('.track'), bar = pl.querySelector('.bar');
          const cs = getComputedStyle(t), tr = t.getBoundingClientRect();
          return {lines: tr.height / (parseFloat(cs.lineHeight) || 18),
                  display: cs.display, bar: bar.getBoundingClientRect().width};
        }""")
        if r:
            check("player label is one line %s" % path, r["lines"] < 1.6,
                  "%.1f lines, display:%s" % (r["lines"], r["display"]))
            check("player progress bar has width %s" % path, r["bar"] > 10,
                  "%.0fpx" % r["bar"])
        f.close()

    # the feed's own cards must not disagree with the ones scrolled in after them
    h = b.new_page(viewport={"width": 1100, "height": 900})
    h.goto(BASE + "/", wait_until="networkidle")
    h.wait_for_timeout(300)
    for _ in range(3):
        h.evaluate("() => { const f=document.querySelector('.feed'); if(f) f.scrollTop=f.scrollHeight; }")
        h.wait_for_timeout(300)
    hs = h.evaluate("""() => {
      const g = s => [...new Set([...document.querySelectorAll(s)].map(e => e.textContent.trim()))];
      return {li: g('.post.li .handle'), x: g('.post.x .handle')};
    }""")
    check("one LinkedIn handle in the feed", len(hs["li"]) <= 1, str(hs["li"]))
    check("one X handle in the feed", len(hs["x"]) <= 1, str(hs["x"]))
    h.close()

    # a folded post must always have a way out. it clamps only when a script
    # is there to open it, otherwise the reader is stuck with half a story.
    f = b.new_page(viewport={"width": 900, "height": 900})
    f.goto(BASE + "/ventures/minideed/", wait_until="networkidle")
    f.wait_for_timeout(400)
    r = f.evaluate("""() => {
      const el = document.querySelector('.body.folded p');
      if (!el) return null;
      return {clipped: el.scrollHeight > el.clientHeight + 4,
              controls: document.querySelectorAll('.unfold').length};
    }""")
    if r:
        check("folded post has an open control", r["controls"] > 0, str(r))
        f.click(".unfold")
        f.wait_for_timeout(450)
        opened = f.evaluate("() => {const e=document.querySelector('.body.folded p');"
                            "return e.scrollHeight <= e.clientHeight + 4;}")
        check("folded post opens fully", opened, "still clipped after click")
    f.close()

    nojs = b.new_context(java_script_enabled=False)
    n = nojs.new_page()
    n.goto(BASE + "/ventures/minideed/", wait_until="domcontentloaded")
    n.wait_for_timeout(300)
    r2 = n.evaluate("""() => {const el=document.querySelector('.body.folded p');
      return el ? el.scrollHeight > el.clientHeight + 4 : false;}""")
    check("no-JS shows the whole post", not r2, "clipped with no way to open it")
    nojs.close()

    b.close()

bad = [r for r in results if not r[1]]
for name, ok, note in results:
    if not ok:
        print("FAIL  %-44s %s" % (name, note))
print("\n%d/%d passed" % (len(results) - len(bad), len(results)))
sys.exit(1 if bad else 0)
