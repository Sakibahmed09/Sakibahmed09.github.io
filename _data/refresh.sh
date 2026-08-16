#!/bin/bash
# Weekly refresh: pull new posts, rebuild the venture pages, ship.
# The curated spine in ventures.json is never touched. New posts land in the
# live lane on each venture page.
set -euo pipefail

SITE="$HOME/claude-experiments/sakib-site"
DATA="$SITE/_data"
LOG="$DATA/refresh.log"

exec >> "$LOG" 2>&1
echo "--- $(date '+%Y-%m-%d %H:%M') refresh starting"

# 1. top up the LinkedIn cache (cache-first, only calls Apify when stale)
if [ -x "$HOME/scripts/scrape-linkedin.sh" ]; then
  "$HOME/scripts/scrape-linkedin.sh" sakib-ahmed1 --limit 40 --max-age-days 6 \
    || echo "warn: linkedin scrape failed, carrying on with cache"
else
  echo "warn: scrape-linkedin.sh missing, using cache only"
fi

# 2. re-mine both sources into buckets
cd "$DATA"
python3 mine.py | tail -3

# 3. regenerate the venture pages
python3 build.py | tail -6

# 4. ship, only if something actually changed and a remote exists
cd "$SITE"
if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -q -m "Refresh: new posts through $(date '+%d %b %Y')"
  if git remote get-url origin >/dev/null 2>&1; then
    git push -q origin HEAD && echo "pushed"
  else
    echo "committed locally (no remote yet)"
  fi
else
  echo "nothing new"
fi

echo "--- done"
