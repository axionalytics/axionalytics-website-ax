# -*- coding: utf-8 -*-
"""
Scan staged content against the substitution list. Called by the pre-commit hook.

WHY SCAN CONTENT AND NOT JUST PATHS
-----------------------------------
Keeping _private/ out of git stops the obvious mistake. It does nothing about
the quiet one: a term from the substitution list pasted into an article, a code
sample, or documentation, where no path rule would ever see it.

Paths are easy to guard. Content is where things actually slip through.

Reads the list from _private/terms.py. Prints the matched file and the rule
reason, never the term itself, so the output is safe in a terminal log.

Exit 1 blocks the commit. Exit 0 allows it.

Usage: python _build/scripts/scan-staged.py   (normally via the pre-commit hook)
"""
import importlib.util
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TERMS_PATH = os.path.join(ROOT, "_private", "terms.py")

BINARY = (".png", ".jpg", ".jpeg", ".ico", ".xlsx", ".woff", ".woff2", ".pdf")


def load_terms():
    if not os.path.exists(TERMS_PATH):
        return []
    spec = importlib.util.spec_from_file_location("axio_terms", TERMS_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Only the "before" side is searched. Short needles and markup fragments
    # produce false positives that would train the user to bypass the hook,
    # which is worse than not having it.
    return [(n, why) for n, _r, why in mod.RULES
            if len(n) > 3 and "data-count" not in n]


def staged_files():
    out = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        cwd=ROOT).decode("utf-8", "replace")
    return [f for f in out.split("\n") if f.strip()]


def staged_content(path):
    """The staged blob, not the working copy — they can differ."""
    try:
        return subprocess.check_output(
            ["git", "show", ":" + path], cwd=ROOT,
            stderr=subprocess.DEVNULL).decode("utf-8", "replace")
    except Exception:
        return ""


def main():
    terms = load_terms()
    if not terms:
        return 0

    findings = []
    for path in staged_files():
        if path.lower().endswith(BINARY):
            continue
        text = staged_content(path)
        if not text:
            continue
        low = text.lower()
        for needle, why in terms:
            if needle.lower() in low:
                findings.append((path, why))

    if not findings:
        return 0

    print("")
    print("  COMMIT REFUSED")
    print("")
    print("  Staged content matches the substitution list:")
    print("")
    seen = set()
    for path, why in findings:
        key = (path, why)
        if key in seen:
            continue
        seen.add(key)
        print("      %-44s  [%s]" % (path, why))
    print("")
    print("  The term itself is withheld so this message is safe to share.")
    print("  Look up the reason in _private/terms.py, fix the file, re-stage.")
    print("")
    # Plain ASCII only below: this prints into a Windows console at the moment
    # someone is already alarmed, and a mojibaked warning reads as a broken tool.
    print("  If this is a false positive, commit with --no-verify - but read")
    print("  the flagged line first.")
    print("")
    return 1


if __name__ == "__main__":
    sys.exit(main())
