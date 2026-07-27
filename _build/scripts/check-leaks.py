# -*- coding: utf-8 -*-
"""
Confirm nothing client-identifying escaped, by two independent routes.

WHY THIS EXISTS AS A SCRIPT
---------------------------
The obvious way to check is a grep with the sensitive terms typed into it. That
creates a second problem: the command itself names the client, so it cannot go
in the README, a commit message, a CI log, or anywhere else someone might read.

This reads the terms from _private/terms.py — the single place they are declared,
and a file git never sees — and reports only counts and rule descriptions. The
output is safe to paste anywhere. It also means the check can never drift from
the sanitiser: add a rule there and it is covered here automatically.

TWO CHECKS, NOT ONE
-------------------
  1. TERM SCAN — does any sensitive string appear in the published output?
     Needs _private/terms.py. Skipped with a warning if absent.

  2. TRACKING CHECK — is any file under _private/ staged or committed to git?
     Needs nothing but git, and matters more than check 1 now that the
     repository is public. The published site being clean is worth little if
     the source documents are sitting in the repo next to it.

Check 2 is the one that would catch the catastrophic mistake. A `git add -f`,
a rewritten .gitignore, or a fresh clone without the ignore rules would all put
_private/ into a public repository, and no amount of HTML scanning would notice.

Exit code is 1 if either check fails, so it can gate a deploy.

Usage: python _build/scripts/check-leaks.py
"""
import glob
import importlib.util
import io
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TERMS_PATH = os.path.join(ROOT, "_private", "terms.py")


def load_rules():
    """Sensitive terms, or None when the private list is not present."""
    if not os.path.exists(TERMS_PATH):
        return None
    spec = importlib.util.spec_from_file_location("axio_terms", TERMS_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.RULES


def published_files():
    """Everything a stranger can fetch: both language trees plus assets."""
    out = []
    out += glob.glob(os.path.join(ROOT, "*.html"))
    out += glob.glob(os.path.join(ROOT, "es", "*.html"))
    out += glob.glob(os.path.join(ROOT, "assets", "*"))
    for name in ("sitemap.xml", "rss.xml", "llms.txt", "robots.txt"):
        p = os.path.join(ROOT, name)
        if os.path.exists(p):
            out.append(p)
    return [p for p in out if os.path.isfile(p)]


def check_terms():
    """Scan the published output for sensitive strings. Returns 0 or 1."""
    rules = load_rules()
    if rules is None:
        print("  [1/2] term scan  SKIPPED - no _private/terms.py on this machine")
        print("        Expected in a clone of the public repository. Expected")
        print("        NOWHERE ELSE: if you are the maintainer and see this, the")
        print("        term list is missing and the check is not protecting you.")
        return 0

    files = published_files()

    # Only the "before" side of each rule is a sensitive term. Skip rules whose
    # needle is a markup fragment rather than a word (counters, attributes).
    terms = [(needle, why) for needle, _repl, why in rules
             if "data-count" not in needle and len(needle) > 3]

    findings = []
    for path in files:
        try:
            text = io.open(path, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        for needle, why in terms:
            if needle in text:
                findings.append((rel, why, text.count(needle)))

    print("  [1/2] term scan  %d published files against %d sensitive terms"
          % (len(files), len(terms)))

    if not findings:
        print("        CLEAN - no client-identifying term reached the output")
        return 0

    print("\n        LEAKS FOUND (term withheld; see the rule reason):\n")
    for rel, why, n in findings:
        print("          %-44s %2d x  [%s]" % (rel, n, why))
    print("\n        Run: python _build/scripts/sanitize-sources.py"
          " && bash _build/scripts/build.sh")
    return 1


def check_tracking():
    """Fail if git is tracking anything under _private/. Returns 0 or 1."""
    if not os.path.isdir(os.path.join(ROOT, ".git")):
        print("  [2/2] tracking   SKIPPED - not a git repository")
        return 0

    try:
        out = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard",
             "_private"],
            cwd=ROOT, stderr=subprocess.STDOUT).decode("utf-8", "replace")
    except Exception as exc:
        print("  [2/2] tracking   COULD NOT RUN (%s)" % exc)
        return 0

    # --others --exclude-standard lists untracked-and-not-ignored files, so a
    # correctly ignored _private/ produces no output at all. Anything here is
    # either already committed or about to be picked up by `git add -A`.
    leaked = [ln for ln in out.split("\n") if ln.strip()]

    if not leaked:
        print("  [2/2] tracking   CLEAN - _private/ is invisible to git")
        return 0

    print("  [2/2] tracking   *** STOP *** git can see %d file(s) under "
          "_private/:" % len(leaked))
    for ln in leaked[:20]:
        print("          %s" % ln)
    if len(leaked) > 20:
        print("          ... and %d more" % (len(leaked) - 20))
    print("""
        This repository is PUBLIC. These files must never be committed.

        Fix:
          1. confirm .gitignore still contains a line reading  _private/
          2. if any are already staged:   git rm -r --cached _private
          3. if any are already COMMITTED and pushed, the history is
             compromised. Do not simply delete them in a new commit — git
             keeps the old ones. Delete the GitHub repository, recreate it,
             and push a fresh history.""")
    return 1


def main():
    a = check_terms()
    b = check_tracking()
    return 1 if (a or b) else 0


if __name__ == "__main__":
    sys.exit(main())
