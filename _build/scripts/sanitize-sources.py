# -*- coding: utf-8 -*-
"""
Apply the editorial substitution list to the page sources.

Marketing copy drafted from technical working notes tends to carry over detail
that is accurate but too specific to publish: over-precise figures, named
third-party products, and identifiers that mean something only inside one
system. Substituting the general term keeps the claim true and makes the copy
read better to a buyer, who does not need the specificity.

This script is the mechanism. It holds no substitution list of its own — the
list lives in _private/terms.py, outside version control, and is loaded at
runtime. Without that file the script is a clear no-op, which is the correct
behaviour for a fresh clone: the committed sources already reflect every
substitution, so there is nothing left to apply.

Runs against _build/ sources so the substitutions survive a rebuild. Idempotent.

Usage: python _build/scripts/sanitize-sources.py
"""
import glob
import importlib.util
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TERMS_PATH = os.path.join(ROOT, "_private", "terms.py")


def load_terms():
    """Return (RULES, REGEX_RULES), or empty lists when the private file is absent.

    Absent is not an error. Anyone working from the public repository has clean
    sources and no term list, and should still be able to build the site.
    """
    if not os.path.exists(TERMS_PATH):
        return [], []
    spec = importlib.util.spec_from_file_location("axio_terms", TERMS_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.RULES, mod.REGEX_RULES


RULES, REGEX_RULES = load_terms()

TARGETS = (
    glob.glob("_build/pages/*.body.html")
    + glob.glob("_build/pages/*.meta.html")
    + glob.glob("_build/src/articles/*.html")
    + glob.glob("_build/src/partials/*.html")
    + ["index.html"]
)


def main():
    if not RULES:
        print("  no substitution list at _private/terms.py - nothing to apply.")
        print("  (Expected in a fresh clone. The committed sources already")
        print("   reflect every substitution.)")
        return

    hits = {}
    touched = 0

    for path in TARGETS:
        if not os.path.exists(path):
            continue
        src = io.open(path, encoding="utf-8").read()
        out = src

        for needle, repl, why in RULES:
            if needle in out:
                n = out.count(needle)
                out = out.replace(needle, repl)
                hits.setdefault(why, 0)
                hits[why] += n

        for pattern, repl, why in REGEX_RULES:
            out, n = re.subn(pattern, repl, out)
            if n:
                hits.setdefault(why, 0)
                hits[why] += n

        if out != src:
            io.open(path, "w", encoding="utf-8").write(out)
            touched += 1

    if hits:
        print("  replacements by reason:")
        for why, n in sorted(hits.items(), key=lambda x: -x[1]):
            print("    %-52s %d" % (why, n))
    else:
        print("  nothing to change (already sanitized)")
    print("\n  %d file(s) modified" % touched)


if __name__ == "__main__":
    main()
