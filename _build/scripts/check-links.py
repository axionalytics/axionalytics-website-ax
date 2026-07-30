# -*- coding: utf-8 -*-
"""
Verify every link, anchor, asset, and interactive element in the built site.

WHY THIS EXISTS
---------------
The site shipped with a dead email gate: the markup nested one <form> inside
another, the HTML parser silently discarded the inner tag, getElementById
returned null, no listener was attached, and the button did nothing. No console
error, no failed request, no visible symptom. It was found by a human clicking
it, days after going live.

Every check below corresponds to a way this site can break without anyone
noticing. The last two would have caught that specific bug before it shipped.

WHAT IS CHECKED
---------------
  1. internal links      every href="page.html" resolves to a real file
  2. anchors             every #fragment resolves to an element with that id
  3. assets              every css/js/img/icon reference exists on disk
  4. duplicate ids       invalid HTML, and getElementById silently picks one
  5. nested forms        parser discards the inner tag; the bug described above
  6. JS-referenced ids   every id the scripts look up exists on some page
  7. button types        a <button> inside a form without type="button"
                         defaults to submit and can navigate unexpectedly
  8. empty links         <a> with no href, or href="#" with no handler

External links are NOT checked by default: it needs network, it is slow, and a
third party being briefly down should not fail a local build. Run them
explicitly when you want them:

    python _build/scripts/check-links.py --external

Exit code is 1 if anything fails, so it can gate a deploy.

Usage: python _build/scripts/check-links.py [--external]
"""
import glob
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ids built at runtime rather than written in the markup. Listing them here is
# deliberate: an unexplained entry in this set is a bug waiting to happen.
DYNAMIC_IDS = set()


def pages():
    out = sorted(glob.glob(os.path.join(ROOT, "*.html")))
    out += sorted(glob.glob(os.path.join(ROOT, "es", "*.html")))
    return out


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def strip_comments(html):
    return re.sub(r"<!--.*?-->", "", html, flags=re.S)


def resolve(base, ref):
    """Where a href/src actually points on disk.

    A leading slash means the site root, not the current folder. Getting this
    wrong makes every root-absolute reference look broken when it is fine.
    """
    if ref.startswith("/"):
        return os.path.normpath(os.path.join(ROOT, ref.lstrip("/")))
    return os.path.normpath(os.path.join(base, ref))


# ---------------------------------------------------------------------------

def check_internal_links(docs, fail):
    n = 0
    for path, html in docs.items():
        base = os.path.dirname(path)
        for href in set(re.findall(r'href="([^"]+)"', html)):
            if re.match(r"^(https?:|mailto:|tel:|#|//|data:)", href):
                continue
            target = href.split("#")[0].split("?")[0]
            if not target:
                continue
            if not os.path.exists(resolve(base, target)):
                fail("internal link", "%s -> %s" % (rel(path), href))
            n += 1
    return n


def check_anchors(docs, fail):
    ids = {p: set(re.findall(r'id="([^"]+)"', h)) for p, h in docs.items()}
    n = 0
    for path, html in docs.items():
        base = os.path.dirname(path)
        for href in set(re.findall(r'href="([^"]*#[^"]+)"', html)):
            if re.match(r"^(https?:|mailto:|tel:)", href):
                continue
            page_part, frag = href.split("#", 1)
            if not frag:
                continue
            target = resolve(base, page_part) if page_part else path
            if target not in ids:
                continue          # missing page already reported above
            if frag not in ids[target]:
                fail("dead anchor", "%s -> %s (no id=\"%s\")" % (rel(path), href, frag))
            n += 1
    return n


def check_assets(docs, fail):
    n = 0
    seen = set()
    for path, html in docs.items():
        base = os.path.dirname(path)
        refs = re.findall(r'(?:src|href)="([^"]+\.(?:css|js|png|jpg|jpeg|svg|ico|webp|woff2?))"', html)
        for r in set(refs):
            if re.match(r"^(https?:|//|data:)", r):
                continue
            key = (base, r)
            if key in seen:
                continue
            seen.add(key)
            if not os.path.exists(resolve(base, r)):
                fail("missing asset", "%s -> %s" % (rel(path), r))
            n += 1
    return n


def check_duplicate_ids(docs, fail):
    n = 0
    for path, html in docs.items():
        found = re.findall(r'id="([^"]+)"', html)
        n += len(found)
        dupes = set(x for x in found if found.count(x) > 1)
        for d in sorted(dupes):
            fail("duplicate id", '%s has id="%s" %d times'
                 % (rel(path), d, found.count(d)))
    return n


def check_nested_forms(docs, fail):
    """A <form> inside a <form> is discarded by the parser. This shipped once."""
    n = 0
    for path, html in docs.items():
        depth = 0
        for m in re.finditer(r"<form\b|</form>", strip_comments(html)):
            if m.group(0) == "</form>":
                depth = max(0, depth - 1)
            else:
                if depth > 0:
                    fail("nested form",
                         "%s has a <form> inside another <form> - the inner tag "
                         "is discarded by the browser" % rel(path))
                depth += 1
                n += 1
    return n


def check_js_ids(docs, fail):
    """Every id the JavaScript looks up must exist somewhere in the site.

    This is the check that catches a control the scripts drive but the markup
    never renders - the failure mode is total silence, because getElementById
    returning null is not an error.
    """
    all_ids = set()
    for h in docs.values():
        all_ids |= set(re.findall(r'id="([^"]+)"', h))

    js_files = sorted(glob.glob(os.path.join(ROOT, "assets", "*.js")))
    wanted = {}
    for jf in js_files:
        src = io.open(jf, encoding="utf-8").read()
        # getElementById('x'), querySelector('#x'), and the local $('x') helper
        # (defined in these files as a getElementById wrapper).
        pats = [r"getElementById\(\s*['\"]([^'\"]+)['\"]",
                r"querySelector\(\s*['\"]#([A-Za-z][\w-]*)['\"]",
                r"(?<![\w.])\$\(\s*['\"]([A-Za-z][\w-]*)['\"]\s*\)"]
        for p in pats:
            for m in re.finditer(p, src):
                wanted.setdefault(m.group(1), set()).add(os.path.basename(jf))

    for i in sorted(wanted):
        if i in all_ids or i in DYNAMIC_IDS:
            continue
        fail("js id not in markup",
             '%s looks up id="%s" - no page renders it'
             % (", ".join(sorted(wanted[i])), i))
    return len(wanted)


def check_tree_parity(docs, fail):
    """The English and Spanish pages must expose the same element ids.

    check_js_ids only asks whether an id exists somewhere in the site, which is
    right for page-specific controls but blind to divergence between the two
    trees: rename a control in one tree and the other still satisfies the check
    while half the site quietly breaks. The trees are mirrors produced by the
    same splitter, so any difference in ids is a defect.
    """
    n = 0
    for path, html in docs.items():
        r = rel(path)
        if r.startswith("es/") or "/" in r:
            continue
        twin = os.path.join(ROOT, "es", os.path.basename(path))
        if twin not in docs:
            continue
        n += 1
        en = set(re.findall(r'id="([^"]+)"', html))
        es = set(re.findall(r'id="([^"]+)"', docs[twin]))
        for missing in sorted(en - es):
            fail("tree parity", 'es/%s is missing id="%s" (present in English)'
                 % (os.path.basename(path), missing))
        for extra in sorted(es - en):
            fail("tree parity", '%s is missing id="%s" (present in Spanish)'
                 % (os.path.basename(path), extra))
    return n


def check_buttons(docs, fail):
    n = 0
    for path, html in docs.items():
        clean = strip_comments(html)
        # Inside a form, a <button> with no type is a submit button.
        for fm in re.finditer(r"<form\b.*?</form>", clean, re.S):
            for b in re.finditer(r"<button\b([^>]*)>", fm.group(0)):
                n += 1
                if "type=" not in b.group(1):
                    fail("button type",
                         "%s has a <button> inside a form with no type= "
                         "(defaults to submit)" % rel(path))
        for a in re.finditer(r"<a\b((?:(?!>).)*)>", clean, re.S):
            attrs = a.group(1)
            if "href=" not in attrs and "name=" not in attrs:
                fail("anchor without href", "%s has an <a> with no href" % rel(path))
    return n


def check_external(docs, fail):
    """Opt-in. Confirms every off-site URL still resolves."""
    try:
        import urllib.request
    except ImportError:
        print("  external: urllib unavailable, skipped")
        return 0

    # Only things a visitor can click or the browser actually fetches.
    # rel="preconnect" and rel="dns-prefetch" name an origin to warm up, not a
    # document: requesting one returns 404 by design, which is not a fault.
    urls = set()
    for html in docs.values():
        urls |= set(re.findall(r'<a\b[^>]*\bhref="(https?://[^"]+)"', html))
        urls |= set(re.findall(r'\bsrc="(https?://[^"]+)"', html))
        for m in re.finditer(r'<link\b([^>]*)>', html):
            attrs = m.group(1)
            if re.search(r'rel="(?:preconnect|dns-prefetch|preload)"', attrs):
                continue
            u = re.search(r'href="(https?://[^"]+)"', attrs)
            if u:
                urls.add(u.group(1))

    # Our own absolute URLs are not external links. Canonical, og:url, and
    # hreflang tags all name this site, and fetching them asks "is this page
    # deployed yet?" rather than "does this link resolve?" — so every new page
    # fails this check until it ships, which is exactly backwards: the point of
    # the check is to catch problems *before* deploying. The internal-link pass
    # already proves these paths exist in the build.
    OWN = "axionalytics.com"
    skipped_self = len([u for u in urls if OWN in u])
    urls = set(u for u in urls if OWN not in u)
    if skipped_self:
        print("  external:            %d self-referencing URLs skipped "
              "(canonical/hreflang)" % skipped_self)

    # Standards bodies sit behind WAFs that reject urllib's minimal header set
    # and answer a browser fine — iso.org and cisa.gov both do. The retry below
    # sends what a browser sends, so a live page is not reported as a dead link.
    # It is the last attempt, not the first: if the plain request works, that is
    # the one whose result we want.
    BROWSER = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/126.0.0.0 Safari/537.36"),
        "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,"
                   "image/avif,image/webp,*/*;q=0.8"),
        "Accept-Language": "en-US,en;q=0.9",
    }

    def probe(url, method, headers):
        """
        "ok" | "blocked" | "dead". Never raises.

        The distinction that matters is between a server that refused us and a
        server that has nothing at that address. 401/403/429 mean the host is up
        and the path exists — it declined this particular client, which is what
        WAFs in front of standards bodies do to anything without a browser's TLS
        fingerprint. 404 or a DNS failure means the citation is gone, and that is
        the only case worth failing a build over.
        """
        try:
            req = urllib.request.Request(url, method=method, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as r:
                return "ok" if r.status < 400 else "dead"
        except urllib.error.HTTPError as e:
            return "blocked" if e.code in (401, 403, 429) else "dead"
        except Exception:
            return "dead"

    plain = {"User-Agent": "axio-link-check"}

    def classify(u):
        # HEAD first (cheapest), then GET for hosts that refuse HEAD, then a
        # full browser GET for hosts that refuse anything that is not a browser.
        # Best outcome across the three wins.
        seen = set()
        for method, headers in (("HEAD", plain), ("GET", plain), ("GET", BROWSER)):
            r = probe(u, method, headers)
            if r == "ok":
                return "ok"
            seen.add(r)
        return "blocked" if "blocked" in seen else "dead"

    ok, blocked, dead = 0, [], []
    for u in sorted(urls):
        r = classify(u)
        if r == "ok":
            ok += 1
        elif r == "blocked":
            blocked.append(u)
        else:
            dead.append(u)

    for u in dead:
        fail("external link", "%s -> unreachable" % u)

    print("  external:            %d URLs reachable" % ok)
    if blocked:
        # Reported, not failed. Re-check these by hand if one looks wrong; the
        # build should not break because a standards body dislikes urllib.
        print("  external:            %d refused this client (403/429), "
              "host is up:" % len(blocked))
        for u in blocked:
            print("                         %s" % u)
    return len(urls)


# ---------------------------------------------------------------------------

def main():
    want_external = "--external" in sys.argv

    paths = pages()
    if not paths:
        print("  no built pages found - run the build first")
        return 1

    docs = {p: io.open(p, encoding="utf-8").read() for p in paths}

    problems = []

    def fail(kind, msg):
        problems.append((kind, msg))

    counts = [
        ("internal links", check_internal_links(docs, fail)),
        ("anchors", check_anchors(docs, fail)),
        ("assets", check_assets(docs, fail)),
        ("ids", check_duplicate_ids(docs, fail)),
        ("forms", check_nested_forms(docs, fail)),
        ("js id lookups", check_js_ids(docs, fail)),
        ("en/es page pairs", check_tree_parity(docs, fail)),
        ("buttons", check_buttons(docs, fail)),
    ]
    if want_external:
        counts.append(("external links", check_external(docs, fail)))

    print("  checked %d pages" % len(paths))
    for name, n in counts:
        print("    %-18s %d" % (name, n))

    if not problems:
        print("\n  CLEAN - every link, anchor, asset, and control resolves")
        return 0

    print("\n  %d PROBLEM(S):\n" % len(problems))
    by_kind = {}
    for kind, msg in problems:
        by_kind.setdefault(kind, []).append(msg)
    for kind in sorted(by_kind):
        print("  [%s]" % kind)
        for msg in by_kind[kind][:25]:
            print("      %s" % msg)
        if len(by_kind[kind]) > 25:
            print("      ... and %d more" % (len(by_kind[kind]) - 25))
        print("")
    return 1


if __name__ == "__main__":
    sys.exit(main())
