# -*- coding: utf-8 -*-
"""
Migrate the three legal pages onto the new design system.

The pre-2026 versions wrapped their content in `<div data-lang-XX class="policy-content">`
with page-local CSS. The legal text itself is unchanged — only the surrounding
chrome and typography move to the shared system, so the published terms a
visitor agreed to are not silently reworded by a restyle.

Usage: python _build/scripts/extract-legal.py
"""
import io
import os
import re

BASE = "https://www.axionalytics.com"
OUT = "_build/pages"

PAGES = [
    {
        "slug": "privacy",
        "src": "_legacy/privacy.html",
        "type": "PrivacyPolicy",
        "title_en": "Privacy Policy", "title_es": "Política de Privacidad",
        "desc": "How Axionalytics collects, uses, discloses, and safeguards your information.",
        "eyebrow_en": "Legal", "eyebrow_es": "Legal",
    },
    {
        "slug": "terms",
        "src": "_legacy/terms.html",
        "type": "TermsOfService",
        "title_en": "Terms &amp; Conditions", "title_es": "Términos y Condiciones",
        "desc": "The terms governing use of the Axionalytics website and services.",
        "eyebrow_en": "Legal", "eyebrow_es": "Legal",
    },
    {
        "slug": "accessibility",
        "src": "_legacy/accessibility.html",
        "type": "WebPage",
        "title_en": "Accessibility Statement", "title_es": "Declaración de Accesibilidad",
        "desc": "Axionalytics' commitment to web accessibility and the adjustments implemented on this site.",
        "eyebrow_en": "Accessibility", "eyebrow_es": "Accesibilidad",
    },
]


def grab(html, lang):
    """Pull the inner HTML of <div data-lang-XX class="policy-content"> ... </div>."""
    marker = '<div data-lang-%s class="policy-content">' % lang
    start = html.find(marker)
    if start == -1:
        raise SystemExit("no policy-content block for lang=%s" % lang)
    pos = start + len(marker)
    depth = 1
    for m in re.finditer(r"<(/?)div\b", html[pos:]):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return html[pos:pos + m.start()]
    raise SystemExit("unbalanced policy-content block for lang=%s" % lang)


def clean(block):
    """Drop the old orange link utility classes; .ax-prose styles links now."""
    block = re.sub(r'\s*class="text-orange-500[^"]*"', "", block)
    block = re.sub(r'\s*class="text-orange-600[^"]*"', "", block)
    return block


def effective_date(html):
    """First date only. Some source pages append a mid-dot separated
    'Last Updated' clause in the same span, which must not be carried through."""
    m = re.search(r"<span data-lang-en>Effective Date:\s*([^<]+)</span>", html)
    if not m:
        m = re.search(r"<span data-lang-en>Last Updated:\s*([^<]+)</span>", html)
    if not m:
        return "February 2026"
    value = m.group(1)
    value = re.split(r"&middot;|·|\|", value)[0]
    return value.strip().rstrip(",").strip()


def indent(block, spaces=8):
    pad = " " * spaces
    lines = [l.rstrip() for l in block.strip("\n").split("\n")]
    widths = [len(l) - len(l.lstrip()) for l in lines if l.strip()]
    trim = min(widths) if widths else 0
    return "\n".join((pad + l[trim:]) if l.strip() else "" for l in lines)


META = u"""
  <title>{title_plain} | Axionalytics</title>
  <meta name="description" content="{desc}">
  <link rel="canonical" href="{base}/{slug}.html">
  <meta name="robots" content="index, follow">
  <meta property="og:title" content="{title_plain} | Axionalytics">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{base}/{slug}.html">

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "WebPage",
    "@id": "{base}/{slug}.html#page",
    "name": "{title_plain}",
    "description": "{desc}",
    "url": "{base}/{slug}.html",
    "inLanguage": ["en", "es"],
    "dateModified": "{iso}",
    "isPartOf": {{ "@type": "WebSite", "url": "{base}/" }},
    "publisher": {{ "@type": "Organization", "name": "Axionalytics", "url": "{base}/" }}
  }}
  </script>
"""

BODY = u"""
<!-- ==========================================================================
     PAGE HERO
     Content migrated from the pre-2026 site by _build/scripts/extract-legal.py.
     The legal text is unchanged; only chrome and typography moved.
     ========================================================================== -->
<section class="ax-hero ax-noise relative pt-36 pb-14 lg:pt-44 lg:pb-16 overflow-hidden">
  <div class="ax-grid-bg"></div>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative">

    <nav class="flex items-center gap-2 text-xs font-semibold text-white/35 mb-8 ax-reveal" aria-label="Breadcrumb">
      <a href="index.html" class="hover:text-ax-cyan transition-colors">
        <span data-lang-en>Home</span><span data-lang-es>Inicio</span>
      </a>
      <span>/</span>
      <span class="text-white/60">
        <span data-lang-en>{title_en}</span><span data-lang-es>{title_es}</span>
      </span>
    </nav>

    <p class="ax-eyebrow text-ax-cyan mb-5 ax-reveal">
      <span data-lang-en>{eyebrow_en}</span><span data-lang-es>{eyebrow_es}</span>
    </p>

    <h1 class="font-heading font-extrabold text-white text-[2.2rem] sm:text-4xl lg:text-[3rem] leading-[1.08] mb-5 ax-reveal">
      <span data-lang-en>{title_en}</span>
      <span data-lang-es>{title_es}</span>
    </h1>

    <p class="text-white/50 text-sm ax-reveal">
      <span data-lang-en>Effective date: {eff}</span>
      <span data-lang-es>Fecha de vigencia: {eff}</span>
    </p>
  </div>
</section>

<!-- ==========================================================================
     CONTENT
     ========================================================================== -->
<section class="py-16 lg:py-20 bg-white">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">

    <div data-lang-en class="ax-block ax-prose ax-legal">
{body_en}
    </div>

    <div data-lang-es class="ax-block ax-prose ax-legal">
{body_es}
    </div>

    <!-- Cross-links between the three legal documents -->
    <div class="mt-16 pt-8 border-t border-ax-ink/10">
      <p class="ax-label text-ax-ink/40 mb-4">
        <span data-lang-en>Related documents</span><span data-lang-es>Documentos relacionados</span>
      </p>
      <div class="flex flex-wrap gap-2.5">
        <a href="privacy.html" class="ax-pill bg-ax-ink/5 text-ax-ink/70 border border-ax-ink/12 hover:border-ax-blue/40 hover:text-ax-blue transition-colors">
          <span data-lang-en>Privacy Policy</span><span data-lang-es>Política de Privacidad</span>
        </a>
        <a href="terms.html" class="ax-pill bg-ax-ink/5 text-ax-ink/70 border border-ax-ink/12 hover:border-ax-blue/40 hover:text-ax-blue transition-colors">
          <span data-lang-en>Terms &amp; Conditions</span><span data-lang-es>Términos y Condiciones</span>
        </a>
        <a href="accessibility.html" class="ax-pill bg-ax-ink/5 text-ax-ink/70 border border-ax-ink/12 hover:border-ax-blue/40 hover:text-ax-blue transition-colors">
          <span data-lang-en>Accessibility</span><span data-lang-es>Accesibilidad</span>
        </a>
        <a href="contact.html" class="ax-pill bg-ax-ink/5 text-ax-ink/70 border border-ax-ink/12 hover:border-ax-blue/40 hover:text-ax-blue transition-colors">
          <span data-lang-en>Contact</span><span data-lang-es>Contacto</span>
        </a>
      </div>
    </div>
  </div>
</section>
"""

ISO = {
    "February 2026": "2026-02-09",
    "January 2026": "2026-01-15",
    "October 17, 2025": "2025-10-17",
}

for p in PAGES:
    if not os.path.exists(p["src"]):
        print("  skip  %s (missing %s)" % (p["slug"], p["src"]))
        continue

    html = io.open(p["src"], encoding="utf-8").read()
    en, es = clean(grab(html, "en")), clean(grab(html, "es"))
    eff = effective_date(html)

    title_plain = p["title_en"].replace("&amp;", "&")

    meta = META.format(base=BASE, slug=p["slug"], desc=p["desc"],
                       title_plain=title_plain, iso=ISO.get(eff, "2026-02-09"))
    body = BODY.format(body_en=indent(en), body_es=indent(es), eff=eff, **p)

    io.open(os.path.join(OUT, p["slug"] + ".meta.html"), "w", encoding="utf-8").write(meta)
    io.open(os.path.join(OUT, p["slug"] + ".body.html"), "w", encoding="utf-8").write(body)

    print("  %-16s en=%5d  es=%5d bytes   effective: %s" % (p["slug"], len(en), len(es), eff))

print("\n  %d legal pages migrated" % len(PAGES))
