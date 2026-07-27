# -*- coding: utf-8 -*-
"""
Split the bilingual build into two single-language URL trees.

THE PROBLEM THIS SOLVES
-----------------------
Until now every page carried both languages in one document, with Spanish
hidden by CSS and revealed by a localStorage toggle. That works for a human who
clicks the switch and is worthless for search:

  * one URL can only have one canonical language, so Spanish could never rank;
  * hreflang requires distinct URLs, so none could be declared;
  * CSS-hidden content is discounted regardless;
  * every page shipped roughly twice the bytes it needed.

Around ten thousand words of Spanish were returning nothing.

WHAT THIS DOES
--------------
Post-processes the build output into two trees:

    /<slug>.html      English only  — Spanish spans removed
    /es/<slug>.html   Spanish only  — English spans removed

Each page then declares one language, carries a self-referencing canonical, and
carries reciprocal hreflang for both languages plus x-default. The language
control becomes a real link between the two URLs rather than a client-side
class toggle, which is what makes the pair discoverable.

Span removal is nesting-aware: several strings wrap inner markup, for example
`<span data-lang-en>Agentic AI that <span class="ax-spectrum-text">survives
review</span>.</span>`, so a non-greedy regex would cut at the wrong tag.

RUN ORDER
---------
Always after _build/scripts/build.sh, which regenerates the bilingual sources this
consumes. _build/scripts/all.sh enforces that.

Usage: python _build/scripts/make-i18n.py
"""
import io
import os
import re
import shutil

BASE = "https://www.axionalytics.com"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ES_DIR = os.path.join(ROOT, "es")

# Redirect stubs are noindex and language-neutral; they stay single-copy.
SKIP = {"datatransformation.html", "aitransformation.html",
        "training.html", "successstories.html"}

# Spanish page titles are derived from the ES copy already in the document
# where possible; these cover the <title> and description, which have no
# data-lang spans to draw from.
ES_META = {
    "index.html": (
        u"Axionalytics | IA Agéntica que Sobrevive a la Revisión de Seguridad Empresarial",
        u"Axionalytics construye IA agéntica en producción para organizaciones Fortune 500 de ingeniería, datos e ingresos. Desplegada dentro de su VPC, gobernada por aprobación humana, trazable hasta la llamada que produjo cada afirmación."),
    "solutions.html": (
        u"Soluciones | Sistemas de IA Agéntica Empresarial | Axionalytics",
        u"Tres plataformas entregadas y la capa de gobernanza debajo: ingeniería de pruebas agéntica, flujos autónomos empresariales, inteligencia de negocios agéntica y gobernanza de confianza cero."),
    "agentic-test-engineering.html": (
        u"Ingeniería de Pruebas Agéntica | De Requisitos y Código a Casos Verificados | Axionalytics",
        u"Convierta especificaciones, repositorios y PRs fusionados en casos de prueba revisados y trazables — y adapte miles de pruebas heredadas a una estructura consistente."),
    "enterprise-agentic-ai.html": (
        u"IA Agéntica Empresarial | Agentes Autónomos Dentro de su VPC | Axionalytics",
        u"Agentes autónomos multi-paso desplegados dentro de su propio perímetro. Aislamiento por hardware, aprobación humana en cada escritura y procedencia de citas determinista."),
    "agentic-business-intelligence.html": (
        u"Inteligencia de Negocios Agéntica | De Lenguaje Natural a Power BI | Axionalytics",
        u"Una frase y una fuente gobernada producen un artefacto real de Power BI — modelo semántico, medidas DAX, visuales y diseños — en 30 a 90 segundos."),
    "enterprise-ai-security.html": (
        u"Gobernanza de IA de Confianza Cero | Arquitectura de Seguridad | Axionalytics",
        u"La topología de despliegue, el aislamiento, la integración de identidad y la arquitectura de auditoría que hacen pasar la IA agéntica por la revisión de seguridad Fortune 500."),
    "roi-calculator.html": (
        u"Calculadora de ROI para IA Empresarial | Modele el Caso de Negocio | Axionalytics",
        u"Modele capacidad de ingeniería recuperada, recuperación de costos anualizada y periodo de retorno. Corre completamente en su navegador — nada se transmite mientras modela."),
    "case-studies.html": (
        u"Casos de Éxito | Despliegues de IA Agéntica Fortune 500 | Axionalytics",
        u"Tres despliegues Fortune 500 anonimizados: generación de pruebas de verificación, flujos de ingresos autónomos e inteligencia de negocios a escala empresarial."),
    "about.html": (
        u"Nosotros | Por Qué Construimos en Lugar de Aconsejar | Axionalytics",
        u"Una firma de ingeniería pequeña en Davenport, Iowa que entrega IA agéntica en producción para organizaciones Fortune 500. Sin pirámide de entrega, sin cajas negras, con transferencia completa del código."),
    "contact.html": (
        u"Contacto | Agende una Sesión Técnica | Axionalytics",
        u"Cuarenta y cinco minutos con los ingenieros que construyen los sistemas, no con un equipo comercial. Envíe su cuestionario de seguridad o agende directamente."),
    "blog.html": (
        u"Blog | Arquitectura, Seguridad y Analítica de IA Empresarial | Axionalytics",
        u"Escritos sobre las decisiones de arquitectura que determinan si la IA empresarial llega a producción: topología de despliegue, aislamiento, puertas de aprobación y procedencia de datos."),
    "glossary.html": (
        u"Glosario de IA Empresarial | Definiciones Claras | Axionalytics",
        u"Definiciones directas de los términos que aparecen en la compra y la revisión de seguridad de IA empresarial — IA agéntica, BYOC, aprobación humana, inyección de prompts y más."),
    "pricing.html": (
        u"Precios y Modelo de Trabajo | Qué Cuesta un Proyecto de IA Empresarial | Axionalytics",
        u"Proyectos de alcance fijo, no por horas. Qué cuesta cada fase, qué incluye, qué mueve la cifra y qué recibe usted al terminar."),
    "privacy.html": (u"Política de Privacidad | Axionalytics",
                     u"Cómo Axionalytics recopila, usa, divulga y protege su información."),
    "terms.html": (u"Términos y Condiciones | Axionalytics",
                   u"Los términos que rigen el uso del sitio web y los servicios de Axionalytics."),
    "accessibility.html": (u"Declaración de Accesibilidad | Axionalytics",
                           u"El compromiso de Axionalytics con la accesibilidad web y los ajustes implementados en este sitio."),
}


# ---------------------------------------------------------------------------
# Nesting-aware span surgery
# ---------------------------------------------------------------------------

OPEN_RE = re.compile(r'<span\s+data-lang-(en|es)\s*>', re.I)


def transform_spans(html, keep):
    """Unwrap `keep`-language spans, delete the other language entirely.

    Walks the document once, tracking span depth from each match so nested
    markup inside a translated string survives intact.
    """
    out = []
    i = 0
    while True:
        m = OPEN_RE.search(html, i)
        if not m:
            out.append(html[i:])
            break

        out.append(html[i:m.start()])
        lang = m.group(1).lower()

        # Find the </span> that closes this one.
        depth = 1
        j = m.end()
        while depth:
            nxt = re.search(r'<span\b|</span>', html[j:], re.I)
            if not nxt:
                raise SystemExit("unbalanced <span> near offset %d" % m.start())
            tok = html[j + nxt.start(): j + nxt.end()]
            depth += -1 if tok.lower().startswith("</") else 1
            j += nxt.end()

        inner = html[m.end(): j - len("</span>")]
        if lang == keep:
            out.append(inner)
        i = j

    return "".join(out)


DIV_OPEN_RE = re.compile(r'<div\s+data-lang-(en|es)\b([^>]*)>', re.I)


def transform_divs(html, keep):
    """Same treatment for block-level containers.

    The legal pages wrap each language in `<div data-lang-XX class="ax-prose">`
    rather than per-string spans. The container carries layout classes, so the
    kept language keeps its div minus the language attribute; the other
    language's div is removed whole.
    """
    out = []
    i = 0
    while True:
        m = DIV_OPEN_RE.search(html, i)
        if not m:
            out.append(html[i:])
            break

        out.append(html[i:m.start()])
        lang, rest = m.group(1).lower(), m.group(2)

        depth = 1
        j = m.end()
        while depth:
            nxt = re.search(r'<div\b|</div>', html[j:], re.I)
            if not nxt:
                raise SystemExit("unbalanced <div> near offset %d" % m.start())
            tok = html[j + nxt.start(): j + nxt.end()]
            depth += -1 if tok.lower().startswith("</") else 1
            j += nxt.end()

        if lang == keep:
            inner = html[m.end(): j - len("</div>")]
            out.append("<div%s>%s</div>" % (rest, inner))
        i = j

    return "".join(out)


# ---------------------------------------------------------------------------
# Head rewriting
# ---------------------------------------------------------------------------

def alternates(slug, depth):
    """Reciprocal hreflang block. x-default points at English."""
    en = BASE + "/" + ("" if slug == "index.html" else slug)
    es = BASE + "/es/" + ("" if slug == "index.html" else slug)
    return (
        '  <link rel="alternate" hreflang="en" href="%s">\n'
        '  <link rel="alternate" hreflang="es" href="%s">\n'
        '  <link rel="alternate" hreflang="x-default" href="%s">\n' % (en, es, en))


def set_canonical(html, url):
    if re.search(r'<link rel="canonical"[^>]*>', html):
        return re.sub(r'<link rel="canonical"[^>]*>',
                      '<link rel="canonical" href="%s">' % url, html, count=1)
    return html.replace("</head>", '  <link rel="canonical" href="%s">\n</head>' % url)


def inject_alternates(html, block):
    html = re.sub(r'\n?\s*<link rel="alternate" hreflang="[^"]*"[^>]*>', "", html)
    return html.replace("</head>", block + "</head>", 1)


# ---------------------------------------------------------------------------
# Language control: a link between the two URLs, not a class toggle
# ---------------------------------------------------------------------------

DESKTOP_BTN = re.compile(
    r'<button data-lang-toggle[^>]*>.*?</button>', re.S)
MOBILE_BTN = re.compile(
    r'<button data-lang-toggle[^>]*class="w-full[^>]*>.*?</button>', re.S)

GLOBE = ('<svg class="w-4 h-4 opacity-70" fill="none" stroke="currentColor" '
         'stroke-width="2" viewBox="0 0 24 24" aria-hidden="true">'
         '<circle cx="12" cy="12" r="9"/>'
         '<path d="M3 12h18M12 3c2.5 2.7 2.5 15.3 0 18M12 3c-2.5 2.7-2.5 15.3 0 18"/></svg>')


def swap_toggles(html, slug, to_lang):
    """Replace both toggle buttons with anchors to the counterpart URL."""
    href = ("es/" + slug) if to_lang == "es" else ("../" + slug)
    label = "Español" if to_lang == "es" else "English"
    code = "ES" if to_lang == "es" else "EN"
    aria = ("Ver esta página en español" if to_lang == "es"
            else "View this page in English")

    def desktop(_m):
        return ('<a href="%s" hreflang="%s" aria-label="%s" '
                'class="flex items-center gap-1.5 text-xs font-bold text-white/70 '
                'hover:text-white transition-colors px-2.5 py-2 rounded-lg hover:bg-white/5">'
                '%s<span>%s</span></a>' % (href, to_lang, aria, GLOBE, code))

    def mobile(_m):
        return ('<a href="%s" hreflang="%s" aria-label="%s" '
                'class="w-full flex items-center justify-center gap-2 text-sm '
                'font-semibold text-white/80 border border-white/15 rounded-xl '
                'py-3 mb-3 hover:bg-white/5 transition-colors">'
                '%s<span>%s</span></a>' % (href, to_lang, aria, GLOBE, label))

    html = MOBILE_BTN.sub(mobile, html, count=1)
    html = DESKTOP_BTN.sub(desktop, html)
    return html


# ---------------------------------------------------------------------------

def depth_fix(html):
    """Rewrite root-relative-ish asset paths for pages one directory down."""
    for attr in ("src", "href"):
        html = re.sub(r'%s="(assets/[^"]+)"' % attr, r'%s="../\1"' % attr, html)
    html = html.replace('src="logo_fixed.png"', 'src="../logo_fixed.png"')
    html = html.replace('href="logo_fixed.png"', 'href="../logo_fixed.png"')
    return html


def main():
    pages = sorted(f for f in os.listdir(ROOT)
                   if f.endswith(".html") and f not in SKIP
                   and os.path.isfile(os.path.join(ROOT, f)))

    en_bytes = es_bytes = 0

    # This script consumes the bilingual build and overwrites the root pages
    # with English-only output. Running it twice without an intervening
    # build.sh would therefore feed it its own output, and the second pass
    # would emit an English "Spanish" tree — silently, because every other
    # check still passes. Refuse instead.
    unsplit = [f for f in pages
               if "data-lang-" in io.open(os.path.join(ROOT, f), encoding="utf-8").read()]
    if len(unsplit) != len(pages):
        already = sorted(set(pages) - set(unsplit))
        raise SystemExit(
            "refusing to run: %d page(s) carry no data-lang spans, so they have\n"
            "already been split: %s\n"
            "Run 'bash _build/scripts/build.sh' first to regenerate the bilingual source,\n"
            "or just use 'bash _build/scripts/all.sh', which sequences this correctly."
            % (len(already), ", ".join(already[:6]) + ("..." if len(already) > 6 else "")))

    # Safe to destroy the previous tree only now that the input is known good.
    if os.path.isdir(ES_DIR):
        shutil.rmtree(ES_DIR)
    os.makedirs(ES_DIR)

    for slug in pages:
        src = io.open(os.path.join(ROOT, slug), encoding="utf-8").read()
        block = alternates(slug, 0)

        # ---- English tree -------------------------------------------------
        en = transform_divs(transform_spans(src, keep="en"), keep="en")
        en = swap_toggles(en, slug, to_lang="es")
        en = set_canonical(en, BASE + "/" + ("" if slug == "index.html" else slug))
        en = inject_alternates(en, block)
        en = en.replace("Bilingual: every string carries data-lang-en / data-lang-es.",
                        "Language: English. The Spanish tree lives at /es/ with reciprocal hreflang.")
        io.open(os.path.join(ROOT, slug), "w", encoding="utf-8").write(en)
        en_bytes += len(en.encode("utf-8"))

        # ---- Spanish tree -------------------------------------------------
        es = transform_divs(transform_spans(src, keep="es"), keep="es")
        es = swap_toggles(es, slug, to_lang="en")
        es = depth_fix(es)
        es = set_canonical(es, BASE + "/es/" + ("" if slug == "index.html" else slug))
        es = inject_alternates(es, block)
        es = es.replace('<html lang="en">', '<html lang="es">', 1)
        es = es.replace("Bilingual: every string carries data-lang-en / data-lang-es.",
                        "Language: Spanish. Generated from the English tree by _build/scripts/make-i18n.py.")

        if slug in ES_META:
            title, desc = ES_META[slug]
            es = re.sub(r"<title>.*?</title>", "<title>%s</title>" % title, es, count=1, flags=re.S)
            es = re.sub(r'<meta name="description" content="[^"]*">',
                        '<meta name="description" content="%s">' % desc, es, count=1)
            es = re.sub(r'<meta property="og:title" content="[^"]*">',
                        '<meta property="og:title" content="%s">' % title, es, count=1)
            es = re.sub(r'<meta property="og:description" content="[^"]*">',
                        '<meta property="og:description" content="%s">' % desc, es, count=1)
        es = re.sub(r'<meta property="og:url" content="%s/([^"]*)">' % re.escape(BASE),
                    r'<meta property="og:url" content="%s/es/\1">' % BASE, es, count=1)

        io.open(os.path.join(ES_DIR, slug), "w", encoding="utf-8").write(es)
        es_bytes += len(es.encode("utf-8"))

        print("  %-44s en %5.1f KB   es %5.1f KB"
              % (slug, len(en.encode("utf-8")) / 1024.0, len(es.encode("utf-8")) / 1024.0))

    print("\n  %d pages per tree" % len(pages))
    print("  English tree: %.0f KB    Spanish tree: %.0f KB"
          % (en_bytes / 1024.0, es_bytes / 1024.0))


if __name__ == "__main__":
    main()
