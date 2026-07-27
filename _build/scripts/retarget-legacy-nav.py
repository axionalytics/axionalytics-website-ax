# -*- coding: utf-8 -*-
"""
Retarget navigation links inside the four pages kept from the pre-2026 site
(blog + the three legal pages). Their chrome still uses the old visual design,
but their nav pointed at retired URLs, sending every visitor through a redirect
stub. This rewrites both the href and the visible label so the links land
directly on the new pillars.

Styling is deliberately left alone — restyling these pages is separate work.

Usage: python _build/scripts/retarget-legacy-nav.py
"""
import io, re, os

FILES = ["blog.html", "privacy.html", "terms.html", "accessibility.html"]

# old href -> (new href, new EN label, new ES label)
NAV = {
    "datatransformation.html": ("agentic-business-intelligence.html",
                                "Agentic BI", "BI Ag&#233;ntica"),
    "aitransformation.html":   ("enterprise-agentic-ai.html",
                                "Agentic AI", "IA Ag&#233;ntica"),
    "training.html":           ("solutions.html",
                                "Solutions", "Soluciones"),
    "successstories.html":     ("case-studies.html",
                                "Case Studies", "Casos de &#201;xito"),
}

# Old label text -> replacement, applied only inside a rewritten <a> block.
OLD_LABELS = {
    "Data Transformation": "datatransformation.html",
    "Transformaci&#243;n de Datos": "datatransformation.html",
    "AI Integration": "aitransformation.html",
    "Integraci&#243;n de IA": "aitransformation.html",
    "Team Training": "training.html",
    "Capacitaci&#243;n": "training.html",
    "Capacitaci&#243;n de Equipos": "training.html",
    "Success Stories": "successstories.html",
    "Historias de &#201;xito": "successstories.html",
}

# Matches a whole <a ...href="X">...</a> block for the four retired targets.
BLOCK = re.compile(
    r'(<a\s+href=")(' + "|".join(re.escape(k) for k in NAV) + r')(")([^>]*>)(.*?)(</a>)',
    re.S,
)

def rewrite(match):
    pre, old_href, quote, rest, inner, close = match.groups()
    new_href, en, es = NAV[old_href]

    # Swap the label text, preserving the surrounding span markup.
    inner = re.sub(r'(<span data-lang-en>)[^<]*(</span>)',
                   lambda m: m.group(1) + en + m.group(2), inner)
    inner = re.sub(r'(<span data-lang-es>)[^<]*(</span>)',
                   lambda m: m.group(1) + es + m.group(2), inner)
    return pre + new_href + quote + rest + inner + close

total = 0
for name in FILES:
    if not os.path.exists(name):
        print("  skip  %s (not found)" % name)
        continue
    src = io.open(name, encoding="utf-8").read()
    out, n = BLOCK.subn(rewrite, src)
    if n:
        io.open(name, "w", encoding="utf-8").write(out)
    total += n
    print("  %-22s %2d links retargeted" % (name, n))

print("\n  %d total" % total)
