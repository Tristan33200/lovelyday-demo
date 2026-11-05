"""Renomme les photos d'articles (img/journal) avec des noms parlants, d'après leur texte alternatif,
dans un dossier de sortie déjà généré (prod/ ou demo/), et met à jour toutes les références."""
import sys, os, re, glob, html, hashlib, unicodedata
D = sys.argv[1]
J = os.path.join(D, "img", "journal")
STOP = set("de la le les du des et pour un une a au aux en votre vos vous qu il elle d l sur sur par avec son sa ses ce cette ces est the of and for your to in at on with a an photo".split())
def slug(t, n=8):
    t = unicodedata.normalize("NFKD", html.unescape(t)).encode("ascii", "ignore").decode().lower()
    w = [x for x in re.split(r"[^a-z0-9]+", t) if x and x not in STOP and not (x.isdigit() and len(x) > 4)]
    out = []
    for x in w:
        if x not in out:
            out.append(x)
    return "-".join(out[:n]) or "mariage"
files = sorted(glob.glob(os.path.join(D, "**", "*.html"), recursive=True), key=lambda f: ("/en/" in f, f))
first = {}
for f in files:
    s = open(f, encoding="utf-8").read()
    tm = re.search(r"<title>(.*?)</title>", s)
    ptitle = tm.group(1).split(" · ")[0] if tm else ""
    for m in re.finditer(r'<img [^>]*?src="[^"]*img/journal/([^"/]+?)\.webp"[^>]*>', s):
        name = m.group(1)
        if name.endswith(".w800") or name in first:
            continue
        a = re.search(r'alt="([^"]*)"', m.group(0))
        alt = a.group(1) if a else ""
        first[name] = alt if " " in alt.strip() else ptitle
ren, used = {}, set()
for name, alt in first.items():
    new = f"{slug(alt)}-{hashlib.md5(name.encode()).hexdigest()[:4]}"
    while new in used:
        new += "x"
    used.add(new)
    ren[name] = new
    for suf in (".webp", ".w800.webp"):
        src = os.path.join(J, name + suf)
        if os.path.exists(src):
            os.rename(src, os.path.join(J, new + suf))
pat = re.compile(r"img/journal/([^\"'/\s,)]+?)\.(w800\.webp|webp)")
for f in glob.glob(os.path.join(D, "**", "*"), recursive=True):
    if not f.endswith((".html", ".xml", ".txt", ".json")) or not os.path.isfile(f):
        continue
    s = open(f, encoding="utf-8").read()
    t = pat.sub(lambda m: f"img/journal/{ren.get(m.group(1), m.group(1))}.{m.group(2)}", s)
    if t != s:
        open(f, "w", encoding="utf-8").write(t)
print(len(ren), "photos renommées")
