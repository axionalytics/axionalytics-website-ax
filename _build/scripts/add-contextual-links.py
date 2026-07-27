# -*- coding: utf-8 -*-
"""
Insert contextual links into article and glossary prose.

WHY
---
Before this step the site had zero in-content internal links. Every internal
link lived in navigation, the related-articles grid, or the pillar callout —
all boilerplate that repeats on every page. Search engines weight a link inside
body prose, on relevant anchor text, far above a link in a repeated template,
because the first one is an editorial signal and the second is furniture.

It also helps readers: a reader who hits "catch-all domain" mid-paragraph and
does not know the term currently has to go looking.

WHERE IT RUNS
-------------
On the built pages, after build.sh and before the language split. That makes it
idempotent for free — every build regenerates the pages from source, so links
are inserted exactly once per build rather than accumulating.

THE RULES
---------
Conservative on purpose. Over-linking reads as spam and dilutes the signal.

  * only inside .ax-prose bodies, and only inside <p> elements
  * never inside a heading, a callout title, or an existing <a>
  * first occurrence of a term only, per page
  * never links a page to itself
  * hard cap per page
  * English terms match English spans, Spanish terms match Spanish spans

Relative hrefs are used so the same markup resolves correctly in both the root
tree and /es/.

Usage: python _build/scripts/add-contextual-links.py
"""
import glob
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MAX_LINKS_PER_PAGE = 6

# (target page, [English phrases], [Spanish phrases])
# Ordered most specific first: a longer phrase should win over a shorter one
# that is contained inside it.
TARGETS = [
    ("what-is-requirements-traceability.html",
     ["requirements traceability", "traceability matrix"],
     ["trazabilidad de requisitos", "matriz de trazabilidad"]),
    ("what-is-email-deliverability.html",
     ["catch-all domain", "sender reputation", "deliverability"],
     ["dominio que acepta todo", "reputación del remitente", "entregabilidad"]),
    ("what-is-prompt-injection.html",
     ["prompt injection"],
     ["inyección de prompts"]),
    ("what-is-human-in-the-loop.html",
     ["human-in-the-loop", "human approval gate", "approval gate"],
     ["aprobación humana", "puerta de aprobación"]),
    ("what-is-a-semantic-layer.html",
     ["semantic layer"],
     ["capa semántica"]),
    ("what-is-byoc.html",
     ["bring-your-own-cloud", "BYOC"],
     ["nube propia", "BYOC"]),
    ("what-is-agentic-ai.html",
     ["agentic AI", "agentic system"],
     ["IA agéntica", "sistema agéntico"]),

    ("enterprise-ai-security.html",
     ["security review", "deployment topology"],
     ["revisión de seguridad", "topología de despliegue"]),
    ("agentic-test-engineering.html",
     ["verification coverage", "test case generation"],
     ["cobertura de verificación", "generación de casos de prueba"]),
    ("agentic-business-intelligence.html",
     ["BI backlog", "dashboard generation"],
     ["backlog de BI", "generación de tableros"]),
    # "outbound" alone is not usable here: on the security pages it means
    # outbound network traffic, and linking that to a sales page is nonsense
    # to a reader and a wrong topical signal to a crawler. Every term in this
    # table has to be unambiguous in isolation — precision over recall.
    ("agentic-revenue-development.html",
     ["outbound sales", "cold outreach", "sales development", "pipeline generation"],
     ["prospección comercial", "contacto en frío", "generación de pipeline"]),

    ("roi-calculator.html",
     ["payback period", "reclaimed capacity"],
     ["periodo de retorno", "capacidad recuperada"]),
    ("pricing.html",
     ["fixed-scope", "build investment"],
     ["alcance fijo", "inversión de construcción"]),
]

LINK_CLASS = ""   # inherit .ax-prose a styling


def prose_blocks(html):
    """Yield (start, end) spans of every .ax-prose container."""
    out = []
    for m in re.finditer(r'<div class="ax-prose[^"]*">', html):
        start = m.end()
        depth = 1
        i = start
        while depth:
            nxt = re.search(r"<div\b|</div>", html[i:])
            if not nxt:
                break
            tok = html[i + nxt.start(): i + nxt.end()]
            depth += -1 if tok.startswith("</") else 1
            i += nxt.end()
        out.append((start, i - len("</div>")))
    return out


def linkable_paragraphs(block):
    """(start, end) of the inner text of each <p> in this block."""
    return [(m.end(), block.index("</p>", m.end()))
            for m in re.finditer(r"<p>", block)
            if "</p>" in block[m.end():]]


def already_linked(text, pos):
    """True if pos sits inside an <a> element."""
    before = text[:pos]
    return before.rfind("<a ") > before.rfind("</a>")


def insert_links(html, self_slug):
    """Link each target at most once per language.

    The two languages are tracked separately on purpose. A single shared
    "already used this target" set lets whichever span appears first in the
    document — always the English one — claim every target, leaving the Spanish
    tree with almost no contextual links. Since /es/ is half the published site,
    that would forfeit half the benefit of this step.
    """
    blocks = prose_blocks(html)
    if not blocks:
        return html, 0

    used = {"en": set(), "es": set()}
    count = {"en": 0, "es": 0}

    # Work back to front so earlier offsets stay valid as we edit.
    for bstart, bend in reversed(blocks):
        block = html[bstart:bend]

        for lang in ("en", "es"):
            changed = True
            while changed:
                changed = False
                for entry in TARGETS:
                    target = entry[0]
                    terms = entry[1] if lang == "en" else entry[2]

                    if count[lang] >= MAX_LINKS_PER_PAGE:
                        break
                    if target in used[lang] or target == self_slug:
                        continue

                    hit = None
                    for term in terms:
                        pat = re.compile(
                            r"(<span data-lang-%s>(?:(?!</span>).)*?)\b(%s)\b"
                            % (lang, re.escape(term)), re.S | re.I)
                        for m in pat.finditer(block):
                            # Skip headings, callout titles, existing links.
                            head = block[max(0, m.start() - 220): m.start()]
                            if re.search(r"<h[1-6][^>]*>\s*$|<h[1-6][^>]*>(?:(?!</h).)*$",
                                         head, re.S):
                                continue
                            if already_linked(block, m.start(2)):
                                continue
                            hit = m
                            break
                        if hit:
                            break
                    if not hit:
                        continue

                    a, b = hit.start(2), hit.end(2)
                    block = (block[:a]
                             + '<a href="%s">%s</a>' % (target, hit.group(2))
                             + block[b:])
                    used[lang].add(target)
                    count[lang] += 1
                    changed = True
                    break

        html = html[:bstart] + block + html[bend:]

    return html, count["en"] + count["es"]


def main():
    pages = sorted(glob.glob(os.path.join(ROOT, "*.html")))
    total = touched = 0

    for path in pages:
        slug = os.path.basename(path)
        html = io.open(path, encoding="utf-8").read()
        if 'class="ax-prose' not in html:
            continue

        out, n = insert_links(html, slug)
        if n:
            io.open(path, "w", encoding="utf-8").write(out)
            total += n
            touched += 1

    print("  %d contextual links inserted across %d pages (cap %d per page)"
          % (total, touched, MAX_LINKS_PER_PAGE))


if __name__ == "__main__":
    main()
