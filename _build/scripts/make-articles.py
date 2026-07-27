# -*- coding: utf-8 -*-
"""
Assemble the article set.

STRUCTURE
---------
Content and chrome are kept apart so the article template can change once and
propagate to every piece:

    _build/src/articles/<slug>.html   bilingual prose only (.ax-prose markup)
    ARTICLES (below)              metadata, and the pillar each piece supports
    this script                   wraps content in the shared article chrome

PILLAR & CLUSTER
----------------
Every article declares a `pillar`. The template renders an explicit link up to
that pillar page and pulls its sibling cluster articles into "related", so link
equity concentrates on the four commercial pages rather than spreading evenly
across the blog. Articles without a pillar do not exist here by design.

Usage: python _build/scripts/make-articles.py
"""
import io
import os
import re
import importlib.util


def _load_author():
    """Named-author config. Inert until a name is filled in."""
    spec = importlib.util.spec_from_file_location(
        "author", os.path.join("_build", "scripts", "author.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

AUTHOR = _load_author()

BASE = "https://www.axionalytics.com"
SRC = "_build/src/articles"
OUT = "_build/pages"

PILLARS = {
    "security": {
        "url": "enterprise-ai-security.html",
        "name_en": "Zero-Trust AI Governance",
        "name_es": "Gobernanza de IA de Confianza Cero",
        "blurb_en": "The deployment topology, isolation model, and audit architecture that get agentic systems through security review.",
        "blurb_es": "La topología de despliegue, el modelo de aislamiento y la arquitectura de auditoría que hacen pasar los sistemas agénticos por la revisión de seguridad.",
        "accent": "#0EA5A5",
    },
    "agentic": {
        "url": "enterprise-agentic-ai.html",
        "name_en": "Enterprise Agentic AI",
        "name_es": "IA Agéntica Empresarial",
        "blurb_en": "Autonomous multi-step agents inside your VPC, with human approval on every write and citations the backend generates.",
        "blurb_es": "Agentes autónomos multi-paso dentro de su VPC, con aprobación humana en cada escritura y citas generadas por el backend.",
        "accent": "#A855F7",
    },
    "testing": {
        "url": "agentic-test-engineering.html",
        "name_en": "Agentic Test Engineering",
        "name_es": "Ingeniería de Pruebas Agéntica",
        "blurb_en": "Requirements, source code, and merged pull requests become reviewed, traceable verification test cases.",
        "blurb_es": "Requisitos, código fuente y PRs fusionados se convierten en casos de prueba revisados y trazables.",
        "accent": "#22D3EE",
    },
    "bi": {
        "url": "agentic-business-intelligence.html",
        "name_en": "Agentic Business Intelligence",
        "name_es": "Inteligencia de Negocios Agéntica",
        "blurb_en": "A sentence and a governed source produce a real Power BI artifact your BI team owns and edits.",
        "blurb_es": "Una frase y una fuente gobernada producen un artefacto real de Power BI que su equipo posee y edita.",
        "accent": "#3B82F6",
    },
    "revenue": {
        "url": "agentic-revenue-development.html",
        "name_en": "Agentic Revenue Development",
        "name_es": "Desarrollo de Ingresos Agéntico",
        "blurb_en": "Account discovery, research, contact resolution, and drafted outreach — with the send decision left to a person.",
        "blurb_es": "Descubrimiento de cuentas, investigación, resolución de contactos y borradores de contacto — con la decisión de envío en manos de una persona.",
        "accent": "#C026D3",
    },
}

# Newest first — this order drives the blog index.
ARTICLES = [
    {
        "slug": "why-ai-pilots-fail-security-review",
        "pillar": "security",
        "date": "2026-07-20",
        "date_en": "July 2026", "date_es": "Julio 2026",
        "cat_en": "Security", "cat_es": "Seguridad",
        "title_en": "Why Enterprise AI Pilots Die in Security Review",
        "title_es": "Por Qué los Pilotos de IA Empresarial Mueren en la Revisión de Seguridad",
        "desc_en": "The pilot worked. Eighteen months later it still is not in production. Five architectural questions decide that outcome, and all five are settled before the first line of code.",
        "desc_es": "El piloto funcionó. Dieciocho meses después sigue sin estar en producción. Cinco preguntas de arquitectura deciden ese resultado, y las cinco se resuelven antes de la primera línea de código.",
    },
    {
        "slug": "prompt-injection-tool-abuse-defense",
        "pillar": "security",
        "date": "2026-07-17",
        "date_en": "July 2026", "date_es": "Julio 2026",
        "cat_en": "Security", "cat_es": "Seguridad",
        "title_en": "Prompt Injection Is a Containment Problem, Not a Prompting Problem",
        "title_es": "La Inyección de Prompts Es un Problema de Contención, No de Prompts",
        "desc_en": "The defence and the attack share a channel, so no instruction closes the class. Four named attacks, and the architectural layers that make a successful one harmless.",
        "desc_es": "La defensa y el ataque comparten canal, así que ninguna instrucción cierra la clase. Cuatro ataques nombrados y las capas arquitectónicas que vuelven inofensivo uno exitoso.",
    },
    {
        "slug": "outbound-research-not-volume",
        "pillar": "revenue",
        "date": "2026-07-24",
        "date_en": "July 2026", "date_es": "Julio 2026",
        "cat_en": "Revenue", "cat_es": "Ingresos",
        "title_en": "Outbound Broke Because Volume Got Cheap",
        "title_es": "La Prospección se Rompió Porque el Volumen se Abarató",
        "desc_en": "Research and volume trade against each other, and every team eventually picks the losing side. The way out is to automate the research and leave the send alone.",
        "desc_es": "La investigación y el volumen se contraponen, y todo equipo termina eligiendo el lado perdedor. La salida es automatizar la investigación y no tocar el envío.",
    },
    {
        "slug": "email-deliverability-firewall",
        "pillar": "revenue",
        "date": "2026-07-10",
        "date_en": "July 2026", "date_es": "Julio 2026",
        "cat_en": "Revenue", "cat_es": "Ingresos",
        "title_en": "Your Sending Domain Is an Asset. Bounces Are How You Spend It.",
        "title_es": "Su Dominio de Envío Es un Activo. Los Rebotes Son Cómo lo Gasta.",
        "desc_en": "Guessed addresses cost more than the campaign that produced them. Three escalating verification tiers, and the design decision that matters most when none of them can answer.",
        "desc_es": "Las direcciones adivinadas cuestan más que la campaña que las produjo. Tres niveles de verificación escalonados, y la decisión de diseño que más importa cuando ninguno puede responder.",
    },
    {
        "slug": "byoc-vs-saas-enterprise-ai",
        "pillar": "security",
        "date": "2026-07-14",
        "date_en": "July 2026", "date_es": "Julio 2026",
        "cat_en": "Architecture", "cat_es": "Arquitectura",
        "title_en": "BYOC, SaaS, or On-Premises: Choosing a Deployment Topology for Enterprise AI",
        "title_es": "BYOC, SaaS u On-Premises: Cómo Elegir la Topología de Despliegue para IA Empresarial",
        "desc_en": "Deployment topology is not an infrastructure detail you settle later. It determines which data the system may touch, and it is the hardest decision to reverse.",
        "desc_es": "La topología de despliegue no es un detalle de infraestructura que se resuelve después. Determina qué datos puede tocar el sistema, y es la decisión más difícil de revertir.",
    },
    {
        "slug": "human-in-the-loop-ai-architecture",
        "pillar": "agentic",
        "date": "2026-07-07",
        "date_en": "July 2026", "date_es": "Julio 2026",
        "cat_en": "Architecture", "cat_es": "Arquitectura",
        "title_en": "Human-in-the-Loop That Actually Holds: Write Gates, Blast Radius, and Replay Protection",
        "title_es": "Aprobación Humana Que Realmente Resiste: Puertas de Escritura, Radio de Impacto y Protección Contra Repetición",
        "desc_en": "Most human-in-the-loop is a confirmation dialog. Three properties separate a real approval gate from a checkbox that manufactures consent.",
        "desc_es": "La mayoría de las aprobaciones humanas son un diálogo de confirmación. Tres propiedades separan una puerta de aprobación real de una casilla que fabrica consentimiento.",
    },
    {
        "slug": "agentic-data-exploration-at-scale",
        "pillar": "agentic",
        "date": "2026-06-30",
        "date_en": "June 2026", "date_es": "Junio 2026",
        "cat_en": "Engineering", "cat_es": "Ingeniería",
        "title_en": "How an Agent Queries a 50,000-Table Warehouse Without Reading the Schema",
        "title_es": "Cómo un Agente Consulta un Almacén de 50.000 Tablas Sin Leer el Esquema",
        "desc_en": "Every demo works against twelve tables. Real catalogs have tens of thousands, and the standard approach collapses on cost, latency, and accuracy at the same time.",
        "desc_es": "Toda demostración funciona con doce tablas. Los catálogos reales tienen decenas de miles, y el enfoque estándar colapsa en costo, latencia y precisión a la vez.",
    },
    {
        "slug": "requirements-traceability-automation",
        "pillar": "testing",
        "date": "2026-06-23",
        "date_en": "June 2026", "date_es": "Junio 2026",
        "cat_en": "Verification", "cat_es": "Verificación",
        "title_en": "Requirements Traceability Without the Spreadsheet",
        "title_es": "Trazabilidad de Requisitos Sin la Hoja de Cálculo",
        "desc_en": "The traceability matrix is accurate the day it is written and wrong within a sprint. Generating the link at authoring time is what makes it survive.",
        "desc_es": "La matriz de trazabilidad es exacta el día que se escribe y errónea en un sprint. Generar el vínculo al momento de crear el caso es lo que la hace sobrevivir.",
    },
    {
        "slug": "coverage-gap-analysis",
        "pillar": "testing",
        "date": "2026-06-26",
        "date_en": "June 2026", "date_es": "Junio 2026",
        "cat_en": "Verification", "cat_es": "Verificación",
        "title_en": "Line Coverage Is Not Verification Coverage",
        "title_es": "La Cobertura de Líneas No Es Cobertura de Verificación",
        "desc_en": "Most organisations can report line coverage to two decimals and cannot say which implemented behaviour nobody has written a test for. Those are different numbers.",
        "desc_es": "La mayoría de las organizaciones reporta cobertura de líneas con dos decimales y no puede decir para qué comportamiento implementado nadie escribió una prueba. Son cifras distintas.",
    },
    {
        "slug": "legacy-test-suite-modernization",
        "pillar": "testing",
        "date": "2026-06-19",
        "date_en": "June 2026", "date_es": "Junio 2026",
        "cat_en": "Verification", "cat_es": "Verificación",
        "title_en": "Paying Down Legacy Test Debt Without an Engineer-Year",
        "title_es": "Cómo Saldar la Deuda de Pruebas Heredadas Sin un Año-Ingeniero",
        "desc_en": "The assertions in a decade-old suite are usually fine. What is missing is everything around them — and retrofitting that is tractable in a way rewriting is not.",
        "desc_es": "Las verificaciones de una suite de hace una década suelen estar bien. Lo que falta es todo lo que las rodea — y adaptarlo es abordable de una forma en que reescribir no lo es.",
    },
    {
        "slug": "bi-backlog-bottleneck",
        "pillar": "bi",
        "date": "2026-06-16",
        "date_en": "June 2026", "date_es": "Junio 2026",
        "cat_en": "Analytics", "cat_es": "Analítica",
        "title_en": "Your BI Backlog Is a Transcription Bottleneck, Not a Capacity Problem",
        "title_es": "Su Backlog de BI Es un Cuello de Botella de Transcripción, No un Problema de Capacidad",
        "desc_en": "Adding analysts to a forty-item queue buys a quarter of relief. The queue is long because the same dashboard is being hand-built for the eleventh time.",
        "desc_es": "Agregar analistas a una cola de cuarenta ítems compra un trimestre de alivio. La cola es larga porque el mismo tablero se construye a mano por undécima vez.",
    },

    # --- Retargeted from the pre-2026 blog. URLs preserved. ---
    {
        "slug": "excel-vs-power-bi",
        "pillar": "bi",
        "date": "2026-06-09",
        "date_en": "June 2026", "date_es": "Junio 2026",
        "cat_en": "Analytics", "cat_es": "Analítica",
        "title_en": "Excel Sprawl vs a Governed Semantic Model",
        "title_es": "Proliferación de Excel vs un Modelo Semántico Gobernado",
        "desc_en": "The question is not which tool is better. It is which numbers the board sees when four departments each maintain their own version of revenue.",
        "desc_es": "La pregunta no es qué herramienta es mejor. Es qué cifras ve el directorio cuando cuatro departamentos mantienen cada uno su propia versión de los ingresos.",
    },
    {
        "slug": "data-analytics-roi",
        "pillar": "bi",
        "date": "2026-06-02",
        "date_en": "June 2026", "date_es": "Junio 2026",
        "cat_en": "Strategy", "cat_es": "Estrategia",
        "title_en": "Building the Business Case for Enterprise AI",
        "title_es": "Cómo Construir el Caso de Negocio para la IA Empresarial",
        "desc_en": "Finance rejects AI business cases for predictable reasons. Understated loaded cost, unfalsifiable benefits, and an automation rate nobody believes.",
        "desc_es": "Finanzas rechaza los casos de negocio de IA por razones predecibles. Costo cargado subestimado, beneficios no verificables y una tasa de automatización que nadie cree.",
    },
    {
        "slug": "business-dashboard-guide",
        "pillar": "bi",
        "date": "2026-05-26",
        "date_en": "May 2026", "date_es": "Mayo 2026",
        "cat_en": "Analytics", "cat_es": "Analítica",
        "title_en": "Why Enterprise Dashboards Get Abandoned",
        "title_es": "Por Qué se Abandonan los Tableros Empresariales",
        "desc_en": "A dashboard nobody opens is not a design failure. It is a specification failure — it was built from the data that existed rather than the decision it serves.",
        "desc_es": "Un tablero que nadie abre no es una falla de diseño. Es una falla de especificación — se construyó con los datos que existían y no con la decisión a la que sirve.",
    },
    {
        "slug": "ai-tools-for-business",
        "pillar": "agentic",
        "date": "2026-05-19",
        "date_en": "May 2026", "date_es": "Mayo 2026",
        "cat_en": "Strategy", "cat_es": "Estrategia",
        "title_en": "Build, Buy, or Assemble: Sourcing Enterprise AI Capability",
        "title_es": "Construir, Comprar o Ensamblar: Cómo Adquirir Capacidad de IA Empresarial",
        "desc_en": "The build-versus-buy framing hides the option most enterprises actually need, and the three constraints that decide it have nothing to do with engineering capacity.",
        "desc_es": "El marco construir-o-comprar oculta la opción que la mayoría de las empresas realmente necesita, y las tres restricciones que la deciden no tienen que ver con capacidad de ingeniería.",
    },
]

WPM = 225


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

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
    "isPartOf": {{ "@type": "Blog", "@id": "{base}/blog.html#blog" }},
    "about": {{ "@type": "Thing", "name": "{pillar_name}", "url": "{base}/{pillar_url}" }},
    "author": {author_json},
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
      {{ "@type": "ListItem", "position": 3, "name": "{title_esc}", "item": "{base}/{slug}.html" }}
    ]
  }}
  </script>
{faq}"""

FAQ_BLOCK = u"""
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [{items}
    ]
  }}
  </script>
"""

BODY = u"""
<!-- ==========================================================================
     ARTICLE HEADER
     Generated by _build/scripts/make-articles.py from _build/src/articles/{slug}.html
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
      <span class="w-1.5 h-1.5 rounded-full" style="background:{accent}"></span>
      <span data-lang-en>{cat_en}</span><span data-lang-es>{cat_es}</span>
    </span>

    <h1 class="font-heading font-extrabold text-white text-[1.95rem] sm:text-4xl lg:text-[2.75rem] leading-[1.1] mb-6 ax-reveal">
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
      </span>{byline}
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

    <!-- Cluster -> pillar link -->
    <aside class="mt-14 rounded-2xl border border-ax-ink/10 bg-ax-mist p-7">
      <p class="ax-label text-ax-ink/40 mb-3">
        <span data-lang-en>The system behind this</span><span data-lang-es>El sistema detrás de esto</span>
      </p>
      <h2 class="font-heading font-bold text-xl mb-2.5">
        <a href="{pillar_url}" class="hover:text-ax-blue transition-colors">
          <span data-lang-en>{pillar_name}</span><span data-lang-es>{pillar_name_es}</span>
        </a>
      </h2>
      <p class="text-ax-ink/65 leading-relaxed mb-5">
        <span data-lang-en>{pillar_blurb}</span><span data-lang-es>{pillar_blurb_es}</span>
      </p>
      <a href="{pillar_url}" class="ax-btn ax-btn-outline px-5 py-2.5 text-sm">
        <span data-lang-en>How it works</span><span data-lang-es>Cómo funciona</span>
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5-5 5M5 12h13"/></svg>
      </a>
    </aside>

    <div class="mt-10 pt-8 border-t border-ax-ink/10 flex flex-wrap items-center gap-4">
      <img src="assets/logo-mark.png" alt="" class="w-12 h-12 object-contain" width="141" height="160" loading="lazy" decoding="async">
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
        <span data-lang-en>Facing this in your own environment?</span>
        <span data-lang-es>¿Enfrenta esto en su propio entorno?</span>
      </h2>
      <p class="text-white/60 leading-relaxed mb-8 max-w-2xl mx-auto">
        <span data-lang-en>Forty-five minutes with the engineers who build these systems. Bring the constraint that has been blocking you — you will leave with an architecture opinion whether or not you work with us.</span>
        <span data-lang-es>Cuarenta y cinco minutos con los ingenieros que construyen estos sistemas. Traiga la restricción que lo ha estado bloqueando — saldrá con una opinión arquitectónica trabaje con nosotros o no.</span>
      </p>
      <div class="flex flex-col sm:flex-row gap-3.5 justify-center">
        <a href="https://calendar.app.google/AYww7wSmkwANWDxR9" target="_blank" rel="noopener" class="ax-btn ax-btn-primary px-7 py-3.5">
          <span data-lang-en>Book a Technical Briefing</span><span data-lang-es>Agendar Sesión Técnica</span>
        </a>
        <a href="roi-calculator.html" class="ax-btn ax-btn-ghost px-7 py-3.5">
          <span data-lang-en>Model the ROI</span><span data-lang-es>Modelar el ROI</span>
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def esc(s):
    return s.replace('"', '\\"')


def indent(block, spaces=6):
    pad = " " * spaces
    lines = [l.rstrip() for l in block.strip("\n").split("\n")]
    widths = [len(l) - len(l.lstrip()) for l in lines if l.strip()]
    trim = min(widths) if widths else 0
    return "\n".join((pad + l[trim:]) if l.strip() else "" for l in lines)


def english_words(block):
    en_only = re.sub(r"<span data-lang-es>.*?</span>", "", block, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", en_only)
    text = re.sub(r"&[a-zA-Z#0-9]+;", " ", text)
    return len(text.split())


def check_wellformed(block, slug):
    bad = re.findall(r'data-lang-(?:en|es)"', block)
    if bad:
        raise SystemExit("%s: %d malformed data-lang attributes" % (slug, len(bad)))
    en = len(re.findall(r"<span data-lang-en>", block))
    es = len(re.findall(r"<span data-lang-es>", block))
    if en != es:
        raise SystemExit("%s: bilingual parity broken - %d EN spans vs %d ES spans"
                         % (slug, en, es))
    return en


def extract_faq(block):
    """Pull <!--FAQ q|a--> comments into FAQPage schema and strip them out."""
    pairs = re.findall(r"<!--FAQ\s+(.*?)\s*\|\s*(.*?)\s*-->", block, re.S)
    body = re.sub(r"<!--FAQ.*?-->\n?", "", block, flags=re.S)
    if not pairs:
        return body, ""
    items = []
    for q, a in pairs:
        items.append(
            '\n      { "@type": "Question", "name": "%s",'
            '\n        "acceptedAnswer": { "@type": "Answer", "text": "%s" } }'
            % (esc(q.strip()), esc(a.strip())))
    return body, FAQ_BLOCK.format(items=",".join(items))


# ---------------------------------------------------------------------------

def main():
    if not os.path.isdir(SRC):
        raise SystemExit("missing %s" % SRC)

    total_words = 0
    built = 0
    stats = {}

    for art in ARTICLES:
        path = os.path.join(SRC, art["slug"] + ".html")
        if not os.path.exists(path):
            print("  skip  %-40s (no content file)" % art["slug"])
            continue

        raw = io.open(path, encoding="utf-8").read()
        body, faq = extract_faq(raw)
        spans = check_wellformed(body, art["slug"])

        words = english_words(body)
        read = max(1, int(round(words / float(WPM))))
        total_words += words

        p = PILLARS[art["pillar"]]

        # Related: siblings in the same pillar first, then anything else.
        sibs = [a for a in ARTICLES
                if a["slug"] != art["slug"] and a["pillar"] == art["pillar"]]
        others = [a for a in ARTICLES
                  if a["slug"] != art["slug"] and a["pillar"] != art["pillar"]]
        picks = (sibs + others)[:3]
        related = "\n".join(RELATED_CARD.format(**o) for o in picks)

        meta = META.format(
            base=BASE, words=words, read=read, faq=faq,
            author_json=AUTHOR.person_schema(),
            title_esc=esc(art["title_en"]),
            pillar_name=p["name_en"], pillar_url=p["url"],
            **art)

        page = BODY.format(
            body=indent(body), related=related,
            byline=AUTHOR.byline_html(),
            read=read, accent=p["accent"],
            pillar_url=p["url"],
            pillar_name=p["name_en"], pillar_name_es=p["name_es"],
            pillar_blurb=p["blurb_en"], pillar_blurb_es=p["blurb_es"],
            **art)

        io.open(os.path.join(OUT, art["slug"] + ".meta.html"), "w",
                encoding="utf-8").write(meta)
        io.open(os.path.join(OUT, art["slug"] + ".body.html"), "w",
                encoding="utf-8").write(page)

        faq_n = faq.count('"@type": "Question"')
        stats[art["slug"]] = {"words": words, "read": read, "faq": faq_n}
        print("  %-40s %5d words  %2d min  %2d spans  %d FAQ  [%s]"
              % (art["slug"], words, read, spans, faq_n, art["pillar"]))
        built += 1

    print("\n  %d articles, %d English words total (avg %d)"
          % (built, total_words, total_words // max(1, built)))

    write_index(stats)


# ---------------------------------------------------------------------------
# Blog index — generated from the same manifest so it cannot drift
# ---------------------------------------------------------------------------

INDEX_CARD = u"""          <article class="ax-card ax-card-top p-7" style="--ax-accent:linear-gradient(90deg,{accent},#A855F7)">
            <div class="flex flex-wrap items-center gap-3 mb-3">
              <span class="ax-pill ax-pill-cyan">
                <span data-lang-en>{cat_en}</span><span data-lang-es>{cat_es}</span>
              </span>
              <span class="text-xs text-ax-ink/40">
                <time datetime="{date}">
                  <span data-lang-en>{date_en}</span><span data-lang-es>{date_es}</span>
                </time>
                &middot; <span data-lang-en>{read} min read</span><span data-lang-es>{read} min de lectura</span>
              </span>
            </div>
            <h2 class="font-heading font-bold text-2xl leading-snug mb-3">
              <a href="{slug}.html" class="hover:text-ax-blue transition-colors">
                <span data-lang-en>{title_en}</span>
                <span data-lang-es>{title_es}</span>
              </a>
            </h2>
            <p class="text-ax-ink/60 leading-relaxed mb-4">
              <span data-lang-en>{desc_en}</span>
              <span data-lang-es>{desc_es}</span>
            </p>
            <a href="{slug}.html" class="inline-flex items-center gap-2 text-sm font-bold text-ax-blue hover:gap-3 transition-all">
              <span data-lang-en>Read article</span><span data-lang-es>Leer art&iacute;culo</span>
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5-5 5M5 12h13"/></svg>
            </a>
          </article>"""

INDEX_PILLAR_ROW = u"""            <a href="{url}" class="flex items-start gap-3 rounded-xl border border-ax-ink/10 p-4 hover:border-ax-blue/40 transition-colors">
              <span class="w-2 h-2 rounded-full mt-2 shrink-0" style="background:{accent}"></span>
              <span>
                <span class="block font-heading font-bold text-sm mb-0.5">
                  <span data-lang-en>{name_en}</span><span data-lang-es>{name_es}</span>
                </span>
                <span class="block text-xs text-ax-ink/50">
                  <span data-lang-en>{n} article{s}</span><span data-lang-es>{n} art&iacute;culo{s}</span>
                </span>
              </span>
            </a>"""


def write_index(stats):
    """Emit _build/pages/blog.body.html and the Blog JSON-LD for blog.meta.html."""
    cards, posts = [], []
    counts = {}

    for art in ARTICLES:
        if art["slug"] not in stats:
            continue
        p = PILLARS[art["pillar"]]
        counts[art["pillar"]] = counts.get(art["pillar"], 0) + 1
        cards.append(INDEX_CARD.format(accent=p["accent"],
                                       read=stats[art["slug"]]["read"], **art))
        posts.append(
            '      {\n'
            '        "@type": "BlogPosting",\n'
            '        "headline": "%s",\n'
            '        "url": "%s/%s.html",\n'
            '        "datePublished": "%s",\n'
            '        "articleSection": "%s"\n'
            '      }' % (esc(art["title_en"]), BASE, art["slug"],
                         art["date"], art["cat_en"]))

    rows = []
    for key, p in PILLARS.items():
        n = counts.get(key, 0)
        if n:
            rows.append(INDEX_PILLAR_ROW.format(
                url=p["url"], accent=p["accent"],
                name_en=p["name_en"], name_es=p["name_es"],
                n=n, s="" if n == 1 else "s"))

    body = io.open(os.path.join(SRC, "_index.template.html"),
                   encoding="utf-8").read()
    body = body.replace("{{CARDS}}", "\n\n".join(cards))
    body = body.replace("{{PILLARS}}", "\n".join(rows))
    body = body.replace("{{COUNT}}", str(len(cards)))
    io.open(os.path.join(OUT, "blog.body.html"), "w", encoding="utf-8").write(body)

    meta = io.open(os.path.join(SRC, "_index.meta.template.html"),
                   encoding="utf-8").read()
    meta = meta.replace("{{POSTS}}", ",\n".join(posts))
    io.open(os.path.join(OUT, "blog.meta.html"), "w", encoding="utf-8").write(meta)

    print("  blog index: %d cards, %d pillar rows" % (len(cards), len(rows)))


if __name__ == "__main__":
    main()
