# -*- coding: utf-8 -*-
"""
Generate the glossary hub and its definition pages.

WHY THESE PAGES EXIST
---------------------
"What is X" queries are the highest-volume entry point in this category and the
ones answer engines quote most readily. A definition page that opens with a
direct 40-60 word answer, carries DefinedTerm schema, and links onward to the
commercial pillar is the cheapest qualified traffic available — the reader is
early-stage by definition, and the link up the cluster is what moves them.

Each term is deliberately mapped to a pillar so the glossary feeds the same
four commercial pages the blog does, rather than becoming an orphan wing.

STRUCTURE
---------
    _build/src/glossary/<slug>.html   bilingual body prose (.ax-prose markup)
    TERMS (below)                 definition, metadata, parent pillar
    this script                   wraps in shared chrome, emits hub + pages

Usage: python _build/scripts/make-glossary.py
"""
import io
import os
import re
import importlib.util

BASE = "https://www.axionalytics.com"
SRC = "_build/src/glossary"
OUT = "_build/pages"


def pillars():
    spec = importlib.util.spec_from_file_location("ma", "_build/scripts/make-articles.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.PILLARS


# `answer` is the BLUF definition: it appears verbatim as the lead paragraph,
# in the meta description, and in DefinedTerm.description. Keep it 40-60 words
# and self-contained — it is written to be quoted out of context.
TERMS = [
    {
        "slug": "what-is-agentic-ai",
        "term_en": "Agentic AI", "term_es": "IA Agéntica",
        "pillar": "agentic",
        "title_en": "What Is Agentic AI?", "title_es": "¿Qué Es la IA Agéntica?",
        "answer_en": "Agentic AI describes a system where a language model plans and executes a multi-step task using tools, rather than only producing text. It decides which action to take next, calls the tool, observes the result, and repeats until the task is done or a control stops it.",
        "answer_es": "La IA agéntica describe un sistema donde un modelo de lenguaje planifica y ejecuta una tarea de varios pasos usando herramientas, en lugar de solo producir texto. Decide qué acción tomar, llama a la herramienta, observa el resultado y repite hasta terminar o hasta que un control lo detenga.",
    },
    {
        "slug": "what-is-byoc",
        "term_en": "BYOC (Bring Your Own Cloud)", "term_es": "BYOC (Nube Propia)",
        "pillar": "security",
        "title_en": "What Is BYOC Deployment?", "title_es": "¿Qué Es el Despliegue BYOC?",
        "answer_en": "Bring-your-own-cloud is a deployment model where the vendor's software runs inside the customer's own cloud account rather than the vendor's. The vendor operates a control plane that orchestrates work and holds no customer data, while the component that touches customer systems runs entirely within the customer's perimeter.",
        "answer_es": "La nube propia es un modelo de despliegue donde el software del proveedor corre dentro de la cuenta de nube del cliente y no en la del proveedor. El proveedor opera un plano de control que orquesta el trabajo sin retener datos, mientras el componente que toca los sistemas del cliente corre dentro de su perímetro.",
    },
    {
        "slug": "what-is-human-in-the-loop",
        "term_en": "Human-in-the-Loop (HITL)", "term_es": "Aprobación Humana (HITL)",
        "pillar": "agentic",
        "title_en": "What Is Human-in-the-Loop AI?", "title_es": "¿Qué Es la IA con Aprobación Humana?",
        "answer_en": "Human-in-the-loop means an automated system pauses at a defined point and requires a person to approve before it proceeds. In an agentic system the gate sits on write actions: reads run freely, while anything that modifies a record stops and shows the reviewer what would change before it commits.",
        "answer_es": "La aprobación humana significa que un sistema automatizado se detiene en un punto definido y requiere que una persona apruebe antes de continuar. En un sistema agéntico la puerta está en las escrituras: las lecturas fluyen, y todo lo que modifica un registro se detiene y muestra al revisor qué cambiaría antes de confirmar.",
    },
    {
        "slug": "what-is-prompt-injection",
        "term_en": "Prompt Injection", "term_es": "Inyección de Prompts",
        "pillar": "security",
        "title_en": "What Is Prompt Injection?", "title_es": "¿Qué Es la Inyección de Prompts?",
        "answer_en": "Prompt injection is an attack where instructions are hidden inside content a language model processes — a document, a database field, a tool description — and the model treats them as direction rather than data. In agentic systems it matters more than in chatbots, because the model holds tools and the attack redirects actions.",
        "answer_es": "La inyección de prompts es un ataque donde se ocultan instrucciones dentro del contenido que procesa un modelo — un documento, un campo de base de datos, la descripción de una herramienta — y el modelo las trata como órdenes y no como datos. En sistemas agénticos importa más que en chatbots, porque el modelo tiene herramientas y el ataque redirige acciones.",
    },
    {
        "slug": "what-is-email-deliverability",
        "term_en": "Email Deliverability", "term_es": "Entregabilidad de Correo",
        "pillar": "revenue",
        "title_en": "What Is Email Deliverability?", "title_es": "¿Qué Es la Entregabilidad de Correo?",
        "answer_en": "Email deliverability is whether a message reaches the inbox rather than the spam folder. It is decided mainly by the sending domain's reputation, which is spent by bounces and spam complaints — so it is a property of sender behaviour over time, not of any individual message.",
        "answer_es": "La entregabilidad de correo es si un mensaje llega a la bandeja de entrada en lugar de la de spam. La decide sobre todo la reputación del dominio remitente, que se gasta con rebotes y quejas — así que es una propiedad del comportamiento del remitente en el tiempo, no de un mensaje individual.",
    },
    {
        "slug": "what-is-a-semantic-layer",
        "term_en": "Semantic Layer", "term_es": "Capa Semántica",
        "pillar": "bi",
        "title_en": "What Is a Semantic Layer?", "title_es": "¿Qué Es una Capa Semántica?",
        "answer_en": "A semantic layer is where a business metric is defined once, in a form that can be inspected, versioned, and secured, so every report that references it inherits the same definition. It is what prevents four departments from each maintaining their own incompatible version of revenue.",
        "answer_es": "Una capa semántica es donde una métrica de negocio se define una sola vez, de forma inspeccionable, versionable y protegible, para que todo informe que la referencia herede la misma definición. Es lo que evita que cuatro departamentos mantengan cada uno su propia versión incompatible de los ingresos.",
    },
    {
        "slug": "what-is-requirements-traceability",
        "term_en": "Requirements Traceability", "term_es": "Trazabilidad de Requisitos",
        "pillar": "testing",
        "title_en": "What Is Requirements Traceability?", "title_es": "¿Qué Es la Trazabilidad de Requisitos?",
        "answer_en": "Requirements traceability is the recorded link between a requirement and the test cases that verify it, in both directions. Forward traceability answers which tests verify a requirement; backward traceability answers which requirement justifies a test, and is what identifies cases that outlived their justification.",
        "answer_es": "La trazabilidad de requisitos es el vínculo registrado entre un requisito y los casos de prueba que lo verifican, en ambas direcciones. La trazabilidad directa responde qué pruebas verifican un requisito; la inversa responde qué requisito justifica una prueba, e identifica casos que sobrevivieron a su justificación.",
    },
]


META = u"""
  <title>{title_en} | Axionalytics Glossary</title>
  <meta name="description" content="{answer_short}">
  <link rel="canonical" href="{base}/{slug}.html">
  <meta property="og:title" content="{title_en}">
  <meta property="og:description" content="{answer_short}">
  <meta property="og:url" content="{base}/{slug}.html">

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "DefinedTerm",
    "@id": "{base}/{slug}.html#term",
    "name": "{term_en}",
    "description": "{answer_esc}",
    "inDefinedTermSet": {{
      "@type": "DefinedTermSet",
      "name": "Axionalytics Enterprise AI Glossary",
      "url": "{base}/glossary.html"
    }},
    "subjectOf": {{ "@type": "WebPage", "url": "{base}/{slug}.html" }}
  }}
  </script>

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {{
        "@type": "Question",
        "name": "{title_esc}",
        "acceptedAnswer": {{ "@type": "Answer", "text": "{answer_esc}" }}
      }}
    ]
  }}
  </script>

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{ "@type": "ListItem", "position": 1, "name": "Home", "item": "{base}/" }},
      {{ "@type": "ListItem", "position": 2, "name": "Glossary", "item": "{base}/glossary.html" }},
      {{ "@type": "ListItem", "position": 3, "name": "{term_esc}", "item": "{base}/{slug}.html" }}
    ]
  }}
  </script>
"""

BODY = u"""
<!-- ==========================================================================
     GLOSSARY TERM — generated by _build/scripts/make-glossary.py
     ========================================================================== -->
<section class="ax-hero ax-noise relative pt-36 pb-14 lg:pt-44 lg:pb-16 overflow-hidden">
  <div class="ax-grid-bg"></div>
  <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 relative">

    <nav class="flex items-center gap-2 text-xs font-semibold text-white/35 mb-8 ax-reveal" aria-label="Breadcrumb">
      <a href="index.html" class="hover:text-ax-cyan transition-colors">
        <span data-lang-en>Home</span><span data-lang-es>Inicio</span>
      </a>
      <span>/</span>
      <a href="glossary.html" class="hover:text-ax-cyan transition-colors">
        <span data-lang-en>Glossary</span><span data-lang-es>Glosario</span>
      </a>
      <span>/</span>
      <span class="text-white/60">{term_en}</span>
    </nav>

    <span class="ax-pill ax-pill-dark mb-6 ax-reveal">
      <span class="w-1.5 h-1.5 rounded-full" style="background:{accent}"></span>
      <span data-lang-en>Definition</span><span data-lang-es>Definici&oacute;n</span>
    </span>

    <h1 class="font-heading font-extrabold text-white text-[2.1rem] sm:text-4xl lg:text-[2.9rem] leading-[1.08] mb-6 ax-reveal">
      <span data-lang-en>{title_en}</span>
      <span data-lang-es>{title_es}</span>
    </h1>
  </div>
</section>

<!-- The direct answer is the first thing on the page, in its own block, so an
     answer engine can lift it cleanly. -->
<section class="bg-white pt-12 lg:pt-16">
  <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="rounded-2xl border-l-4 border-ax-cyan bg-ax-mist p-7 lg:p-8 ax-reveal">
      <p class="text-lg lg:text-xl leading-relaxed font-medium">
        <span data-lang-en>{answer_en}</span>
        <span data-lang-es>{answer_es}</span>
      </p>
    </div>
  </div>
</section>

<article class="pb-16 lg:pb-20 bg-white">
  <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="ax-prose pt-12">
{body}
    </div>

    <aside class="mt-14 rounded-2xl border border-ax-ink/10 bg-ax-mist p-7">
      <p class="ax-label text-ax-ink/40 mb-3">
        <span data-lang-en>Related solution</span><span data-lang-es>Soluci&oacute;n relacionada</span>
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
        <span data-lang-en>How it works</span><span data-lang-es>C&oacute;mo funciona</span>
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5-5 5M5 12h13"/></svg>
      </a>
    </aside>
  </div>
</article>

<section class="ax-band py-16 lg:py-20 relative overflow-hidden">
  <div class="ax-grid-bg opacity-50"></div>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative">
    <p class="ax-eyebrow text-ax-cyan mb-7 ax-reveal">
      <span data-lang-en>More definitions</span><span data-lang-es>M&aacute;s definiciones</span>
    </p>
    <div class="grid sm:grid-cols-3 gap-4 ax-stagger">
{related}
    </div>
  </div>
</section>
"""

RELATED = u"""      <a href="{slug}.html" class="rounded-xl border border-white/10 bg-white/[0.03] p-5 hover:border-ax-cyan/40 hover:bg-white/[0.06] transition-colors">
        <p class="font-heading font-bold text-white leading-snug mb-1">
          <span data-lang-en>{term_en}</span><span data-lang-es>{term_es}</span>
        </p>
        <p class="text-xs text-white/45">
          <span data-lang-en>Definition</span><span data-lang-es>Definici&oacute;n</span>
        </p>
      </a>"""


def esc(s):
    return s.replace('"', '\\"')


def indent(block, n=6):
    pad = " " * n
    lines = [l.rstrip() for l in block.strip("\n").split("\n")]
    w = [len(l) - len(l.lstrip()) for l in lines if l.strip()]
    trim = min(w) if w else 0
    return "\n".join((pad + l[trim:]) if l.strip() else "" for l in lines)


def check(block, slug):
    if re.search(r'data-lang-(?:en|es)"', block):
        raise SystemExit("%s: malformed data-lang attribute" % slug)
    en = len(re.findall(r"<span data-lang-en>", block))
    es = len(re.findall(r"<span data-lang-es>", block))
    if en != es:
        raise SystemExit("%s: parity %d EN vs %d ES" % (slug, en, es))


def main():
    P = pillars()
    built = 0

    for t in TERMS:
        path = os.path.join(SRC, t["slug"] + ".html")
        if not os.path.exists(path):
            print("  skip  %-38s (no content file)" % t["slug"])
            continue
        body = io.open(path, encoding="utf-8").read()
        check(body, t["slug"])

        p = P[t["pillar"]]
        others = [o for o in TERMS if o["slug"] != t["slug"]][:3]
        related = "\n".join(RELATED.format(**o) for o in others)

        short = t["answer_en"]
        if len(short) > 300:
            short = short[:297].rsplit(" ", 1)[0] + "..."

        meta = META.format(base=BASE, answer_short=esc(short),
                           answer_esc=esc(t["answer_en"]),
                           title_esc=esc(t["title_en"]),
                           term_esc=esc(t["term_en"]), **t)
        page = BODY.format(body=indent(body), related=related,
                           accent=p["accent"], pillar_url=p["url"],
                           pillar_name=p["name_en"], pillar_name_es=p["name_es"],
                           pillar_blurb=p["blurb_en"], pillar_blurb_es=p["blurb_es"],
                           **t)

        io.open(os.path.join(OUT, t["slug"] + ".meta.html"), "w", encoding="utf-8").write(meta)
        io.open(os.path.join(OUT, t["slug"] + ".body.html"), "w", encoding="utf-8").write(page)
        print("  %-38s -> %s" % (t["slug"], p["name_en"]))
        built += 1

    write_hub(P)
    print("\n  %d term pages + hub" % built)


HUB_CARD = u"""          <a href="{slug}.html" class="ax-card ax-card-top p-6 block" style="--ax-accent:linear-gradient(90deg,{accent},#A855F7)">
            <h2 class="font-heading font-bold text-xl mb-2.5">
              <span data-lang-en>{term_en}</span><span data-lang-es>{term_es}</span>
            </h2>
            <p class="text-ax-ink/60 leading-relaxed text-[0.95rem] mb-4">
              <span data-lang-en>{answer_trim_en}</span>
              <span data-lang-es>{answer_trim_es}</span>
            </p>
            <span class="inline-flex items-center gap-2 text-sm font-bold text-ax-blue">
              <span data-lang-en>Read the definition</span><span data-lang-es>Leer la definici&oacute;n</span>
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5-5 5M5 12h13"/></svg>
            </span>
          </a>"""


def trim(s, n=150):
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "..."


def write_hub(P):
    cards, terms_json = [], []
    for t in TERMS:
        p = P[t["pillar"]]
        cards.append(HUB_CARD.format(accent=p["accent"],
                                     answer_trim_en=trim(t["answer_en"]),
                                     answer_trim_es=trim(t["answer_es"]), **t))
        terms_json.append(
            '      {\n'
            '        "@type": "DefinedTerm",\n'
            '        "name": "%s",\n'
            '        "description": "%s",\n'
            '        "url": "%s/%s.html"\n'
            '      }' % (esc(t["term_en"]), esc(t["answer_en"]), BASE, t["slug"]))

    meta = io.open(os.path.join(SRC, "_hub.meta.template.html"), encoding="utf-8").read()
    meta = meta.replace("{{TERMS}}", ",\n".join(terms_json))
    io.open(os.path.join(OUT, "glossary.meta.html"), "w", encoding="utf-8").write(meta)

    body = io.open(os.path.join(SRC, "_hub.template.html"), encoding="utf-8").read()
    body = body.replace("{{CARDS}}", "\n\n".join(cards))
    body = body.replace("{{COUNT}}", str(len(TERMS)))
    io.open(os.path.join(OUT, "glossary.body.html"), "w", encoding="utf-8").write(body)


if __name__ == "__main__":
    main()
