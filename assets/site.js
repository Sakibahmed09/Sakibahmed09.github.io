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
      var t = fmt.format(new Date()).replace(/\s/g, "");
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

  /* Only one sound source at a time. The footer beats and the track list are
     separate players and would happily overlap otherwise. */
  var AUDIO_BUS = "sakib:audio-claim";
  var claimAudio = function (owner) {
    window.dispatchEvent(new CustomEvent(AUDIO_BUS, { detail: owner }));
  };
  var onAudioClaim = function (owner, stop) {
    window.addEventListener(AUDIO_BUS, function (e) {
      if (e.detail !== owner) stop();
    });
  };

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

      /* Carry the beats across pages. Browsers will not always let a fresh
         document start audio on its own, so if resume is refused we keep the
         position and the next press picks up exactly where it left off. */
      var KEEP = "lofi";
      var remember = function () {
        if (!audio) return;
        try {
          sessionStorage.setItem(KEEP, JSON.stringify({
            i: at, t: audio.currentTime, on: !audio.paused
          }));
        } catch (e) {}
      };
      window.addEventListener("pagehide", remember);
      document.addEventListener("visibilitychange", function () {
        if (document.visibilityState === "hidden") remember();
      });

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
          claimAudio("footer");
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
      onAudioClaim("footer", function () {
        if (audio && !audio.paused) {
          audio.pause();
          player.classList.remove("on");
          ppBtn.setAttribute("aria-label", "Play the beats");
        }
      });
      paint();

      (function resume() {
        var raw;
        try { raw = sessionStorage.getItem(KEEP); } catch (e) { return; }
        if (!raw) return;
        var st;
        try { st = JSON.parse(raw); } catch (e) { return; }
        if (typeof st.i !== "number" || !TRACKS[st.i]) return;
        at = st.i;
        paint();
        load();
        var seek = function () {
          try { audio.currentTime = st.t || 0; } catch (e) {}
          tick();
        };
        if (audio.readyState >= 1) seek();
        else audio.addEventListener("loadedmetadata", seek, { once: true });
        if (st.on) {
          audio.play().then(function () {
            player.classList.add("on");
            ppBtn.setAttribute("aria-label", "Pause the beats");
          }).catch(function () {
            /* blocked on a fresh document; position is kept for the next press */
          });
        }
      })();

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
     Native-feeling drag: resistance is asymptotic so it never runs out of
     road, commit is velocity-aware so a flick works, and the release is a
     spring rather than a fixed slide. */
  (function () {
    if (REDUCED) return;
    var page = $(".page");
    var prevA = $(".prevnext .prev"), nextA = $(".prevnext .next");
    if (!page || (!prevA && !nextA)) return;

    var LIMIT = 96;        // px the page can travel, asymptotically
    var COMMIT = 62;       // px of real travel to commit on a slow drag
    var FLICK = 0.45;      // px/ms that counts as a flick
    var x0 = 0, y0 = 0, raw = 0, shown = 0, locked = null;
    var tracking = false, lastX = 0, lastT = 0, vel = 0, armed = false;

    /* a quiet label of where you are heading */
    var peek = document.createElement("div");
    peek.className = "peek";
    peek.innerHTML = '<span></span>';
    document.body.appendChild(peek);
    var peekText = peek.firstChild;

    var resist = function (d) {
      // asymptotic: the further you pull, the less it gives
      var sign = d < 0 ? -1 : 1;
      return sign * LIMIT * (1 - Math.exp(-Math.abs(d) / LIMIT));
    };
    var target = function () { return raw < 0 ? nextA : prevA; };

    var settle = function () {
      page.style.transition = "transform 420ms cubic-bezier(0.22, 1, 0.36, 1)";
      page.style.transform = "";
      peek.classList.remove("show", "ready");
      setTimeout(function () { page.style.transition = ""; }, 440);
    };

    var go = function (a) {
      var dir = a === nextA ? "next" : "prev";
      root.dataset.nav = dir;
      page.style.transition = "transform 220ms cubic-bezier(0.32, 0, 0.67, 0)";
      page.style.transform = "translate3d(" + (dir === "next" ? -1 : 1) * 42 + "px,0,0)";
      page.style.opacity = "0.65";
      setTimeout(function () { location.href = a.getAttribute("href"); }, 120);
    };

    page.addEventListener("touchstart", function (e) {
      if (e.touches.length !== 1) return;
      x0 = lastX = e.touches[0].clientX;
      y0 = e.touches[0].clientY;
      lastT = e.timeStamp;
      raw = shown = vel = 0; locked = null; tracking = true; armed = false;
      page.style.transition = "";
    }, { passive: true });

    page.addEventListener("touchmove", function (e) {
      if (!tracking || e.touches.length !== 1) return;
      var x = e.touches[0].clientX, y = e.touches[0].clientY;
      var mx = x - x0, my = y - y0;
      if (locked === null) {
        if (Math.abs(mx) < 9 && Math.abs(my) < 9) return;
        locked = Math.abs(mx) > Math.abs(my) * 1.3 ? "x" : "y";
      }
      if (locked !== "x") return;

      var dt = e.timeStamp - lastT;
      if (dt > 0) vel = (x - lastX) / dt;
      lastX = x; lastT = e.timeStamp;

      raw = mx;
      var t = target();
      shown = resist(mx) * (t ? 1 : 0.28);   // heavy resistance into a dead end
      page.style.transform = "translate3d(" + shown.toFixed(2) + "px,0,0)";

      if (t) {
        peekText.textContent = t.querySelector(".t").textContent;
        peek.classList.add("show");
        peek.classList.toggle("left", raw > 0);
        var ready = Math.abs(shown) >= COMMIT * 0.72;
        if (ready && !armed) {           // one tick as it arms, like a real control
          armed = true;
          if (navigator.vibrate) { try { navigator.vibrate(7); } catch (err) {} }
        } else if (!ready) { armed = false; }
        peek.classList.toggle("ready", ready);
      }
    }, { passive: true });

    var finish = function () {
      if (!tracking) return;
      tracking = false;
      if (locked !== "x") { settle(); return; }
      var t = target();
      var flick = Math.abs(vel) > FLICK && Math.abs(shown) > 16 &&
                  ((vel < 0 && t === nextA) || (vel > 0 && t === prevA));
      if (t && (Math.abs(shown) >= COMMIT || flick)) { go(t); return; }
      settle();
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
      if (p.f) bits.push(p.f.toLocaleString() +
        (isX ? (p.f === 1 ? " like" : " likes") : (p.f === 1 ? " reaction" : " reactions")));
      if (p.r) bits.push(p.r.toLocaleString() + (p.r === 1 ? " repost" : " reposts"));
      var who = isX
        ? '<span class="name">sakib</span><span class="handle">@mertesakib</span>'
        : '<span class="name">Sakib Ahmed</span><span class="handle">Co-founder of Draper \u00b7 Own your distribution</span>';
      var el = document.createElement("article");
      el.className = "post " + (isX ? "x" : "li");
      el.innerHTML =
        '<img class="pfp" src="' + media + 'avatar.jpg" alt="" loading="lazy">' +
        '<div class="col">' +
          '<header>' + who +
          '<span class="sep">\u00b7</span><time>' + pretty(p.d) + '</time>' +
          '<span class="mark" aria-hidden="true">' + (isX ? "\ud835\udd4f" : "in") + '</span></header>' +
          '<div class="body"><p>' + esc(txt) + '</p>' +
          (p.m ? '<img class="shot" src="' + media + p.m + '" alt="Photo from the post." loading="lazy">' : '') +
          '</div>' +
          '<footer><span class="stats">' + bits.join(" \u00b7 ") + '</span>' +
          '<a class="open" data-out href="' + p.u + '">Open</a></footer>' +
        '</div>';
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

  /* ---------- tracks: press a row, hear the thing ---------- */
  (function () {
    var rows = $$(".track");
    if (!rows.length || !window.Audio) return;
    var current = null, playing = null;
    onAudioClaim("tracks", function () {
      if (current && !current.paused) { current.pause(); }
      rows.forEach(function (r) { r.classList.remove("on"); });
      playing = null;
    });
    rows.forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (playing === btn) {
          current.pause();
          btn.classList.remove("on");
          playing = null;
          return;
        }
        if (current) { current.pause(); }
        rows.forEach(function (r) { r.classList.remove("on"); });
        current = new Audio(btn.getAttribute("data-src"));
        current.volume = 0.85;
        current.addEventListener("ended", function () {
          btn.classList.remove("on"); playing = null;
        });
        claimAudio("tracks");
        current.play().then(function () {
          btn.classList.add("on"); playing = btn;
        }).catch(function () { playing = null; });
      });
    });
  })();

  /* ---------- command palette ---------- */
  var veil = $("#veil"), input = $("#palette-input"), list = $("#palette-list");
  if (veil && input && list) {
    var depth = (location.pathname.replace(/\/index\.html$/, "/")
                  .match(/\/[^/]+(?=\/)/g) || []).length;
    var HOME = depth ? new Array(depth + 1).join("../") : "./";
        /* Icons drawn inline in Lucide's idiom (24x24, 2px stroke, round caps).
       Hand-authored rather than imported so the site keeps its promise of
       asking no other origin for anything. */
    var ICON = {
      home:   '<path d="M3 10.5 12 3.5l9 7V20a1 1 0 0 1-1 1h-5v-6.5H9V21H4a1 1 0 0 1-1-1z"/>',
      grid:   '<rect x="3" y="3" width="7.5" height="7.5" rx="1.2"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="1.2"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="1.2"/><rect x="3" y="13.5" width="7.5" height="7.5" rx="1.2"/>',
      heart:  '<path d="M19 13.6c1.4-1.4 2-3.1 2-4.8a4.8 4.8 0 0 0-9-2.3 4.8 4.8 0 0 0-9 2.3c0 1.7.6 3.4 2 4.8l7 6.9z"/>',
      burger: '<path d="M4 8.5a8 8 0 0 1 16 0z"/><path d="M3.5 12.5h17"/><path d="M4 16h16a4 4 0 0 1-4 3H8a4 4 0 0 1-4-3z"/>',
      bowl:   '<path d="M3.5 11h17a8.5 8.5 0 0 1-17 0z"/><path d="M9 4.5V7M12 3.5V7M15 4.5V7"/>',
      pen:    '<path d="M20.5 3.5 10 14"/><path d="M20.5 3.5c0 7-5.2 12-11.5 12H5l3.2-3.2"/>',
      beads:  '<circle cx="12" cy="12" r="8.5" stroke-dasharray="2.2 3.4"/><circle cx="12" cy="3.5" r="1.6" fill="currentColor" stroke="none"/>',
      tv:     '<rect x="2.5" y="7" width="19" height="12.5" rx="1.8"/><path d="M7.5 3 12 6.5 16.5 3"/>',
      waves:  '<path d="M2.5 12h1.4M7 8.5v7M11.5 5.5v13M16 9.5v5M20.5 12h1"/>',
      phones: '<path d="M3.5 14v-1.5a8.5 8.5 0 0 1 17 0V14"/><path d="M3.5 14a1.8 1.8 0 0 1 1.8-1.8H7v6.6H5.3A1.8 1.8 0 0 1 3.5 17z"/><path d="M20.5 14a1.8 1.8 0 0 0-1.8-1.8H17v6.6h1.7A1.8 1.8 0 0 0 20.5 17z"/>',
      shirt:  '<path d="M15.5 3 12 4.8 8.5 3 3.5 5.8l2 4.2 2-1V21h9V9l2 1 2-4.2z"/>',
      book:   '<path d="M12 7.5v13"/><path d="M12 7.5A4 4 0 0 0 8 4.5H3.5v13H8a4 4 0 0 1 4 3"/><path d="M12 7.5a4 4 0 0 1 4-3h4.5v13H16a4 4 0 0 0-4 3"/>',
      scroll: '<path d="M5.5 4.5h11a1.8 1.8 0 0 1 1.8 1.8v11.4a1.8 1.8 0 0 0 1.8 1.8H8.5a1.8 1.8 0 0 1-1.8-1.8V6.3"/><path d="M9 8.5h6.5M9 12h6.5"/>',
      pencil: '<path d="m12.5 19.5 7-7-4-4-7 7-1.2 5.2z"/><path d="M15 7 18 10"/>',
      moon:   '<path d="M20.8 13.2A8.7 8.7 0 1 1 11 3.4a6.8 6.8 0 0 0 9.8 9.8z"/>',
      dot:    '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="2.4" fill="currentColor" stroke="none"/>',
      at:     '<circle cx="12" cy="12" r="3.8"/><path d="M15.8 12v1.6a2.6 2.6 0 0 0 5.2 0V12a9 9 0 1 0-3.8 7.3"/>'
    };
    function svg(k) {
      return k && ICON[k]
        ? '<svg class="glyph" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + ICON[k] + '</svg>'
        : '';
    }

    var ACTIONS = [
      { t: "Home",               i: "home", k: "sakib start", go: HOME },
      { t: "Ventures",           i: "grid", k: "mains sides projects built", go: HOME + "ventures/" },
      { t: "MiniDeed",           i: "heart", k: "charity app likes pennies main", go: HOME + "ventures/minideed/" },
      { t: "Simply Smashed",     i: "burger", k: "burger joint main food", go: HOME + "ventures/simply-smashed/" },
      { t: "Peruvian Street Kitchen", i: "bowl", k: "psk chicken rice green sauce main", go: HOME + "ventures/psk/" },
      { t: "Draper",             i: "pen", k: "founders authorities content main work", go: HOME + "ventures/draper/" },
      { t: "dhikry",             i: "beads", k: "side dhikr circle invite ios", go: HOME + "ventures/dhikry/" },
      { t: "Bilal",              i: "tv", k: "side athan masjid times tv", go: HOME + "ventures/bilal/" },
      { t: "vibenasheeds",       i: "waves", k: "side halal music nasheed ai", go: HOME + "ventures/vibenasheeds/" },
      { t: "Lofi Muslim",        i: "phones", k: "side beats youtube vocals", go: HOME + "ventures/lofi-muslim/" },
      { t: "Simply Clo",         i: "shirt", k: "side hoodie palestine clothing", go: HOME + "ventures/simply-clo/" },
      { t: "Simply Foundation",  i: "book", k: "side school huffadh charity", go: HOME + "ventures/simply-foundation/" },
      { t: "Chapters",           i: "scroll", k: "story writing timeline", go: HOME + "chapters/" },
      { t: "How this site works", i: "pencil", k: "craft colophon design type", go: HOME + "craft/" },
      { t: "Toggle dark mode",   i: "moon", k: "theme light night maghrib", fn: toggleTheme },
      { t: "Count tasbih",       i: "dot", k: "dhikr beads 33", fn: function () { var b = $("#tasbih"); if (b) b.click(); } },
      { t: "Copy email",         i: "at",      k: "contact mail", fn: function () {
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
        li.innerHTML = (a.i ? svg(a.i) : "<span class='glyph'>" + (a.g || "") + "</span>") + "<span>" + a.t + "</span>";
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
