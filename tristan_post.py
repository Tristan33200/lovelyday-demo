# Article « Tristan Perrier » : portrait officiel, texte mis à jour (style actuel), 3e du journal
TP_PORTRAIT = "local:tristan-portrait"
TP_GARDE = "local:alexandra-chateau-de-garde"
TP_IMGS = {TP_PORTRAIT: "ShootingPortraitCorpo_ChateauMader_TristanPerrier-007.webp",
           TP_GARDE: "mariage-chateau-de-garde-MSoS-019_TristanPerrier.webp"}

TP_INTRO = """<p>Le <strong>mariage</strong> est une étape de vie unique, chargée d’<strong>émotions</strong>, que vous n’êtes pas prêts d’oublier… Alors autant <strong>bien choisir</strong> celui qui sera chargé d’en garder la mémoire.</p><p>Laissez-moi vous présenter <strong>Tristan Perrier</strong>, <strong>photographe de mariage éditorial</strong> basé à Bordeaux. Ce n’est pas par hasard que j’ai choisi de vous le présenter : Tristan est un photographe aux grandes <strong>qualités humaines et professionnelles</strong>, et nous travaillons ensemble depuis de nombreuses années lors de <a href="https://lovelydayevent.fr/">mariages dans la région de Bordeaux</a> et au-delà.</p>"""

TP_STYLE = """<p>Sa <strong>passion</strong> ? La <strong>photographie</strong>, depuis toujours. Tristan est une personne très <strong>sensible</strong>, profondément attachée aux relations humaines. Sa devise : la <strong>communication</strong>, le <strong>partage</strong> et surtout la <strong>bienveillance</strong>. Au-delà des images, il propose une <strong>expérience personnalisée</strong>, construite sur la <strong>confiance</strong>, la <strong>discrétion</strong> et l’exigence du détail, pour que les mariés se sentent pleinement à l’aise et vivent leur journée avec naturel.</p><p>Depuis plus de dix ans, il accompagne des couples en France et à l’international, avec plus de <strong>150 mariages haut de gamme</strong> à son actif. Son approche s’inscrit dans l’héritage de la photographie <em>fine art</em>, enrichie d’une <strong>direction artistique éditoriale</strong> inspirée de l’univers du luxe et de la mode. <strong>Lumière naturelle maîtrisée</strong>, composition équilibrée, colorimétrie subtile, travail du mouvement et de la matière : chaque image est pensée comme une photographie d’édition. Chez Tristan, l’<strong>élégance</strong> prime toujours sur la mise en scène excessive, et l’<strong>authenticité</strong> reste au cœur de sa démarche.</p><p>Au cours du <strong>mariage de Marie-Sophie &amp; Sébastien</strong>, en octobre 2020, Tristan et moi avons collaboré ensemble. Moi, chef d’orchestre de cette journée incroyable, et lui, <strong>photographe des festivités hors norme</strong>. Le mariage a eu lieu au <strong>Château de Garde</strong>, un lieu d’exception alliant architecture du XVIII<sup>e</sup> siècle et décoration intérieure raffinée : le cadre parfait pour <strong>sublimer chaque détail</strong>.</p>"""

TP_OUTRO = """<p>Je pourrais parler encore des heures du travail de Tristan et de sa sensibilité artistique, mais une image vaut mille mots : je vous invite à découvrir <strong>son travail</strong> directement sur son <strong>site internet</strong>, <a href="https://www.tristanperrier.fr/">tristanperrier.fr</a>, et à vous laisser emporter par son univers.</p>"""


def apply_tristan_post(posts, img_map):
    img_map.update(TP_IMGS)
    p = next(x for x in posts if x["slug"] == "tristan-perrier-le-photographe-mariage")
    p["date"] = "2026-07-20"
    p["desc"] = "Tristan Perrier, photographe de mariage éditorial basé à Bordeaux : l’héritage fine art, une direction artistique inspirée du luxe et de la mode, et l’authenticité avant tout. Je vous présente le photographe avec qui je travaille depuis des années."
    b = p["blocks"]
    b[1] = {"t": "html", "v": TP_INTRO}
    b[2] = {"t": "img", "v": TP_PORTRAIT, "alt": "Tristan Perrier, photographe de mariage à Bordeaux"}
    b[5:6] = [{"t": "html", "v": TP_STYLE},
              {"t": "img", "v": TP_GARDE, "alt": "Alexandra Ambert, wedding planner, au Château de Garde"},
              {"t": "html", "v": TP_OUTRO}]
