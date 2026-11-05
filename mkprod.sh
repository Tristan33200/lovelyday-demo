#!/bin/bash
# Production : site/ + _redirects + _headers -> branche "production" du dépôt -> Sevalla (lovelydayevent.fr)
set -e
S=/tmp/claude-0/-home-user/20887b6f-fabe-5ce1-a4a5-fdc0d980e6c3/scratchpad
P=$S/prodrepo
rm -rf $S/prod && cp -r $S/site $S/prod && rm -f $S/prod/.htaccess
python3 -I $S/rename_imgs.py $S/prod
printf 'google-site-verification: googlefcf2685566146d48.html' > $S/prod/googlefcf2685566146d48.html
cat > $S/prod/_redirects <<'R'
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
/en/location-de-decoration-de-mariage   /en/prestations/                          301
/delphine-ludovic                       /weddingbook-exemples-de-mariages/         301
/en/delphine-ludovic                    /en/weddingbook-exemples-de-mariages/      301
/emilie-aurelien                        /weddingbook-exemples-de-mariages/         301
/en/emilie-aurelien                     /en/weddingbook-exemples-de-mariages/      301
/melissa-sebastien-boheme-mariafe       /weddingbook-exemples-de-mariages/         301
/en/melissa-sebastien-boheme-mariafe    /en/weddingbook-exemples-de-mariages/      301
/mai-rufus                              /weddingbook-exemples-de-mariages/         301
/en/mai-rufus                           /en/weddingbook-exemples-de-mariages/      301
/marie-martin                           /weddingbook-exemples-de-mariages/         301
/en/marie-martin                        /en/weddingbook-exemples-de-mariages/      301
# Page introuvable
/*                                      /index.html                               404
R
cp $S/llms.txt $S/prod/llms.txt
cat > $S/prod/_headers <<'H'
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
if [ ! -d $P/.git ]; then git clone -q --no-checkout /home/user/lovelyday-demo $P; cd $P; git remote set-url origin "$(git -C /home/user/lovelyday-demo remote get-url origin)"; git checkout -q --orphan production; fi
cd $P && find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} + && cp -r $S/prod/. ./
git add -A && git commit -qm "$1

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_013Na2xn24ndN6rfzWREi6KN" && git push -u origin production 2>&1 | tail -1
