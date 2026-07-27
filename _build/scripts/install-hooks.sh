#!/usr/bin/env bash
# =============================================================================
# INSTALL THE PRE-COMMIT GUARD
# -----------------------------------------------------------------------------
# Git hooks live in .git/hooks/, which is NOT part of the repository and is not
# cloned. So this script exists to reinstall the guard on any machine, and it is
# committed precisely because the hook itself cannot be.
#
# Run once per clone:  bash _build/scripts/install-hooks.sh
#
# The hook it installs refuses any commit that stages a file under _private/,
# and any commit whose staged content matches the substitution list.
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [ ! -d .git ]; then
  echo "not a git repository - nothing to install"
  exit 1
fi

mkdir -p .git/hooks

cat > .git/hooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
# Refuses to commit local-only material. Installed by
# _build/scripts/install-hooks.sh - do not edit here, edit there.
set -uo pipefail

fail() { echo ""; echo "  COMMIT REFUSED"; echo ""; }

staged=$(git diff --cached --name-only --diff-filter=ACMR)
[ -z "$staged" ] && exit 0

# ---- 1. no paths under _private/ -------------------------------------------
private=$(echo "$staged" | grep '^_private/' || true)
if [ -n "$private" ]; then
  fail
  echo "  These files are under _private/ and stay local:"
  echo ""
  echo "$private" | sed 's/^/      /'
  echo ""
  echo "  Unstage them:   git rm -r --cached _private"
  echo "  Then check .gitignore still has a line reading:   _private/"
  echo ""
  exit 1
fi

# ---- 2. no listed term in staged content -----------------------------------
# The list is read from _private/terms.py, which is not committed. If it is
# absent the check cannot run, which is fine: that machine has nothing to
# match against in the first place.
if [ -f _private/terms.py ] && command -v python >/dev/null 2>&1; then
  if ! python _build/scripts/scan-staged.py; then
    exit 1
  fi
fi

exit 0
HOOK

chmod +x .git/hooks/pre-commit
echo "installed .git/hooks/pre-commit"
echo
echo "  guard 1: refuses any staged path under _private/"
echo "  guard 2: refuses any staged content matching the substitution list"
echo
echo "verifying it is executable and syntactically valid..."
bash -n .git/hooks/pre-commit && echo "  ok"
