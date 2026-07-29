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
import re
from email.utils import format_datetime
from datetime import datetime, timezone

BASE = "https://www.axionalytics.com"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ART_SRC = os.path.join(ROOT, "_build", "src", "articles")
GLO_SRC = os.path.join(ROOT, "_build", "src", "glossary")


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


def glossary_terms():
    """TERMS from the glossary generator, which owns them."""
    spec = importlib.util.spec_from_file_location(
        "mg", os.path.join(ROOT, "_build", "scripts", "make-glossary.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.TERMS


def to_markdown(html, lang="en"):
    """
    One language of a bilingual source, as plain Markdown.

    Written for llms-full.txt, where the reader is a model with a fixed context
    window: every token spent on markup is a token not spent on the argument.
    Structure is preserved (headings, lists, emphasis) because that is what
    carries the document's shape; everything else is dropped.
    """
    other = "es" if lang == "en" else "en"

    # Drop the other language, then unwrap our own.
    html = re.sub(r'<span data-lang-%s>.*?</span>' % other, '', html, flags=re.S)
    html = re.sub(r'<span data-lang-%s>(.*?)</span>' % lang, r'\1', html, flags=re.S)

    html = re.sub(r'(?is)<!--.*?-->', '', html)
    html = re.sub(r'(?is)<(script|style|svg).*?</\1>', '', html)

    # Heading text sits on its own line in the sources, so the captured group
    # arrives full of newlines. Flatten it, or every heading breaks after its
    # own hashes and stops being a heading at all.
    def flat(text):
        return re.sub(r'\s+', ' ', re.sub(r'(?s)<[^>]+>', ' ', text)).strip()

    for tag, hashes in (("h2", "##"), ("h3", "###"), ("h4", "####")):
        html = re.sub(r'(?is)<%s[^>]*>(.*?)</%s>' % (tag, tag),
                      lambda m, h=hashes: "\n\n%s %s\n" % (h, flat(m.group(1))),
                      html)
    html = re.sub(r'(?is)<li[^>]*>(.*?)</li>',
                  lambda m: "\n- %s" % flat(m.group(1)), html)
    html = re.sub(r'(?is)<(strong|b)>(.*?)</\1>', r'**\2**', html)
    html = re.sub(r'(?is)<(em|i)>(.*?)</\1>', r'*\2*', html)
    html = re.sub(r'(?is)<p[^>]*>', '\n\n', html)

    html = re.sub(r'(?s)<[^>]+>', ' ', html)

    ent = {'&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
           '&#39;': "'", '&nbsp;': ' ', '&mdash;': '—', '&ndash;': '–',
           '&oacute;': 'ó', '&aacute;': 'á', '&eacute;': 'é', '&iacute;': 'í',
           '&uacute;': 'ú', '&ntilde;': 'ñ', '&uuml;': 'ü', '&iquest;': '¿',
           '&iexcl;': '¡'}
    for k, v in ent.items():
        html = html.replace(k, v)

    # Collapse whitespace without destroying paragraph breaks.
    html = re.sub(r'[ \t]+', ' ', html)
    html = re.sub(r' *\n *', '\n', html)
    html = re.sub(r'\n{3,}', '\n\n', html)
    return html.strip()


def faq_pairs(raw):
    """The <!--FAQ q | a--> comments an article carries, as (q, a)."""
    out = []
    for m in re.finditer(r'<!--FAQ\s+(.*?)\s*\|\s*(.*?)-->', raw, re.S):
        out.append((m.group(1).strip(), m.group(2).strip()))
    return out


def build_llms_full(ma):
    """
    Every article and glossary entry, in full, as one Markdown document.

    llms.txt tells an agent what exists; this tells it what the pages say. An
    agent researching a technical question can ingest the whole corpus in one
    request instead of fetching thirty pages and parsing the chrome out of each,
    which is the difference between being cited accurately and being paraphrased
    from whatever fragment survived retrieval.

    English only, deliberately: this file is a token budget, and the Spanish
    tree is a translation of it rather than additional information.
    """
    terms = glossary_terms()
    out = [
        "# Axionalytics — full text",
        "",
        "> Complete text of every article and glossary entry on axionalytics.com,",
        "> concatenated for retrieval. Source of truth is the published page; each",
        "> section links to its canonical URL. Generated by _build/scripts/make-feeds.py.",
        "",
        "Production agentic AI for enterprise engineering, data, and revenue",
        "organizations: deployed inside the customer's own cloud perimeter, human",
        "approval on every write, every claim traceable to the tool call behind it,",
        "and full source transfer at the end of the engagement.",
        "",
        "---",
        "",
        "# Articles",
        "",
    ]

    for a in ma.ARTICLES:
        path = os.path.join(ART_SRC, a["slug"] + ".html")
        if not os.path.exists(path):
            continue
        raw = io.open(path, encoding="utf-8").read()
        pillar = ma.PILLARS[a["pillar"]]

        out += [
            "## %s" % a["title_en"],
            "",
            "URL: %s/%s.html" % (BASE, a["slug"]),
            "Published: %s · Topic: %s · Solution: %s"
            % (a["date"], a["cat_en"], pillar["name_en"]),
            "",
            "> %s" % a["desc_en"],
            "",
            to_markdown(raw, "en"),
            "",
        ]

        faqs = faq_pairs(raw)
        if faqs:
            out += ["### Questions this answers", ""]
            for q, ans in faqs:
                out += ["**%s**" % q, "", ans, ""]

        refs = ma.SOURCES.get(a["slug"], [])
        if refs:
            out += ["### References", ""]
            out += ["- %s — %s: %s" % (t, o, u) for u, t, o in refs]
            out += [""]

        out += ["---", ""]

    out += ["# Glossary", ""]
    for t in terms:
        path = os.path.join(GLO_SRC, t["slug"] + ".html")
        out += [
            "## %s" % t["title_en"],
            "",
            "URL: %s/%s.html" % (BASE, t["slug"]),
            "",
            "> %s" % t["answer_en"],
            "",
        ]
        if os.path.exists(path):
            out += [to_markdown(io.open(path, encoding="utf-8").read(), "en"), ""]
        out += ["---", ""]

    return "\n".join(out)


COPY = {
    "en": {
        "root": BASE,
        "summary": [
            "> Axionalytics designs and ships production agentic AI systems for enterprise",
            "> engineering, data, and revenue organizations. Systems are deployed inside the",
            "> customer's own cloud perimeter, every write action requires human approval, and",
            "> every factual claim is traceable to the tool call that produced it. Engagements",
            "> end in full source transfer.",
        ],
        "based": "Based in the Quad Cities, Iowa. Work is delivered in English and Spanish.",
        "solutions": "Solutions",
        "tools": "Tools",
        "company": "Company",
        "writing": "Writing",
        "glossary": "Glossary",
        "optional": "Optional",
        "roi": ("ROI Calculator", "roi-calculator.html",
                "Client-side model of reclaimed capacity, net annualized recovery, and "
                "payback period. Every assumption is stated; no input is transmitted."),
        "about": ("About", "about.html",
                  "How engagements are structured and when we are the wrong fit."),
        "cases": ("Case Studies", "case-studies.html",
                  "Four anonymized deployment accounts with the architecture and the "
                  "constraint stated. Client names are withheld deliberately."),
        "contact": ("Contact", "contact.html",
                    "Direct contact and technical briefing booking."),
        "blog": ("Blog index", "blog.html"),
        "gloss_hub": ("Glossary hub", "glossary.html"),
        # Site-wide files live at the root in both trees, so these are absolute.
        "full": ("Full text of every article and glossary entry, one file",
                 BASE + "/llms-full.txt"),
        "rss": ("RSS feed", BASE + "/rss.xml"),
        "sitemap": ("Sitemap", BASE + "/sitemap.xml"),
        "other_lang": ("Spanish edition of this index", BASE + "/es/llms.txt"),
    },
    "es": {
        "root": BASE + "/es",
        "summary": [
            "> Axionalytics diseña y entrega sistemas de IA agéntica en producción para",
            "> organizaciones empresariales de ingeniería, datos e ingresos. Los sistemas se",
            "> despliegan dentro del perímetro de nube del propio cliente, toda acción de",
            "> escritura requiere aprobación humana, y toda afirmación es trazable a la llamada",
            "> de herramienta que la produjo. Los proyectos terminan con transferencia completa",
            "> del código fuente.",
        ],
        "based": "Con sede en Quad Cities, Iowa. El trabajo se entrega en inglés y español.",
        "solutions": "Soluciones",
        "tools": "Herramientas",
        "company": "Empresa",
        "writing": "Artículos",
        "glossary": "Glosario",
        "optional": "Opcional",
        "roi": ("Calculadora de ROI", "roi-calculator.html",
                "Modelo del lado del cliente de capacidad recuperada, recuperación neta "
                "anualizada y periodo de retorno. Cada supuesto está declarado; ningún "
                "dato se transmite."),
        "about": ("Acerca de", "about.html",
                  "Cómo se estructuran los proyectos y cuándo no somos la opción correcta."),
        "cases": ("Casos de éxito", "case-studies.html",
                  "Cuatro despliegues anonimizados con la arquitectura y la restricción "
                  "declaradas. Los nombres de clientes se omiten deliberadamente."),
        "contact": ("Contacto", "contact.html",
                    "Contacto directo y agenda de sesión técnica."),
        "blog": ("Índice del blog", "blog.html"),
        "gloss_hub": ("Portada del glosario", "glossary.html"),
        "full": ("Texto completo de cada articulo y termino, en un archivo",
                 BASE + "/llms-full.txt"),
        "rss": ("Feed RSS", BASE + "/rss.xml"),
        "sitemap": ("Mapa del sitio", BASE + "/sitemap.xml"),
        "other_lang": ("English edition of this index", BASE + "/llms.txt"),
    },
}


def build_llms(ma, lang="en"):
    """
    The index an agent reads first: what this site is, and what is on it.

    One per language tree. A single file listing both would make every entry
    ambiguous about which URL to cite, which is the same reason the pages
    themselves are split.
    """
    c = COPY[lang]
    root = c["root"]
    suf = "_en" if lang == "en" else "_es"

    def item(tup):
        name, path, desc = tup
        return "- [%s](%s/%s): %s" % (name, root, path, desc)

    lines = ["# Axionalytics", ""] + c["summary"] + ["", c["based"], "",
                                                     "## " + c["solutions"], ""]

    for key in ("testing", "agentic", "bi", "security"):
        p = ma.PILLARS[key]
        lines.append("- [%s](%s/%s): %s"
                     % (p["name" + suf], root, p["url"], p["blurb" + suf]))

    lines += ["", "## " + c["tools"], "", item(c["roi"]),
              "", "## " + c["company"], "",
              item(c["about"]), item(c["cases"]), item(c["contact"]),
              "", "## " + c["writing"], ""]

    for key in ("security", "agentic", "testing", "bi", "revenue"):
        p = ma.PILLARS.get(key)
        arts = [a for a in ma.ARTICLES if a["pillar"] == key]
        if not p or not arts:
            continue
        lines += ["### %s" % p["name" + suf], ""]
        for a in arts:
            lines.append("- [%s](%s/%s.html): %s"
                         % (a["title" + suf], root, a["slug"], a["desc" + suf]))
        lines.append("")

    # The glossary was absent from this index entirely. Definition pages are
    # what an engine reaches for on a "what is X" query, so leaving them out
    # forfeited the queries the site is best positioned to answer.
    terms = glossary_terms()
    if terms:
        lines += ["## " + c["glossary"], ""]
        for t in terms:
            answer = t["answer" + suf]
            first = answer.split(". ")[0].rstrip(".") + "."
            lines.append("- [%s](%s/%s.html): %s"
                         % (t["title" + suf], root, t["slug"], first))
        lines.append("")

    lines += ["## " + c["optional"], "",
              "- [%s](%s/%s)" % (c["blog"][0], root, c["blog"][1]),
              "- [%s](%s/%s)" % (c["gloss_hub"][0], root, c["gloss_hub"][1])]
    # These four are absolute: one copy each, shared by both trees.
    for k in ("full", "rss", "sitemap", "other_lang"):
        lines.append("- [%s](%s)" % (c[k][0], c[k][1]))
    lines.append("")
    return "\n".join(lines)


def main():
    ma = load_manifest()

    rss = build_rss(ma)
    io.open(os.path.join(ROOT, "rss.xml"), "w", encoding="utf-8").write(rss)
    print("  rss.xml      %d items, %.1f KB"
          % (rss.count("<item>"), len(rss.encode("utf-8")) / 1024.0))

    for lang, path in (("en", "llms.txt"), ("es", os.path.join("es", "llms.txt"))):
        text = build_llms(ma, lang)
        dest = os.path.join(ROOT, path)
        parent = os.path.dirname(dest)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        io.open(dest, "w", encoding="utf-8").write(text)
        print("  %-12s %d links, %.1f KB"
              % (path.replace(os.sep, "/"), text.count("](http"),
                 len(text.encode("utf-8")) / 1024.0))

    full = build_llms_full(ma)
    io.open(os.path.join(ROOT, "llms-full.txt"), "w", encoding="utf-8").write(full)
    print("  llms-full.txt %d sections, %.1f KB"
          % (full.count("\n## "), len(full.encode("utf-8")) / 1024.0))


if __name__ == "__main__":
    main()
