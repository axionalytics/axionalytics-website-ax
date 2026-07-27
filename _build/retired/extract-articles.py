# -*- coding: utf-8 -*-
"""
Break the pre-2026 blog out of its accordion.

_legacy/blog.html carried four full articles inside `.blog-content` wrappers
styled `max-height:0; overflow:hidden`. All four lived at a single URL, so each
competed with the others for the same page's ranking signals and none could be
linked, shared, or cited independently.

This lifts each article body out verbatim — the markup already interleaves
data-lang-en / data-lang-es spans, which is exactly the pattern the new site
uses — and emits a `_build/pages/<slug>.body.html` + `.meta.html` pair per
article, wrapped in the new chrome with Article + BreadcrumbList JSON-LD.

Article prose is migrated as-authored. It is not rewritten here; retargeting the
editorial voice is a separate decision.

Usage: python _build/extract-articles.py
"""
import io
import os
import re

SRC = "_legacy/blog.html"
OUT = "_build/pages"
BASE = "https://www.axionalytics.com"

# Ordered to match document order in the source file.
ARTICLES = [
    {
        "slug": "business-dashboard-guide",
        "cat_en": "Getting Started", "cat_es": "Comenzando",
        "date": "2024-12-01", "read": "12",
        "date_en": "December 2024", "date_es": "Diciembre 2024",
        "title_en": "How to Build Your First Business Dashboard",
        "title_es": "Cómo Construir Tu Primer Dashboard Empresarial",
        "desc_en": "Build a dashboard people actually use. Start from the decisions you need to make, not the charts you can produce.",
        "desc_es": "Construya un tablero que la gente realmente use. Empiece por las decisiones que necesita tomar, no por los gráficos que puede producir.",
    },
    {
        "slug": "data-analytics-roi",
        "cat_en": "Strategy", "cat_es": "Estrategia",
        "date": "2024-12-15", "read": "14",
        "date_en": "December 2024", "date_es": "Diciembre 2024",
        "title_en": "The ROI of Data Analytics for Small Business",
        "title_es": "El ROI de la Analítica de Datos para Pequeñas Empresas",
        "desc_en": "Where analytics return actually comes from — receivables, unprofitable customers, inventory waste, marketing, and operations — and how to calculate yours.",
        "desc_es": "De dónde viene realmente el retorno de la analítica — cobranzas, clientes no rentables, desperdicio de inventario, marketing y operaciones — y cómo calcular el suyo.",
    },
    {
        "slug": "ai-tools-for-business",
        "cat_en": "AI Tools", "cat_es": "Herramientas de IA",
        "date": "2025-01-10", "read": "15",
        "date_en": "January 2025", "date_es": "Enero 2025",
        "title_en": "7 AI Tools Every Small Business Should Know About",
        "title_es": "7 Herramientas de IA que Toda Pequeña Empresa Debería Conocer",
        "desc_en": "A working shortlist of AI tools that earn their subscription — what each one is genuinely good at, and where to start.",
        "desc_es": "Una lista práctica de herramientas de IA que justifican su suscripción — en qué es realmente buena cada una y por dónde empezar.",
    },
    {
        "slug": "excel-vs-power-bi",
        "cat_en": "Comparison", "cat_es": "Comparación",
        "date": "2025-01-25", "read": "16",
        "date_en": "January 2025", "date_es": "Enero 2025",
        "title_en": "Excel vs Power BI: Which Is Right for Your Business?",
        "title_es": "Excel vs Power BI: ¿Cuál Es Adecuado para Su Negocio?",
        "desc_en": "A direct comparison, the scenarios that decide it, and the hybrid approach that suits most teams better than either alone.",
        "desc_es": "Una comparación directa, los escenarios que la deciden y el enfoque híbrido que conviene a la mayoría de los equipos más que cualquiera por separado.",
    },
]


def extract_bodies(html):
    """Return the inner HTML of each `.blog-content-inner` block, in order."""
    out, idx = [], 0
    marker = '<div class="blog-content-inner">'
    while True:
        start = html.find(marker, idx)
        if start == -1:
            break
        pos = start + len(marker)
        depth = 1
        # Walk div open/close tags to find this block's true closing tag,
        # since the bodies contain nested callout divs.
        for m in re.finditer(r"<(/?)div\b", html[pos:]):
            depth += -1 if m.group(1) else 1
            if depth == 0:
                out.append(html[pos:pos + m.start()])
                idx = pos + m.end()
                break
        else:
            break
    return out


def repair_lang_attrs(block):
    """Fix malformed bilingual attributes inherited from the source.

    The pre-2026 blog contained 28 spans written as `<span data-lang-es">` —
    a stray quote that makes the attribute name literally `data-lang-es"`.
    No `[data-lang-es]` selector matches it, so both languages rendered at
    once and Spanish leaked into the English view ("Data Limits: Límites de
    Datos:"). The bug was latent in the original too; it is repaired here
    rather than left for the CSS to work around.
    """
    return re.sub(r'(data-lang-(?:en|es))"(?=[\s>])', r"\1", block)


def assert_lang_wellformed(block, slug):
    """Fail the build rather than ship a page that renders both languages."""
    bad = re.findall(r'data-lang-(?:en|es)"', block)
    if bad:
        raise SystemExit("%s: %d malformed data-lang attributes survived repair"
                         % (slug, len(bad)))

    en = len(re.findall(r"<span data-lang-en>", block))
    es = len(re.findall(r"<span data-lang-es>", block))
    if en != es:
        print("    warn %s: %d EN spans vs %d ES spans" % (slug, en, es))


def indent(block, spaces=8):
    pad = " " * spaces
    lines = [l.rstrip() for l in block.strip("\n").split("\n")]
    # Strip the deepest common indentation, then re-indent uniformly.
    widths = [len(l) - len(l.lstrip()) for l in lines if l.strip()]
    trim = min(widths) if widths else 0
    return "\n".join((pad + l[trim:]) if l.strip() else "" for l in lines)


META = u"""
  <title>{title_en} | Axionalytics</title>
  <meta name="description" content="{desc_en}">
  <link rel="canonical" href="{base}/{slug}.html">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{title_en}">
  <meta property="og:description" content="{desc_en}">
  <meta property="og:url" content="{base}/{slug}.html">
  <meta property="article:published_time" content="{date}">
  <meta property="article:section" content="{cat_en}">

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "@id": "{base}/{slug}.html#article",
    "headline": "{title_en}",
    "description": "{desc_en}",
    "datePublished": "{date}",
    "dateModified": "{date}",
    "articleSection": "{cat_en}",
    "inLanguage": ["en", "es"],
    "wordCount": {words},
    "timeRequired": "PT{read}M",
    "mainEntityOfPage": {{ "@type": "WebPage", "@id": "{base}/{slug}.html" }},
    "author": {{ "@type": "Organization", "name": "Axionalytics", "url": "{base}/" }},
    "publisher": {{
      "@type": "Organization",
      "name": "Axionalytics",
      "url": "{base}/",
      "logo": {{ "@type": "ImageObject", "url": "{base}/assets/favicon-512.png" }}
    }}
  }}
  </script>

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{ "@type": "ListItem", "position": 1, "name": "Home", "item": "{base}/" }},
      {{ "@type": "ListItem", "position": 2, "name": "Blog", "item": "{base}/blog.html" }},
      {{ "@type": "ListItem", "position": 3, "name": "{title_en}", "item": "{base}/{slug}.html" }}
    ]
  }}
  </script>
"""

BODY = u"""
<!-- ==========================================================================
     ARTICLE HEADER
     Migrated from the pre-2026 accordion blog by _build/extract-articles.py
     ========================================================================== -->
<section class="ax-hero ax-noise relative pt-36 pb-16 lg:pt-44 lg:pb-20 overflow-hidden">
  <div class="ax-grid-bg"></div>
  <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 relative">

    <nav class="flex items-center gap-2 text-xs font-semibold text-white/35 mb-8 ax-reveal" aria-label="Breadcrumb">
      <a href="index.html" class="hover:text-ax-cyan transition-colors">
        <span data-lang-en>Home</span><span data-lang-es>Inicio</span>
      </a>
      <span>/</span>
      <a href="blog.html" class="hover:text-ax-cyan transition-colors">Blog</a>
      <span>/</span>
      <span class="text-white/60">
        <span data-lang-en>{cat_en}</span><span data-lang-es>{cat_es}</span>
      </span>
    </nav>

    <span class="ax-pill ax-pill-dark mb-6 ax-reveal">
      <span class="w-1.5 h-1.5 rounded-full bg-ax-cyan"></span>
      <span data-lang-en>{cat_en}</span><span data-lang-es>{cat_es}</span>
    </span>

    <h1 class="font-heading font-extrabold text-white text-[2rem] sm:text-4xl lg:text-[2.9rem] leading-[1.1] mb-6 ax-reveal">
      <span data-lang-en>{title_en}</span>
      <span data-lang-es>{title_es}</span>
    </h1>

    <p class="text-lg text-white/60 leading-relaxed mb-7 ax-reveal">
      <span data-lang-en>{desc_en}</span>
      <span data-lang-es>{desc_es}</span>
    </p>

    <div class="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-white/40 ax-reveal">
      <time datetime="{date}">
        <span data-lang-en>{date_en}</span><span data-lang-es>{date_es}</span>
      </time>
      <span class="w-1 h-1 rounded-full bg-white/20"></span>
      <span>
        <span data-lang-en>{read} min read</span><span data-lang-es>{read} min de lectura</span>
      </span>
    </div>
  </div>
</section>

<!-- ==========================================================================
     ARTICLE BODY
     ========================================================================== -->
<article class="py-16 lg:py-20 bg-white">
  <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="ax-prose">
{body}
    </div>

    <!-- Author / disclosure -->
    <div class="mt-14 pt-8 border-t border-ax-ink/10 flex flex-wrap items-center gap-4">
      <img src="assets/logo-mark.png" alt="" class="w-12 h-12 object-contain">
      <div>
        <p class="font-heading font-bold">Axionalytics</p>
        <p class="text-sm text-ax-ink/55">
          <span data-lang-en>Production agentic AI for enterprise engineering, data, and revenue teams.</span>
          <span data-lang-es>IA agéntica en producción para equipos empresariales de ingeniería, datos e ingresos.</span>
        </p>
      </div>
    </div>
  </div>
</article>

<!-- ==========================================================================
     RELATED + CTA
     ========================================================================== -->
<section class="ax-band py-20 lg:py-24 relative overflow-hidden">
  <div class="ax-grid-bg opacity-50"></div>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative">

    <p class="ax-eyebrow text-ax-cyan mb-7 ax-reveal">
      <span data-lang-en>Keep reading</span><span data-lang-es>Seguir leyendo</span>
    </p>

    <div class="grid sm:grid-cols-3 gap-4 mb-14 ax-stagger">
{related}
    </div>

    <div class="rounded-2xl border border-white/10 bg-white/[0.03] p-8 lg:p-10 text-center ax-reveal">
      <h2 class="font-heading font-extrabold text-2xl lg:text-3xl text-white leading-tight mb-4">
        <span data-lang-en>Running into this at enterprise scale?</span>
        <span data-lang-es>¿Enfrenta esto a escala empresarial?</span>
      </h2>
      <p class="text-white/60 leading-relaxed mb-8 max-w-2xl mx-auto">
        <span data-lang-en>We build the production systems behind these problems — deployed inside your own perimeter, governed by human approval, and handed over with the source.</span>
        <span data-lang-es>Construimos los sistemas en producción detrás de estos problemas — desplegados dentro de su perímetro, gobernados por aprobación humana y entregados con el código fuente.</span>
      </p>
      <div class="flex flex-col sm:flex-row gap-3.5 justify-center">
        <a href="https://calendar.app.google/AYww7wSmkwANWDxR9" target="_blank" rel="noopener" class="ax-btn ax-btn-primary px-7 py-3.5">
          <span data-lang-en>Book a Technical Briefing</span><span data-lang-es>Agendar Sesión Técnica</span>
        </a>
        <a href="solutions.html" class="ax-btn ax-btn-ghost px-7 py-3.5">
          <span data-lang-en>See the solutions</span><span data-lang-es>Ver las soluciones</span>
        </a>
      </div>
    </div>
  </div>
</section>
"""

RELATED_CARD = u"""      <a href="{slug}.html" class="rounded-xl border border-white/10 bg-white/[0.03] p-5 hover:border-ax-cyan/40 hover:bg-white/[0.06] transition-colors">
        <p class="text-2xs font-bold uppercase tracking-wider text-ax-cyan mb-2">
          <span data-lang-en>{cat_en}</span><span data-lang-es>{cat_es}</span>
        </p>
        <p class="font-heading font-bold text-white leading-snug">
          <span data-lang-en>{title_en}</span><span data-lang-es>{title_es}</span>
        </p>
      </a>"""


def main():
    if not os.path.exists(SRC):
        raise SystemExit("missing %s" % SRC)

    html = io.open(SRC, encoding="utf-8").read()
    bodies = extract_bodies(html)
    if len(bodies) != len(ARTICLES):
        raise SystemExit("expected %d bodies, found %d" % (len(ARTICLES), len(bodies)))

    for i, art in enumerate(ARTICLES):
        body = repair_lang_attrs(bodies[i])
        assert_lang_wellformed(body, art["slug"])

        # Measure the English reading text: drop the Spanish spans, then strip
        # markup and entities. The pre-2026 pages advertised 12-16 minute reads
        # on 180-465 word articles; read time is recomputed here at 225 wpm so
        # the visible label and the schema agree with the actual content.
        en_only = re.sub(r"<span data-lang-es>.*?</span>", "", body, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", en_only)
        text = re.sub(r"&[a-zA-Z#0-9]+;", " ", text)
        words = len(text.split())
        art = dict(art, read=str(max(1, int(round(words / 225.0)))))

        others = [a for a in ARTICLES if a["slug"] != art["slug"]][:3]
        related = "\n".join(RELATED_CARD.format(**o) for o in others)

        meta = META.format(base=BASE, words=words, **art)
        page = BODY.format(body=indent(body), related=related, **art)

        io.open(os.path.join(OUT, art["slug"] + ".meta.html"), "w", encoding="utf-8").write(meta)
        io.open(os.path.join(OUT, art["slug"] + ".body.html"), "w", encoding="utf-8").write(page)

        print("  %-28s %5d words  %6d bytes body" % (art["slug"], words, len(body)))

    print("\n  %d articles extracted" % len(ARTICLES))


if __name__ == "__main__":
    main()
