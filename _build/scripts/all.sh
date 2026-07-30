#!/usr/bin/env bash
# =============================================================================
# AXIONALYTICS — FULL SITE BUILD
# -----------------------------------------------------------------------------
# Order matters. Each step consumes the previous step's output:
#
#   1. make-articles    _build/src/articles/  -> _build/pages/*.{meta,body}.html
#                       and the blog index, from the ARTICLES manifest
#   2. make-glossary    _build/src/glossary/  -> _build/pages/*, plus the hub
#  2b. make-controls    the governance control matrix, from the CONTROLS manifest
#   3. extract-legal    _legacy/          -> _build/pages/* (legal text, unchanged)
#   4. add-breadcrumbs  injects BreadcrumbList into hand-written core meta files
#  4b. add-local-business  LocalBusiness schema on home + contact
#   5. make-author-page emits author.html once a name is set in author.py
#   6. sanitize-sources applies the editorial substitution list; idempotent
#   7. build.sh         assembles _build/pages/* + partials -> root *.html
#                       (still bilingual at this point)
#   8. add-contextual-links  inserts in-prose internal links; runs on built
#                       output so it is idempotent by construction
#  8b. add-pillar-clusters  links each pillar back down to its cluster, closing
#                       the one-way pillar/cluster relationship
#   9. build-tailwind   harvests the utility classes now present -> tailwind.css
#  10. make-i18n        splits the bilingual build into /  (en) and /es/ (es)
#  11. make-feeds       rss.xml + llms.txt from the article manifest
#  12. make-sitemap     sitemap.xml across both language trees
#  13. make-redirects   noindex stubs for retired URLs
#  14. check-leaks      fails the build if a substitution was missed
#  15. check-links      every link, anchor, asset, id, and control resolves
#
# make-i18n must run after build.sh, because build.sh regenerates the bilingual
# pages it consumes. Running build.sh alone leaves the site in an intermediate
# state where every page carries both languages.
#
# Usage: bash _build/scripts/all.sh
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

step() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

step "1/15  articles + blog index"
python _build/scripts/make-articles.py

step "2/15  glossary"
python _build/scripts/make-glossary.py

step "2b/15 governance control mapping"
python _build/scripts/make-controls.py

step "3/15  legal pages"
python _build/scripts/extract-legal.py

step "4/15  breadcrumbs"
python _build/scripts/add-breadcrumbs.py

step "4b/15 local business schema"
python _build/scripts/add-local-business.py

step "5/15  author page"
python _build/scripts/make-author-page.py

step "6/15  sanitize"
python _build/scripts/sanitize-sources.py

step "7/15  assemble pages"
bash _build/scripts/build.sh

step "8/15  contextual links"
python _build/scripts/add-contextual-links.py

step "8b/15 pillar -> cluster back-links"
python _build/scripts/add-pillar-clusters.py

step "9/15  compile tailwind"
python _build/scripts/build-tailwind.py

step "10/15 split language trees"
python _build/scripts/make-i18n.py

step "11/15 feeds"
python _build/scripts/make-feeds.py

step "12/15 sitemap"
python _build/scripts/make-sitemap.py

step "13/15 redirect stubs"
bash _build/scripts/make-redirects.sh

step "14/15 verification"
python _build/scripts/check-leaks.py

step "15/15 links, anchors, and controls"
python _build/scripts/check-links.py

printf '\n\033[1mdone.\033[0m  %s pages en  ·  %s pages es\n' \
  "$(ls -1 *.html | wc -l)" "$(ls -1 es/*.html | wc -l)"
