# -*- coding: utf-8 -*-
"""
The named author, in one place.

WHY A NAMED AUTHOR MATTERS
--------------------------
Google's quality guidance weights demonstrable experience, expertise,
authority, and trust. An article attributed to a company is anonymous; an
article attributed to a named engineer with a bio, a track record, and a stable
identity across the site is evidence. For technical B2B content this is one of
the cheapest ranking improvements available, and the site currently forgoes it
entirely — every article is authored by "Axionalytics".

HOW TO TURN IT ON
-----------------
Fill in NAME below and rebuild. That single change:

  * switches every article and glossary page from Organization to Person author
  * adds a visible byline to each one
  * publishes author.html with full Person schema
  * links every byline to it

Leave NAME empty and none of that happens — the site keeps the current
Organization attribution and author.html is not generated. Nothing half-built
reaches the public, so this file is safe to ship unfilled.

Do not invent a name here. The value of the signal comes from it being a real
person a reader could look up; a fabricated byline is worse than none.
"""

# ---------------------------------------------------------------------------
# FILL THIS IN
# ---------------------------------------------------------------------------

NAME = ""            # e.g. "Jorge Carbajal"
ROLE_EN = "Founder & Principal Engineer"
ROLE_ES = "Fundador e Ingeniero Principal"

# Two or three sentences. Concrete beats flattering: what this person has
# actually built and for whom, in the terms a technical buyer would recognise.
BIO_EN = (
    "Builds production agentic AI systems for enterprise engineering, data, and "
    "revenue organisations — deployed inside the customer's own perimeter, governed "
    "by human approval, and handed over with the source. Writes here about the "
    "architecture decisions that determine whether these systems reach production."
)
BIO_ES = (
    "Construye sistemas agénticos de IA en producción para organizaciones "
    "empresariales de ingeniería, datos e ingresos — desplegados dentro del "
    "perímetro del cliente, gobernados por aprobación humana y entregados con el "
    "código fuente. Escribe aquí sobre las decisiones de arquitectura que "
    "determinan si estos sistemas llegan a producción."
)

# Public profiles. Anything left empty is omitted from sameAs rather than
# emitted as a broken link.
LINKEDIN = "https://www.linkedin.com/company/axionalytics"
GITHUB = ""

# Areas of demonstrable expertise, used in Person.knowsAbout.
KNOWS_ABOUT = [
    "Agentic AI architecture",
    "Zero-trust AI deployment",
    "Verification and validation automation",
    "Business intelligence automation",
    "Enterprise AI security review",
]

BASE = "https://www.axionalytics.com"


# ---------------------------------------------------------------------------

def enabled():
    """True once a real name has been supplied."""
    return bool(NAME.strip())


def person_schema(indent=6):
    """Person object for use as an Article author. Falls back to Organization."""
    pad = " " * indent
    if not enabled():
        return ('{ "@type": "Organization", "name": "Axionalytics", '
                '"url": "%s/" }' % BASE)

    same = [u for u in (LINKEDIN, GITHUB) if u]
    same_json = ""
    if same:
        same_json = ',\n%s  "sameAs": [%s]' % (
            pad, ", ".join('"%s"' % u for u in same))

    return (
        '{\n'
        '%s  "@type": "Person",\n'
        '%s  "@id": "%s/author.html#person",\n'
        '%s  "name": "%s",\n'
        '%s  "jobTitle": "%s",\n'
        '%s  "url": "%s/author.html",\n'
        '%s  "worksFor": { "@type": "Organization", "name": "Axionalytics", "url": "%s/" }%s\n'
        '%s}' % (pad, pad, BASE, pad, esc(NAME), pad, esc(ROLE_EN),
                 pad, BASE, pad, BASE, same_json, pad)
    )


def byline_html():
    """Visible byline for the article header. Empty string when disabled."""
    if not enabled():
        return ""
    return (
        '\n      <span class="w-1 h-1 rounded-full bg-white/20"></span>\n'
        '      <span>\n'
        '        <span data-lang-en>By <a href="author.html" rel="author" '
        'class="text-white/70 hover:text-ax-cyan transition-colors">%s</a></span>\n'
        '        <span data-lang-es>Por <a href="author.html" rel="author" '
        'class="text-white/70 hover:text-ax-cyan transition-colors">%s</a></span>\n'
        '      </span>' % (esc_html(NAME), esc_html(NAME))
    )


def esc(s):
    return s.replace('"', '\\"')


def esc_html(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
