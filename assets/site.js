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
    /* Android Chrome supports this; iOS Safari does not, so treat it as a
       bonus rather than the mechanism. */
    var buzz = function (pattern) {
      if (navigator.vibrate) { try { navigator.vibrate(pattern); } catch (e) {} }
    };
    var bump = function () {
      count += 1;
      buzz(count >= 33 ? [14, 45, 14] : 8);
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

  /* ---------- the beats: opt-in only, his own tracks ----------
     Scoped on purpose: `var` is function-scoped, and paint/label/tick
     would otherwise clobber the tasbih and the clock. */
  (function () {
    var player = $("#player");
    if (player && window.Audio) {
      var depth2 = (location.pathname.replace(/\/index\.html$/, "/")
                     .match(/\/[^/]+(?=\/)/g) || []).length;
      var root2 = depth2 ? new Array(depth2 + 1).join("../") : "./";
      var TRACKS = [
        { src: root2 + "assets/audio/open-road.mp3", name: "Open Road" },
        { src: root2 + "assets/audio/quiet-current.mp3", name: "Quiet Current" }
      ];
      var at = 0, audio = null;
      var ppBtn = $("#pp"), label = $("#track"), bar = $("#bar");
      player.hidden = false;

      var paint = function () {
        label.textContent = "Lofi Muslim \u00b7 " + TRACKS[at].name;
      };
      var load = function () {
        if (audio) { audio.pause(); audio.removeEventListener("timeupdate", tick); }
        audio = new Audio(TRACKS[at].src);
        audio.loop = false;
        audio.volume = 0.55;
        audio.addEventListener("timeupdate", tick);
        audio.addEventListener("ended", function () {
          at = (at + 1) % TRACKS.length;
          paint();
          load();
          audio.play();
        });
      };
      var tick = function () {
        if (!audio || !audio.duration) return;
        bar.style.width = (audio.currentTime / audio.duration * 100) + "%";
      };
      var toggle = function () {
        if (!audio) load();
        if (audio.paused) {
          audio.play().then(function () {
            player.classList.add("on");
            ppBtn.setAttribute("aria-label", "Pause the beats");
          }).catch(function () { /* browser said no, leave it alone */ });
        } else {
          audio.pause();
          player.classList.remove("on");
          ppBtn.setAttribute("aria-label", "Play the beats");
        }
      };
      ppBtn.addEventListener("click", toggle);
      paint();

      /* on the Lofi Muslim page the player owns up to itself */
      if (/lofi-muslim/.test(location.pathname)) {
        var mine = document.createElement("span");
        mine.className = "mine";
        mine.textContent = "these are the ones";
        player.appendChild(mine);
        var io2 = new IntersectionObserver(function (es) {
          es.forEach(function (e) { if (e.isIntersecting) mine.classList.add("show"); });
        });
        io2.observe(player);
      }
    }
  })();

  /* ---------- swipe between ventures ----------
     Only ever acts on a clearly horizontal drag, so vertical scrolling is
     never fought. Falls back to the visible prev/next links. */
  (function () {
    if (REDUCED) return;
    var page = $(".page");
    var prevA = $(".prevnext .prev"), nextA = $(".prevnext .next");
    if (!page || (!prevA && !nextA)) return;

    var x0 = 0, y0 = 0, dx = 0, locked = null, tracking = false;
    var LIMIT = 0.32;      // how far the page may follow the thumb
    var TRIGGER = 64;      // px before it counts as a swipe

    var reset = function (animate) {
      if (animate) {
        root.classList.add("settling");
        setTimeout(function () { root.classList.remove("settling"); }, 280);
      }
      page.style.transform = "";
      root.classList.remove("swiping");
    };

    page.addEventListener("touchstart", function (e) {
      if (e.touches.length !== 1) return;
      x0 = e.touches[0].clientX; y0 = e.touches[0].clientY;
      dx = 0; locked = null; tracking = true;
    }, { passive: true });

    page.addEventListener("touchmove", function (e) {
      if (!tracking || e.touches.length !== 1) return;
      var mx = e.touches[0].clientX - x0;
      var my = e.touches[0].clientY - y0;
      if (locked === null) {
        if (Math.abs(mx) < 8 && Math.abs(my) < 8) return;
        locked = Math.abs(mx) > Math.abs(my) * 1.4 ? "x" : "y";
        if (locked === "x") root.classList.add("swiping");
      }
      if (locked !== "x") return;
      // nothing to go to in that direction: heavy resistance
      var target = mx < 0 ? nextA : prevA;
      dx = mx * (target ? LIMIT : LIMIT * 0.25);
      page.style.transform = "translate3d(" + dx.toFixed(1) + "px,0,0)";
    }, { passive: true });

    var finish = function () {
      if (!tracking) return;
      tracking = false;
      if (locked !== "x") { reset(false); return; }
      var went = dx / LIMIT;
      if (went <= -TRIGGER && nextA) { location.href = nextA.getAttribute("href"); return; }
      if (went >= TRIGGER && prevA) { location.href = prevA.getAttribute("href"); return; }
      reset(true);
    };
    page.addEventListener("touchend", finish, { passive: true });
    page.addEventListener("touchcancel", finish, { passive: true });
  })();

  /* ---------- the feed: his own posts, streamed as you scroll ---------- */
  (function () {
    var wrap = $(".feed-wrap");
    if (!wrap) return;
    var list = $(".feed", wrap), endEl = $(".feed-end", wrap);
    var url = wrap.getAttribute("data-feed");
    if (!list || !endEl || !url) return;

    var BATCH = 6;
    var shown = list.children.length;   // the ones rendered at build time
    var data = null, loading = false, done = false;

    var esc = function (t) {
      return String(t).replace(/[&<>"']/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;",
                 '"': "&quot;", "'": "&#39;" }[c];
      });
    };
    var MON = ["Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"];
    var pretty = function (d) {
      var b = d.split("-");
      return (+b[2]) + " " + MON[+b[1] - 1] + " " + b[0];
    };
    var media = url.indexOf("../") === 0 ? "../../assets/media/" : "assets/media/";

    var render = function (p) {
      var isX = p.s === "x";
      var txt = p.t.length > 300
        ? p.t.slice(0, p.t.slice(0, 300).lastIndexOf(" ")) + "\u2026" : p.t;
      var bits = [];
      if (p.f) bits.push(p.f.toLocaleString() + (isX ? " likes" : " reactions"));
      if (p.r) bits.push(p.r.toLocaleString() + " reposts");
      var who = isX
        ? '<span class="name">sakib</span><span class="handle">@mertesakib</span>'
        : '<span class="name">Sakib Ahmed</span><span class="handle">Co-founder of Draper \u00b7 Own your distribution</span>';
      var el = document.createElement("article");
      el.className = "post " + (isX ? "x" : "li");
      el.innerHTML =
        '<header><img class="pfp" src="' + media + 'avatar.jpg" alt="" loading="lazy">' +
        '<span class="who">' + who + '</span>' +
        '<span class="mark" aria-hidden="true">' + (isX ? "\ud835\udd4f" : "in") + '</span></header>' +
        '<div class="body"><p>' + esc(txt) + '</p>' +
        (p.m ? '<img class="shot" src="' + media + p.m + '" alt="Photo from the post." loading="lazy">' : '') +
        '</div>' +
        '<footer><time>' + pretty(p.d) + '</time>' +
        '<span class="stats">' + bits.join(" \u00b7 ") + '</span>' +
        '<a class="open" data-out href="' + p.u + '">Open</a></footer>';
      return el;
    };

    var more = function () {
      if (done || !data) return;
      var frag = document.createDocumentFragment();
      var next = data.slice(shown, shown + BATCH);
      next.forEach(function (p) { frag.appendChild(render(p)); });
      list.appendChild(frag);
      shown += next.length;
      if (shown >= data.length) {
        done = true;
        endEl.textContent = "That\u2019s all of it. " + data.length + " posts.";
        endEl.classList.add("spent");
      }
    };

    /* Auto-load a few batches, then hand control back with a button.
       Endless auto-loading pushes the footer away forever and the tasbih and
       theme toggle become unreachable. */
    var autoLeft = 3;
    var button = null;
    var offerButton = function () {
      if (button || done) return;
      button = document.createElement("button");
      button.className = "feed-more";
      button.textContent = "Keep going";
      button.addEventListener("click", function () {
        autoLeft = 3;
        button.remove(); button = null;
        more();
      });
      endEl.appendChild(button);
    };
    var step = function () {
      if (autoLeft > 0) { autoLeft -= 1; more(); if (!done && autoLeft === 0) offerButton(); }
    };

    var io = new IntersectionObserver(function (es) {
      if (!es[0].isIntersecting || loading || done || button) return;
      if (data) { step(); return; }
      loading = true;
      fetch(url).then(function (r) { return r.json(); }).then(function (j) {
        data = j; loading = false; step();
      }).catch(function () {
        loading = false; done = true;
        endEl.textContent = "Could not load the rest.";
      });
    }, { root: list, rootMargin: "400px 0px" });
    io.observe(endEl);
  })();

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
