# Sources du site lovelydayevent.fr

Branche de sauvegarde des sources (la branche `production` contient le site généré, déployé par Sevalla).

- `python3 build.py site` régénère toutes les pages dans `site/` (FR + EN).
- `posts.json` : articles ; `posts_en/` : traductions anglaises ; `weddings_en.py` : récits de mariages.
- `site/assets/` : CSS, JS, polices ; `site/img/` : photos.
- `mkprod.sh` : copie `site/` vers la branche `production` avec `_redirects`, `_headers` et `llms.txt`.

Les chemins absolus des scripts sont à adapter si on reconstruit ailleurs.
