# -*- coding: utf-8 -*-
# Liens internes automatiques dans le texte des articles (SEO).
# Chaque règle : (cible, motifs FR, motifs EN). Le premier motif trouvé dans un paragraphe
# (hors titres, hors liens existants) devient un lien. Au plus 1 lien « commercial » + 2 liens d'articles.
import re

COMMERCIAL = [
    ("index", [r"wedding planner (?:à|de|sur|en région de) Bordeaux", r"wedding planner bordelaise", r"organisatrice de mariage", r"wedding planner"],
              [r"wedding planner (?:in|near|based in) Bordeaux", r"Bordeaux wedding planner", r"wedding planner"]),
    ("prestations", [r"coordination (?:du |le )?jour J", r"accompagnement sur[- ]mesure", r"organisation de (?:votre|leur) mariage", r"wedding designer", r"décoration de mariage"],
                    [r"on-the-day coordination", r"wedding[- ]day coordination", r"wedding designer", r"wedding decoration"]),
    ("photobooth", [r"photo ?booth", r"borne photo"], [r"photo ?booth"]),
]
TOPICS = [
    ("mariagesansstress", [r"sans stress"], [r"stress-free"]),
    ("les-lieux-de-reception-ou-se-marier-sur-le-bassin-darcachon", [r"[Bb]assin d['’]Arcachon"], [r"Arcachon Bay"]),
    ("details-comment-se-passe-la-coordination-du-jour-de-votre-mariage-avec-une-organisatrice-d-evenementiel-dans-la-region-bordelaise-194-html",
        [r"coordinatrice", r"coordination du mariage"], [r"coordinator"]),
    ("ceremonie-laique-bord-de-leau-arcachon", [r"au bord de l['’]eau", r"bord de mer"], [r"waterside", r"by the sea"]),
    ("faire-mariage-100-eco-responsable-sur-bordeaux", [r"éco-?responsable", r"écologique"], [r"eco-friendly", r"sustainable"]),
    ("mariage-champetre-sobre-elegant-bordeaux", [r"champêtre"], [r"country-style", r"rustic"]),
    ("le-rituel-du-sable-en-mariage-laique-symbolisme-et-signification", [r"rituel du sable", r"cérémonie du sable"], [r"sand ritual", r"sand ceremony"]),
    ("le-rituel-des-rubans-en-mariage-laique", [r"rituel des rubans", r"cérémonie des rubans"], [r"ribbon ritual", r"ribbon ceremony"]),
    ("comment-organiser-une-ceremonie-laique-pres-de-bordeaux", [r"cérémonie laïque"], [r"symbolic ceremony", r"humanist ceremony"]),
    ("musiquesentreedemariage", [r"entrée des mariés", r"musique d['’]entrée"], [r"(?:couple's|grand) entrance"]),
    ("ideesoriginalesplandetable", [r"plan de table"], [r"seating plan"]),
    ("dispositiondestablesdemariage", [r"disposition des tables"], [r"table layout"]),
    ("retroplanning-de-mariage-guide-complet-de-a-a-z", [r"r[ée]tro-?planning"], [r"wedding timeline"]),
    ("ouverturedebal", [r"ouverture de bal"], [r"first dance"]),
    ("lieu-de-reception", [r"lieu de réception"], [r"reception venue"]),
    ("prendre-un-videaste-de-mariage", [r"vidéaste"], [r"videographer"]),
    ("la-liste-13-maquilleuses-mariage-de-bordeaux", [r"maquilleuse", r"maquillage"], [r"make-up artist"]),
    ("7-choix-de-gateaux-pour-un-mariage-a-votre-image", [r"gâteau", r"wedding cake"], [r"wedding cake"]),
    ("organiser-lune-de-miel-inoubliable-sept-etapes", [r"lune de miel"], [r"honeymoon"]),
    ("conseils-pour-choisir-la-robe-de-mariee-parfaite", [r"robe de mariée"], [r"wedding dress"]),
    ("lelopement-un-mariage-en-tout-intimite", [r"[ée]lopement"], [r"elopement"]),
    ("mariagesintimes", [r"petit comité", r"mariage intime"], [r"intimate wedding"]),
    ("faire-part-personnalise-en-gironde", [r"faire-part"], [r"invitations"]),
    ("organiser-sa-demande-en-fiancailles", [r"demande en mariage", r"demande en fiançailles"], [r"proposal"]),
    ("5-conseils-pour-choisir-sa-bague-de-fiancailles", [r"bague de fiançailles"], [r"engagement ring"]),
    ("checklist-de-mariage-la-to-do-list-indispensable", [r"check-?list", r"to-do list"], [r"checklist", r"to-do list"]),
    ("definir-budget-mariage", [r"budget"], [r"budget"]),
    ("les-animations-des-temoins-aux-mariages", [r"témoins"], [r"witnesses"]),
    ("tristan-perrier-le-photographe-mariage", [r"photographe"], [r"photographer"]),
    ("prestataires-choix-mariage", [r"prestataires"], [r"suppliers"]),
    ("mariagealetranger", [r"à l['’]étranger"], [r"abroad"]),
]

_SPLIT = re.compile(r"(<a\b.*?</a>|<h[1-6]\b.*?</h[1-6]>|<[^>]+>)", re.S | re.I)


def _link_once(html, pats, href):
    parts = _SPLIT.split(html)
    for i, part in enumerate(parts):
        if not part or part.startswith("<"):
            continue
        for p in pats:
            m = re.search(r"(?<![\w-])(" + p + r")(?![\w-])", part, re.I)
            if m:
                parts[i] = part[:m.start()] + f'<a href="{href}">{m.group(1)}</a>' + part[m.end():]
                return "".join(parts), True
    return html, False


def autolink(c, slug, html_blocks, available):
    """html_blocks: liste d'indices->html ; renvoie la liste modifiée."""
    en = c.lang == "en"
    allhtml = " ".join(html_blocks)
    def already(href):
        return f'href="{href}"' in allhtml
    budget_c, budget_t = 1, 2
    out = list(html_blocks)
    def apply(rules, n, commercial):
        done = 0
        for key, fr, enp in rules:
            if done >= n:
                break
            page = key if commercial else "post:" + key
            if not commercial and (key == slug or key not in available):
                continue
            href = c.href(page)
            if already(href):
                continue
            for i, h in enumerate(out):
                h2, ok = _link_once(h, enp if en else fr, href)
                if ok:
                    out[i] = h2
                    done += 1
                    break
    apply(COMMERCIAL, budget_c, True)
    apply(TOPICS, budget_t, False)
    return out
