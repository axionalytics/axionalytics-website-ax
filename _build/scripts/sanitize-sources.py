# -*- coding: utf-8 -*-
"""
Remove client-identifying specifics from the public site copy.

The solution pages were drafted from internal platform documentation. Some of
that documentation's detail is fine to publish — architectural patterns, the
shape of a pipeline, capability names. Some of it is not:

  1. Real identifiers from a client's namespace. A requirement ID and three
     signal names were carried through verbatim into an illustrative terminal
     mock. Those belong to the customer's system, not to us, and a reader in
     that industry could recognise them.

  2. Exact-match metrics. Unrounded counts fingerprint one specific deployment:
     search the figure, find the customer. Rounding preserves the honesty of the
     scale claim while removing the match.

  3. Named vendor components. Product names taken from an internal stack
     description imply commitments we do not need to make publicly, and read
     as over-specific to a buyer. The general category term carries the same
     technical weight.

WHERE THE RULES LIVE
--------------------
Not here. A sanitiser has to name what it removes, which would make this the
single most sensitive file in a public repository. The literal strings live in
_private/terms.py, which is never committed. This file is the mechanism; that
file is the secret.

Without _private/terms.py this script is a clear no-op. That is correct
behaviour for a clone of the public repository: the committed sources are
already sanitised, so there is nothing left to do and nothing to leak.

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
        print("  no term list at _private/terms.py - nothing to sanitize.")
        print("  (Expected when working from the public repository. The committed")
        print("   sources are already clean; there is nothing to remove.)")
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
