#!/usr/bin/env python3
"""Génère le site Lovely Day Event.

FR à la racine, EN dans /en/. Les adresses reprennent celles du site WordPress
actuel (/prestations/, /contact/, /<slug-article>/…) pour garder le référencement.

    python3 build.py <dossier>             # version à héberger (liens « dossier/ »)
    python3 build.py <dossier> --preview   # aperçu hors serveur (liens « dossier/index.html »)
"""
import os, sys, re, json, html as H

OUT = sys.argv[1] if len(sys.argv) > 1 else "site"
PREVIEW = "--preview" in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
SITE_URL = "https://lovelydayevent.fr/"

ROUTES = {
    "index": "",
    "agence": "agence-evenementielle/",
    "prestations": "prestations/",
    "mariages": "weddingbook-exemples-de-mariages/",
    "inspirations": "les-idees-de-lovely-day-inspirations/",
    "photobooth": "location-photobooth-gironde-bordeaux/",
    "contact": "contact/",
    "mentions": "mentions-legales-et-cgu/",
}
NAV = {
    "fr": [("index", "Accueil"), ("agence", "L'agence"), ("prestations", "Prestations"), ("mariages", "Mariages"), ("inspirations", "Inspirations"), ("contact", "Contact")],
    "en": [("index", "Home"), ("agence", "About"), ("prestations", "Services"), ("mariages", "Weddings"), ("inspirations", "Inspiration"), ("contact", "Contact")],
}
TP = "TristanPerrier"

# ------------------------------------------------------------ Articles
POSTS = json.load(open(os.path.join(HERE, "posts.json"), encoding="utf-8"))
for _p in POSTS:
    _p["title"] = re.sub(r"\s*(Lovely Day Event)?\s*33\s*$", "", _p["title"]).strip()
    # titres trop longs (introduction reprise comme titre) : on garde la première phrase
    if len(_p["title"]) > 110:
        _p["title"] = re.split(r"(?<=[.!?])\s", _p["title"])[0].strip()
    # majuscules des noms propres
    for _a, _b in (("bordeaux", "Bordeaux"), ("tristan perrier", "Tristan Perrier"), ("bassin d'arcachon", "Bassin d'Arcachon"),
                   ("Cap ferret", "Cap Ferret"), ("eco-responsable", "éco-responsable"), ("mariage: ", "mariage : ")):
        _p["title"] = re.sub(r"\b" + re.escape(_a), _b, _p["title"])
# Parution programmée (demande de Tristan, 2026-11-05) : un article par mois.
# La date de l'article devient sa date de parution ; avant cette date il n'est pas généré.
# PUBLISH_DATE=AAAA-MM-JJ simule la date du jour (mkprod.sh prépare ainsi les versions à venir).
SCHEDULE = {
    "menudemariage": "2026-12-01",
    "rituels-mariage-ceremonie-origines-handfasting": "2027-01-01",
    "psychologie-couleurs-mariage-palettes": "2027-02-01",
    "scenarios-secours-plan-b-mariage": "2027-03-01",
    "personnalites-famille-conflits-conseils": "2027-04-01",
    "kit-experience-temoins-demoiselles-honneur": "2027-05-01",
}
import datetime as _dt
PUBLISH_DATE = os.environ.get("PUBLISH_DATE") or _dt.date.today().isoformat()
for _p in POSTS:
    if _p["slug"] in SCHEDULE:
        _p["date"] = SCHEDULE[_p["slug"]]
UNPUBLISHED = {p["slug"] for p in POSTS if p["date"] > PUBLISH_DATE}
POSTS = [p for p in POSTS if p["slug"] not in UNPUBLISHED]
POST_BY_SLUG = {p["slug"]: p for p in POSTS}
IMG_MAP = {}
for line in open(os.path.join(HERE, "img_map.tsv"), encoding="utf-8").read().splitlines():
    u, n, st = line.split("\t")
    if not st.startswith("ERR"):
        IMG_MAP[u] = n
sys.path.insert(0, HERE)
from weddings_en import EN as WED_EN, FR_HEAD_FIX
from tristan_post import apply_tristan_post, TP_IMGS
apply_tristan_post(POSTS, IMG_MAP)
# récits retirés à la demande d'Alexandra (2026-11-04) ; anciennes adresses redirigées vers le Weddingbook
REMOVED_WED = {"delphine-ludovic", "emilie-aurelien", "melissa-sebastien-boheme-mariafe", "mai-rufus", "marie-martin"}
WEDDING_SLUGS = [s for s in WED_EN if s not in REMOVED_WED]
BLOG = sorted([p for p in POSTS if p["slug"] not in WED_EN], key=lambda p: p["date"], reverse=True)

# Traductions anglaises des articles : posts_en/<slug>.txt (repères [T] titre, [D] description,
# [n] bloc n, [a n] texte alternatif de l'image n) + posts_en/_common.txt (blocs répétés, repère [FR]/[EN])
EN_DIR = os.path.join(HERE, "posts_en")
SEG_RE = re.compile(r"^\[(T|D|a?\d+)\] ?", re.M)


def parse_segs(txt):
    parts = SEG_RE.split(txt)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


COMMON_EN = {}
if os.path.exists(os.path.join(EN_DIR, "_common.txt")):
    for blk in open(os.path.join(EN_DIR, "_common.txt"), encoding="utf-8").read().split("\n[FR] ")[1:]:
        fr, en = blk.split("\n[EN] ", 1)
        COMMON_EN[fr.strip()] = en.strip()
POSTS_EN = {}
for p in (BLOG if os.environ.get("EN_POSTS", "1") == "1" else []):
    f = os.path.join(EN_DIR, p["slug"] + ".txt")
    if os.path.exists(f):
        POSTS_EN[p["slug"]] = parse_segs(open(f, encoding="utf-8").read())


def loc(c, p):
    """L'article dans la langue de la page."""
    if c.lang != "en" or p["slug"] not in POSTS_EN:
        return p
    e = POSTS_EN[p["slug"]]
    q = dict(p, title=e.get("T", p["title"]), desc=e.get("D", p["desc"]))
    bl = []
    for i, b in enumerate(p["blocks"]):
        b = dict(b)
        if b["t"] in ("html", "h2", "h3", "quote"):
            b["v"] = e.get(str(i)) or COMMON_EN.get(b["v"].strip(), b["v"])
        if b["t"] == "img" and b.get("alt"):
            b["alt"] = e.get("a" + str(i)) or COMMON_EN.get(b["alt"].strip(), b["alt"])
        bl.append(b)
    q["blocks"] = bl
    return q


if "--extract" in sys.argv:
    import collections
    cnt = collections.Counter(b["v"].strip() for p in BLOG for b in p["blocks"] if b["t"] in ("html", "h2", "h3", "quote"))
    os.makedirs("src_en", exist_ok=True)
    with open("src_en/_common.txt", "w", encoding="utf-8") as f:
        for v, n in cnt.most_common():
            if n > 1:
                f.write(f"\n[FR] {v}\n[EN] \n")
    for k, p in enumerate(BLOG):
        lines = [f"[T] {p['title']}", f"[D] {p['desc']}"]
        for i, b in enumerate(p["blocks"]):
            if b["t"] in ("html", "h2", "h3", "quote") and cnt[b["v"].strip()] == 1:
                lines.append(f"[{i}] {b['v']}")
            elif b["t"] == "img" and b.get("alt") and cnt[b["alt"].strip()] <= 1:
                lines.append(f"[a{i}] {b['alt']}")
        open(f"src_en/{k:02d}_{p['slug']}.txt", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    sys.exit(0)

# Aperçu : nombre de fichiers limité, on garde une sélection d'images
ALLOWED_J = None
if PREVIEW and os.path.exists(os.path.join(HERE, "preview_imgs.json")):
    ALLOWED_J = set(json.load(open(os.path.join(HERE, "preview_imgs.json"))))
    ALLOWED_J |= set(TP_IMGS.values())
USED_J = []  # ordre de priorité des images d'articles utilisées


def jname(url):
    n = IMG_MAP.get(url)
    if not n:
        return None
    if n not in USED_J:
        USED_J.append(n)
    if ALLOWED_J is not None and n not in ALLOWED_J:
        return None
    return n


ROUTES_EN = {
    "index": "", "agence": "about/", "prestations": "services/", "mariages": "weddings/",
    "inspirations": "journal/", "photobooth": "photo-booth-hire-bordeaux/", "contact": "contact/", "mentions": "legal-notice/",
}
_EN_SLUGS = {}
_EN_STOP = set("a an the of and or for to in on at by with your you our my is are be how what why which who it its this that from as do does can should will we i us".split())


def _slugify_en(text, n=8):
    import unicodedata
    t = unicodedata.normalize("NFKD", H.unescape(text)).encode("ascii", "ignore").decode().lower()
    w = [x for x in re.split(r"[^a-z0-9]+", t) if x and x not in _EN_STOP]
    return "-".join(w[:n])


def en_slug(slug):
    """Adresse anglaise d'un article ou d'un récit (tirée du titre anglais)."""
    if not _EN_SLUGS:
        used = set(ROUTES_EN.values())
        for s in sorted(set(WEDDING_SLUGS) | set(POSTS_EN)):
            if s in WED_EN:
                base = _slugify_en(WED_NAMES.get(s, POST_BY_SLUG[s]["title"])) + "-wedding"
            else:
                base = _slugify_en(POSTS_EN[s].get("T", s)) or s
            cand, i = base, 2
            while cand + "/" in used:
                cand, i = f"{base}-{i}", i + 1
            used.add(cand + "/")
            _EN_SLUGS[s] = cand
    return _EN_SLUGS.get(slug, slug)


def route_of(key, lang="fr"):
    if lang == "en":
        if key.startswith("post:"):
            return "en/" + en_slug(key[5:]) + "/"
        return "en/" + ROUTES_EN[key]
    if key.startswith("post:"):
        return key[5:] + "/"
    return ROUTES[key]


def has_en(key):
    if key == "inspirations":
        return bool(POSTS_EN)
    return not key.startswith("post:") or key[5:] in WED_EN or key[5:] in POSTS_EN


_SIZES = {}


import hashlib as _h
ASSET_V = _h.md5(open(os.path.join(HERE,"site/assets/style.css"),"rb").read()+open(os.path.join(HERE,"site/assets/site.js"),"rb").read()).hexdigest()[:8]

def img_size(rel):
    """Dimensions réelles de l'image (pour réserver la place et composer les galeries)."""
    if rel not in _SIZES:
        try:
            from PIL import Image
            with Image.open(os.path.join(HERE, "site", rel)) as im:
                _SIZES[rel] = im.size
        except Exception:
            _SIZES[rel] = None
    return _SIZES[rel]


def gallery_rows(m):
    """Regroupe les photos d'une galerie en rangées de hauteur égale (1 à 3 photos)."""
    figs = re.findall(r"<figure.*?</figure>", m.group(2), re.S)
    def ar(f):
        d = re.search(r'width="(\d+)" height="(\d+)"', f)
        return int(d.group(1)) / int(d.group(2)) if d else 1.5
    if "data-carousel" in m.group(1):
        # longues suites de photos : la section reste épinglée et les photos défilent
        # de droite à gauche au fil du scroll (comme sur tristanperrier.fr)
        slides = "".join(f.replace("<figure", f'<figure class="hs-fig" style="--ar:{ar(f):.4f}"', 1) for f in figs)
        return f'<div class="hscroll"><div class="hs-sticky"><div class="hs-track">{slides}</div></div></div>'
    rows, cur = [], []
    for f in figs:
        cur.append(f)
        if sum(map(ar, cur)) >= 1.25 or len(cur) == 2:
            rows.append(cur)
            cur = []
    if cur:
        if rows and len(rows[-1]) == 2 and ar(cur[0]) < 1 and all(ar(x) < 1 for x in rows[-1]):
            rows[-1] += cur
        else:
            rows.append(cur)
    out = []
    for r in rows:
        if len(r) == 1 and ar(r[0]) < 1:
            out.append(f'<div class="g-row g-solo" style="--ar:{ar(r[0]):.4f}">{r[0]}</div>')
        else:
            out.append('<div class="g-row">' + "".join(f.replace("<figure", f'<figure style="flex:{ar(f):.4f} 1 0%"', 1) for f in r) + "</div>")
    return f'<div class="gallery"{m.group(1)}>{"".join(out)}</div>'


def add_srcset(m):
    """Version 800 px pour les téléphones quand la photo d'origine est plus large."""
    src, rest = m.group(1), m.group(2)
    rel = re.sub(r"^(\.\./)+|^\./", "", src)
    if "srcset" in rest or not os.path.exists(os.path.join(HERE, "site", rel + ".w800.webp")):
        return m.group(0)
    w = (img_size(rel + ".webp") or (1600, 0))[0]
    sizes = "100vw" if ("fetchpriority" in rest or 'class="cover"' not in rest and "width=" not in rest) else "(max-width: 900px) 100vw, 60vw"
    return f'<img src="{src}.webp" srcset="{src}.w800.webp 800w, {src}.webp {w}w" sizes="{sizes}"{rest}>'


PORTRAIT_FRAMES = ("ratio-tall", "ratio-portrait")


def pick_fitting(cands, ratio):
    """Première photo dont l'orientation convient au cadre (évite de couper un portrait dans un cadre paysage, et inversement)."""
    want_portrait = ratio in PORTRAIT_FRAMES
    usable = []
    for kind, v in cands:
        if not v:
            continue
        if kind == "img":
            rel = f"img/{v}.webp"
        else:
            n = IMG_MAP.get(v)
            if not n or (ALLOWED_J is not None and n not in ALLOWED_J):
                continue
            rel = f"img/journal/{n}"
        wh = img_size(rel)
        if not wh:
            continue
        usable.append((kind, v))
        ar = wh[0] / wh[1]
        if (want_portrait and ar < 0.95) or (not want_portrait and ar > 1.1):
            return kind, v
    return usable[0] if usable else (cands[0] if cands else (None, None))


def fitted_img(c, cands, alt, ratio):
    kind, v = pick_fitting(cands, ratio)
    if kind == "img":
        return c.img(v, alt, ratio)
    return c.jimg(v, alt, ratio) if v else ""


class Ctx:
    def __init__(self, lang, page):
        self.lang, self.page = lang, page
        path = route_of(page, lang)
        self.depth = path.count("/")
        self.root = "../" * self.depth

    def t(self, fr, en):
        return fr if self.lang == "fr" else en

    def href(self, page, lang=None):
        lang = lang or self.lang
        if lang == "en" and not has_en(page):
            page = "mariages" if page.startswith("post:") else "index"
        r = route_of(page, lang)
        if PREVIEW:
            r += "index.html"
        return (self.root + r) or "./"

    def img(self, name, alt, ratio="", cls="", eager=False, ext=None, folder="img"):
        ext = ext or ("png" if name in ("wedding-academy", "branche") else "webp")
        src = f"{self.root}{folder}/{name}" + ("" if name.endswith(".webp") else f".{ext}")
        credit = '<span class="credit">© Tristan Perrier</span>' if TP in name else ""
        load = "eager" if eager else "lazy"
        wh = img_size(f"{folder}/{name}" + ("" if name.endswith(".webp") else f".{ext}"))
        dim = f' width="{wh[0]}" height="{wh[1]}" style="--ar:{wh[0] / wh[1]:.4f}"' if wh else ""
        inner = f'<img src="{src}" alt="{H.escape(alt)}"{dim} loading="{load}" decoding="async" class="{"cover" if ratio else ""}">'
        rc = f"{ratio} zoom" if ratio else ""
        klass = " ".join(x for x in (rc, cls) if x)
        return f'<figure class="{klass}">{inner}{credit}</figure>'

    def jimg(self, url, alt="", ratio="", cls="", eager=False):
        n = jname(url)
        if not n:
            return ""
        credit_name = TP in n or "tristan" in url.lower()
        out = self.img(n, alt, ratio, cls, eager, folder="img/journal")
        if credit_name and "credit" not in out:
            out = out.replace("</figure>", '<span class="credit">© Tristan Perrier</span></figure>')
        return out


def header(c):
    items = [f'<a href="{c.href(p)}"{" aria-current=\"page\"" if p == c.page else ""}>{lab}</a>'
             for p, lab in NAV[c.lang] if p not in ("index", "contact") and has_en(p) | (c.lang == "fr")]
    # menu réparti de part et d'autre du logo : 3 liens à gauche, le reste à droite avec Contact
    links, links_r = "".join(items[:3]), "".join(items[3:])
    lang = (f'<span class="lang"><a href="{c.href(c.page, "fr")}"{" aria-current=\"true\"" if c.lang=="fr" else ""} hreflang="fr" lang="fr">FR</a>'
            f'<a href="{c.href(c.page, "en")}"{" aria-current=\"true\"" if c.lang=="en" else ""} hreflang="en" lang="en">EN</a></span>')
    mob = "".join(f'<a href="{c.href(p)}">{lab}</a>' for p, lab in NAV[c.lang] if c.lang == "fr" or has_en(p))
    return f'''<header class="site-header">
  <div class="wrap bar">
    <nav class="nav" aria-label="{c.t("Navigation principale", "Main navigation")}">{links}</nav>
    <a class="brand" href="{c.href("index")}">Lovely Day Event<small>Wedding Planner</small></a>
    <div class="nav-r">{links_r}<a href="{c.href("contact")}"{" aria-current=\"page\"" if c.page=="contact" else ""}>{c.t("Contact", "Enquire")}</a>{lang}</div>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="mnav" data-open="Menu" data-close="{c.t("Fermer", "Close")}">Menu</button>
  </div>
  <div class="wrap"><nav class="mobile-nav" id="mnav" data-open="false">{mob}{lang}</nav></div>
</header>'''


def footer(c):
    nav = "".join(f'<a href="{c.href(p)}">{lab}</a>' for p, lab in NAV[c.lang] if c.lang == "fr" or has_en(p))
    more = "".join(f'<a href="{c.href(p)}">{lab}</a>' for p, lab in (
        ("photobooth", c.t("Location photobooth", "Photo booth rental")),))
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div class="footer-top">
      <div>
        <a class="brand" href="{c.href("index")}" style="text-align:left">Lovely Day Event<small>Wedding Planner</small></a>
        <p class="small" style="max-width:34ch;margin-top:18px">{c.t("Organisation et design de mariages sur mesure. Bordeaux, Dordogne, Bassin d'Arcachon, Pays Basque et partout en France.", "Bespoke wedding planning and design. Bordeaux, Dordogne, Arcachon Bay, the Basque Country and throughout France.")}</p>
      </div>
      <div><span class="label">{c.t("Pages", "Pages")}</span>{nav}{more}</div>
      <div><span class="label">Contact</span>
        <a href="mailto:contact@lovelydayevent.fr">contact@lovelydayevent.fr</a>
        <a href="tel:+33689966731">+33 6 89 96 67 31</a>
        <span class="small">Bordeaux, Gironde</span>
      </div>
      <div><span class="label">{c.t("Suivre", "Follow")}</span>
        <a href="https://www.instagram.com/lovelydayevent/" target="_blank" rel="noopener">Instagram</a>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© 2026 Lovely Day Event · Alexandra Ambert</span>
      <span class="fb-credits"><span>{c.t("Site conçu par", "Website designed by")} Tristan Perrier</span><span>{c.t("Photographies :", "Photography:")} <a href="https://www.tristanperrier.fr/{c.t("", "en/")}" target="_blank" rel="noopener">Tristan Perrier</a> {c.t("et photographes partenaires", "and partner photographers")}</span></span>
      <a href="{c.href("mentions")}">{c.t("Mentions légales", "Legal notice")}</a>
    </div>
  </div>
</footer>'''


TITLES = {
    "index": ("Wedding Planner Bordeaux & organisation de mariage · Lovely Day Event", "Wedding Planner in Bordeaux, France · Lovely Day Event"),
    "agence": ("L'agence · Lovely Day Event", "About · Lovely Day Event"),
    "prestations": ("Prestations · Lovely Day Event", "Services · Lovely Day Event"),
    "mariages": ("Mariages · Lovely Day Event", "Weddings · Lovely Day Event"),
    "inspirations": ("Inspirations · Lovely Day Event", "Inspiration · Lovely Day Event"),
    "photobooth": ("Location photobooth à Bordeaux · Lovely Day Event", "Photo booth rental in Bordeaux · Lovely Day Event"),
    "location": ("Location de décoration de mariage · Lovely Day Event", "Wedding decor rental · Lovely Day Event"),
    "contact": ("Contact · Lovely Day Event", "Enquire · Lovely Day Event"),
    "mentions": ("Mentions légales · Lovely Day Event", "Legal notice · Lovely Day Event"),
}
DESCS = {
    "fr": "Wedding planner et designer à Bordeaux depuis 2014. Organisation, design et coordination de mariages sur mesure en Gironde, Dordogne, Bassin d'Arcachon, Pays Basque et partout en France.",
    "en": "Wedding planner and designer based in Bordeaux since 2014. Bespoke wedding planning, design and on-the-day coordination in Bordeaux, Dordogne, Arcachon Bay, the Basque Country and across France.",
}



ORG_ID = SITE_URL + "#organisation"
SAME_AS = ["https://www.instagram.com/lovelydayevent/", "https://www.mariages.net/organisation-mariage/lovely-day--e148855", "https://g.page/r/Ccty5Dtg7yumEAE"]


def org_ld(c):
    t = c.t
    return {
        "@type": ["LocalBusiness", "ProfessionalService"], "@id": ORG_ID,
        "name": "Lovely Day Event", "alternateName": "LOVELY DAY EVENT",
        "description": DESCS[c.lang], "url": SITE_URL,
        "image": SITE_URL + "img/MariageChateauGrattequina_TristanPerrier_NA-274.webp",
        "logo": SITE_URL + "assets/favicon.svg",
        "telephone": "+33689966731", "email": "contact@lovelydayevent.fr",
        "foundingDate": "2014", "priceRange": "€€€",
        "founder": {"@type": "Person", "name": "Alexandra Ambert", "jobTitle": t("Wedding planner et Wedding Designer certifiée", "Wedding planner and certified Wedding Designer")},
        "hasMap": "https://g.page/r/Ccty5Dtg7yumEAE",
        "address": {"@type": "PostalAddress", "streetAddress": "8 rue des Primevères", "postalCode": "33140", "addressLocality": "Villenave-d'Ornon", "addressRegion": "Nouvelle-Aquitaine", "addressCountry": "FR"},
        "geo": {"@type": "GeoCoordinates", "latitude": 44.7806, "longitude": -0.5583},
        "knowsAbout": [t("Organisation de mariage", "Wedding planning"), t("Décoration de mariage", "Wedding design"), t("Coordination jour J", "Wedding day coordination")],
        "areaServed": ["Bordeaux", "Gironde", t("Bassin d'Arcachon", "Arcachon Bay"), "Dordogne", t("Pays basque", "Basque Country"), "France"],
        "knowsLanguage": ["fr", "en"], "sameAs": SAME_AS,
    }


def faq_ld(body):
    qa = re.findall(r"<details><summary>(.*?)</summary><div class=\"ans\">(.*?)</div></details>", body, re.S)
    if not qa:
        return None
    clean = lambda x: H.unescape(re.sub(r"<[^>]+>", " ", x)).strip()
    return {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": clean(q), "acceptedAnswer": {"@type": "Answer", "text": " ".join(clean(a).split())}} for q, a in qa]}


def fix_headings(html):
    """Hiérarchie Hn sans saut (h1 > h2 > h3), sans changer l'apparence."""
    prev, stack = 1, []
    def rep(m):
        nonlocal prev
        close, lvl, attrs = m.group(1), int(m.group(2)), m.group(3) or ""
        if close:
            return f"</h{stack.pop() if stack else lvl}>"
        new = min(lvl, prev + 1)
        prev = new
        stack.append(new)
        if new != lvl and "class=" not in attrs:
            attrs += f' class="as-h{lvl}"'
        return f"<h{new}{attrs}>"
    return re.sub(r"<(/?)h([1-6])(\s[^>]*)?>", rep, html)


def abs_img(c, body):
    m = re.search(r'<img src="([^"]+\.(?:webp|jpg|png))"', body)
    if not m:
        return None
    src = m.group(1)
    if src.startswith("http"):
        return src
    return SITE_URL + re.sub(r"^(\.\./)+|^\./", "", src)


def page(c, body, title=None, desc=None, image=None):
    if title is None:
        title = TITLES[c.page][0 if c.lang == "fr" else 1]
    desc = desc or DESCS[c.lang]
    fr_url = SITE_URL + route_of(c.page)
    en_url = SITE_URL + route_of(c.page, "en")
    alt = f'<link rel="alternate" hreflang="fr" href="{fr_url}">'
    if has_en(c.page):
        alt += f'\n<link rel="alternate" hreflang="en" href="{en_url}">\n<link rel="alternate" hreflang="x-default" href="{fr_url}">'
    canonical = en_url if c.lang == "en" else fr_url
    body = fix_headings(body)
    # pas de mention « © Tristan Perrier » sur les photos (demande de Tristan, 2026-11-05) : crédit en pied de page, mentions légales et récits
    body = re.sub(r"\s*<span class=\"credit\">[^<]*</span>", "", body)
    is_post = c.page.startswith("post:")
    image = image or (abs_img(c, body) if is_post else None) or SITE_URL + "img/MariageChateauGrattequina_TristanPerrier_NA-274.webp"
    loc, loc_alt = ("fr_FR", "en_GB") if c.lang == "fr" else ("en_GB", "fr_FR")
    graph = [org_ld(c)]
    if c.page == "index":
        graph.append({"@type": "WebSite", "@id": SITE_URL + "#site", "url": SITE_URL, "name": "Lovely Day Event", "inLanguage": ["fr", "en"], "publisher": {"@id": ORG_ID}})
    if is_post:
        slug = c.page[5:]
        pd = next((p for p in POSTS if p["slug"] == slug), {})
        art = {"@type": "BlogPosting", "headline": title.split(" · ")[0], "description": desc, "image": image, "url": canonical,
               "mainEntityOfPage": canonical, "inLanguage": c.lang, "author": {"@type": "Person", "name": "Alexandra Ambert", "url": SITE_URL + "agence-evenementielle/"},
               "publisher": {"@id": ORG_ID}}
        if pd.get("date"):
            art["datePublished"] = pd["date"]
        graph.append(art)
    fq = faq_ld(body)
    if fq:
        graph.append(fq)
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("</", "<\\/")
    head = f'''<title>{H.escape(title)}</title>
<meta name="description" content="{H.escape(desc)}">
<link rel="canonical" href="{canonical}">
{alt}
<meta property="og:type" content="{"article" if is_post else "website"}">
<meta property="og:site_name" content="Lovely Day Event">
<meta property="og:locale" content="{loc}">
<meta property="og:locale:alternate" content="{loc_alt}">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{H.escape(title)}">
<meta property="og:description" content="{H.escape(desc)}">
<meta property="og:image" content="{image}">
<meta property="og:image:alt" content="{H.escape(title)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{H.escape(title)}">
<meta name="twitter:description" content="{H.escape(desc)}">
<meta name="twitter:image" content="{image}">
<script type="application/ld+json">{ld}</script>
<link rel="preload" href="{c.root}assets/fonts/CormorantGaramond-normal-300-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{c.root}assets/fonts/Jost-normal-300-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="icon" href="{c.root}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{c.root}assets/style.css?v={ASSET_V}">'''
    content = f'''{header(c)}
<main>
{body}
</main>
{footer(c)}
<script src="{c.root}assets/site.js?v={ASSET_V}"></script>'''
    if PREVIEW and c.lang == "fr" and c.page == "index":
        return head.replace(H.escape(title), "Lovely Day Event", 1) + "\n" + content
    return f'''<!doctype html>
<html lang="{c.lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{head}
</head>
<body>
{content}
</body>
</html>'''


# ---------------------------------------------------------------- Mariages
WEDDINGS = [
    dict(img="marie-charles", n="Marie & Charles", place="Château Pontac Lynch", date=("4 octobre 2025", "4 October 2025"),
         fr="Le 4 octobre 2025, Marie et Charles ont célébré leur mariage au Château Pontac Lynch entourés de 80 invités, dans une atmosphère rétro boudoir anglais, chic et pleine de caractère.",
         en="On 4 October 2025, Marie and Charles celebrated their wedding at Château Pontac Lynch surrounded by 80 guests, in a retro English boudoir atmosphere: chic and full of character."),
    dict(img="yvonne-thomas", n="Yvonne & Thomas", place="Château Belle Époque, Landes", date=("6 septembre 2025", "6 September 2025"),
         fr="Couple franco-allemand, Yvonne & Thomas ont traversé la France pour célébrer leur union au Château Belle Époque, dans les Landes. Pensé comme une parenthèse hors du temps, leur mariage s'est déployé sur quatre jours.",
         en="A Franco-German couple, Yvonne & Thomas crossed France to celebrate their union at Château Belle Époque, in the Landes. Imagined as a timeless interlude, their wedding unfolded over four days."),
    dict(img="alexandra-clement", n="Alexandra & Clément", place="Domaine de la Dame Blanche, Grignols", date=("2025", "2025"),
         fr="Alexandra & Clément ont imaginé un mariage à leur image : élégant, vintage, moka café, et surtout rempli de surprises. Entourés de 100 proches, chaque instant avait une saveur particulière.",
         en="Alexandra & Clément imagined a wedding that was truly theirs: elegant, vintage, in mocha tones, and above all full of surprises. Surrounded by 100 loved ones, every moment had its own flavour."),
    dict(img="alicia-alexandre", n="Alicia & Alexandre", place="Collines d'Iduki, Pays Basque", date=("Juin 2025", "June 2025"),
         fr="Un mariage profondément tourné vers la famille et les amis, pensé comme un moment intime, hors du temps. La nature, les jeux de lumière, les bougies et les teintes vertes ont créé une atmosphère chaleureuse et enveloppante.",
         en="A wedding devoted to family and friends, designed as an intimate, timeless moment. Nature, plays of light, candles and green tones created a warm, enveloping atmosphere."),
    dict(img="chloe-romain", n="Chloé & Romain", place="La Ferme d'en Chon", date=("1er juin 2024", "1 June 2024"),
         fr="Une journée aussi pétillante qu'élégante, portée par une robe voluptueuse et une décoration raffinée inspirée du Vietnam, le pays où nos deux amoureux se sont rencontrés.",
         en="A day as sparkling as it was elegant, carried by a voluptuous gown and refined decor inspired by Vietnam, the country where the couple first met."),
    dict(img="caroline-jackson", n="Caroline & Jackson", place="Domaine de Cap'Bat", date=("22 juillet 2023", "22 July 2023"),
         fr="Beaux en amitié, beaux en amour, beaux en générosité, beaux en humour : des mariés solaires ! Après la mairie en petit comité, une cérémonie laïque haute en émotions.",
         en="Beautiful in friendship, in love, in generosity and in humour: a radiant couple! After an intimate civil ceremony, a deeply moving celebrant-led ceremony."),
    dict(img="jennifer-laurent", n="Jennifer & Laurent", place="Château de Garde", date=("27 mai 2023", "27 May 2023"),
         fr="Après une demande en mariage sur une petite plage vers la pointe du Cap Ferret, face à la dune du Pyla, Jennifer et Laurent ont célébré leur mariage dans ce magnifique château.",
         en="After a proposal on a small beach near the tip of Cap Ferret, facing the Dune du Pilat, Jennifer and Laurent celebrated their wedding at this magnificent château."),
    dict(img="mai-rufus", n="Maï & Rufus", place="Domaine de Conseillant", date=("25 juin 2022", "25 June 2022"),
         fr="Deux cœurs, une âme. Maï et Rufus se sont dit « oui » en Gironde, lors d'une cérémonie laïque pleine de joie et d'émotion au domaine de Conseillant.",
         en="Two hearts, one soul. Maï and Rufus said “I do” in Gironde, during a joyful, emotional celebrant-led ceremony at Domaine de Conseillant."),
    dict(img="emilie-aurelien", n="Emilie & Aurélien", place="La Chartreuse des Eyres", date=("3 juillet 2021", "3 July 2021"),
         fr="C'est sous un soleil éclatant qu'Emilie et Aurélien se sont dit « oui » pour la vie, lors d'une journée champêtre et sur mesure en Gironde.",
         en="Under a brilliant sun, Emilie and Aurélien said “I do” for life, on a bespoke countryside day in Gironde."),
    dict(img="delphine-ludovic", n="Delphine & Ludovic", place="Domaine d'Arès", date=("10 juillet 2021", "10 July 2021"),
         fr="Jeunes parents d'un bébé d'un mois, se marier était pour Delphine & Ludovic une évidence : celle d'unir leur famille.",
         en="New parents of a one-month-old baby, marrying was obvious for Delphine & Ludovic: a way to bring their family together."),
]


WEDDINGS = [w for w in WEDDINGS if w["img"] not in ("mai-rufus", "emilie-aurelien", "delphine-ludovic")]


IMG2SLUG = {"marie-charles": "marie-charles-mariage-2025-lovely-day-event", "yvonne-thomas": "yvonne-thomas-mariage-2025",
            "alexandra-clement": "alexandra-clement-mariage-2025", "alicia-alexandre": "alicia-alexandre-mariage-2025",
            "chloe-romain": "mariagecolorealaplage", "caroline-jackson": "caroline-jackson", "jennifer-laurent": "jennifer-laurent",
            "mai-rufus": "mai-rufus", "emilie-aurelien": "emilie-aurelien", "delphine-ludovic": "delphine-ludovic"}


def wedding_card(c, w):
    url = c.href("post:" + IMG2SLUG[w["img"]])
    return f'''<a class="wedding reveal" href="{url}">
  {fitted_img(c, [("img", w["img"])] + [("j", u) for u in wedding_data(IMG2SLUG[w["img"]], c.lang)["gallery"]], f'{w["n"]}, {w["place"]}', "ratio-tall")}
  <div class="meta"><span class="label">{w["place"]}</span><span class="label">{c.t(*w["date"])}</span></div>
  <h3 class="h3">{w["n"]}</h3>
  <p>{c.t(w["fr"], w["en"])}</p>
  <span class="link" style="justify-self:start">{c.t("Lire leur histoire", "Read their story")}</span>
</a>'''


# ---------------------------------------------------------------- Accueil
def p_index(c):
    t = c.t
    feat = [WEDDINGS[0], WEDDINGS[1], WEDDINGS[3], WEDDINGS[2]]
    return f'''
<section class="hero">
  <img src="{c.root}img/MariageChateauGrattequina_TristanPerrier_NA-274.webp" alt="{t("Mariés main dans la main dans le parc d'un château bordelais", "Bride and groom hand in hand in the gardens of a Bordeaux château")}" fetchpriority="high">
  <span class="credit">© Tristan Perrier</span>
  <div class="hero-text wrap">
    <span class="label">Bordeaux · Dordogne · {t("Bassin d'Arcachon", "Arcachon Bay")}</span>
    <h1 class="h1">Wedding Planner<br>&amp; Designer {t("à Bordeaux", "in Bordeaux, France")}</h1>
    <p class="it">{t("Organisation et design de mariages sur mesure, pour des célébrations élégantes, fluides et profondément personnelles.", "Bespoke wedding planning and design, for elegant, seamless and deeply personal celebrations.")}</p>
    <a class="btn btn--light" href="{c.href("contact")}">{t("Parlez-moi de votre projet", "Tell me about your wedding")}</a>
  </div>
</section>

<section class="section">
  <div class="wrap statement reveal">
    <span class="label">{t("Organisation de mariage à Bordeaux et partout en France", "Wedding planning in Bordeaux and throughout France")}</span>
    <h2 class="h2">{t("Chaque détail,<br>imaginé pour vous ressembler", "Every detail,<br>designed around you")}</h2>
    <hr class="rule">
    <div class="prose">
      <p>{t("Wedding planner à Bordeaux depuis 2014, j'accompagne des couples français et internationaux dans l'organisation de mariages élégants et parfaitement orchestrés, en Gironde comme partout en France.", "A wedding planner in Bordeaux since 2014, I work with French and international couples to plan elegant, flawlessly orchestrated weddings, in Gironde and throughout France.")}</p>
      <p>{t("Chaque projet est pensé comme une expérience unique, où chaque détail est soigneusement imaginé pour vous ressembler. De la sélection du lieu à la coordination du jour J, je vous guide avec exigence, sens du détail et sérénité.", "Each project is conceived as a unique experience, where every detail is carefully imagined to reflect who you are. From choosing the venue to coordinating the day itself, I guide you with high standards, an eye for detail and a sense of calm.")}</p>
    </div>
  </div>
</section>

<section class="section section--stone">
  <div class="wrap stack-lg">
    <div class="stack center" style="text-align:center">
      <span class="label">{t("Prestations", "Services")}</span>
      <h2 class="h2">{t("Une approche sur mesure", "A bespoke approach")}</h2>
      <p class="it" style="color:var(--muted)">{t("Chaque mariage est conçu comme un projet unique, alliant exigence esthétique et organisation fluide.", "Every wedding is a unique project, combining aesthetic ambition with seamless organisation.")}</p>
    </div>
    <div class="services">
      <article class="service reveal">
        {c.img("MariageChateauGrattequina_TristanPerrier_NA-016", t("Faire-part, alliances et détails de mariage", "Wedding stationery, rings and details"), "ratio-portrait")}
        <h3 class="h3">{t("Organisation de mariage", "Full wedding planning")}</h3>
        <p>{t("J'interviens sur toutes les étapes de vos préparatifs et vous guide dans vos choix. Je suis force de proposition pour que votre mariage ne ressemble qu'à vous.", "I take care of every stage of your preparations and guide you through each decision, always bringing ideas so that your wedding is unmistakably yours.")}</p>
        <a class="link" href="{c.href("prestations")}#organisation">{t("Découvrir", "Discover")}</a>
      </article>
      <article class="service reveal">
        {c.img("MariageChateauGrattequina_TristanPerrier_NA-430", t("Table de réception dressée, verrerie et fleurs blanches", "Reception table with glassware and white flowers"), "ratio-portrait")}
        <h3 class="h3">Design &amp; {t("Scénographie", "Styling")}</h3>
        <p>{t("Créative et passionnée, je suis certifiée Wedding Designer et je conçois une ambiance scénographique qui correspond au thème de votre mariage.", "Creative and passionate, I am a certified Wedding Designer and create a complete scenography that matches the theme of your wedding.")}</p>
        <a class="link" href="{c.href("prestations")}#design">{t("Découvrir", "Discover")}</a>
      </article>
      <article class="service reveal">
        {c.img("alexandra-jour-j", t("Alexandra Ambert en pleine mise en place le jour du mariage", "Alexandra Ambert setting up on the wedding day"), "ratio-portrait")}
        <h3 class="h3">{t("Coordination Jour J", "On-the-day coordination")}</h3>
        <p>{t("Je serai la cheffe d'orchestre qui gère les différents prestataires, la mise en place de votre décoration et le déroulement de cette belle journée.", "I conduct the orchestra on the day: managing your suppliers, installing your decor and keeping the whole day flowing.")}</p>
        <a class="link" href="{c.href("prestations")}#coordination">{t("Découvrir", "Discover")}</a>
      </article>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap stack-lg">
    <div class="split">
      <div class="s-txt stack c-1-6">
        <span class="label">{t("Mariages récents", "Recent weddings")}</span>
        <h2 class="h2">{t("Mariages récents en France", "Recent weddings in France")}</h2>
      </div>
      <div class="s-txt c-8-5"><p class="it" style="color:var(--muted)">{t("Des célébrations uniques imaginées en Gironde, Dordogne, Pays Basque et au-delà.", "Unique celebrations imagined in Gironde, Dordogne, the Basque Country and beyond.")}</p></div>
    </div>
    <div class="weddings">{"".join(wedding_card(c, w) for w in feat)}</div>
    <div style="text-align:center"><a class="btn" href="{c.href("mariages")}">{t("Voir tous les mariages", "See all weddings")}</a></div>
  </div>
</section>

<section class="band">
  <img src="{c.root}img/MariageChateauGrattequina_TristanPerrier_NA-428.webp" alt="{t("Tables de réception à la lueur des bougies", "Candlelit reception tables")}" loading="lazy">
  <span class="credit">© Tristan Perrier</span>
  <div class="band-text wrap">
    <span class="label">{t("Ma philosophie", "My philosophy")}</span>
    <h2 class="h2">{t("Une attention portée<br>à chaque détail", "Attention given<br>to every detail")}</h2>
    <p class="it" style="max-width:40ch">{t("Je prends le temps de comprendre vos envies, vos priorités et votre histoire, pour transformer cette vision en une expérience fluide, élégante et parfaitement orchestrée.", "I take the time to understand your wishes, your priorities and your story, and turn that vision into a seamless, elegant and perfectly orchestrated experience.")}</p>
  </div>
</section>

<section class="section">
  <div class="wrap split">
    <div class="s-img-sm reveal">{c.img("alexandra-ambert", "Alexandra Ambert, wedding planner à Bordeaux", "ratio-tall")}</div>
    <div class="s-txt stack">
      <span class="label">{t("L'agence", "About")}</span>
      <h2 class="h2">Alexandra Ambert</h2>
      <div class="prose">
        <p>{t("Fondée en 2014, je suis Alexandra Ambert, wedding planner à Bordeaux, et je suis toujours autant touchée d'accompagner des couples.", "I founded Lovely Day Event in 2014. I am Alexandra Ambert, a wedding planner in Bordeaux, and accompanying couples still moves me as much as on the very first day.")}</p>
        <p>{t("J'imagine et orchestre des mariages sur mesure, alliant exigence, sens du détail et approche profondément humaine.", "I imagine and orchestrate bespoke weddings, combining high standards, an eye for detail and a deeply human approach.")}</p>
      </div>
      <a class="link" href="{c.href("agence")}">{t("Découvrir l'agence", "About the agency")}</a>
    </div>
  </div>
</section>

<section class="section section--stone">
  <div class="wrap stack-lg">
    <div class="stack" style="max-width:780px">
      <span class="label">{t("Méthode", "How I work")}</span>
      <h2 class="h2">{t("Une organisation pensée pour votre sérénité", "Planning designed for your peace of mind")}</h2>
      <p class="it" style="color:var(--muted)">{t("Votre mariage doit être unique en son genre. Je vous accompagne dès le début pour organiser le plus beau jour de votre vie.", "Your wedding should be one of a kind. I am by your side from the very beginning to plan the most beautiful day of your life.")}</p>
    </div>
    <div class="steps">
      <div class="step"><span class="num">01</span><h3 class="h3">{t("L'organisation", "Planning")}</h3><p>{t("Un premier échange pour comprendre votre histoire et définir les bases de votre mariage. Chaque étape est ensuite structurée avec clarté et sérénité.", "A first conversation to understand your story and lay the foundations of your wedding. Every step is then structured with clarity and calm.")}</p></div>
      <div class="step"><span class="num">02</span><h3 class="h3">{t("La production", "Production")}</h3><p>{t("Une sélection rigoureuse de prestataires locaux et spécialisés, choisis pour leur exigence et leur capacité à sublimer votre mariage en Gironde, Dordogne ou Pays Basque.", "A rigorous selection of local, specialist suppliers, chosen for their standards and their ability to elevate your wedding in Gironde, Dordogne or the Basque Country.")}</p></div>
      <div class="step"><span class="num">03</span><h3 class="h3">{t("Le design", "Design")}</h3><p>{t("Une direction esthétique pensée dans les moindres détails, inspirée par votre lieu de réception et l'atmosphère que vous souhaitez créer.", "An aesthetic direction considered down to the smallest detail, inspired by your venue and the atmosphere you wish to create.")}</p></div>
      <div class="step"><span class="num">04</span><h3 class="h3">{t("Le Jour J", "The day")}</h3><p>{t("Une présence discrète et attentive pour orchestrer chaque moment, où que vous célébriez votre mariage dans le Sud-Ouest ou en France.", "A discreet, attentive presence orchestrating every moment, wherever you celebrate in South-West France or beyond.")}</p></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap split split--rev">
    <div class="s-img reveal">{c.img("MariageChateauGrattequina_TristanPerrier_NA-474", t("Château Grattequina, Gironde", "Château Grattequina, Gironde"), "ratio-tall")}</div>
    <div class="s-txt stack">
      <span class="label">{t("Sud-Ouest &amp; France", "South-West France &amp; beyond")}</span>
      <h2 class="h2">{t("Votre wedding planner à Bordeaux et en Gironde", "Your wedding planner in Bordeaux and Gironde")}</h2>
      <div class="prose">
        <p>{t("La Nouvelle-Aquitaine regorge de paysages magnifiques et de délicieuses spécialités culinaires. Avec ses vignobles à perte de vue, la région bordelaise bénéficie des meilleurs vins du pays pour accompagner votre dîner de mariage. Ses décors naturels et sauvages ajouteront une touche sublime à vos photos.", "Nouvelle-Aquitaine is full of breathtaking landscapes and wonderful regional cuisine. With vineyards as far as the eye can see, the Bordeaux region offers some of the finest wines in the country for your wedding dinner, and its natural, untamed scenery adds something sublime to your photographs.")}</p>
        <p>{t("Que vous rêviez d'un château pour un mariage chic, d'une villa privée en bord de plage, du cœur des vignobles bordelais ou d'un grand hôtel pour un mariage raffiné, la région a assurément le lieu idéal pour votre jour inoubliable.", "Whether you dream of a château for a chic celebration, a private beachfront villa, the heart of the Bordeaux vineyards or a grand hotel for a refined affair, the region has the perfect venue for your unforgettable day.")}</p>
        <p class="small">{t("Châteaux du Médoc et de Saint-Émilion, domaines de l'Entre-deux-Mers, Bassin d'Arcachon : je connais les lieux et les prestataires bordelais. Mes couples en Gironde, Dordogne, Pays Basque et dans d'autres régions de France font appel à moi pour être leur wedding planner.", "Médoc and Saint-Émilion châteaux, Entre-deux-Mers estates, the Arcachon Bay: I know the Bordeaux venues and suppliers. Couples in Gironde, Dordogne, the Basque Country and other regions of France choose me as their wedding planner.")}</p>
      </div>
    </div>
  </div>
</section>

<section class="section section--stone">
  <div class="wrap stack-lg">
    <div class="stack center" style="text-align:center"><span class="label">{t("Ils nous ont fait confiance", "Kind words")}</span><h2 class="h2">{t("Mots de mariés", "From our couples")}</h2></div>
    {ratings(c)}
    <div class="quotes">
      <figure class="quote"><blockquote>{t("« Avoir confié la coordination de notre mariage à Alexandra a été la clef de notre sérénité. Dès la première entrevue, nous avons su qu'elle serait la bonne personne. Elle a un très bon relationnel avec les prestataires, ce qui a permis de constituer une véritable équipe autour de notre mariage. »", "“Entrusting the coordination of our wedding to Alexandra was the key to our peace of mind. From our first meeting we knew she was the right person. Her excellent relationships with suppliers built a true team around our wedding.”")}</blockquote><figcaption class="label"><cite>Delphine &amp; Haythem</cite></figcaption></figure>
      <figure class="quote"><blockquote>{t("« Nous descendons à peine de notre petit nuage, le 18 juin dernier était magique ! On ne s'attendait pas à prendre autant de plaisir le jour J, tout le monde a adoré la décoration, les prestataires, l'organisation. Merci Alexandra pour avoir fait de ce jour notre mariage parfait ! »", "“We are only just coming down from cloud nine: 18 June was magical! We never expected to enjoy the day so much. Everyone loved the decor, the suppliers, the organisation. Thank you Alexandra for making it our perfect wedding!”")}</blockquote><figcaption class="label"><cite>Charlotte &amp; Arnaud</cite></figcaption></figure>
      <figure class="quote"><blockquote>{t("« Dès notre première rencontre, nous avons eu la certitude d'avoir trouvé la perle rare. Un an de préparatifs encadré par ses soins, son écoute, ses conseils avisés, sa bienveillance, son humour… Et quand le jour arrive, elle est bien là, entourée des meilleurs. »", "“From our very first meeting we knew we had found a rare gem. A year of preparations guided by her care, her listening, her wise advice, her kindness and humour… And when the day comes, she is right there, surrounded by the very best.”")}</blockquote><figcaption class="label"><cite>Christelle &amp; Edouard</cite></figcaption></figure>
    </div>
  </div>
</section>

<section class="section section--tight">
  <div class="wrap mosaic">
    <div class="m-a reveal">{c.img("MariageChateauGrattequina_TristanPerrier_NA-450", t("Mariés au coucher du soleil", "Couple at golden hour"), "ratio-tall")}</div>
    <div class="m-b reveal">{c.img("MariageChateauGrattequina_TristanPerrier_NA-198", t("Panneau de bienvenue fleuri", "Floral welcome sign"), "ratio-tall")}</div>
    <div class="m-c reveal">{c.img("MariageChateauGrattequina_TristanPerrier_NA-184", t("Chaise de cérémonie ornée de fleurs blanches", "Ceremony chair with white flowers"), "ratio-tall")}</div>
  </div>
</section>

<section class="band">
  <img src="{c.root}img/table-margot-loic.webp" alt="{t("Longue table de réception fleurie", "Long floral reception table")}" loading="lazy">
  <div class="band-text wrap">
    <span class="label">Contact</span>
    <h2 class="h2">{t("Parlez-moi de votre projet", "Tell me about your wedding")}</h2>
    <p class="it" style="max-width:38ch">{t("Racontez-moi votre histoire et votre vision. Je prendrai le temps de vous guider avec attention et de vous accompagner à chaque étape.", "Share your story and your vision. I will take the time to guide you with care and accompany you at every step.")}</p>
    <a class="btn btn--light" href="{c.href("contact")}">{t("Me contacter", "Enquire")}</a>
  </div>
</section>'''


# ---------------------------------------------------------------- Agence
def VIDEO_AGENCE(c):
    """Vidéo de présentation d'Alexandra au Château Belle Époque (YouTube, sans cookies)."""
    t = c.t
    cap = t("Alexandra au Château Belle Époque", "Alexandra at Château Belle Époque")
    return f'''<figure class="video-agence reveal"><div class="video"><iframe src="https://www.youtube-nocookie.com/embed/QngWOuPwvco?rel=0" title="{t("Vidéo", "Video")} : {cap}" loading="lazy" allow="encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe></div>
      <figcaption class="label">{cap}</figcaption></figure>'''


def p_agence(c):
    t = c.t
    return f'''
<section class="page-hero wrap">
  <span class="label">{t("L'agence · Depuis 2014", "About · Since 2014")}</span>
  <h1 class="h1">Wedding Planner<br>&amp; Designer</h1>
  <p class="it">{t("Organisation de mariages sur mesure, haut de gamme et authentiques, à Bordeaux et sur le Bassin d'Arcachon.", "Bespoke, refined and authentic weddings in Bordeaux and on the Arcachon Bay.")}</p>
</section>

<section class="section" style="padding-top:0">
  <div class="wrap split">
    <div class="s-img reveal">{c.img("alexandra-ambert", "Alexandra Ambert, fondatrice de Lovely Day Event", "ratio-tall")}</div>
    <div class="s-txt stack">
      <span class="label">Alexandra Ambert</span>
      <h2 class="h2">{t("Des valeurs humaines avant tout", "Human values first")}</h2>
      <div class="prose">
        <p>{t("Créée par Alexandra en 2014 à Bordeaux, Lovely Day Event est une agence évènementielle française spécialisée dans la décoration et l'organisation de mariages sur mesure, haut de gamme et authentiques dans la région bordelaise et le Bassin d'Arcachon.", "Founded by Alexandra in Bordeaux in 2014, Lovely Day Event is a French events agency specialising in the design and planning of bespoke, refined and authentic weddings in the Bordeaux region and on the Arcachon Bay.")}</p>
        <p>{t("Pour gérer, parfaire et coordonner votre mariage à votre image, je mets tout en œuvre pour rendre cet évènement unique d'une vie simple, rigoureux et soigné dans les moindres détails.", "To plan, perfect and coordinate a wedding that reflects you, I do everything to make this once-in-a-lifetime event simple, rigorous and polished down to the smallest detail.")}</p>
        <p>{t("Ma plus grande force de wedding planner, ce sont les valeurs humaines que je place avant toute chose. Pour moi, organiser un mariage sur mesure, c'est savoir écouter, répondre à vos besoins et surtout s'adapter à votre histoire de couple.", "My greatest strength as a wedding planner is the human values I put before everything else. To me, planning a bespoke wedding means listening, meeting your needs and, above all, adapting to your story as a couple.")}</p>
      </div>
    </div>
  </div>
</section>

<section class="section section--stone">
  <div class="wrap statement reveal">
    <span class="label">{t("Votre histoire", "Your story")}</span>
    <h2 class="h2">{t("Quels sont les moments importants du mariage pour vous ?", "Which moments of the day matter most to you?")}</h2>
    <p class="it" style="max-width:44ch;color:var(--muted)">{t("Racontez-moi votre rencontre, vos envies, vos idées : je vous promets d'être force de proposition et toujours passionnée pour vous accompagner dans un si grand projet.", "Tell me how you met, your wishes, your ideas. I promise to bring ideas of my own and to accompany you with passion through such a meaningful project.")}</p>
  </div>
</section>

<section class="section" id="metier">
  <div class="wrap stack-lg">
    <div class="statement" style="padding:0">
      <span class="label">{t("Mon cœur de métier", "What I really do")}</span>
      <h2 class="h2">{t("Wedding planner : bien plus qu'un carnet d'adresses", "Wedding planner: far more than an address book")}</h2>
      <p class="it" style="max-width:52ch;color:var(--muted)">{t("Un mariage, ce sont des centaines de décisions, une vingtaine de prestataires et une seule journée pour que tout soit juste. Mon métier, c'est de porter tout cela pour vous, du premier rendez-vous jusqu'au dernier slow.", "A wedding means hundreds of decisions, around twenty suppliers and a single day for everything to come together. My job is to carry all of that for you, from the first meeting to the last dance.")}</p>
    </div>
    {VIDEO_AGENCE(c)}
    <div class="roles roles--4">
      <div><h3 class="role-t">{t("Écouter &amp; imaginer", "Listen &amp; imagine")}</h3><p>{t("Comprendre votre histoire, vos envies et votre budget, puis traduire tout cela en un projet clair, cohérent et à votre image.", "Understanding your story, your wishes and your budget, then turning them into a clear, coherent project that truly reflects you.")}</p></div>
      <div><h3 class="role-t">{t("Choisir &amp; négocier", "Select &amp; negotiate")}</h3><p>{t("Sélectionner les bons prestataires, comparer les devis, négocier et sécuriser chaque contrat. Vous gagnez du temps, de l'argent et de la tranquillité.", "Selecting the right suppliers, comparing quotes, negotiating and securing every contract. You save time, money and worry.")}</p></div>
      <div><h3 class="role-t">{t("Concevoir &amp; créer", "Design &amp; create")}</h3><p>{t("Imaginer la scénographie, chiner, fabriquer et installer le décor : c'est ma signature de Wedding Designer certifiée.", "Imagining the scenography, sourcing, making and installing the decor: my signature as a certified Wedding Designer.")}</p></div>
      <div><h3 class="role-t">{t("Orchestrer le jour J", "Orchestrate the day")}</h3><p>{t("Être la cheffe d'orchestre sur le terrain : timing, prestataires, imprévus. Vous, vous profitez de chaque instant.", "Conducting everything on the ground: timing, suppliers, the unexpected. You simply enjoy every moment.")}</p></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap split split--rev">
    <div class="s-img reveal">{c.img("alexandra-mise-en-place", t("Alexandra dresse une table de réception", "Alexandra setting a reception table"), "ratio-tall")}</div>
    <div class="s-txt stack">
      <span class="label">{t("Créatrice de mariages", "Wedding creator")}</span>
      <h2 class="h2">{t("Saviez-vous qu'on m'appelle « créatrice de mariages » ?", "They call me a “wedding creator”")}</h2>
      <div class="prose">
        <p>{t("Véritable passionnée de l'organisation de mariage et entière dans tout ce que j'entreprends, je mets un point d'honneur à offrir aux futurs mariés les détails et conseils qui feront de leurs préparatifs un moment unique et serein.", "Truly passionate about wedding planning and wholehearted in everything I do, I make it a point of honour to give couples the details and advice that make their preparations a unique and serene time.")}</p>
        <p>{t("Je ne pourrais vous proposer de si beaux moments sans des prestataires de qualité en qui j'ai confiance, et qui correspondent à votre personnalité. Mon agence travaille avec de nombreux partenaires dans la région de Bordeaux, alliant prestations de qualité et respect du budget de mes clients.", "None of this would be possible without trusted, high-quality suppliers who match your personality. My agency works with many partners across the Bordeaux region, combining excellent service with respect for each couple's budget.")}</p>
      </div>
    </div>
  </div>
</section>

<section class="section section--stone">
  <div class="wrap split">
    <div class="s-img-sm reveal" style="display:grid;gap:20px">{c.img("MariageChateauGrattequina_TristanPerrier_NA-425", t("Fleurs pastel et bougies sur une table de réception", "Pastel flowers and candles on a reception table"), "ratio-portrait")}</div>
    <div class="s-txt stack">
      <span class="label">{t("Formation &amp; expérience", "Training &amp; experience")}</span>
      <h2 class="h2">{t("Wedding Designer certifiée", "Certified Wedding Designer")}</h2>
      <div class="prose">
        <p>{t("Formée aux méthodes de travail de la Wedding Academy, en véritable experte du mariage, je gère pour vous toutes les facettes de votre projet en gardant une belle cohérence et harmonie.", "Trained in the methods of the Wedding Academy, I manage every facet of your wedding for you, with consistency and harmony throughout.")}</p>
        <p>{t("Mon atout, c'est ma créativité. J'aime la décoration, les dernières tendances, les ambiances que créent les matières et les couleurs. Je vous propose de manière cadrée et structurée une scénographie complète, afin que vous puissiez vous projeter dans votre jour.", "My strength is creativity. I love decoration, the latest trends, the atmospheres created by textures and colours. I present a complete, clearly structured scenography so you can truly picture your day.")}</p>
      </div>
      <img src="{c.root}img/wedding-academy.png" alt="Wedding Academy · Wedding Designer Certified" width="96" height="96" loading="lazy" style="width:96px;height:96px;border-radius:50%">
    </div>
  </div>
</section>

<section class="band">
  <img src="{c.root}img/MariageChateauGrattequina_TristanPerrier_NA-163.webp" alt="{t("Mariés enlacés en noir et blanc", "Couple embracing, black and white")}" loading="lazy">
  <span class="credit">© Tristan Perrier</span>
  <div class="band-text wrap">
    <span class="label">{t("Mon leitmotiv", "My motto")}</span>
    <h2 class="h2">{t("Simplicité, sérénité<br>et efficacité", "Simplicity, serenity<br>and efficiency")}</h2>
    <p class="it" style="max-width:40ch">{t("« Un mariage heureux est une longue conversation qui semble toujours trop brève. » Je fais en sorte que le vôtre ne soit que souvenirs et bonheur.", "“A happy marriage is a long conversation that always seems too short.” I make sure your wedding is nothing but memories and joy.")}</p>
  </div>
</section>

<section class="section">
  <div class="wrap statement reveal">
    <h2 class="h2">{t("Vous placer au centre de votre mariage", "You, at the heart of your wedding")}</h2>
    <div class="prose">
      <p>{t("Ne gardez que le meilleur de votre mariage. C'est un événement très important dans une vie : il me semble essentiel que les mariés rayonnent et puissent avoir confiance le jour J. Des rires, des larmes, de l'amour et surtout beaucoup d'émotions. Quelle chance de vous accompagner tout au long de votre projet !", "Keep only the best of your wedding. It is one of life's most important events, and I believe the couple should shine and feel completely confident on the day. Laughter, tears, love and, above all, so much emotion. What a privilege to accompany you throughout.")}</p>
    </div>
    <a class="btn" href="{c.href("contact")}">{t("Parlez-moi de vous", "Tell me about you")}</a>
  </div>
</section>'''


# ---------------------------------------------------------------- Prestations
def ul(items):
    return '<ul class="clean">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


GOOGLE_URL = "https://g.page/r/Ccty5Dtg7yumEAE"
MNET_URL = "https://www.mariages.net/organisation-mariage/lovely-day--e148855"


def ratings(c):
    t = c.t
    def one(n, name, url):
        return f'''<div class="rating"><span class="stars" aria-hidden="true">★★★★★</span><strong>5,0 / 5</strong><span class="label">{n} {t("avis sur", "reviews on")} <a href="{url}" target="_blank" rel="noopener">{name}</a></span></div>'''
    return f'''<div class="ratings" role="group" aria-label="{t("Avis clients", "Client reviews")}">{one(58, "Google", GOOGLE_URL)}{one(41, "Mariages.net", MNET_URL)}</div>'''


def pkg(c, star, label, title, intro, items, price, href, cta, photo=None, option=None):
    t = c.t
    badge = ""  # « La plus choisie » retiré à la demande d'Alexandra (2026-11-05) ; la carte reste mise en avant
    pic = f'<a class="pkg-img" href="{href}" tabindex="-1" aria-hidden="true">{c.img(photo[0], photo[1], "ratio-land")}</a>' if photo else ""
    return f'''<article class="pkg{" pkg--star" if star else ""}">{badge}{pic}
        <span class="label">{label}</span>
        <h3 class="h3">{title}</h3>
        <p class="small">{intro}</p>
        <div class="pkg-list">{ul(items)}{f'<p class="pkg-opt"><span class="label">{t("En option", "Add-on")}</span><span>{option}</span></p>' if option else ""}</div>
        <div class="price"><span class="label">{t("À partir de", "From")}</span><strong>{price}</strong></div>
        <a class="link" href="{href}">{cta}</a>
      </article>'''


def p_prestations(c):
    t = c.t
    steps6 = [
        (t("Briefing", "Briefing"), t("Ce que vous aimez, ce que vous n'aimez pas, votre rencontre, votre histoire, une passion commune… Vous avez plein d'idées pour votre mariage : à mon tour de rendre vos rêves réels, pour vous et vos invités.", "What you love, what you don't, how you met, your story, a shared passion… You have plenty of ideas for your wedding. Now it is my turn to make those dreams real, for you and your guests.")),
        (t("Accompagnement", "Guidance"), t("La confiance se construit au fil du temps : échanges réguliers par téléphone, e-mail ou en personne, outils de gestion et supports de suivi. Je deviens votre principal point de contact avec les prestataires.", "Trust is built over time: regular conversations by phone, email or in person, plus my planning tools and progress documents. I become your main point of contact with every supplier.")),
        (t("Gestion des prestataires", "Supplier management"), t("Je sélectionne une liste de prestataires de confiance adaptés à vos caractères, vos exigences et votre budget. Je recueille et examine les devis, organise les rencontres et assure la gestion des contrats.", "I curate a list of trusted suppliers suited to your personalities, expectations and budget. I gather and review quotes, arrange meetings and manage contracts.")),
        (t("Scénographie", "Scenography"), t("Une compilation d'inspirations pour chaque espace éphémère, une estimation budgétaire globale et des propositions de devis de prestataires spécialisés : fleurs, mobilier, éclairage, location.", "A collection of inspiration for every temporary space, an overall decor budget and quotes from specialist suppliers: flowers, furniture, lighting and rentals.")),
        (t("Réalisation", "Production"), t("J'effectue les achats ou la location grâce à mes privilèges professionnels, puis je prends en charge le stockage et la réalisation de tous les éléments décoratifs : cadeaux invités, signalétique, plans de table…", "I purchase or rent through my professional accounts, then store and produce every decorative element: guest favours, signage, seating plans and more.")),
        (t("Installation &amp; Jour J", "Installation &amp; the day"), t("J'installe tous les éléments pour créer une ambiance visuelle et esthétique, puis je coordonne l'événement : prestataires, imprévus, animations. Et surtout, je reste à vos côtés.", "I install every element to create the visual atmosphere, then coordinate the event itself: suppliers, the unexpected, entertainment. Above all, I stay by your side.")),
    ]
    pk = [
        (True, t("Formule Signature", "Signature package"), t("Organisation, design &amp; Jour J", "Planning, design &amp; the day"),
         t("L'expérience complète : je conçois l'univers de votre mariage et j'en orchestre chaque détail.", "The complete experience: I design the world of your wedding and orchestrate every detail."),
         [t("Organisation complète et gestion des prestataires", "Full planning and supplier management"), t("Design, scénographie et décoration sur mesure", "Bespoke design, scenography and styling"), t("Achats, confection et installation du décor", "Sourcing, making and installing the decor"), t("Coordination la veille et le jour J", "Coordination the day before and on the day")],
         "6 900 €", "#signature", t("Voir le détail", "See the details")),
        (False, t("Organisation + Jour J", "Planning + the day"), t("Organisation de mariage", "Wedding planning"),
         t("Je prends en charge les préparatifs et je coordonne votre journée.", "I take care of the preparations and coordinate your day."),
         [t("Organisation complète et gestion des prestataires", "Full planning and supplier management"), t("Budget, plannings et suivi financier", "Budget, timelines and financial tracking"), t("Coordination la veille et le jour J", "Coordination the day before and on the day")],
         "5 000 €", "#organisation", t("Voir le détail", "See the details")),
        (False, t("Coordination", "Coordination"), t("Coordination Jour J", "On-the-day coordination"),
         t("Vous avez tout préparé : je m'occupe du jour J pour que vous en profitiez.", "You have planned it all: I take care of the day so you can enjoy it."),
         [t("Rendez-vous 3 mois avant", "Meeting 3 months ahead"), t("Contact des prestataires pour les derniers détails", "Liaising with suppliers on final details"), t("Rétroplanning du jour J", "Wedding-day run sheet"), t("Coordination du timing et des imprévus", "Managing timing and the unexpected")],
         "2 200 €", "#coordination", t("Voir le détail", "See the details"), None,
         f'<a href="#design">{t("Design &amp; décoration", "Design &amp; styling")}</a>, {t("dès 2 000 €", "from €2,000")}'),
    ]
    faq = [
        (t("La décoration est-elle comprise ?", "Is styling included?"),
         t("Elle est comprise dans la formule Signature. Avec la Coordination Jour J, elle s'ajoute en option à partir de 2 000 €. Elle n'est proposée ni seule, ni avec la formule Organisation. Le design est un vrai travail de création : book décoration, achats, confection, stockage, installation et désinstallation. Le séparer vous permet de comparer les formules d'égal à égal.", "It is included in the Signature package. It can be added to On-the-day coordination from €2,000. It is not offered on its own or with the Planning package. Design is real creative work: design book, sourcing, making, storage, installation and take-down. Keeping it separate lets you compare packages like for like.")),
        (t("À quel moment dois-je faire appel à une wedding planner ?", "When should we hire a wedding planner?"),
         t("Dès que vous entamez la planification de votre grand jour. Plus tôt vous faites appel à moi, plus nous avons le temps de prendre en charge l'essentiel et de vous accompagner à chaque étape clé. Je préconise un an de préparatifs pour lisser les rendez-vous avec les prestataires, mais un mariage peut se préparer en 2 à 12 mois.", "As soon as you start planning. The earlier you reach out, the more time we have to take care of the essentials and guide you at every key stage. I recommend a year of preparation so supplier meetings are spread out, but a wedding can be planned in 2 to 12 months.")),
        (t("Nous avons déjà notre lieu de réception, comment se déroule la suite ?", "We already have our venue. What happens next?"),
         t("Je prends en charge dès le départ la communication avec le lieu. Après une visite minutieuse, je consigne toutes les informations indispensables à la conception de la scénographie et de la décoration, et nous avançons ensemble dans la planification de votre jour J.", "I take over communication with the venue from the start. After a thorough visit, I record everything needed to design the scenography and decor, and we move forward together with planning your day.")),
        (t("Que se passe-t-il si quelque chose ne se déroule pas comme prévu ?", "What if something doesn't go to plan on the day?"),
         t("J'anticipe toujours avec un plan de secours, notamment en cas d'intempéries. Je suis présente le jour même pour coordonner tout changement nécessaire, afin que vous profitiez pleinement de votre journée sans vous soucier des imprévus.", "I always prepare a back-up plan, especially for bad weather. I am there on the day to coordinate any change, so you can enjoy every moment without worrying about the unexpected.")),
        (t("Organisez-vous des mariages pour des couples venant de l'étranger ?", "Do you plan weddings for couples living abroad?"),
         t("Oui. J'accompagne des couples français et internationaux, comme Yvonne & Thomas venus d'Allemagne. Les échanges se font par visio, e-mail ou WhatsApp, et votre dossier de mariage en ligne reste accessible 24h/24.", "Yes. I work with French and international couples, such as Yvonne & Thomas from Germany. We stay in touch by video call, email or WhatsApp, and your online wedding file is available around the clock.")),
    ]
    return f'''
<section class="page-hero wrap">
  <span class="label">{t("Prestations", "Services")}</span>
  <h1 class="h1">{t("Des formules<br>à votre mesure", "Packages<br>made to measure")}</h1>
  <p class="it">{t("De l'organisation complète à la coordination du jour J, avec un vrai travail de design pour un mariage qui vous ressemble.", "From full planning to on-the-day coordination, with true design work for a wedding that feels like you.")}</p>
</section>
<nav class="subnav wrap" aria-label="{t("Formules", "Packages")}">
  <a href="#formules">{t("Formules", "Packages")}</a>
  <a href="#signature">{t("Signature", "Signature")}</a>
  <a href="#organisation">{t("Organisation + Jour J", "Planning + the day")}</a>
  <a href="#coordination">{t("Coordination Jour J", "On-the-day coordination")}</a>
  <a href="#design">{t("Design &amp; décoration", "Design &amp; styling")}</a>
  <a href="#location">Photobooth</a>
  <a href="#faq">{t("Questions", "FAQ")}</a>
</nav>

<section class="section" id="formules">
  <div class="wrap stack-lg">
    <div class="stack center" style="text-align:center"><span class="label">{t("Formules", "Packages")}</span><h2 class="h2">{t("Choisir votre accompagnement", "Choose your level of support")}</h2></div>
    <div class="packages">
      {"".join(pkg(c, *x) for x in pk)}
    </div>
    <p class="small center" style="text-align:center">{t("Design &amp; décoration en option avec la Coordination Jour J : à partir de 2 000 € · Photobooth : 400 €", "Design &amp; styling as an add-on to On-the-day coordination: from €2,000 · Photo booth: €400")}</p>
    {ratings(c)}
  </div>
</section>

<section class="section section--stone" id="signature">
  <div class="wrap stack-lg">
    <div class="stack" style="max-width:760px">
      <span class="label">{t("Formule Signature", "Signature package")}</span>
      <h2 class="h2">{t("Organisation, design &amp; Jour J", "Planning, design &amp; the day")}</h2>
      <p class="it" style="color:var(--muted)">{t("L'expérience complète, en six étapes : je conçois l'univers de votre mariage et j'en orchestre chaque détail.", "The complete experience, in six steps: I design the world of your wedding and orchestrate every detail.")}</p>
      <div class="price"><span class="label">{t("À partir de", "From")}</span><strong>6 900 €</strong></div>
    </div>
    <div class="steps" style="grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr))">
      {"".join(f'<div class="step"><span class="num">{i+1:02d}</span><h3 class="h3">{a}</h3><p>{b}</p></div>' for i,(a,b) in enumerate(steps6))}
    </div>
  </div>
</section>

<section class="section" id="organisation">
  <div class="wrap stack-lg">
    <div class="split">
      <div class="s-img reveal">{c.img("MariageChateauGrattequina_TristanPerrier_NA-017", t("Faire-part, sceau de cire et écrins", "Invitation, wax seal and ring boxes"), "ratio-tall")}</div>
      <div class="s-txt offer-head">
        <span class="label">{t("Organisation + Jour J", "Planning + the day")}</span>
        <h2 class="h2">{t("Organisation de mariage", "Wedding planning")}</h2>
        <p class="it" style="color:var(--muted)">{t("Organisation complète et sur mesure, à Bordeaux et partout en France.", "Complete, bespoke planning in Bordeaux and throughout France.")}</p>
        <div class="prose">
          <p>{t("L'organisation d'un mariage prend du temps, et il n'est pas toujours facile pour les futurs mariés de trouver les meilleurs prestataires : lieu de réception, traiteur, DJ…", "Planning a wedding takes time, and finding the best suppliers (venue, caterer, DJ…) is not always easy.")}</p>
          <p>{t("En faisant appel à mes services de wedding planner et designer, vous vous assurez d'une préparation en toute sérénité. Je suis à vos côtés pour personnaliser votre mariage avec mon savoir-faire et ma bienveillance.", "With me as your wedding planner and designer, your preparations stay serene. I am by your side to personalise your wedding with my expertise and care.")}</p>
        </div>
        <div class="price"><span class="label">{t("À partir de", "From")}</span><strong>5 000 €</strong></div>
        <p class="small">{t("En option : ma présence et la coordination du brunch du lendemain. Pour le design et la décoration, choisissez la formule Signature.", "Optional: my presence to coordinate the day-after brunch. For design and styling, choose the Signature package.")}</p>
      </div>
    </div>
    <div class="roles roles--3">
      <div><h3 class="role-t">{t("Organisation", "Planning")}</h3>{ul([t("Rendez-vous de découverte : qui êtes-vous, qu'attendez-vous de votre mariage ?", "Discovery meeting: who you are and what you expect from your wedding"), t("Cahier des charges et plannings jusqu'au jour J", "Brief and timelines through to the day"), t("Outils de gestion partagés et conseil continu", "Shared planning tools and ongoing advice"), t("Budget, répartition des dépenses et suivi financier", "Budget, cost allocation and financial tracking"), t("Hébergements et transports : proposition et gestion", "Accommodation and transport: proposals and management")])}</div>
      <div><h3 class="role-t">Production</h3>{ul([t("Choix, essais, négociations, rendez-vous, devis et contrats des prestataires", "Supplier selection, tastings, negotiation, meetings, quotes and contracts"), t("Suivi financier et management des prestataires", "Financial follow-up and supplier management"), t("Visites techniques du lieu de réception", "Technical visits of the venue"), t("Logistique : mise en place et montage des espaces", "Logistics: set-up and installation of each space")])}</div>
      <div><h3 class="role-t">Coordination</h3>{ul([t("Accueil et management des prestataires et des invités", "Welcoming and managing suppliers and guests"), t("Accompagnement des mariés la veille et le jour J", "By your side the day before and on the day"), t("Gestion des animations avec votre entourage", "Coordinating speeches and surprises with your loved ones"), t("Supervision et coordination de votre jour J", "Supervision and coordination of your wedding day")])}</div>
    </div>
    <div class="split" style="margin-top:24px">
      <div class="s-txt stack c-1-6"><span class="label">{t("Mes outils de gestion", "Planning tools")}</span><h3 class="h3">{t("Un dossier de mariage en ligne, accessible 24h/24", "An online wedding file, available 24/7")}</h3></div>
      <div class="s-txt prose c-8-5"><p>{t("Budget, planning du jour J, to-do list, briefing de chaque prestataire, liste des invités, plan de table, briefing déco et shopping list, liste des photos… Le book décoration vous donne un aperçu de la scénographie. Des rendez-vous ponctuent chaque étape importante, et je reste disponible par téléphone et WhatsApp.", "Budget, wedding-day schedule, to-do list, a briefing for every supplier, guest list, seating plan, design brief and shopping list, photo list… The design book gives you a preview of the scenography. Meetings mark each key stage, and I remain available by phone and WhatsApp.")}</p></div>
    </div>
  </div>
</section>

<section class="section section--stone" id="coordination">
  <div class="wrap split">
    <div class="s-img reveal">{c.img("MariageChateauGrattequina_TristanPerrier_NA-069", t("Le marié dans un salon de château", "The groom in a château salon"), "ratio-tall")}</div>
    <div class="s-txt offer-head">
      <span class="label">{t("Coordination", "Coordination")}</span>
      <h2 class="h2">{t("Coordination Jour J", "On-the-day coordination")}</h2>
      <p class="it" style="color:var(--muted)">{t("Vous avez tout préparé ? Profitez de votre mariage.", "You have planned it all? Now enjoy your wedding.")}</p>
      <div class="prose">
        <p>{t("Je rentre en scène pour m'occuper du timing, accueillir les prestataires, mettre en place votre décoration et les petits détails qui vous tiennent à cœur. Quelques mois avant votre union, je vous accompagne dans les derniers préparatifs, avec discrétion.", "I step in to manage the timing, welcome your suppliers, set up your decor and the small details that matter to you. A few months before the wedding, I discreetly guide you through the final preparations.")}</p>
      </div>
      {ul([t("Rendez-vous de découverte des préparatifs engagés, 3 mois avant", "Discovery meeting about your plans, 3 months ahead"), t("Contact des prestataires choisis pour les derniers détails", "Liaising with your chosen suppliers on final details"), t("Rétroplanning du jour J et gestion des animations", "Wedding-day run sheet and coordination of surprises"), t("Supervision de la fleuriste et des décorations", "Supervising the florist and decor"), t("Accueil et orientation des invités", "Welcoming and guiding guests"), t("Coordination du timing et des imprévus", "Managing timing and the unexpected")])}
      <div class="price"><span class="label">{t("À partir de", "From")}</span><strong>2 200 €</strong></div>
    </div>
  </div>
</section>

<section class="section" id="design">
  <div class="wrap stack-lg">
    <div class="split split--rev">
      <div class="s-img reveal">{c.img("MariageChateauGrattequina_TristanPerrier_NA-325", t("Mur à champagne « Santé ! » fleuri", "Floral champagne wall"), "ratio-tall")}</div>
      <div class="s-txt offer-head">
        <span class="label">{t("Ma signature", "My signature")}</span>
        <h2 class="h2">{t("Design &amp; décoration", "Design &amp; styling")}</h2>
        <p class="it" style="color:var(--muted)">{t("Construire un thème, un univers qui vous ressemble.", "Building a theme, a world that is entirely yours.")}</p>
        <div class="prose">
          <p>{t("Un mariage, on s'en souvient pour l'ambiance et la beauté du moment. Vous avez sûrement mille et une idées en tête : mon métier de wedding designer, c'est créer de la magie, une expérience nouvelle, et faire de vos rêves une réalité.", "A wedding is remembered for its atmosphere and the beauty of the moment. You probably have a thousand ideas in mind; my role as a wedding designer is to create magic, a new experience, and turn your dreams into reality.")}</p>
          <p>{t("Je mène d'une main de fer dans un gant de velours tous les prestataires qui rendent cette journée époustouflante : décors éphémères, solutions esthétiques et techniques, sécurité des installations.", "I lead every supplier with an iron hand in a velvet glove to make the day breathtaking: temporary sets, aesthetic and technical solutions, and the safety of every installation.")}</p>
          <p>{t("C'est ce qui distingue Lovely Day Event : un vrai travail de création, du premier moodboard à la désinstallation, que la plupart des wedding planners ne proposent pas. Il demande du temps, des achats, de la fabrication et du stockage. C'est pourquoi il est compris dans la formule Signature, ou proposé en option avec la coordination du jour J.", "This is what sets Lovely Day Event apart: true creative work, from the first moodboard to the final take-down, which most wedding planners do not offer. It takes time, sourcing, making and storage, which is why it is included in the Signature package or offered as an add-on to on-the-day coordination.")}</p>
        </div>
        <div class="price"><span class="label">{t("En option, à partir de", "As an add-on, from")}</span><strong>2 000 €</strong><span class="small">{t("Inclus dans la formule Signature, en option avec la Coordination Jour J", "Included in the Signature package, or as an add-on to On-the-day coordination")}</span></div>
      </div>
    </div>
    <div class="roles">
      <div><h3 class="role-t">{t("Mon rôle", "My role")}</h3>{ul([t("Élaboration du cahier des charges", "Drawing up the brief"), t("Rendez-vous wedding styling : thème, concept, couleurs, ambiance et budget", "Wedding styling meeting: theme, concept, colours, mood and budget"), t("Devis techniques et scéniques : tentes, sols, son et lumière, fleuriste, graphiste, mobilier, art de la table", "Technical quotes: marquees, flooring, sound and lighting, florist, graphic designer, furniture, tableware"), t("Moodboards, palettes de couleurs et proposition de papeterie", "Moodboards, colour palettes and stationery proposals")])}</div>
      <div><div class="list-title" aria-hidden="true">&nbsp;</div>{ul([t("Shopping list et budget prévisionnel des achats et locations", "Shopping list and projected budget for purchases and rentals"), t("Recherche, achat et location des décorations", "Sourcing, buying and renting decor"), t("Confection des derniers détails : art de la table, espace enfants, cérémonie, signalétique, plan de table, urne, livre d'or…", "Making the final details: tableware, kids' corner, ceremony, signage, seating plan, card box, guest book…"), t("Installation du design de la réception le jour J", "Installing the reception design on the day")])}</div>
    </div>
    <div class="gallery" data-carousel>
      {c.img("MariageChateauGrattequina_TristanPerrier_NA-430", t("Art de la table blanc et doré", "White and gold tableware"))}
      {c.img("TristanPerrier_TraiteurAuroreAmbert_AA-117", t("Bar à cocktails, verres ciselés", "Cocktail bar with cut-glass tumblers"))}
      {c.img("MariageChateauGrattequina_TristanPerrier_NA-184", t("Bouquet de lisianthus noué sur une chaise de cérémonie", "Lisianthus posy tied to a ceremony chair"))}
      {c.img("table-rouge", t("Table aux serviettes rouges", "Table with red napkins"))}
      {c.img("MariageChateauGrattequina_TristanPerrier_NA-198", t("Panneau de bienvenue", "Welcome sign"))}
      {c.img("jennifer-laurent-table", t("Table bohème aux tons crème", "Bohemian cream-toned table"))}
    </div>
  </div>
</section>

<section class="section section--stone" id="location">
  <div class="wrap stack-lg">
    <div class="stack center" style="text-align:center"><span class="label">{t("Location", "Rentals")}</span><h2 class="h2">{t("Mais Lovely Day Event, c'est aussi…", "Lovely Day Event also offers…")}</h2></div>
    <div class="split">
      <div class="s-img reveal">{c.img("photobooth-margot", t("Borne photo en bois dans un parc", "Wooden photo booth in a park"), "ratio-tall")}</div>
      <div class="s-txt offer-head">
        <span class="label">Photobooth</span>
        <h3 class="h2">{t("Location de borne photo", "Photo booth rental")}</h3>
        <div class="prose">
          <p>{t("Entre le smartphone et le Photomaton, le photobooth capture instantanément des moments de convivialité et de joie, et imprime vos photos en quelques secondes. Il fait aussi des GIFs, des boomerangs et des mini-vidéos.", "Somewhere between a smartphone and a vintage photo booth, it instantly captures moments of fun and joy and prints your pictures in seconds. It also makes GIFs, boomerangs and short videos.")}</p>
          <p>{t("Facile à transporter et à mettre en marche, il est livré avec 400 tirages 10×15 de qualité professionnelle, personnalisés selon le thème de votre mariage. Toutes les photos sont partagées sur un drive 48 h après l'événement.", "Easy to transport and set up, it comes with 400 professional-quality 4×6 prints personalised to your wedding theme. Every photo is shared on a drive 48 hours after the event.")}</p>
        </div>
        <div class="price"><span class="label">{t("Location", "Rental")}</span><strong>400 €</strong><span class="small">{t("tirages supplémentaires : 90 €", "extra prints: €90")}</span></div>
        <p class="small">{t("Besoin d'un décor pour vos photos ? Je crée aussi l'espace photobooth assorti à votre thème.", "Need a backdrop? I also design a photo booth corner to match your theme.")}</p>
        <a class="link" href="{c.href("photobooth")}">{t("Tout savoir sur le photobooth", "More about the photo booth")}</a>
      </div>
    </div>
  </div>
</section>

<section class="section" id="faq">
  <div class="wrap split" style="align-items:start">
    <div class="s-txt stack c-1-4"><span class="label">{t("Questions fréquentes", "FAQ")}</span><h2 class="h2">{t("Vos questions", "Your questions")}</h2></div>
    <div class="faq c-6-7">
      {"".join(f'<details><summary>{q}</summary><div class="ans">{a}</div></details>' for q,a in faq)}
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap statement">
    <p class="it">{t("« Quand on aime le jour de son mariage, on aime pour la vie. »", "“Love your wedding day, and you'll love for a lifetime.”")}</p>
    <a class="btn" href="{c.href("contact")}">{t("Contactez-moi", "Enquire")}</a>
  </div>
</section>'''


# ---------------------------------------------------------------- Mariages
def p_mariages(c):
    t = c.t
    gal = ["016", "047", "069", "150", "167", "184", "198", "325", "425", "428", "430", "450", "453", "474"]
    alt = t("Mariage au Château Grattequina", "Wedding at Château Grattequina")
    return f'''
<section class="page-hero wrap">
  <span class="label">Weddingbook</span>
  <h1 class="h1">{t("Mariages récents<br>en France", "Recent weddings<br>in France")}</h1>
  <p class="it">{t("Des célébrations uniques imaginées en Gironde, Dordogne, Pays Basque et au-delà.", "Unique celebrations imagined in Gironde, Dordogne, the Basque Country and beyond.")}</p>
</section>

<section class="section" style="padding-top:0">
  <div class="wrap stack-lg">
    <figure class="ratio-wide zoom reveal"><img class="cover" src="{c.root}img/MariageChateauGrattequina_TristanPerrier_NA-001.webp" alt="{alt}" loading="eager"><span class="credit">© Tristan Perrier</span></figure>
    <div class="split">
      <div class="s-txt stack c-1-6"><span class="label">{t("Récit en images", "A story in pictures")}</span><h2 class="h2">Château Grattequina</h2></div>
      <div class="s-txt stack c-8-5"><p class="it" style="color:var(--muted)">{t("Un mariage tout en blanc et en lumière, au bord de la Garonne.", "A wedding in white and light, on the banks of the Garonne.")}</p><p class="label">{t("Photographies", "Photography")} · <a href="https://www.tristanperrier.fr/{t("", "en/")}" target="_blank" rel="noopener">Tristan Perrier</a></p></div>
    </div>
    <div class="gallery">
      {"".join(c.img(f"MariageChateauGrattequina_TristanPerrier_NA-{n}", alt) for n in gal)}
    </div>
  </div>
</section>

<section class="section section--stone">
  <div class="wrap stack-lg">
    <div class="stack center" style="text-align:center"><span class="label">{t("Ils se sont dit oui", "They said I do")}</span><h2 class="h2">{t("Nos mariés", "Our couples")}</h2></div>
    <div class="weddings">{"".join(wedding_post_card(c, sl) for sl in WEDDING_SLUGS)}</div>
  </div>
</section>

<section class="section">
  <div class="wrap statement">
    <h2 class="h2">{t("Et si le prochain récit était le vôtre ?", "Could the next story be yours?")}</h2>
    <a class="btn" href="{c.href("contact")}">{t("Parlez-moi de votre projet", "Tell me about your wedding")}</a>
  </div>
</section>'''


# ---------------------------------------------------------------- Contact
def p_contact(c):
    t = c.t
    return f'''
<section class="page-hero wrap">
  <span class="label">Contact</span>
  <h1 class="h1">{t("Votre love story", "Your love story")}</h1>
  <p class="it">{t("Parlez-moi de votre projet, de votre histoire et de votre vision. Je prendrai le temps de vous guider avec attention.", "Tell me about your plans, your story and your vision. I will take the time to guide you with care.")}</p>
</section>

<section class="section" style="padding-top:0">
  <div class="wrap contact-grid">
    <div class="coords">
      {c.img("MariageChateauGrattequina_TristanPerrier_NA-453", t("Mariés souriants dans un parc", "Smiling couple in a park"), "ratio-portrait")}
      <div class="stack" style="gap:10px"><span class="label">E-mail</span><a href="mailto:contact@lovelydayevent.fr" style="font-family:var(--display);font-size:24px">contact@lovelydayevent.fr</a></div>
      <div class="stack" style="gap:10px"><span class="label">{t("Téléphone &amp; WhatsApp", "Phone &amp; WhatsApp")}</span><a href="tel:+33689966731" style="font-family:var(--display);font-size:24px">+33 6 89 96 67 31</a></div>
      <div class="stack" style="gap:10px"><span class="label">{t("Basée à", "Based in")}</span><span style="font-family:var(--display);font-size:24px">Bordeaux, France</span><span class="small">{t("Gironde · Dordogne · Bassin d'Arcachon · Pays Basque · partout en France", "Gironde · Dordogne · Arcachon Bay · Basque Country · throughout France")}</span></div>
    </div>
    <form class="enquiry" novalidate data-subject="{t("Demande de mariage", "Wedding enquiry")}" data-done="{t("Votre messagerie s'ouvre avec votre demande prête à envoyer. Si rien ne s'affiche, écrivez directement à contact@lovelydayevent.fr.", "Your email app is opening with your enquiry ready to send. If nothing appears, write directly to contact@lovelydayevent.fr.")}">
      <div class="field full"><label for="f-names">{t("Vos prénoms", "Your names")}</label><input id="f-names" name="names" required autocomplete="name"></div>
      <div class="field"><label for="f-email">E-mail</label><input id="f-email" name="email" type="email" required autocomplete="email"></div>
      <div class="field"><label for="f-tel">{t("Téléphone", "Phone")}</label><input id="f-tel" name="tel" type="tel" autocomplete="tel"></div>
      <div class="field"><label for="f-date">{t("Date envisagée", "Wedding date")}</label><input id="f-date" name="date" placeholder="{t("ex. juin 2027", "e.g. June 2027")}"></div>
      <div class="field"><label for="f-guests">{t("Nombre d'invités", "Number of guests")}</label><select id="f-guests" name="guests"><option value="">—</option><option>{t("Moins de 50", "Under 50")}</option><option>50 – 100</option><option>100 – 200</option><option>{t("Plus de 200", "Over 200")}</option></select></div>
      <div class="field"><label for="f-place">{t("Lieu ou région", "Venue or region")}</label><input id="f-place" name="place"></div>
      <div class="field"><label for="f-offer">{t("Formule souhaitée", "Service")}</label><select id="f-offer" name="offer"><option value="">—</option><option>{t("Formule Signature (organisation, design, Jour J)", "Signature (planning, design, the day)")}</option><option>{t("Organisation + Jour J", "Planning + the day")}</option><option>{t("Design &amp; décoration", "Design &amp; styling")}</option><option>{t("Coordination Jour J", "On-the-day coordination")}</option><option>Photobooth</option></select></div>
      <div class="field full"><label for="f-msg">{t("Votre histoire, vos envies", "Your story, your wishes")}</label><textarea id="f-msg" name="message" required></textarea></div>
      <div class="full" style="display:flex;gap:24px;align-items:center;flex-wrap:wrap"><button class="btn" type="submit">{t("Envoyer ma demande", "Send my enquiry")}</button><p class="form-note" role="status">{t("Je vous réponds sous 48 heures.", "I reply within 48 hours.")}</p></div>
    </form>
  </div>
</section>

<section class="section section--stone">
  <div class="wrap figures">
    <div><strong>2014</strong><span class="label">{t("Agence créée dans la région bordelaise", "Agency founded near Bordeaux")}</span></div>
    <div><strong>3</strong><span class="label">{t("Formules : organisation, design, Jour&nbsp;J", "Packages: planning, design, the day")}</span></div>
    <div><strong>62</strong><span class="label">{t("Mariages orchestrés", "Weddings orchestrated")}</span></div>
  </div>
</section>

<section class="section">
  <div class="wrap split">
    <div class="s-txt stack c-1-5">
      <span class="label">{t("Bon à savoir", "Good to know")}</span>
      <h2 class="h2">{t("Tout préparer, c'est bien. Profiter, c'est mieux.", "Planning is good. Enjoying it is better.")}</h2>
    </div>
    <div class="s-txt prose c-7-6">
      <p>{t("Je préconise un an de préparatifs pour que les rendez-vous avec les prestataires soient lissés dans le temps. La vie continue pendant que le projet avance, et selon le mariage on peut le préparer en 2 à 12 mois : à court ou long terme, pensez à demander de l'aide à tout moment.", "I recommend a year of preparation so supplier meetings are spread out over time. Life goes on while the project moves forward, and depending on the wedding it can be planned in 2 to 12 months. Short or long notice, ask for help whenever you need it.")}</p>
      <p>{t("La coordination de votre jour J reste le plus important. Un mariage ne dure qu'une journée : il serait dommage de ne pas en profiter, et votre wedding planner est là pour mener à bien tout ce que vous aviez prévu.", "Coordinating your wedding day matters most. A wedding lasts only one day; it would be a shame not to enjoy it, and your wedding planner is there to carry out everything you planned.")}</p>
      <p class="it">{t("« Et puis un jour on rencontre une personne sans même le vouloir, puis elle devient notre plus belle histoire. »", "“And then one day you meet someone without even trying, and they become your most beautiful story.”")}</p>
    </div>
  </div>
</section>'''


# ---------------------------------------------------------------- Articles & récits
MONTHS = {"fr": "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split(),
          "en": "January February March April May June July August September October November December".split()}
WED_NAMES = {"yvonne-thomas-mariage-2025": "Yvonne & Thomas"}
SLUG2IMG = {v: k for k, v in IMG2SLUG.items()}
OLD_PATHS = {"": "index", "agence/": "agence", "organisation-de-mariage/": "prestations#organisation",
             "decoration-de-mariage/": "prestations#design", "coordination-le-jour-du-mariage/": "prestations#coordination",
             "en/agence-organisation-mariage-gironde/": "index"}
OLD_PATHS.update({v: k for k, v in ROUTES.items() if v})


def fmt_date(c, d):
    if not d:
        return ""
    y, m, dd = d.split("-")
    return f"{int(dd)} {MONTHS[c.lang][int(m) - 1]} {y}"


def text_of(html):
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", html))).strip()


def excerpt(txt, n=170):
    if len(txt) <= n:
        return txt
    cut = txt[:n].rsplit(" ", 1)[0]
    return cut.rstrip(",;:") + "…"


def rewrite_links(c, html):
    def rep(m):
        href = H.unescape(m.group(1))
        mm = re.match(r"https?://(?:www\.)?lovelydayevent\.fr/(.*)$", href)
        if mm:
            path = mm.group(1).split("?")[0]
            anchor = ""
            if "#" in path:
                path, anchor = path.split("#", 1)
                anchor = "#" + anchor
            if path and not path.endswith("/"):
                path += "/"
            key = OLD_PATHS.get(path)
            if key is None and path.strip("/") in POST_BY_SLUG:
                key = "post:" + path.strip("/")
            if key:
                k, _, a = key.partition("#")
                return f'href="{c.href(k)}{"#" + a if a else anchor}"'
            return f'href="{H.escape(href)}"'
        if href.startswith("http"):
            return f'href="{H.escape(href)}" target="_blank" rel="noopener"'
        return m.group(0)
    return re.sub(r'href="([^"]*)"', rep, html)


def wedding_data(slug, lang):
    p = POST_BY_SLUG[slug]
    b = p["blocks"]
    heads = [x for x in b if x["t"] == "h2"]
    htmls = [x for x in b if x["t"] == "html"]
    quotes = [x for x in b if x["t"] == "quote" and x["v"].strip().lower() != "en attente"]
    gallery = next((x["v"] for x in b if x["t"] == "gallery"), [])
    credit = ""
    for i, x in enumerate(b):
        if x["t"] == "h2" and "photos" in x["v"].lower() and i + 1 < len(b) and b[i + 1]["t"] == "html":
            credit = b[i + 1]["v"]
    story_fr = next((h["v"] for h in htmls if h["v"] != credit), "")
    name = WED_NAMES.get(slug, p["title"])
    head_fr = FR_HEAD_FIX.get(slug) or (heads[0]["v"].replace(" - ", " · ") if heads else "")
    if lang == "en":
        en = WED_EN[slug]
        return dict(name=name, head=en["head"], story=en["story"], quote=en["quote"] if quotes else "",
                    who=name, credit=credit.replace("<p>par", "<p>by"), gallery=gallery, cover=p["cover"])
    return dict(name=name, head=head_fr, story=story_fr, quote=quotes[0]["v"] if quotes else "",
                who=name, credit=credit, gallery=gallery, cover=p["cover"])


def wedding_post_card(c, slug):
    d = wedding_data(slug, c.lang)
    cands = ([("img", SLUG2IMG[slug])] if slug in SLUG2IMG else []) + [("j", d["cover"])] + [("j", u) for u in d["gallery"]]
    img = fitted_img(c, cands, d["name"], "ratio-tall")
    return f'''<a class="wedding reveal" href="{c.href("post:" + slug)}">
  {img}
  <div class="meta"><span class="label">{H.escape(d["head"])}</span></div>
  <h3 class="h3">{H.escape(d["name"])}</h3>
  <p>{H.escape(excerpt(text_of(d["story"])))}</p>
  <span class="link" style="justify-self:start">{c.t("Lire leur histoire", "Read their story")}</span>
</a>'''


def p_wedding(c, slug):
    t = c.t
    d = wedding_data(slug, c.lang)
    cover = c.img(SLUG2IMG[slug], d["name"], cls="post-cover", eager=True) if slug in SLUG2IMG else c.jimg(d["cover"], d["name"], cls="post-cover", eager=True)
    wp = next((w["place"] for w in WEDDINGS if IMG2SLUG.get(w["img"]) == slug), "")
    where = f' {t("à", "at")} {wp}' if wp else ""
    n_g = len(d["gallery"])
    gal = "".join(c.jimg(u, f'{d["name"]}, {t("mariage", "wedding")}{where} · photo {i + 1} {t("sur", "of")} {n_g}') for i, u in enumerate(d["gallery"]))
    idx = WEDDING_SLUGS.index(slug)
    others = [WEDDING_SLUGS[(idx + k) % len(WEDDING_SLUGS)] for k in (1, 2)]
    quote = ""
    if d["quote"]:
        quote = f'''<section class="section section--stone">
  <div class="wrap statement">
    <span class="label">{t("L'avis des mariés", "In their words")}</span>
    <blockquote class="it" style="margin:0;max-width:56ch">« {H.escape(d["quote"])} »</blockquote>
    <span class="label">{H.escape(d["who"])}</span>
    {"" if c.lang == "fr" else '<span class="small">Translated from French</span>'}
  </div>
</section>'''
    body = f'''
<section class="page-hero wrap">
  <span class="label">{t("Mariage", "Wedding")} · {H.escape(d["head"])}</span>
  <h1 class="h1">{H.escape(d["name"])}</h1>
</section>
<div class="wrap">{cover}</div>
<section class="section">
  <div class="wrap article">{rewrite_links(c, d["story"])}</div>
</section>
{quote}
<section class="section">
  <div class="wrap stack-lg">
    <div class="stack center" style="text-align:center"><span class="label">{t("Les photos du mariage", "The photographs")}</span><div class="small credit-line">{rewrite_links(c, d["credit"]).replace('tristanperrier.fr/"', 'tristanperrier.fr/' + t("", "en/") + '"')}</div></div>
    <div class="gallery">{gal}</div>
  </div>
</section>
<section class="section section--stone">
  <div class="wrap stack-lg">
    <div class="stack center" style="text-align:center"><span class="label">{t("Autres mariages", "More weddings")}</span></div>
    <div class="weddings">{"".join(wedding_post_card(c, o) for o in others)}</div>
    <div style="text-align:center"><a class="btn" href="{c.href("mariages")}">{t("Tous les mariages", "All weddings")}</a></div>
  </div>
</section>
{cta(c)}'''
    desc = excerpt(text_of(d["story"]), 155)
    title = f'{d["name"]} · {t("Mariage", "Wedding")} · Lovely Day Event'
    return body, title, desc


def cta(c):
    t = c.t
    return f'''<section class="section">
  <div class="wrap statement">
    <h2 class="h2">{t("Parlez-moi de votre projet", "Tell me about your wedding")}</h2>
    <a class="btn" href="{c.href("contact")}">{t("Me contacter", "Enquire")}</a>
  </div>
</section>'''


def render_blocks(c, blocks, title):
    out = []
    bl = list(blocks)
    while bl and bl[-1]["t"] in ("h2", "h3"):
        bl.pop()
    section = ""
    def alt_for(a):
        if a and not re.fullmatch(r"[A-Za-z0-9_\-]*\d{3,}[A-Za-z0-9_\-]*|[0-9a-f\-]{12,}", a.strip()) and a.strip() != title.strip():
            return a
        return f"{section} · {title.rstrip(' ?:!')}" if section else title
    for b in bl:
        if b["t"] in ("h2", "h3"):
            if b["v"].strip().lower() == title.strip().lower():
                continue
            section = b["v"].strip().rstrip(" :?").strip()
            out.append(f'<{b["t"]}>{H.escape(b["v"])}</{b["t"]}>')
        elif b["t"] == "html":
            out.append(rewrite_links(c, b["v"]))
        elif b["t"] == "img":
            f = c.jimg(b["v"], alt_for(b.get("alt")))
            # photos qui se suivent : regroupées en galerie
            if f and out and out[-1].startswith('<div class="gallery">'):
                out[-1] = out[-1][:-6] + f + "</div>"
            elif f and out and out[-1].startswith("<figure"):
                out[-1] = f'<div class="gallery">{out[-1]}{f}</div>'
            else:
                out.append(f)
        elif b["t"] == "gallery":
            g = "".join(c.jimg(u, alt_for(None)) for u in b["v"])
            if g:
                out.append(f'<div class="gallery">{g}</div>')
        elif b["t"] == "quote":
            who = f'<cite class="label">{H.escape(b.get("who", ""))}</cite>' if b.get("who") else ""
            out.append(f'<blockquote><p>{H.escape(b["v"])}</p>{who}</blockquote>')
    out = [x.replace('<div class="gallery">', '<div class="gallery" data-carousel>', 1) if x.startswith('<div class="gallery">') and x.count("<figure") >= 4 else x for x in out]
    return "\n".join(x for x in out if x)


def journal_card(c, p):
    p = loc(c, p)
    return f'''<a class="jcard reveal" href="{c.href("post:" + p["slug"])}">
  {fitted_img(c, [("j", p["cover"])] + [("j", u) for b in p["blocks"] for u in ([b["v"]] if b["t"] == "img" else b["v"] if b["t"] == "gallery" else [])], p["title"], "ratio-land")}
  <h2>{H.escape(p["title"])}</h2>
</a>'''


def p_post(c, slug):
    p = POST_BY_SLUG[slug]
    i = BLOG.index(p)
    p = loc(c, p)
    pool = [b for b in BLOG if c.lang == "fr" or b["slug"] in POSTS_EN]
    j = pool.index(POST_BY_SLUG[slug])
    related = [pool[(j + k) % len(pool)] for k in (1, 2, 3)]
    first_img = next((b["v"] for b in p["blocks"] if b["t"] == "img"), None)
    cover = c.jimg(p["cover"], p["title"], cls="post-cover", eager=True) if p["cover"] != first_img else ""
    body = f'''
<section class="page-hero wrap">
  <span class="label"><a href="{c.href("inspirations")}" style="text-decoration:none">{c.t("Inspirations", "Inspiration")}</a></span>
  <h1 class="h2" style="max-width:24ch">{H.escape(p["title"])}</h1>
</section>
<div class="wrap">{cover}</div>
<section class="section" style="padding-top:clamp(48px,6vw,88px)">
  <article class="wrap article">
{render_blocks(c, p["blocks"], p["title"])}
  </article>
</section>
<section class="section section--stone">
  <div class="wrap stack-lg">
    <div class="stack center" style="text-align:center"><span class="label">{c.t("À lire aussi", "Read next")}</span></div>
    <div class="journal">{"".join(journal_card(c, r) for r in related)}</div>
  </div>
</section>
{cta(c)}'''
    return body, f'{p["title"]} · Lovely Day Event', p["desc"] or excerpt(text_of(" ".join(b["v"] for b in p["blocks"] if b["t"] == "html")), 155)


def p_inspirations(c):
    return f'''
<section class="page-hero wrap">
  <span class="label">{c.t("Le journal de Lovely Day Event", "The Lovely Day Event journal")}</span>
  <h1 class="h1">{c.t("Inspirations", "Inspiration")}</h1>
  <p class="it">{c.t("Conseils, tendances et coulisses d'une wedding planner bordelaise, pour préparer votre mariage avec sérénité.", "Advice, trends and behind-the-scenes stories from a Bordeaux wedding planner, to help you plan your wedding with peace of mind.")}</p>
</section>
<section class="section" style="padding-top:0">
  <div class="wrap journal">{"".join(journal_card(c, p) for p in BLOG if c.lang == "fr" or p["slug"] in POSTS_EN)}</div>
</section>
{cta(c)}'''


# ---------------------------------------------------------------- Photobooth
def p_photobooth(c):
    t = c.t
    reviews = [
        (t("Fou-rires garantis !", "Laughter guaranteed!"), t("Nous avons loué ce photobooth pour notre mariage et nous avons adoré. Nous nous sommes éclatés avec nos invités. L'appareil est très simple d'utilisation et l'impression instantanée des photos est super sympa et de très bonne qualité. Les photos sont en plus personnalisables !", "We rented this photo booth for our wedding and loved it. We had a blast with our guests. It is very easy to use, the instant prints are great fun and excellent quality, and the photos can even be personalised!"), "Christelle M."),
        (t("C'est génial !", "It's brilliant!"), t("N'hésitez pas sur la location, nous avons tous bien rigolé et tous nos invités sont repartis avec une photo souvenir. Alexandra est très disponible et très sympathique pour toutes questions. La déco et les coloris choisis par Alexandra correspondaient parfaitement au thème de notre mariage.", "Don't hesitate: we all had a great laugh and every guest left with a keepsake photo. Alexandra is very available and friendly for any question, and the decor and colours she chose matched our wedding theme perfectly."), "Aline & Pascal"),
        (t("Génial, à ne pas manquer !", "Brilliant, not to be missed!"), t("Prestataire très à l'écoute, qui s'adapte à nos demandes. Le matériel est de super qualité, esthétique et pratique. Les photos sont magnifiques, les couleurs rendent super bien. Je recommande à 100 % !", "A very attentive supplier who adapts to every request. The equipment is high quality, beautiful and practical. The photos are gorgeous and the colours look wonderful. I recommend it 100%!"), "Jennifer D."),
    ]
    return f'''
<section class="page-hero wrap">
  <span class="label">{t("Location photobooth · Bordeaux", "Photo booth rental · Bordeaux")}</span>
  <h1 class="h1">{t("Un photobooth<br>pour votre mariage", "A photo booth<br>for your wedding")}</h1>
  <p class="it">{t("Des souvenirs inoubliables, imprimés en quelques secondes.", "Unforgettable memories, printed in seconds.")}</p>
</section>
<section class="section" style="padding-top:0">
  <div class="wrap split">
    <div class="s-img reveal">{c.img("photobooth-margot", t("Borne photo en bois dans un parc", "Wooden photo booth in a park"), "ratio-tall")}</div>
    <div class="s-txt stack">
      <span class="label">{t("C'est quoi un photobooth ?", "What is a photo booth?")}</span>
      <div class="prose">
        <p>{t("Entre le smartphone et le Photomaton, le photobooth est une grosse boîte sur pied, un stand photo portatif. Il capture instantanément des moments de convivialité et de joie : quelques instants plus tard, vous tenez votre photo entre vos mains, imprimée directement par la borne.", "Somewhere between a smartphone and a vintage photo booth, it is a portable photo stand on legs. It instantly captures moments of fun and joy: a few seconds later you are holding your print, made right there by the booth.")}</p>
        <p>{t("Le petit plus : il fait aussi des GIFs, des boomerangs et des mini-vidéos. Quoi de mieux pour amuser vos invités et garder un souvenir inoubliable de votre mariage ?", "The bonus: it also makes GIFs, boomerangs and short videos. What better way to entertain your guests and keep an unforgettable memory of your wedding?")}</p>
        <p>{t("La borne se trouve près de Bordeaux : vous venez la récupérer quelques jours avant votre événement et la rapportez le lendemain.", "The booth is based near Bordeaux: collect it a few days before your event and return it the day after.")}</p>
      </div>
    </div>
  </div>
</section>
<section class="section section--stone">
  <div class="wrap stack-lg">
    <div class="stack center" style="text-align:center"><span class="label">{t("Pourquoi louer un photobooth ?", "Why rent a photo booth?")}</span></div>
    <div class="steps" style="grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr))">
      <div class="step"><h3 class="h3">{t("Prise en main facile", "Easy to use")}</h3><p>{t("La borne est facile à transporter et à mettre en marche. Un tutoriel en ligne vous guide pour l'installation.", "Easy to transport and switch on, with an online tutorial to guide set-up.")}</p></div>
      <div class="step"><h3 class="h3">{t("400 tirages inclus", "400 prints included")}</h3><p>{t("Livré avec 400 impressions de qualité professionnelle. Si le stock est épuisé, toutes les photos sont partagées sur un drive 48 h après l'événement.", "Comes with 400 professional-quality prints. If they run out, every photo is shared on a drive 48 hours after the event.")}</p></div>
      <div class="step"><h3 class="h3">{t("Qualité et personnalisation", "Quality &amp; personalisation")}</h3><p>{t("Impression instantanée sur papier photo 10×15, en tirage classique ou format bandelette, personnalisée selon le thème de votre mariage.", "Instant 4×6 prints, classic or photo-strip format, personalised to your wedding theme.")}</p></div>
      <div class="step"><h3 class="h3">{t("Pensez aux accessoires", "Think props")}</h3><p>{t("Moustaches, lunettes, masques… et un fond photo adapté à votre thème : bohème, champêtre, plage.", "Moustaches, glasses, masks… and a backdrop to match your theme: boho, countryside, beach.")}</p></div>
    </div>
  </div>
</section>
<section class="section">
  <div class="wrap split split--rev">
    <div class="s-img reveal">{c.img("photobooth-tirage", t("Bandelettes photo imprimées par la borne", "Photo strips printed by the booth"), "ratio-tall")}</div>
    <div class="s-txt offer-head">
      <span class="label">{t("Tarif", "Pricing")}</span>
      <h2 class="h2">{t("Pour tous les événements", "For every event")}</h2>
      <div class="price"><span class="label">{t("Location", "Rental")}</span><strong>400 €</strong></div>
      <div class="price"><span class="label">{t("Photos supplémentaires", "Extra prints")}</span><strong>90 €</strong></div>
      <p class="prose">{t("Besoin d'un décor pour vos photos ? En tant que décoratrice de mariage, je crée aussi votre espace photobooth, bohème, champêtre ou romantique, pour qu'il corresponde à 100 % à votre mariage.", "Need a backdrop? As a wedding decorator, I can also design your photo booth corner, boho, countryside or romantic, so it matches your wedding perfectly.")}</p>
      <a class="btn" href="{c.href("contact")}" style="justify-self:start">{t("Réserver la borne", "Book the booth")}</a>
    </div>
  </div>
</section>
<section class="section section--tight">
  <div class="wrap mosaic">
    <div class="m-e reveal">{c.img("photobooth-soiree", t("Invités devant le photobooth", "Guests at the photo booth"), "ratio-land")}</div>
    <div class="m-d reveal">{c.img("photobooth", t("Borne photo dans un jardin de château", "Photo booth in a château garden"), "ratio-tall")}</div>
  </div>
</section>
<section class="section section--stone">
  <div class="wrap quotes">
    {"".join(f'<figure class="quote"><span class="label">{a}</span><blockquote>« {b} »</blockquote><figcaption class="label"><cite>{w}</cite></figcaption></figure>' for a, b, w in reviews)}
  </div>
</section>
{cta(c)}'''


# ---------------------------------------------------------------- Location déco
def p_location(c):
    t = c.t
    pics = ["loc-2", "loc-3", "loc-4", "loc-5", "loc-6", "loc-7"]
    return f'''
<section class="page-hero wrap">
  <span class="label">{t("Location de décoration · Bordeaux", "Decor rental · Bordeaux")}</span>
  <h1 class="h1">{t("Sublimer vos<br>événements privés", "Elevate your<br>private events")}</h1>
  <p class="it">{t("Louez vos décorations à Bordeaux, à petits prix.", "Rent your decor in Bordeaux, at gentle prices.")}</p>
</section>
<section class="section" style="padding-top:0">
  <div class="wrap split">
    <div class="s-img reveal">{c.img("location-arche", t("Arche de cérémonie en bois et voilages", "Wooden ceremony arch with drapes"), "ratio-tall")}</div>
    <div class="s-txt stack">
      <div class="prose">
        <p>{t("Organiser une fête à Bordeaux et dans sa région, c'est agréable ; trouver la décoration adéquate est plus compliqué, et surtout cela coûte cher. Étant dans le monde de l'événementiel, je vous propose à la location, à moindre coût, du mobilier et des éléments de décoration.", "Throwing a party in and around Bordeaux is a joy; finding the right decor is harder, and expensive. Working in events, I offer furniture and decorative pieces for rent at a lower cost.")}</p>
        <p>{t("Par exemple : une arche en bois et ses beaux voilages, parfaite pour une cérémonie en extérieur élégante et raffinée ; un candy bar façon charrette en bois, avec bonbonnières et contenants en verre pour vos mignardises ; des photophores et décorations en bois pour un thème naturel ou champêtre. Et bien d'autres choses encore !", "For example: a wooden arch with beautiful drapes, perfect for an elegant outdoor ceremony; a wooden-cart candy bar with glass jars for your sweets; lanterns and wooden pieces for a natural or countryside theme. And much more!")}</p>
        <p>{t("Le retrait se fait à mon local de Villenave-d'Ornon quelques jours avant votre événement.", "Collection is from my studio in Villenave-d'Ornon a few days before your event.")}</p>
      </div>
      <div class="steps" style="grid-template-columns:repeat(2,minmax(0,1fr))">
        <div class="step"><h3 class="h3">{t("Gagnez du temps", "Save time")}</h3><p>{t("Tout est prêt à poser, sélectionné avec un œil de décoratrice.", "Everything is ready to place, chosen with a decorator's eye.")}</p></div>
        <div class="step"><h3 class="h3">{t("Installation facile", "Easy set-up")}</h3><p>{t("Je peux aussi tout installer pour vous : moins de stress et un résultat soigné.", "I can also install everything for you: less stress and a polished result.")}</p></div>
      </div>
      <a class="btn" href="{c.href("contact")}" style="justify-self:start">{t("Demander le catalogue", "Request the catalogue")}</a>
    </div>
  </div>
</section>
<section class="section section--stone">
  <div class="wrap stack-lg">
    <div class="stack center" style="text-align:center"><span class="label">{t("Les petits détails font la différence", "Small details make the difference")}</span></div>
    <div class="gallery">{"".join(c.img(n, t("Élément de décoration de mariage", "Wedding decor piece")) for n in pics)}</div>
  </div>
</section>
{cta(c)}'''


# ---------------------------------------------------------------- Mentions légales
def p_mentions(c):
    t = c.t
    return f'''
<section class="page-hero wrap">
  <h1 class="h2">{t("Mentions légales", "Legal notice")}</h1>
</section>
<section class="section" style="padding-top:0">
  <div class="wrap article">
    <p>{t("Conformément aux dispositions de la loi n° 2004-575 du 21 juin 2004 pour la confiance en l'économie numérique, il est précisé aux utilisateurs du site www.lovelydayevent.fr l'identité des différents intervenants dans le cadre de sa réalisation et de son suivi.", "In accordance with French law no. 2004-575 of 21 June 2004 on confidence in the digital economy, users of www.lovelydayevent.fr are informed of the identity of the parties involved in creating and maintaining the site.")}</p>
    <h2>{t("Propriétaire du site, responsable de la publication", "Site owner and publisher")}</h2>
    <p>Madame Alexandra Ambert, {t("entrepreneur individuel", "sole trader")}<br>{t("Siège social", "Registered office")} : 8 rue des Primevères, 33140 Villenave-d'Ornon, France<br>SIRET : 80305420400018<br>Contact : contact@lovelydayevent.fr</p>
    <h2>{t("Hébergement", "Hosting")}</h2>
    <p>Hostinger International Ltd, 61 Lordou Vironos Street, 6023 Larnaca, {t("Chypre", "Cyprus")}<br><a href="https://www.hostinger.fr/contact" target="_blank" rel="noopener">hostinger.fr/contact</a></p>
    <h2>{t("Propriété intellectuelle", "Intellectual property")}</h2>
    <p>{t("La présentation et chacun des éléments apparaissant sur le site www.lovelydayevent.fr sont protégés par les lois en vigueur sur la propriété intellectuelle, et appartiennent à l'auteur ou font l'objet d'une autorisation d'utilisation.", "The presentation and every element of www.lovelydayevent.fr are protected by intellectual property law and belong to the author or are used with permission.")}</p>
    <p>{t("Aucun élément composant le site ne peut être copié, reproduit, modifié, réédité, dénaturé, transmis ou distribué, de façon partielle ou intégrale, sans l'autorisation écrite et préalable de l'auteur.", "No element of the site may be copied, reproduced, modified, republished, altered, transmitted or distributed, in part or in full, without the author's prior written permission.")}</p>
    <p>{t("Les logos, images et marques des entreprises citées sont la propriété de leurs auteurs. Toute représentation totale ou partielle d'éléments graphiques ou photographiques sans l'autorisation expresse de l'auteur est interdite et constituerait une contrefaçon sanctionnée par les articles L.335-2 et suivants du Code de la propriété intellectuelle.", "Logos, images and trademarks of the companies mentioned belong to their owners. Any reproduction of graphic or photographic elements without the author's express permission is prohibited and constitutes infringement under articles L.335-2 et seq. of the French Intellectual Property Code.")}</p>
    <h2>{t("Crédits photographiques", "Photo credits")}</h2>
    <p>Tristan Perrier, <a href="https://www.tristanperrier.fr/{t("", "en/")}" target="_blank" rel="noopener">tristanperrier.fr</a>, {t("ainsi que les photographes partenaires crédités sur chaque récit de mariage.", "and the partner photographers credited on each wedding story.")}</p>
  </div>
</section>'''


# ---------------------------------------------------------------- Génération
BUILDERS = dict(index=p_index, agence=p_agence, prestations=p_prestations, mariages=p_mariages, contact=p_contact,
                inspirations=p_inspirations, photobooth=p_photobooth, mentions=p_mentions)


def write(c, html):
    html = re.sub(r'<div class="gallery"([^>]*)>(.*?)</div>', gallery_rows, html, flags=re.S)
    html = re.sub(r'<figure class="(|post-cover)"><img ([^>]*?)style="--ar:([0-9.]+)"',
                  lambda m: f'<figure class="{m.group(1)}" style="--fig-ar:{m.group(3)}"><img {m.group(2)}style="--ar:{m.group(3)}"', html)
    if not PREVIEW:
        html = re.sub(r'<img src="([^"]+?)\.webp"([^>]*)>', add_srcset, html)
    path = os.path.join(OUT, route_of(c.page, c.lang), "index.html")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


written = []
for lang in ("fr", "en"):
    for key, fn in BUILDERS.items():
        if lang == "en" and not has_en(key):
            continue
        c = Ctx(lang, key)
        written.append((lang, key))
        write(c, page(c, fn(c)))
    for slug in WEDDING_SLUGS:
        c = Ctx(lang, "post:" + slug)
        body, title, desc = p_wedding(c, slug)
        write(c, page(c, body, title, desc))
for p in BLOG:
    for lang in ("fr", "en"):
        if lang == "en" and p["slug"] not in POSTS_EN:
            continue
        c = Ctx(lang, "post:" + p["slug"])
        body, title, desc = p_post(c, p["slug"])
        write(c, page(c, body, title, desc))

# Sitemap et redirections (version hébergée uniquement)
if not PREVIEW:
    urls = [SITE_URL + route_of(k) for k in BUILDERS] + [SITE_URL + route_of(k, "en") for k in BUILDERS if has_en(k)]
    urls += [SITE_URL + s + "/" for s in WEDDING_SLUGS] + [SITE_URL + route_of("post:" + s, "en") for s in WEDDING_SLUGS]
    urls += [SITE_URL + p["slug"] + "/" for p in BLOG]
    urls += [SITE_URL + route_of("post:" + p["slug"], "en") for p in BLOG if p["slug"] in POSTS_EN]
    with open(os.path.join(OUT, "sitemap.xml"), "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.writelines(f"  <url><loc>{u}</loc></url>\n" for u in urls)
        f.write("</urlset>\n")
    with open(os.path.join(OUT, "robots.txt"), "w") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n")
    with open(os.path.join(OUT, ".htaccess"), "w") as f:
        f.write("""# Lovely Day Event : redirections depuis l'ancien site WordPress
Options -MultiViews
DirectoryIndex index.html

# Compression et cache navigateur (vitesse / PageSpeed)
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css application/javascript text/javascript image/svg+xml application/xml
</IfModule>
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType image/webp "access plus 1 year"
  ExpiresByType image/png "access plus 1 year"
  ExpiresByType image/svg+xml "access plus 1 year"
  ExpiresByType font/woff2 "access plus 1 year"
  ExpiresByType text/css "access plus 1 month"
  ExpiresByType application/javascript "access plus 1 month"
  ExpiresByType text/javascript "access plus 1 month"
  ExpiresByType text/html "access plus 0 seconds"
</IfModule>
AddType font/woff2 .woff2

ErrorDocument 404 /index.html
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
Redirect 301 /agence/ /agence-evenementielle/
RewriteRule ^organisation-de-mariage/?$ /prestations/#organisation [NE,R=301,L]
RewriteRule ^decoration-de-mariage/?$ /prestations/#design [NE,R=301,L]
RewriteRule ^coordination-le-jour-du-mariage/?$ /prestations/#coordination [NE,R=301,L]
Redirect 301 /en/agence-organisation-mariage-gironde/ /en/
RedirectMatch 301 ^/(feed|comments/feed)/?$ /les-idees-de-lovely-day-inspirations/
RedirectMatch 301 ^/wp-admin.*$ /
""")

json.dump(USED_J, open(os.path.join(HERE, "used_journal_imgs.json"), "w"))
print("ok", OUT, len(written), "pages +", len(WEDDING_SLUGS) * 2, "récits +", len(BLOG), "articles")


# Redirections des anciennes adresses anglaises (slugs français) vers les slugs anglais
if not PREVIEW:
    _r = []
    for _k in BUILDERS:
        if has_en(_k) and ROUTES[_k] and ROUTES[_k] != ROUTES_EN[_k]:
            _r.append(("/en/" + ROUTES[_k], "/" + route_of(_k, "en")))
    for _s in sorted(set(WEDDING_SLUGS) | set(POSTS_EN)):
        if en_slug(_s) != _s:
            _r.append((f"/en/{_s}/", "/" + route_of("post:" + _s, "en")))
    with open(os.path.join(HERE, "en_redirects.txt"), "w", encoding="utf-8") as _f:
        for a, b in _r:
            _f.write(f"{a.rstrip('/')}  {b}  301\n{a}  {b}  301\n")
    print(len(_r), "redirections EN")

# Articles pas encore parus : on retire leurs pages d'une génération précédente
import shutil as _sh
for _s in UNPUBLISHED:
    _d = [os.path.join(OUT, _s)]
    _f = os.path.join(EN_DIR, _s + ".txt")
    if os.path.exists(_f):
        _t = parse_segs(open(_f, encoding="utf-8").read()).get("T")
        if _t and _slugify_en(_t):
            _d.append(os.path.join(OUT, "en", _slugify_en(_t)))
    for _x in _d:
        if os.path.isdir(_x):
            _sh.rmtree(_x)
print(len(UNPUBLISHED), "article(s) programmé(s) non publiés au", PUBLISH_DATE)
