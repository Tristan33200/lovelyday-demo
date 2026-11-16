#!/bin/bash
# Publication de lovelydayevent.fr
#   ./publier.sh "message"     -> construit le site du jour, le pousse sur la branche "production"
#                                 (Sevalla redéploie tout seul), et prépare les branches parution-AAAA-MM-JJ
#                                 des articles programmés (SCHEDULE dans build.py).
#   NO_PUSH=1 ./publier.sh "x" -> construit tout sans rien envoyer (pour vérifier).
# À lancer depuis la branche "source" du dépôt. Nécessite python3 + Pillow (pip install pillow).
set -e
S=$(cd "$(dirname "$0")" && pwd)
P=$S/.prod
MSG="${1:-Mise à jour du site}"
TODAY=$(date -u +%F)
# Dates de parution programmées (SCHEDULE dans build.py) encore à venir
DATES=$(S=$S python3 - <<'PY'
import re,datetime
import os
s=open(os.path.join(os.environ["S"],"build.py")).read()
blk=s[s.index("SCHEDULE = {"):s.index("}",s.index("SCHEDULE = {"))]
t=datetime.date.today().isoformat()
print(" ".join(sorted({d for d in re.findall(r'"(\d{4}-\d\d-\d\d)"',blk) if d>t})))
PY
)
prep() {
cd $S && PUBLISH_DATE=$1 python3 build.py site > /dev/null
rm -rf $S/.build && cp -r $S/site $S/.build && rm -f $S/.build/.htaccess
python3 -I $S/rename_imgs.py $S/.build
printf 'google-site-verification: googlefcf2685566146d48.html' > $S/.build/googlefcf2685566146d48.html
cat > $S/.build/_redirects <<'R'
# www -> domaine principal
https://www.lovelydayevent.fr/*        https://lovelydayevent.fr/:splat          301!
# Anciennes adresses du site WordPress
/agence/                                /agence-evenementielle/                   301
/organisation-de-mariage                /prestations/#organisation                301
/decoration-de-mariage                  /prestations/#design                      301
/coordination-le-jour-du-mariage        /prestations/#coordination                301
/en/agence-organisation-mariage-gironde /en/                                      301
/feed                                   /les-idees-de-lovely-day-inspirations/    301
/comments/feed                          /les-idees-de-lovely-day-inspirations/    301
/wp-admin                               /                                         301
/wp-admin/*                             /                                         301
/location-de-decoration-de-mariage      /prestations/                             301
/en/location-de-decoration-de-mariage   /en/services/                          301
/delphine-ludovic                       /weddingbook-exemples-de-mariages/         301
/en/delphine-ludovic                    /en/weddings/      301
/emilie-aurelien                        /weddingbook-exemples-de-mariages/         301
/en/emilie-aurelien                     /en/weddings/      301
/melissa-sebastien-boheme-mariafe       /weddingbook-exemples-de-mariages/         301
/en/melissa-sebastien-boheme-mariafe    /en/weddings/      301
/mai-rufus                              /weddingbook-exemples-de-mariages/         301
/en/mai-rufus                           /en/weddings/      301
/marie-martin                           /weddingbook-exemples-de-mariages/         301
/en/marie-martin                        /en/weddings/      301
R
cat $S/en_redirects.txt >> $S/.build/_redirects
cat >> $S/.build/_redirects <<'R'
# Restes de WordPress (étiquettes, catégories, flux, pagination)
/tag/*                                  /les-idees-de-lovely-day-inspirations/    301
/category/*                             /les-idees-de-lovely-day-inspirations/    301
/page/*                                 /les-idees-de-lovely-day-inspirations/    301
/author/*                               /agence-evenementielle/                   301
/en/tag/*                               /en/journal/                              301
/en/category/*                          /en/journal/                              301
/:slug/feed/                            /:slug/                                   301
/:slug/feed                             /:slug/                                   301
# Page introuvable
/*                                      /index.html                               404
R
cp $S/llms.txt $S/.build/llms.txt
cat > $S/.build/_headers <<'H'
/*
  Strict-Transport-Security: max-age=31536000
  X-Content-Type-Options: nosniff
  X-Frame-Options: SAMEORIGIN
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()
  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; media-src 'self'; frame-src https://www.youtube-nocookie.com; connect-src 'self'; form-action 'self' mailto:; base-uri 'self'; object-src 'none'; frame-ancestors 'self'; upgrade-insecure-requests
/img/*
  Cache-Control: public, max-age=31536000
/assets/fonts/*
  Cache-Control: public, max-age=31536000
/assets/*
  Cache-Control: public, max-age=86400
H
}
commit() {
cd $P && find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} + && cp -r $S/.build/. ./
git add -A && git commit -qm "$1" || true
}
if [ ! -d $P/.git ]; then git clone -q --no-checkout "$(git -C $S remote get-url origin)" $P; fi
cd $P && git fetch -q origin production && (git checkout -q production 2>/dev/null || git checkout -q -b production origin/production)
# 1) version du jour -> branche production (mise en ligne)
prep $TODAY && commit "$MSG"
# 2) versions futures -> branches parution-AAAA-MM-JJ, chacune construite sur la précédente.
#    Le workflow GitHub « parution » avance production sur la bonne branche le jour venu.
git -C $P branch -f prochaine production
for D in $DATES; do
  cd $P && git checkout -q prochaine
  prep $D && commit "Parution programmée du $D"
  git -C $P branch -f parution-$D prochaine
done
cd $P && git checkout -q production
if [ -n "$NO_PUSH" ]; then echo "NO_PUSH : rien n'a été envoyé ($P)"; cd $S && python3 build.py site > /dev/null; exit 0; fi
git push -u origin production 2>&1 | tail -1
for D in $DATES; do git push -fq origin parution-$D; done
# branches de parution déjà passées : supprimées du dépôt
for B in $(git ls-remote --heads origin 'parution-*' | sed 's#.*refs/heads/##'); do
  case " $DATES " in *" ${B#parution-} "*) ;; *) git push -q origin --delete $B;; esac
done
# site/ revient à l'état du jour
cd $S && python3 build.py site > /dev/null
echo "Parutions programmées : $DATES"
