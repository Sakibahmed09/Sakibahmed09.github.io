/* sakib.page — one script, no dependencies */
(function () {
  "use strict";
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  var root = document.documentElement;
  var REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- the clock: always London ---------- */
  var clock = $("#clock");
  if (clock) {
    var fmt = new Intl.DateTimeFormat("en-GB", {
      timeZone: "Europe/London", hour: "numeric", minute: "2-digit", hour12: true
    });
    var tick = function () {
      var t = fmt.format(new Date()).replace(/\s/g, "").replace("am", "am").replace("pm", "pm");
      clock.textContent = "It’s " + t + " in London E1.";
    };
    tick();
    setInterval(tick, 10000);
  }

  /* ---------- theme: the sun sets properly ---------- */
  var moon = $("#moon");
  var isDark = function () {
    var t = root.dataset.theme;
    if (t === "dark") return true;
    if (t === "light") return false;
    return matchMedia("(prefers-color-scheme: dark)").matches;
  };
  var paintMoon = function () {
    if (moon) moon.setAttribute("aria-pressed", String(isDark()));
  };
  var setTheme = function (mode) {
    root.dataset.theme = mode;
    localStorage.setItem("theme", mode);
    paintMoon();
    var bar = mode === "dark" ? "#17150f" : "#f7f4ec";
    $$('meta[name="theme-color"]').forEach(function (m) { m.setAttribute("content", bar); });
  };
  var toggleTheme = function () { setTheme(isDark() ? "light" : "dark"); };
  if (moon) {
    moon.addEventListener("click", toggleTheme);
    paintMoon();
  }

  /* ---------- tasbih: thirty-three, then again ---------- */
  var tasbih = $("#tasbih");
  if (tasbih) {
    var count = 0, rounds = 0;
    var fill = $(".fill", tasbih);
    var label = $("#tasbih-count");
    var phraseEl = $("#tasbih-phrase");
    var PHRASES = ["سبحان الله",           /* subhanAllah */
                   "الحمد لله",                  /* alhamdulillah */
                   "الله أكبر"];                 /* Allahu akbar */
    var paint = function () {
      fill.style.strokeDashoffset = String(100 - (count / 33) * 100);
      label.textContent = count + "/33" + (rounds ? " ×" + (rounds + 1) : "");
    };
    var bump = function () {
      count += 1;
      if (count >= 33) {
        phraseEl.textContent = PHRASES[rounds % 3];
        tasbih.classList.add("done");
        count = 0;
        rounds += 1;
        setTimeout(function () { tasbih.classList.remove("done"); paint(); }, 2400);
        paint();
        fill.style.strokeDashoffset = "0";
      } else {
        tasbih.classList.remove("done");
        paint();
      }
    };
    tasbih.addEventListener("click", bump);
    document.addEventListener("keydown", function (e) {
      if (e.key === "t" && !e.metaKey && !e.ctrlKey && !e.altKey &&
          !/^(INPUT|TEXTAREA)$/.test(document.activeElement.tagName)) bump();
    });
    paint();
  }

  /* ---------- pen notes draw themselves in ---------- */
  var notes = $$(".pen-note");
  if (notes.length) {
    notes.forEach(function (n) {
      /* Each stroke measures itself, so the shaft draws first and the two
         arrowhead barbs follow, the way you'd actually draw one. */
      $$(".stroke path", n).forEach(function (p, idx) {
        var len = Math.ceil(p.getTotalLength()) + 2;
        p.style.strokeDasharray = len;
        p.style.strokeDashoffset = len;
        p.style.animationDelay = (idx === 0 ? 0 : 300 + idx * 55) + "ms";
      });
    });
    if (REDUCED) {
      notes.forEach(function (n) { n.classList.add("drawn"); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) { en.target.classList.add("drawn"); io.unobserve(en.target); }
        });
      }, { rootMargin: "0px 0px -12% 0px" });
      notes.forEach(function (n) { io.observe(n); });
    }
  }

  /* ---------- table of contents scrollspy ---------- */
  var tocLinks = $$(".toc a");
  if (tocLinks.length) {
    var byId = {};
    tocLinks.forEach(function (a) { byId[a.getAttribute("href").slice(1)] = a; });
    var current = null;
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          if (current) current.removeAttribute("aria-current");
          current = byId[en.target.id];
          if (current) current.setAttribute("aria-current", "true");
        }
      });
    }, { rootMargin: "-8% 0px -78% 0px" });
    $$(".article h2[id]").forEach(function (h) { spy.observe(h); });
  }

  /* ---------- toast ---------- */
  var toastEl = $("#toast"), toastTimer;
  var toast = function (msg) {
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove("show"); }, 1800);
  };

  /* ---------- command palette ---------- */
  var veil = $("#veil"), input = $("#palette-input"), list = $("#palette-list");
  if (veil && input && list) {
    var depth = (location.pathname.replace(/\/index\.html$/, "/")
                  .match(/\/[^/]+(?=\/)/g) || []).length;
    var HOME = depth ? new Array(depth + 1).join("../") : "./";
    var ACTIONS = [
      { t: "Home",               g: "⌂", k: "sakib start", go: HOME },
      { t: "Ventures",           g: "▦", k: "mains sides projects built", go: HOME + "ventures/" },
      { t: "MiniDeed",           g: "·", k: "charity app likes pennies main", go: HOME + "ventures/minideed/" },
      { t: "Simply Smashed",     g: "·", k: "burger joint main food", go: HOME + "ventures/simply-smashed/" },
      { t: "Peruvian Street Kitchen", g: "·", k: "psk chicken rice green sauce main", go: HOME + "ventures/psk/" },
      { t: "Draper",             g: "·", k: "founders authorities content main work", go: HOME + "ventures/draper/" },
      { t: "dhikry",             g: "·", k: "side dhikr circle invite ios", go: HOME + "ventures/dhikry/" },
      { t: "Bilal",              g: "·", k: "side athan masjid times tv", go: HOME + "ventures/bilal/" },
      { t: "vibenasheeds",       g: "·", k: "side halal music nasheed ai", go: HOME + "ventures/vibenasheeds/" },
      { t: "Lofi Muslim",        g: "·", k: "side beats youtube vocals", go: HOME + "ventures/lofi-muslim/" },
      { t: "Simply Clo",         g: "·", k: "side hoodie palestine clothing", go: HOME + "ventures/simply-clo/" },
      { t: "Simply Foundation",  g: "·", k: "side school huffadh charity", go: HOME + "ventures/simply-foundation/" },
      { t: "Chapters",           g: "§", k: "story writing timeline", go: HOME + "chapters/" },
      { t: "How this site works", g: "✎", k: "craft colophon design type", go: HOME + "craft/" },
      { t: "Toggle dark mode",   g: "☾", k: "theme light night maghrib", fn: toggleTheme },
      { t: "Count tasbih",       g: "●", k: "dhikr beads 33", fn: function () { var b = $("#tasbih"); if (b) b.click(); } },
      { t: "Copy email",         g: "@",      k: "contact mail", fn: function () {
          navigator.clipboard.writeText("sakib@withsignal.io").then(function () { toast("Copied. Say salaam."); });
        } },
      { t: "X ↗",           g: "𝕏", k: "twitter mertesakib", go: "https://x.com/mertesakib" },
      { t: "LinkedIn ↗",    g: "in", k: "linkedin", go: "https://www.linkedin.com/in/mertesakib" },
      { t: "Draper ↗",      g: "D",  k: "work agency draperhq", go: "https://draperhq.com" }
    ];
    var open = false, sel = 0, shown = [], items = [];

    /* Move the highlight without touching the DOM structure. Rebuilding the
       list on hover destroys the element under the cursor between mousedown
       and mouseup, so clicks never land. */
    var paintSel = function (scroll) {
      items.forEach(function (li, i) {
        if (i === sel) {
          li.setAttribute("aria-selected", "true");
          input.setAttribute("aria-activedescendant", li.id);
          if (scroll && li.scrollIntoView) li.scrollIntoView({ block: "nearest" });
        } else {
          li.removeAttribute("aria-selected");
        }
      });
    };

    var render = function (q) {
      q = (q || "").trim().toLowerCase();
      shown = ACTIONS.filter(function (a) {
        return !q || (a.t + " " + a.k).toLowerCase().indexOf(q) !== -1;
      });
      sel = Math.min(sel, Math.max(shown.length - 1, 0));
      list.innerHTML = "";
      items = [];
      if (!shown.length) {
        var none = document.createElement("li");
        none.className = "none";
        none.textContent = "nothing here. try ‘chapters’";
        list.appendChild(none);
        input.removeAttribute("aria-activedescendant");
        return;
      }
      shown.forEach(function (a, i) {
        var li = document.createElement("li");
        li.setAttribute("role", "option");
        li.id = "opt-" + i;
        li.innerHTML = "<span class='glyph'>" + a.g + "</span><span>" + a.t + "</span>";
        li.addEventListener("mouseenter", function () { sel = i; paintSel(false); });
        /* keep focus in the input so typing still filters after a hover */
        li.addEventListener("mousedown", function (e) { e.preventDefault(); });
        li.addEventListener("click", function () { run(a); });
        items.push(li);
        list.appendChild(li);
      });
      paintSel(false);
    };
    var run = function (a) {
      close();
      if (a.go) { location.href = a.go; }
      else if (a.fn) { a.fn(); }
    };
    var openPalette = function () {
      open = true;
      veil.hidden = false;
      root.classList.add("locked");
      requestAnimationFrame(function () { veil.classList.add("open"); });
      input.value = "";
      sel = 0;
      render("");
      input.focus();
    };
    var close = function () {
      open = false;
      veil.classList.remove("open");
      root.classList.remove("locked");
      setTimeout(function () { if (!open) veil.hidden = true; }, 260);
    };
    var hint = $("#k-hint");
    if (hint) hint.addEventListener("click", function () { open ? close() : openPalette(); });

    document.addEventListener("keydown", function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        open ? close() : openPalette();
      } else if (open && e.key === "Escape") {
        close();
      } else if (open && e.key === "ArrowDown" && shown.length) {
        e.preventDefault(); sel = (sel + 1) % shown.length; paintSel(true);
      } else if (open && e.key === "ArrowUp" && shown.length) {
        e.preventDefault(); sel = (sel - 1 + shown.length) % shown.length; paintSel(true);
      } else if (open && e.key === "Enter" && shown[sel]) {
        e.preventDefault(); run(shown[sel]);
      }
    });
    input.addEventListener("input", function () { sel = 0; render(input.value); });
    veil.addEventListener("click", function (e) { if (e.target === veil) close(); });
    if (location.hash === "#k") openPalette();
  }
})();
