#!/bin/bash
# régénère la démo (noindex) depuis site/ et la pousse sur GitHub -> Sevalla
set -e
S=/tmp/claude-0/-home-user/20887b6f-fabe-5ce1-a4a5-fdc0d980e6c3/scratchpad
rm -rf $S/demo && cp -r $S/site $S/demo
python3 -I $S/rename_imgs.py $S/demo
find $S/demo -name "*.html" -exec sed -i 's|<head>|<head><meta name="robots" content="noindex, nofollow">|' {} +
printf 'User-agent: *\nDisallow: /\n' > $S/demo/robots.txt; rm -f $S/demo/sitemap*.xml
cd /home/user/lovelyday-demo && find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} + && cp -r $S/demo/. ./
git add -A && git commit -qm "$1

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_013Na2xn24ndN6rfzWREi6KN" && git push 2>&1 | tail -1
