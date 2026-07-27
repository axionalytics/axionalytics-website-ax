# -*- coding: utf-8 -*-
"""
Add BreadcrumbList schema to the hand-written core pages.

Articles already emit BreadcrumbList from _build/scripts/make-articles.py, and the
legal pages are shallow enough not to need one. The four commercial pillars,
the solutions hub, and the remaining company pages had visual breadcrumbs in
the markup but no structured data behind them, so search engines rendered a
bare URL in the result instead of a breadcrumb trail.

Idempotent: skips any meta file that already declares a BreadcrumbList.

Usage: python _build/scripts/add-breadcrumbs.py
"""
import io
import os

BASE = "https://www.axionalytics.com"
PAGES = "_build/pages"

# slug -> trail of (name, url-or-None). None means "this page".
TRAILS = {
    "solutions": [("Home", ""), ("Solutions", None)],

    "agentic-test-engineering": [
        ("Home", ""), ("Solutions", "solutions.html"),
        ("Agentic Test Engineering", None)],
    "enterprise-agentic-ai": [
        ("Home", ""), ("Solutions", "solutions.html"),
        ("Enterprise Agentic AI", None)],
    "agentic-business-intelligence": [
        ("Home", ""), ("Solutions", "solutions.html"),
        ("Agentic Business Intelligence", None)],
    "enterprise-ai-security": [
        ("Home", ""), ("Solutions", "solutions.html"),
        ("Zero-Trust AI Governance", None)],

    "roi-calculator": [("Home", ""), ("ROI Calculator", None)],
    "case-studies":   [("Home", ""), ("Case Studies", None)],
    "about":          [("Home", ""), ("About", None)],
    "contact":        [("Home", ""), ("Contact", None)],
    "blog":           [("Home", ""), ("Blog", None)],
}

TEMPLATE = u"""
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
{items}
    ]
  }}
  </script>
"""

ITEM = ('      {{ "@type": "ListItem", "position": {pos}, '
        '"name": "{name}", "item": "{url}" }}')


def build(slug, trail):
    items = []
    for i, (name, href) in enumerate(trail, 1):
        if href is None:
            url = "%s/%s.html" % (BASE, slug)
        elif href == "":
            url = BASE + "/"
        else:
            url = "%s/%s" % (BASE, href)
        items.append(ITEM.format(pos=i, name=name.replace('"', '\\"'), url=url))
    return TEMPLATE.format(items=",\n".join(items))


def main():
    added = skipped = missing = 0
    for slug, trail in sorted(TRAILS.items()):
        path = os.path.join(PAGES, slug + ".meta.html")
        if not os.path.exists(path):
            print("  missing  %s" % path)
            missing += 1
            continue

        s = io.open(path, encoding="utf-8").read()
        if "BreadcrumbList" in s:
            print("  skip     %-34s already present" % slug)
            skipped += 1
            continue

        io.open(path, "w", encoding="utf-8").write(s.rstrip("\n") + "\n" + build(slug, trail))
        print("  added    %-34s %d levels" % (slug, len(trail)))
        added += 1

    print("\n  %d added, %d skipped, %d missing" % (added, skipped, missing))


if __name__ == "__main__":
    main()
