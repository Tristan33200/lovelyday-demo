# Site lovelydayevent.fr — guide pour Claude

Site vitrine bilingue (FR/EN) d'Alexandra Ambert, wedding planner & designer près de Bordeaux depuis 2014.
Site 100 % statique, généré par `build.py`, hébergé sur Sevalla (sites statiques), domaine et e-mail chez Hostinger.
Réponds toujours en français à Alexandra, simplement, sans jargon technique.

## Le dépôt

| Branche | Contenu |
| --- | --- |
| `source` | **Tout ce qu'on modifie** : `build.py`, articles, traductions, CSS/JS, photos. Travailler ici. |
| `production` | Le site généré, servi par Sevalla sur lovelydayevent.fr (redéploiement automatique à chaque push). Ne jamais modifier à la main. |
| `parution-AAAA-MM-JJ` | Le site tel qu'il sera à cette date (articles programmés). Générées par `publier.sh`. |
| `main` | Ancienne démo + le workflow `.github/workflows/parution.yml`. **Ne pas supprimer** : c'est la branche par défaut, le workflow planifié y tourne. |

## Faire une modification puis publier

```bash
pip install pillow            # une fois par session
python3 build.py site         # régénère toutes les pages dans site/ (FR + EN)
# vérifier le rendu (python3 -m http.server --directory site, Playwright pour les captures)
NO_PUSH=1 ./publier.sh "x"    # facultatif : tout construire sans rien envoyer
./publier.sh "Ce qui a changé" # met en ligne + recalcule les branches de parution
git add -A && git commit -m "Ce qui a changé" && git push origin source
```

**Toujours publier avec `publier.sh`**, jamais en poussant directement sur `production` : sinon les branches de parution
(construites à partir de la version du jour) écraseraient la modification le jour de la parution suivante.

## Où sont les choses

- `build.py` : toutes les pages (fonctions `p_index`, `p_agence`, `p_prestations`, `p_mariages`, `p_contact`, `p_inspirations`, `p_photobooth`, `p_mentions`), en-tête, pied de page, données des mariages (`WEDDINGS`), textes FR/EN via `t("français", "english")`.
- `posts.json` : articles (FR) ; `posts_en/<slug>.txt` : traductions (repères `[T]` titre, `[D]` description, `[n]` bloc n, `[a n]` texte alternatif) ; `posts_en/_common.txt` : blocs répétés ; `weddings_en.py` : récits de mariages en anglais.
- `site/assets/style.css`, `site/assets/site.js` ; photos dans `site/img/` (webp).
- `llms.txt` : résumé du site pour les IA (tarifs, accompagnements) — à tenir à jour avec les prix.
- `publier.sh` : `_redirects` (anciennes adresses WordPress), `_headers` (sécurité, cache).

## Articles programmés (un par mois)

`SCHEDULE` dans `build.py` : slug → date de parution. Un article dont la date est future n'apparaît pas.
`publier.sh` prépare une branche `parution-<date>` par date ; le workflow GitHub `parution` (chaque matin, 5 h 17 UTC)
avance `production` jusqu'à la branche du jour. Pour programmer un nouvel article : l'ajouter à `posts.json`
(+ traduction dans `posts_en/`), mettre sa date dans `SCHEDULE`, puis `./publier.sh`.

Inspirations : `PINNED` (3 articles toujours en tête), puis du plus récent au plus ancien.
`HIDDEN` : articles gardés en ligne et dans le plan du site (référencement) mais absents de la liste.
`EN_SLUG_FIXED` : adresses anglaises figées — ne jamais changer une adresse existante (SEO), ajouter une redirection si besoin.

## Décisions validées par Alexandra (à respecter)

- La marque s'écrit toujours **LOVELY DAY EVENT** en entier (« Lovely Day Event »), jamais « Lovely Day » seul.
- Sous le logo : « Wedding Planner & Designer ». Pas de « Bordeaux » dans le logo, mais le référencement sur « wedding planner bordeaux » est prioritaire.
- Ne jamais employer le mot **« formule »** : on dit « accompagnement ». Les trois offres : **Signature** (organisation, design & Jour J, dès 6 900 €), **Collection** (organisation + Jour J, dès 5 000 €), **Sérénité** (coordination Jour J, dès 2 200 €, rendez-vous 4 mois avant).
- Design & décoration : **en option uniquement avec Sérénité**, à partir de 2 000 € ; inclus dans Signature ; jamais avec Collection, jamais seul. Photobooth : 400 €.
- Pas de badge « La plus choisie ». Pas de dates sur les articles ni sur les mariages.
- « +100 / Plus d'une centaine de mariages orchestrés » (ne plus mettre de nombre exact).
- Avis : 59 Google / 43 Mariages.net (16/11/2026) — à mettre à jour quand Alexandra le demande (fonction `ratings`).
- Galeries de 3 photos et plus : défilement horizontal au scroll, sans effet d'apparition du bas vers le haut.
- Photos : pas de filigrane « © Tristan Perrier » sur les images ; crédits dans les mentions légales (Tristan Perrier en premier, avec lien).
- Couleurs : champagne `#9C8466` (accent), fonds `#FBFAF7` et `#F1EEE8`, texte `#2A2825`, secondaire `#6B655D`, filets `#E3DFD7`. Polices : Cormorant Garamond (titres), Jost (texte).
- Feuillage décoratif : les dessins proposés par Claude ont été refusés ; Alexandra fournit les siens (SVG ou PNG transparent).
- Contact : le formulaire ouvre la messagerie (mailto, aucune donnée stockée) ; bouton WhatsApp flottant vers le 06 89 96 67 31.
- RGPD : aucun cookie de mesure ; la vidéo YouTube de L'agence ne se charge qu'au clic. Toute nouvelle intégration externe (carte, Instagram, statistiques) doit rester sans traceur ou être chargée au clic.

## À ne pas toucher

- Les enregistrements MX / e-mail du domaine chez Hostinger (boîte contact@ « Starter Business Email », payée jusqu'au 16/11/2030).
- Les adresses des pages existantes (référencement) : en cas de changement, ajouter une redirection dans `publier.sh`.
