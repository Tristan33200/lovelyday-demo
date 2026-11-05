document.documentElement.classList.add("js");

// Dans un cadre (aperçu sur iPhone), la page parente garde sa position de défilement :
// on remonte en haut à chaque nouvelle page, sinon on croit que le lien n'a pas marché.
(function () {
  var framed = false;
  try { framed = window.self !== window.top; } catch (e) { framed = true; }
  if (!framed || location.hash) return;
  function top() {
    window.scrollTo(0, 0);
    try { document.documentElement.scrollIntoView({ block: "start" }); } catch (e) {}
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", top); else top();
  window.addEventListener("pageshow", top);
})();

// Menu mobile
(function () {
  var btn = document.querySelector(".menu-btn");
  var nav = document.querySelector(".mobile-nav");
  if (!btn || !nav) return;
  btn.addEventListener("click", function () {
    var open = nav.getAttribute("data-open") === "true";
    nav.setAttribute("data-open", open ? "false" : "true");
    btn.setAttribute("aria-expanded", open ? "false" : "true");
    btn.textContent = open ? btn.dataset.open : btn.dataset.close;
  });
})();

// Légère montée des blocs au défilement (le contenu reste visible sans JS)
(function () {
  if (!("IntersectionObserver" in window)) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  var els = document.querySelectorAll(".reveal");
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.remove("pre"); io.unobserve(e.target); }
    });
  }, { rootMargin: "0px 0px -8% 0px" });
  els.forEach(function (el) {
    if (el.getBoundingClientRect().top > window.innerHeight) { el.classList.add("pre"); io.observe(el); }
  });
})();

// Titres « façon écriture » : les lettres apparaissent l'une après l'autre, comme tracées à l'encre
(function () {
  if (!("IntersectionObserver" in window)) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  var vh0 = window.innerHeight;
  function split(h) {
    var tmp = h.cloneNode(true);
    tmp.querySelectorAll("br").forEach(function (b) { b.replaceWith(" "); });
    var label = tmp.textContent.replace(/\s+/g, " ").trim();
    var n = 0;
    function walk(node, out) {
      Array.prototype.slice.call(node.childNodes).forEach(function (ch) {
        if (ch.nodeType === 3) {
          ch.textContent.split(/(\s+)/).forEach(function (part) {
            if (!part) return;
            if (/^\s+$/.test(part)) { out.appendChild(document.createTextNode(" ")); return; }
            var w = document.createElement("span");
            w.className = "tw";
            Array.from(part).forEach(function (c) {
              var l = document.createElement("span");
              l.className = "tc";
              l.textContent = c;
              l.style.setProperty("--i", n++);
              w.appendChild(l);
            });
            out.appendChild(w);
          });
        } else if (ch.nodeType === 1 && ch.tagName !== "BR") {
          var copy = ch.cloneNode(false);
          walk(ch, copy);
          out.appendChild(copy);
        } else {
          out.appendChild(ch.cloneNode(true));
        }
      });
    }
    var wrap = document.createElement("span");
    wrap.setAttribute("aria-hidden", "true");
    walk(h, wrap);
    h.textContent = "";
    h.appendChild(wrap);
    h.setAttribute("aria-label", label);
    h.style.setProperty("--step", Math.min(38, 1500 / Math.max(n, 1)).toFixed(1) + "ms");
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      io.unobserve(e.target);
      e.target.classList.remove("ink-pre");
    });
  }, { rootMargin: "0px 0px -8% 0px" });
  var later = [];
  document.querySelectorAll(".h1, .h2, .article h2").forEach(function (h) {
    if (h.closest(".lb")) return;
    if (h.getBoundingClientRect().top < vh0) {
      // titre déjà à l'écran : il s'écrit dès le chargement
      split(h);
      h.classList.add("ink", "ink-pre");
      requestAnimationFrame(function () { requestAnimationFrame(function () { h.classList.remove("ink-pre"); }); });
    } else later.push(h);
  });
  // les autres titres sont préparés quand le navigateur est libre (page plus fluide au chargement)
  var idle = window.requestIdleCallback || function (fn) { return setTimeout(function () { fn({ timeRemaining: function () { return 8; } }); }, 200); };
  function prep(dl) {
    while (later.length && dl.timeRemaining() > 2) {
      var h = later.shift();
      if (h.getBoundingClientRect().top < window.innerHeight) continue; // déjà visible : on le laisse tel quel
      split(h);
      h.classList.add("ink", "ink-pre");
      io.observe(h);
    }
    if (later.length) idle(prep);
  }
  idle(prep);
})();

// Chiffres clés : chaque chiffre défile comme un compteur avant de se poser
(function () {
  var nums = document.querySelectorAll(".figures strong");
  if (!nums.length || !("IntersectionObserver" in window)) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  nums.forEach(function (el) {
    var value = el.textContent.trim();
    if (!/^\d+$/.test(value)) return;
    el.setAttribute("aria-label", value);
    var html = '<span class="odo" aria-hidden="true">';
    Array.from(value).forEach(function (d, k) {
      var strip = "";
      for (var i = 0; i <= 10 + +d; i++) strip += "<span>" + (i % 10) + "</span>";
      html += '<span class="odo-col" style="--to:' + (10 + +d) + ';--k:' + k + '"><span class="odo-strip">' + strip + "</span></span>";
    });
    el.innerHTML = html + "</span>";
  });
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      io.unobserve(e.target);
      e.target.classList.add("odo-go");
    });
  }, { rootMargin: "0px 0px -10% 0px" });
  document.querySelectorAll(".figures > div").forEach(function (d, i) { d.style.setProperty("--n", i); io.observe(d); });
})();

// Mouvement des photos : dévoilement à l'entrée, profondeur au défilement.
// Au repos, chaque photo est entière : aucun zoom ne la rogne.
(function () {
  if (!("IntersectionObserver" in window)) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  var vh0 = window.innerHeight;

  // 1. Dévoilement : le cadre s'ouvre de bas en haut, la photo se pose
  var uvio = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      uvio.unobserve(e.target);
      var f = e.target, im = f.querySelector("img");
      function go() { f.classList.remove("uv-pre"); }
      if (!im || im.complete) go(); else { im.addEventListener("load", go); im.addEventListener("error", go); setTimeout(go, 1500); }
    });
  }, { rootMargin: "0px 0px 0px 0px" });
  document.querySelectorAll("figure.zoom, .g-row figure, .article figure, figure.post-cover").forEach(function (f) {
    if (f.getBoundingClientRect().top < vh0) return;
    var row = f.parentNode.classList.contains("g-row") ? Array.prototype.indexOf.call(f.parentNode.children, f) : 0;
    f.style.setProperty("--uv-delay", row * 100 + "ms");
    f.classList.add("uv", "uv-pre");
    uvio.observe(f);
  });

  // 2. Profondeur : les blocs photo glissent un peu moins vite que le texte ;
  //    seules les grandes images de fond glissent dans leur cadre
  var items = [];
  document.querySelectorAll(".split .s-img, .split .s-img-sm, .mosaic figure").forEach(function (el, i) {
    var d = el.classList.contains("s-img-sm") ? 0.12 : el.closest(".mosaic") ? (i % 2 ? 0.1 : 0.05) : 0.07;
    items.push({ el: el, d: d, t: 0, bg: false });
  });
  document.querySelectorAll("main .h2").forEach(function (el) {
    if (!el.closest(".band")) items.push({ el: el, d: -0.035, t: 0, bg: false });
  });
  document.querySelectorAll(".band .band-text").forEach(function (el) { items.push({ el: el, d: -0.08, t: 0, bg: false }); });
  var heroText = document.querySelector(".hero .hero-text");
  if (heroText) items.push({ el: heroText, d: 0, t: 0, bg: false, fade: true });
  document.querySelectorAll(".hero > img, .band > img").forEach(function (img) {
    img.classList.add("px");
    items.push({ el: img, d: 0, t: 0, bg: true });
  });
  var live = new Set(), ticking = false;
  function update() {
    ticking = false;
    var vh = window.innerHeight, k = window.innerWidth < 700 ? 0.6 : 1;
    var jobs = [];
    live.forEach(function (it) { jobs.push([it, (it.bg ? it.el.parentNode : it.el).getBoundingClientRect()]); });
    jobs.forEach(function (j) {
      var it = j[0], r = j[1], top = r.top - (it.bg ? 0 : it.t);
      var p = Math.max(-1, Math.min(1, (top + r.height / 2 - vh / 2) / (vh / 2 + r.height / 2)));
      if (it.bg) { it.el.style.setProperty("--py", (p * -0.05 * r.height).toFixed(1) + "px"); return; }
      if (it.fade) {
        var h = it.el.parentNode.getBoundingClientRect(), q = Math.max(0, Math.min(1, -h.top / h.height));
        it.el.style.translate = "0 " + (q * -90).toFixed(1) + "px";
        it.el.style.opacity = (1 - q * 1.4).toFixed(3);
        return;
      }
      it.t = p * vh * 0.5 * it.d * k;
      it.el.style.translate = "0 " + it.t.toFixed(1) + "px";
    });
  }
  function ask() { if (!ticking) { ticking = true; requestAnimationFrame(update); } }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      var it = items.filter(function (x) { return (x.bg ? x.el.parentNode : x.el) === e.target; })[0];
      if (it) { if (e.isIntersecting) live.add(it); else live.delete(it); }
    });
    ask();
  }, { rootMargin: "20% 0px" });
  items.forEach(function (it) { io.observe(it.bg ? it.el.parentNode : it.el); });
  window.addEventListener("scroll", ask, { passive: true });
  window.addEventListener("resize", ask);
})();

// Photos : on lance le chargement bien avant qu'elles n'arrivent à l'écran
(function () {
  if (!("IntersectionObserver" in window)) return;
  var pre = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      pre.unobserve(e.target);
      e.target.loading = "eager";
    });
  }, { rootMargin: "250% 0px" });
  document.querySelectorAll('img[loading="lazy"]').forEach(function (img) { pre.observe(img); });
})();

// Photos : apparition douce une fois chargées
(function () {
  document.querySelectorAll(".g-row img, .article figure img, .hscroll figure img").forEach(function (img) {
    function show() { img.classList.add("is-in"); }
    if (img.complete) show(); else { img.addEventListener("load", show); img.addEventListener("error", show); }
  });
})();

// Vue en grand : clic sur une photo de galerie ou d'article
(function () {
  var imgs = Array.prototype.slice.call(document.querySelectorAll(".g-row img, .article figure img, .hscroll figure img"));
  if (!imgs.length) return;
  var en = document.documentElement.lang === "en";
  var arrow = function (d) { return '<svg viewBox="0 0 22 44" aria-hidden="true"><path d="' + d + '"/></svg>'; };
  var lb = document.createElement("div");
  lb.className = "lb";
  lb.setAttribute("role", "dialog");
  lb.setAttribute("aria-modal", "true");
  lb.setAttribute("aria-label", en ? "Photo viewer" : "Visionneuse de photos");
  lb.innerHTML =
    '<div class="lb-bar"><span class="lb-count"></span><button type="button" class="lb-btn lb-close">' + (en ? "Close" : "Fermer") + ' &#215;</button></div>' +
    '<div class="lb-stage"><img alt=""><span class="lb-credit"></span>' +
    '<button type="button" class="lb-nav lb-prev" aria-label="' + (en ? "Previous photo" : "Photo précédente") + '">' + arrow("M20 2 2 22l18 20") + '</button>' +
    '<button type="button" class="lb-nav lb-next" aria-label="' + (en ? "Next photo" : "Photo suivante") + '">' + arrow("M2 2l18 20L2 42") + '</button></div>' +
    '<div class="lb-foot"></div>';
  document.body.appendChild(lb);
  var view = lb.querySelector(".lb-stage img"), count = lb.querySelector(".lb-count"), credit = lb.querySelector(".lb-credit");
  var closeBtn = lb.querySelector(".lb-close"), i = 0, lastFocus = null;

  function show(n, dir) {
    i = (n + imgs.length) % imgs.length;
    var src = imgs[i];
    count.textContent = (i + 1) + " / " + imgs.length;
    view.classList.add("is-out");
    view.style.translate = (dir || 0) * 24 + "px 0";
    var next = new Image();
    next.onload = next.onerror = function () {
      view.src = src.currentSrc || src.src;
      view.alt = src.alt;
      var c = src.parentNode.querySelector(".credit");
      credit.textContent = c ? c.textContent : "";
      requestAnimationFrame(function () { view.classList.remove("is-out"); view.style.translate = "0 0"; });
    };
    next.src = src.currentSrc || src.src;
    [i + 1, i - 1].forEach(function (k) { var p = imgs[(k + imgs.length) % imgs.length]; (new Image()).src = p.currentSrc || p.src; });
  }
  function open(n) {
    lastFocus = document.activeElement;
    show(n, 0);
    lb.setAttribute("data-open", "true");
    document.documentElement.classList.add("lb-lock");
    closeBtn.focus();
  }
  function close() {
    lb.setAttribute("data-open", "false");
    document.documentElement.classList.remove("lb-lock");
    if (lastFocus) lastFocus.focus();
  }

  imgs.forEach(function (img, n) {
    var fig = img.parentNode;
    fig.setAttribute("data-zoom", "");
    img.setAttribute("tabindex", "0");
    img.setAttribute("role", "button");
    fig.addEventListener("click", function () { open(n); });
    img.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(n); } });
  });
  closeBtn.addEventListener("click", close);
  lb.querySelector(".lb-prev").addEventListener("click", function () { show(i - 1, -1); });
  lb.querySelector(".lb-next").addEventListener("click", function () { show(i + 1, 1); });
  lb.addEventListener("click", function (e) { if (e.target === lb || e.target.classList.contains("lb-stage") || e.target.classList.contains("lb-foot")) close(); });
  document.addEventListener("keydown", function (e) {
    if (lb.getAttribute("data-open") !== "true") return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowRight") show(i + 1, 1);
    else if (e.key === "ArrowLeft") show(i - 1, -1);
    else if (e.key === "Tab") { e.preventDefault(); closeBtn.focus(); }
  });

  // Glisser du doigt pour passer d'une photo à l'autre
  var x0 = null, y0 = 0;
  lb.addEventListener("touchstart", function (e) { x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; view.style.transition = "none"; }, { passive: true });
  lb.addEventListener("touchmove", function (e) { if (x0 !== null) view.style.translate = (e.touches[0].clientX - x0) + "px 0"; }, { passive: true });
  lb.addEventListener("touchend", function (e) {
    if (x0 === null) return;
    var dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
    x0 = null;
    view.style.transition = "";
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) show(i + (dx < 0 ? 1 : -1), dx < 0 ? 1 : -1);
    else if (dy > 90 && Math.abs(dy) > Math.abs(dx)) close();
    else view.style.translate = "0 0";
  });
})();

// Formulaire de contact : prépare un e-mail dans la messagerie du visiteur
(function () {
  var form = document.querySelector("form.enquiry");
  if (!form) return;
  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var note = form.querySelector(".form-note");
    if (!form.checkValidity()) { form.reportValidity(); return; }
    var d = new FormData(form);
    var lines = [];
    form.querySelectorAll("[name]").forEach(function (el) {
      var lab = form.querySelector('label[for="' + el.id + '"]');
      if (el.name && d.get(el.name)) lines.push((lab ? lab.textContent : el.name) + " : " + d.get(el.name));
    });
    var subject = form.dataset.subject + " · " + (d.get("names") || "");
    var href = "mailto:contact@lovelydayevent.fr?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(lines.join("\n"));
    note.textContent = form.dataset.done;
    note.setAttribute("data-state", "ok");
    window.location.href = href;
  });
})();

/* Carrousels de photos dans les articles */
document.querySelectorAll('[data-carousel]').forEach(function (car) {
  var track = car.querySelector('.car-track'), slides = track.querySelectorAll('figure');
  var prev = car.querySelector('.car-prev'), next = car.querySelector('.car-next'), num = car.querySelector('.car-count b');
  function current() {
    var mid = track.scrollLeft + track.clientWidth / 2, best = 0, d = 1e9;
    slides.forEach(function (s, i) { var c = s.offsetLeft - track.offsetLeft + s.offsetWidth / 2, x = Math.abs(c - mid); if (x < d) { d = x; best = i; } });
    return best;
  }
  function go(i) { i = Math.max(0, Math.min(slides.length - 1, i)); var s = slides[i]; track.scrollTo({ left: s.offsetLeft - track.offsetLeft - (track.clientWidth - s.offsetWidth) / 2 }); }
  function update() { var i = current(); num.textContent = i + 1; prev.disabled = track.scrollLeft < 4; next.disabled = track.scrollLeft + track.clientWidth > track.scrollWidth - 4; }
  prev.addEventListener('click', function () { go(current() - 1); });
  next.addEventListener('click', function () { go(current() + 1); });
  track.addEventListener('keydown', function (e) { if (e.key === 'ArrowRight') { e.preventDefault(); go(current() + 1); } if (e.key === 'ArrowLeft') { e.preventDefault(); go(current() - 1); } });
  track.addEventListener('scroll', function () { window.requestAnimationFrame(update); }, { passive: true });
  update();
});

// Suites de photos : la section reste épinglée et les photos défilent de droite à gauche au scroll
(function () {
  var boxes = Array.prototype.slice.call(document.querySelectorAll(".hscroll"));
  if (!boxes.length) return;
  if (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches) {
    boxes.forEach(function (b) { b.classList.add("hs-static"); });
    return;
  }
  var ticking = false;
  function layout() {
    boxes.forEach(function (b) {
      var track = b.querySelector(".hs-track");
      var dist = Math.max(0, track.scrollWidth - window.innerWidth);
      b._dist = dist;
      b.style.height = (window.innerHeight + dist) + "px";
    });
    update();
  }
  function update() {
    ticking = false;
    boxes.forEach(function (b) {
      var r = b.getBoundingClientRect();
      var span = b.offsetHeight - window.innerHeight;
      var p = span > 0 ? Math.max(0, Math.min(1, -r.top / span)) : 0;
      b.querySelector(".hs-track").style.transform = "translate3d(" + (-p * b._dist).toFixed(1) + "px,0,0)";
      // chaque photo monte du bas vers le haut en entrant par la droite
      var vw = window.innerWidth;
      Array.prototype.forEach.call(b.querySelectorAll(".hs-fig"), function (f) {
        var x = f.getBoundingClientRect().left;
        var k = Math.max(0, Math.min(1, (vw - x) / (vw * 0.45)));
        var e = 1 - Math.pow(1 - k, 3);
        f.style.transform = "translate3d(0," + ((1 - e) * 90).toFixed(1) + "px,0)";
        f.style.opacity = (0.25 + 0.75 * e).toFixed(3);
      });
    });
  }
  window.addEventListener("scroll", function () { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
  window.addEventListener("resize", layout);
  window.addEventListener("load", layout);
  layout();
})();
