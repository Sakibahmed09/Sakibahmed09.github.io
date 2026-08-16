#!/usr/bin/env python3
"""Site test suite. Start `python3 -m http.server 5177` in the site root first,
then run: python3 _data/tests/check.py

Covers: structural audit, no-JS, reduced motion, tasbih, theme persistence,
mobile overflow, and command-palette navigation by mouse and keyboard.
"""
from playwright.sync_api import sync_playwright
import collections, sys

BASE = "http://localhost:5177"
PAGES = ["/", "/chapters/", "/craft/", "/ventures/", "/ventures/minideed/",
         "/ventures/simply-smashed/", "/ventures/psk/", "/ventures/draper/",
         "/404.html"]

results = []


def check(name, ok, note=""):
    results.append((name, ok, note))


with sync_playwright() as pw:
    b = pw.chromium.launch()

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
    pg.goto(BASE + "/ventures/", wait_until="networkidle")
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
    op = pg.eval_on_selector(".pen-note .txt", "e => getComputedStyle(e).opacity")
    check("no-JS margin notes readable", op != "0", "opacity=%s" % op)
    ctx.close()

    # ---- reduced motion ----
    ctx = b.new_context(reduced_motion="reduce")
    pg = ctx.new_page()
    pg.goto(BASE + "/", wait_until="networkidle")
    pg.wait_for_timeout(200)
    op = pg.eval_on_selector(".prose p", "e => getComputedStyle(e).opacity")
    check("reduced-motion content visible", op == "1", "opacity=%s" % op)
    ctx.close()

    # ---- tasbih + theme ----
    pg = b.new_page()
    pg.goto(BASE + "/", wait_until="networkidle")
    pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    pg.wait_for_timeout(400)
    for _ in range(5):
        pg.click("#tasbih")
    check("tasbih counts", pg.text_content("#tasbih-count").startswith("5/33"))
    pg.click("#moon")
    pg.wait_for_timeout(150)
    t1 = pg.evaluate("document.documentElement.dataset.theme")
    pg.goto(BASE + "/ventures/psk/", wait_until="networkidle")
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
                              ("/", "lofi", "/ventures/lofi-muslim/"),
                              ("/ventures/psk/", "ventures", "/ventures/")]:
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

    b.close()

bad = [r for r in results if not r[1]]
for name, ok, note in results:
    if not ok:
        print("FAIL  %-44s %s" % (name, note))
print("\n%d/%d passed" % (len(results) - len(bad), len(results)))
sys.exit(1 if bad else 0)
