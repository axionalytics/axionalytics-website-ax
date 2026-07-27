# -*- coding: utf-8 -*-
"""
Generate rss.xml and llms.txt.

rss.xml   Syndication for readers, aggregators, and newsletter tooling. Built
          from the same ARTICLES manifest as the blog index so the two cannot
          drift. English only: the feed advertises one language, and the
          Spanish URL space gets its own feed once it exists.

llms.txt  A plain-text map of the site for AI crawlers and answer engines,
          following the emerging convention of a root-level file that states
          what the site is and lists its canonical pages. Given that the
          business sells AI systems to people who evaluate via AI search, being
          legible to those crawlers is not a novelty — it is the channel.

Usage: python _build/scripts/make-feeds.py
"""
import io
import importlib.util
import os
from email.utils import format_datetime
from datetime import datetime, timezone

BASE = "https://www.axionalytics.com"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_manifest():
    spec = importlib.util.spec_from_file_location(
        "ma", os.path.join(ROOT, "_build", "scripts", "make-articles.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def rfc822(datestr):
    d = datetime.strptime(datestr, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return format_datetime(d)


def build_rss(ma):
    items = []
    for a in ma.ARTICLES:
        pillar = ma.PILLARS[a["pillar"]]
        items.append(
            "    <item>\n"
            "      <title>%s</title>\n"
            "      <link>%s/%s.html</link>\n"
            "      <guid isPermaLink=\"true\">%s/%s.html</guid>\n"
            "      <description>%s</description>\n"
            "      <category>%s</category>\n"
            "      <category>%s</category>\n"
            "      <pubDate>%s</pubDate>\n"
            "    </item>"
            % (esc(a["title_en"]), BASE, a["slug"], BASE, a["slug"],
               esc(a["desc_en"]), esc(a["cat_en"]), esc(pillar["name_en"]),
               rfc822(a["date"])))

    newest = max(a["date"] for a in ma.ARTICLES)
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Axionalytics</title>
    <link>%s/blog.html</link>
    <atom:link href="%s/rss.xml" rel="self" type="application/rss+xml"/>
    <description>Architecture writing on enterprise agentic AI: deployment topology, execution isolation, human approval gates, data provenance, and analytics governance.</description>
    <language>en</language>
    <lastBuildDate>%s</lastBuildDate>
    <generator>_build/scripts/make-feeds.py</generator>
%s
  </channel>
</rss>
""" % (BASE, BASE, rfc822(newest), "\n".join(items))


def build_llms(ma):
    lines = [
        "# Axionalytics",
        "",
        "> Axionalytics designs and ships production agentic AI systems for enterprise",
        "> engineering, data, and revenue organizations. Systems are deployed inside the",
        "> customer's own cloud perimeter, every write action requires human approval, and",
        "> every factual claim is traceable to the tool call that produced it. Engagements",
        "> end in full source transfer.",
        "",
        "Based in the Quad Cities, Iowa. Work is delivered in English and Spanish.",
        "",
        "## Solutions",
        "",
    ]

    for key in ("testing", "agentic", "bi", "security"):
        p = ma.PILLARS[key]
        lines.append("- [%s](%s/%s): %s" % (p["name_en"], BASE, p["url"], p["blurb_en"]))

    lines += [
        "",
        "## Tools",
        "",
        "- [ROI Calculator](%s/roi-calculator.html): Client-side model of reclaimed "
        "capacity, net annualized recovery, and payback period. Every assumption is "
        "stated; no input is transmitted." % BASE,
        "",
        "## Company",
        "",
        "- [About](%s/about.html): How engagements are structured and when we are the wrong fit." % BASE,
        "- [Case Studies](%s/case-studies.html): Anonymized deployment accounts. Client names are withheld deliberately." % BASE,
        "- [Contact](%s/contact.html): Direct contact and technical briefing booking." % BASE,
        "",
        "## Writing",
        "",
    ]

    for key in ("security", "agentic", "testing", "bi"):
        p = ma.PILLARS[key]
        arts = [a for a in ma.ARTICLES if a["pillar"] == key]
        if not arts:
            continue
        lines.append("### %s" % p["name_en"])
        lines.append("")
        for a in arts:
            lines.append("- [%s](%s/%s.html): %s"
                         % (a["title_en"], BASE, a["slug"], a["desc_en"]))
        lines.append("")

    lines += [
        "## Optional",
        "",
        "- [Blog index](%s/blog.html)" % BASE,
        "- [RSS feed](%s/rss.xml)" % BASE,
        "- [Sitemap](%s/sitemap.xml)" % BASE,
        "",
    ]
    return "\n".join(lines)


def main():
    ma = load_manifest()

    rss = build_rss(ma)
    io.open(os.path.join(ROOT, "rss.xml"), "w", encoding="utf-8").write(rss)
    print("  rss.xml      %d items, %.1f KB"
          % (rss.count("<item>"), len(rss.encode("utf-8")) / 1024.0))

    llms = build_llms(ma)
    io.open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf-8").write(llms)
    print("  llms.txt     %d links, %.1f KB"
          % (llms.count("](http"), len(llms.encode("utf-8")) / 1024.0))


if __name__ == "__main__":
    main()
