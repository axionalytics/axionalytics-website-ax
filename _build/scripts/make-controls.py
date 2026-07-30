# -*- coding: utf-8 -*-
"""
AXIONALYTICS — GOVERNANCE CONTROL MAPPING

Generates ai-governance-control-mapping.{meta,body}.html: every control the
platform actually operates, mapped to the framework clauses it satisfies.

WHY THIS PAGE EXISTS
--------------------
The architecture already answers the questions a security review asks. It has
never answered them *in the vocabulary the reviewer uses*. A CISO does not search
for "eBPF egress filter" — they search for how a system satisfies ISO/IEC 42001,
or which NIST AI RMF function covers autonomous write actions. This page is the
translation layer between what was built and what gets asked.

WHAT IS ASSERTED HERE, AND WHAT IS NOT
--------------------------------------
Every control statement below describes something the platform does and is
already documented elsewhere on this site. The framework mapping is our own
analysis of which requirement each control speaks to.

Three deliberate limits on precision, because a mapping that overstates itself is
worse than no mapping:

  1. ISO/IEC 42001 is a paywalled standard. Its Annex A areas are mapped by name.
     Sub-clause identifiers are NOT asserted — inventing them would be the exact
     false precision this page exists to avoid. A customer holding the standard
     can map to sub-clause; we point at the area and cite the standard.

  2. NIST AI RMF is mapped to its four Core functions, which are public. The
     subcategory identifiers (GOVERN 1.1 and so on) live inside the framework
     PDF and are not restated here from memory.

  3. NIST SP 800-53 is mapped to control families, which are stable and public.

None of this is a certification claim. It is a statement of which controls exist
and which requirements they speak to, published so a reviewer can check it.

Usage: python _build/scripts/make-controls.py
"""
import io
import os

BASE = "https://www.axionalytics.com"
OUT = "_build/pages"
SLUG = "ai-governance-control-mapping"


# ---------------------------------------------------------------------------
# The controls. `evidence` points at the page on this site that documents it,
# so every row in the matrix is checkable rather than asserted.
# ---------------------------------------------------------------------------

CONTROLS = [
    {
        "id": "plane-separation",
        "name_en": "Control and execution plane separation",
        "name_es": "Separación de planos de control y ejecución",
        "stmt_en": "The control plane orchestrates sessions, compiles agents, evaluates policy and collects traces, and holds no customer data at rest. The execution plane runs inside the customer VPC and is the only component that touches customer systems.",
        "stmt_es": "El plano de control orquesta sesiones, compila agentes, evalúa políticas y recoge trazas, y no retiene datos del cliente en reposo. El plano de ejecución corre dentro de la VPC del cliente y es el único componente que toca sus sistemas.",
        "iso": ["A.6 AI system life cycle", "A.10 Third-party and customer relationships"],
        "rmf": ["GOVERN", "MAP"],
        "sp53": ["SC — System and Communications Protection"],
        "owasp": [],
        "evidence": "two-plane-execution-architecture.html",
        "check_en": "Network diagram plus a data-flow review. The claim is falsifiable: name the store where customer records would sit in the control plane.",
        "check_es": "Diagrama de red y revisión del flujo de datos. La afirmación es refutable: señale el almacén donde estarían los registros del cliente en el plano de control.",
    },
    {
        "id": "hypervisor-isolation",
        "name_en": "Hypervisor-level execution isolation",
        "name_es": "Aislamiento de ejecución a nivel de hipervisor",
        "stmt_en": "Agent-generated code executes in a MicroVM with its own kernel. The isolation boundary is the hypervisor rather than a namespace, so a kernel escape lands in an empty virtual machine.",
        "stmt_es": "El código generado por el agente se ejecuta en una MicroVM con su propio kernel. La frontera de aislamiento es el hipervisor y no un espacio de nombres, así que un escape de kernel llega a una máquina virtual vacía.",
        "iso": ["A.6 AI system life cycle"],
        "rmf": ["MANAGE"],
        "sp53": ["SC — System and Communications Protection", "SI — System and Information Integrity"],
        "owasp": ["LLM02 Insecure Output Handling"],
        "evidence": "two-plane-execution-architecture.html",
        "check_en": "Inspect the sandbox from inside: it has its own kernel version, independent of the host.",
        "check_es": "Inspeccione el sandbox desde dentro: tiene su propia versión de kernel, independiente del anfitrión.",
    },
    {
        "id": "egress-denied",
        "name_en": "Egress denied by default",
        "name_es": "Salida denegada por defecto",
        "stmt_en": "Each execution sandbox carries an eBPF network filter and a DNS sinkhole restricting outbound traffic to a customer-defined allowlist. The filter blocks the connection; the sinkhole blocks the resolution that would have produced the address.",
        "stmt_es": "Cada sandbox de ejecución lleva un filtro de red eBPF y un sumidero DNS que restringen el tráfico saliente a una lista definida por el cliente. El filtro bloquea la conexión; el sumidero bloquea la resolución que habría producido la dirección.",
        "iso": ["A.6 AI system life cycle", "A.7 Data for AI systems"],
        "rmf": ["MANAGE"],
        "sp53": ["SC — System and Communications Protection", "AC — Access Control"],
        "owasp": ["LLM06 Sensitive Information Disclosure"],
        "evidence": "two-plane-execution-architecture.html",
        "check_en": "Packet capture from inside the sandbox while attempting an unlisted destination.",
        "check_es": "Captura de paquetes desde dentro del sandbox intentando alcanzar un destino no listado.",
    },
    {
        "id": "tokenization",
        "name_en": "Context-aware tokenization of sensitive data",
        "name_es": "Tokenización contextual de datos sensibles",
        "stmt_en": "Sensitive spans are replaced before transmission and the real values re-injected after the response returns, so the model only ever sees placeholders. Policy is declarative and per-tenant: a category allowlist, custom identifier patterns, and a known-safe denylist to prevent over-tokenization degrading the answer.",
        "stmt_es": "Los fragmentos sensibles se reemplazan antes de la transmisión y los valores reales se reinyectan al volver la respuesta, de modo que el modelo solo ve marcadores. La política es declarativa y por inquilino: lista de categorías, patrones de identificadores propios y lista de exclusión para evitar que la sobre-tokenización degrade la respuesta.",
        "iso": ["A.7 Data for AI systems"],
        "rmf": ["MAP", "MANAGE"],
        "sp53": ["SC — System and Communications Protection", "SI — System and Information Integrity"],
        "owasp": ["LLM06 Sensitive Information Disclosure"],
        "evidence": "enterprise-ai-security.html",
        "check_en": "Inspect the payload leaving the perimeter and confirm the sensitive spans are placeholders.",
        "check_es": "Inspeccione la carga que sale del perímetro y confirme que los fragmentos sensibles son marcadores.",
    },
    {
        "id": "identity-federation",
        "name_en": "Enterprise identity, acting as the user",
        "name_es": "Identidad empresarial, actuando como el usuario",
        "stmt_en": "Ingress is SAML 2.0 or OIDC against Azure AD, Okta, Google, ADFS, or a custom provider. The agent acts under the identity of the person driving it rather than a service account, which is what makes the authorization question answerable.",
        "stmt_es": "El ingreso es SAML 2.0 u OIDC contra Azure AD, Okta, Google, ADFS o un proveedor propio. El agente actúa bajo la identidad de la persona que lo dirige y no de una cuenta de servicio, que es lo que hace que la pregunta de autorización tenga respuesta.",
        "iso": ["A.3 Internal organization", "A.9 Use of AI systems"],
        "rmf": ["GOVERN"],
        "sp53": ["IA — Identification and Authentication", "AC — Access Control"],
        "owasp": ["LLM08 Excessive Agency"],
        "evidence": "enterprise-ai-security.html",
        "check_en": "Revoke a user in the identity provider and confirm their agent sessions lose the corresponding access.",
        "check_es": "Revoque un usuario en el proveedor de identidad y confirme que sus sesiones de agente pierden el acceso correspondiente.",
    },
    {
        "id": "tool-compilation",
        "name_en": "Per-turn tool roster compilation",
        "name_es": "Compilación del catálogo de herramientas por turno",
        "stmt_en": "Available tools are computed as the intersection of platform capability, tenant entitlement and the acting user's role, then compiled into a signed session manifest for that turn. A capability outside the intersection is absent rather than denied.",
        "stmt_es": "Las herramientas disponibles se calculan como la intersección de la capacidad de la plataforma, los derechos del inquilino y el rol del usuario que actúa, y se compilan en un manifiesto de sesión firmado para ese turno. Una capacidad fuera de la intersección está ausente, no denegada.",
        "iso": ["A.6 AI system life cycle", "A.9 Use of AI systems"],
        "rmf": ["GOVERN", "MANAGE"],
        "sp53": ["AC — Access Control", "CM — Configuration Management"],
        "owasp": ["LLM08 Excessive Agency", "LLM07 Insecure Plugin Design"],
        "evidence": "write-gate-architecture.html",
        "check_en": "Compare the compiled manifest for two users in different roles on the same tenant.",
        "check_es": "Compare el manifiesto compilado para dos usuarios con roles distintos en el mismo inquilino.",
    },
    {
        "id": "policy-gate",
        "name_en": "Pre-execution policy validation",
        "name_es": "Validación de política previa a la ejecución",
        "stmt_en": "Every proposed tool call is validated against a policy the model cannot see, read back, or influence. Placing the check outside the model's channel is what turns a successful injection into a failed call rather than an unauthorized action.",
        "stmt_es": "Cada llamada de herramienta propuesta se valida contra una política que el modelo no puede ver, leer ni influir. Colocar la verificación fuera del canal del modelo es lo que convierte una inyección exitosa en una llamada fallida en vez de una acción no autorizada.",
        "iso": ["A.6 AI system life cycle"],
        "rmf": ["MANAGE", "MEASURE"],
        "sp53": ["AC — Access Control", "SI — System and Information Integrity"],
        "owasp": ["LLM01 Prompt Injection", "LLM08 Excessive Agency"],
        "evidence": "write-gate-architecture.html",
        "check_en": "Seed a document with an instruction to call a denied tool and confirm the call is refused, not resolved.",
        "check_es": "Inserte en un documento una instrucción para llamar a una herramienta denegada y confirme que la llamada se rechaza, no se resuelve.",
    },
    {
        "id": "write-gate",
        "name_en": "Human approval on every write, with blast radius shown",
        "name_es": "Aprobación humana en cada escritura, con radio de impacto visible",
        "stmt_en": "Every WRITE action stops at a human gate that renders a diff of exactly what would change and how many records it reaches. The approver sees the field-level change and the count, not a description of the action.",
        "stmt_es": "Toda acción de escritura se detiene en una puerta humana que muestra un diff de exactamente qué cambiaría y a cuántos registros alcanza. El aprobador ve el cambio a nivel de campo y el conteo, no una descripción de la acción.",
        "iso": ["A.9 Use of AI systems", "A.5 Assessing impacts of AI systems"],
        "rmf": ["GOVERN", "MANAGE"],
        "sp53": ["AC — Access Control", "AU — Audit and Accountability"],
        "owasp": ["LLM08 Excessive Agency", "LLM09 Overreliance"],
        "evidence": "write-gate-architecture.html",
        "check_en": "Request a bulk update and confirm the record count is displayed before approval is possible.",
        "check_es": "Solicite una actualización masiva y confirme que el conteo de registros aparece antes de poder aprobar.",
    },
    {
        "id": "replay-protection",
        "name_en": "Approvals pinned against replay",
        "name_es": "Aprobaciones ancladas contra reproducción",
        "stmt_en": "Every approval is pinned to an optimistic-concurrency version token and to the schema it was granted against. If the plan, record or tool definition changes after approval, the write is refused rather than retried against the new state.",
        "stmt_es": "Cada aprobación se ancla a un token de versión de concurrencia optimista y al esquema contra el que se concedió. Si el plan, el registro o la definición de herramienta cambian después, la escritura se rechaza en lugar de reintentarse contra el nuevo estado.",
        "iso": ["A.6 AI system life cycle", "A.9 Use of AI systems"],
        "rmf": ["MANAGE"],
        "sp53": ["AU — Audit and Accountability", "SI — System and Information Integrity"],
        "owasp": ["LLM08 Excessive Agency"],
        "evidence": "write-gate-architecture.html",
        "check_en": "Approve a write, modify the underlying record from another session, then release the approval.",
        "check_es": "Apruebe una escritura, modifique el registro subyacente desde otra sesión y luego libere la aprobación.",
    },
    {
        "id": "citation-provenance",
        "name_en": "Deterministic citation provenance",
        "name_es": "Procedencia determinista de citas",
        "stmt_en": "Citations are generated by the backend from the tool-call record, never by the model. Markers the model invents are stripped before rendering, so every marker in delivered text resolves to a real call and its result set.",
        "stmt_es": "Las citas las genera el backend desde el registro de llamadas, nunca el modelo. Los marcadores que el modelo inventa se eliminan antes de renderizar, así que cada marcador en el texto entregado resuelve a una llamada real y su conjunto de resultados.",
        "iso": ["A.6 AI system life cycle", "A.8 Information for interested parties"],
        "rmf": ["MEASURE", "MANAGE"],
        "sp53": ["AU — Audit and Accountability"],
        "owasp": ["LLM09 Overreliance", "LLM02 Insecure Output Handling"],
        "evidence": "citation-provenance-architecture.html",
        "check_en": "Open any citation in a delivered answer and confirm it resolves to a logged call with arguments.",
        "check_es": "Abra cualquier cita de una respuesta entregada y confirme que resuelve a una llamada registrada con sus argumentos.",
    },
    {
        "id": "grounding-critic",
        "name_en": "Grounding critic ahead of human review",
        "name_es": "Crítico de fundamentación antes de la revisión humana",
        "stmt_en": "Output referencing an entity absent from the index is rejected before a reviewer sees it. Filtering ahead of the queue protects reviewer attention, which degrades measurably once a queue starts carrying plausible-but-ungrounded items.",
        "stmt_es": "La salida que referencia una entidad ausente del índice se rechaza antes de que un revisor la vea. Filtrar antes de la cola protege la atención del revisor, que se degrada de forma medible cuando una cola empieza a llevar elementos plausibles pero infundados.",
        "iso": ["A.6 AI system life cycle"],
        "rmf": ["MEASURE"],
        "sp53": ["SI — System and Information Integrity"],
        "owasp": ["LLM09 Overreliance"],
        "evidence": "citation-provenance-architecture.html",
        "check_en": "Ask for output about an entity you know is not indexed and confirm rejection rather than invention.",
        "check_es": "Pida salida sobre una entidad que sepa que no está indexada y confirme el rechazo en lugar de la invención.",
    },
    {
        "id": "distributed-trace",
        "name_en": "End-to-end distributed trace across both planes",
        "name_es": "Traza distribuida extremo a extremo en ambos planos",
        "stmt_en": "W3C trace context propagates across the plane boundary, so an auditor can reconstruct which turn triggered which call with which arguments, what it returned, which citation points at it, and who approved the resulting write against which version.",
        "stmt_es": "El contexto de traza W3C se propaga a través de la frontera entre planos, de modo que un auditor puede reconstruir qué turno disparó qué llamada con qué argumentos, qué devolvió, qué cita apunta a ella y quién aprobó la escritura resultante contra qué versión.",
        "iso": ["A.6 AI system life cycle", "A.8 Information for interested parties"],
        "rmf": ["MEASURE", "GOVERN"],
        "sp53": ["AU — Audit and Accountability"],
        "owasp": [],
        "evidence": "write-gate-architecture.html",
        "check_en": "Pick a write from six months ago and reconstruct the full chain from it.",
        "check_es": "Elija una escritura de hace seis meses y reconstruya la cadena completa a partir de ella.",
    },
]


# ---------------------------------------------------------------------------
# Frequently asked, in the reviewer's own words.
# ---------------------------------------------------------------------------

FAQS = [
    ("Is Axionalytics certified to ISO/IEC 42001?",
     "No, and this page does not claim otherwise. It maps the controls the platform "
     "operates to the requirement areas each one speaks to, so that an organization "
     "pursuing certification can see which of its obligations the system already "
     "supports and which remain its own. Certification is granted to an organization "
     "by an accredited body; a mapping is evidence toward it, not a substitute."),
    ("Does a vendor SOC 2 report cover any of this?",
     "No. A SOC 2 report describes the vendor's own control environment. It does not "
     "state where your data is processed, what an agent may write in your systems, or "
     "what your auditors can reconstruct afterward. Those are properties of the "
     "deployed architecture, which is what this page documents."),
    ("How can these control claims be verified rather than taken on trust?",
     "Each control below states how to check it. Most are verifiable from inside a "
     "deployment in minutes: capture packets from a sandbox, compare compiled tool "
     "manifests across two roles, revoke a user and watch access drop, or open a "
     "citation and follow it to the logged call that produced it."),
    ("Which NIST AI RMF functions do these controls map to?",
     "All four. GOVERN is served by identity federation, per-turn tool compilation and "
     "the human write gate; MAP by plane separation and tokenization policy; MEASURE by "
     "the grounding critic, citation provenance and distributed tracing; MANAGE by "
     "execution isolation, egress denial, policy validation and replay protection."),
]


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def esc(s):
    return s.replace('"', '\\"')


def bi(en, es):
    """One bilingual pair, split later by make-i18n."""
    return ('<span data-lang-en>%s</span><span data-lang-es>%s</span>' % (en, es))


def tags(items, cls):
    if not items:
        return '<span class="text-ax-ink/25">&mdash;</span>'
    return " ".join(
        '<span class="%s">%s</span>' % (cls, i) for i in items)


def matrix_rows():
    out = []
    for c in CONTROLS:
        out.append(
            '            <tr class="border-b border-ax-ink/[0.07]">\n'
            '              <td class="py-3 pr-4 align-top">\n'
            '                <a href="#%s" class="font-semibold hover:text-ax-blue transition-colors">%s</a>\n'
            '              </td>\n'
            '              <td class="py-3 pr-4 align-top text-sm text-ax-ink/60">%s</td>\n'
            '              <td class="py-3 pr-4 align-top text-sm text-ax-ink/60">%s</td>\n'
            '              <td class="py-3 align-top text-sm text-ax-ink/60">%s</td>\n'
            '            </tr>'
            % (c["id"], bi(c["name_en"], c["name_es"]),
               ", ".join(c["rmf"]),
               "<br>".join(c["iso"]),
               "<br>".join(c["sp53"])))
    return "\n".join(out)


def control_cards():
    out = []
    for c in CONTROLS:
        owasp = ""
        if c["owasp"]:
            owasp = (
                '\n        <p class="text-sm text-ax-ink/55 mt-3">%s %s</p>'
                % (bi("<strong>OWASP LLM Top 10:</strong>",
                      "<strong>OWASP LLM Top 10:</strong>"),
                   ", ".join(c["owasp"])))
        out.append(
            '      <div id="%s" class="rounded-2xl border border-ax-ink/10 bg-white p-6 lg:p-7 scroll-mt-28">\n'
            '        <h3 class="font-heading font-bold text-lg mb-3">%s</h3>\n'
            '        <p class="text-ax-ink/70 leading-relaxed mb-4">%s</p>\n'
            '        <div class="grid sm:grid-cols-2 gap-4 text-sm">\n'
            '          <div>\n'
            '            <p class="ax-label text-ax-ink/40 mb-1.5">%s</p>\n'
            '            <p class="text-ax-ink/65">%s</p>\n'
            '          </div>\n'
            '          <div>\n'
            '            <p class="ax-label text-ax-ink/40 mb-1.5">%s</p>\n'
            '            <p class="text-ax-ink/65">%s</p>\n'
            '          </div>\n'
            '        </div>%s\n'
            '        <p class="text-sm mt-4 pt-4 border-t border-ax-ink/[0.07]">\n'
            '          <span class="ax-label text-ax-ink/40">%s</span>\n'
            '          <a href="%s" class="text-ax-blue hover:underline ml-2">%s</a>\n'
            '        </p>\n'
            '      </div>'
            % (c["id"],
               bi(c["name_en"], c["name_es"]),
               bi(c["stmt_en"], c["stmt_es"]),
               bi("Frameworks", "Marcos"),
               ", ".join(c["rmf"]) + " &middot; " + "; ".join(c["iso"]),
               bi("How to verify it", "Cómo verificarlo"),
               bi(c["check_en"], c["check_es"]),
               owasp,
               bi("Documented in", "Documentado en"),
               c["evidence"],
               bi("Architecture teardown", "Desglose de arquitectura")))
    return "\n".join(out)


BODY = u"""
<!-- ==========================================================================
     GOVERNANCE CONTROL MAPPING — generated by _build/scripts/make-controls.py
     ========================================================================== -->
<section class="ax-hero ax-noise relative pt-36 pb-16 lg:pt-44 lg:pb-20 overflow-hidden">
  <div class="ax-grid-bg"></div>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative">

    <nav class="flex items-center gap-2 text-xs font-semibold text-white/35 mb-8" aria-label="Breadcrumb">
      <a href="index.html" class="hover:text-ax-cyan transition-colors">{home}</a>
      <span>/</span>
      <a href="enterprise-ai-security.html" class="hover:text-ax-cyan transition-colors">{sec}</a>
      <span>/</span>
      <span class="text-white/60">{crumb}</span>
    </nav>

    <h1 class="font-heading font-extrabold text-4xl lg:text-5xl text-white leading-[1.05] tracking-tight mb-6">
      {h1}
    </h1>
    <p class="text-lg text-white/60 leading-relaxed max-w-3xl">
      {lede}
    </p>
  </div>
</section>

<section class="py-16 lg:py-20 bg-white">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="ax-prose mb-12">
      <p>{intro}</p>
      <p>{limits}</p>
    </div>

    <div class="overflow-x-auto ax-scroll-dark mb-14">
      <table class="w-full text-left border-collapse min-w-[44rem]">
        <thead>
          <tr class="border-b-2 border-ax-ink/15">
            <th class="py-2.5 pr-4 ax-label text-ax-ink/45">{th_control}</th>
            <th class="py-2.5 pr-4 ax-label text-ax-ink/45">NIST AI RMF</th>
            <th class="py-2.5 pr-4 ax-label text-ax-ink/45">ISO/IEC 42001</th>
            <th class="py-2.5 ax-label text-ax-ink/45">NIST SP 800-53</th>
          </tr>
        </thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </div>

    <h2 class="font-heading font-extrabold text-2xl lg:text-3xl mb-7">{h2_controls}</h2>
    <div class="space-y-4 mb-16">
{cards}
    </div>

    <h2 class="font-heading font-extrabold text-2xl lg:text-3xl mb-7">{h2_faq}</h2>
    <div class="space-y-4 mb-14">
{faqs}
    </div>

    <aside class="rounded-2xl border border-ax-ink/10 bg-ax-mist p-7">
      <p class="ax-label text-ax-ink/40 mb-3">{ref_label}</p>
      <ol class="space-y-2.5 text-sm">
        <li class="flex gap-3">
          <span class="font-mono text-2xs text-ax-ink/35 pt-1 shrink-0">01</span>
          <span><a href="https://www.iso.org/standard/42001" target="_blank" rel="noopener noreferrer" class="text-ax-blue hover:underline">ISO/IEC 42001:2023 &mdash; AI management systems</a><span class="text-ax-ink/45"> &mdash; ISO/IEC</span></span>
        </li>
        <li class="flex gap-3">
          <span class="font-mono text-2xs text-ax-ink/35 pt-1 shrink-0">02</span>
          <span><a href="https://www.nist.gov/itl/ai-risk-management-framework" target="_blank" rel="noopener noreferrer" class="text-ax-blue hover:underline">AI Risk Management Framework (AI RMF 1.0)</a><span class="text-ax-ink/45"> &mdash; NIST</span></span>
        </li>
        <li class="flex gap-3">
          <span class="font-mono text-2xs text-ax-ink/35 pt-1 shrink-0">03</span>
          <span><a href="https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final" target="_blank" rel="noopener noreferrer" class="text-ax-blue hover:underline">SP 800-53 Rev. 5 &mdash; Security and Privacy Controls</a><span class="text-ax-ink/45"> &mdash; NIST</span></span>
        </li>
        <li class="flex gap-3">
          <span class="font-mono text-2xs text-ax-ink/35 pt-1 shrink-0">04</span>
          <span><a href="https://csrc.nist.gov/pubs/sp/800/207/final" target="_blank" rel="noopener noreferrer" class="text-ax-blue hover:underline">SP 800-207 &mdash; Zero Trust Architecture</a><span class="text-ax-ink/45"> &mdash; NIST</span></span>
        </li>
        <li class="flex gap-3">
          <span class="font-mono text-2xs text-ax-ink/35 pt-1 shrink-0">05</span>
          <span><a href="https://owasp.org/www-project-top-10-for-large-language-model-applications/" target="_blank" rel="noopener noreferrer" class="text-ax-blue hover:underline">Top 10 for Large Language Model Applications</a><span class="text-ax-ink/45"> &mdash; OWASP</span></span>
        </li>
      </ol>
    </aside>
  </div>
</section>
"""


def faq_cards():
    out = []
    for q, a in FAQS:
        out.append(
            '      <div class="rounded-2xl border border-ax-ink/10 bg-white p-6">\n'
            '        <h3 class="font-heading font-bold mb-2.5">%s</h3>\n'
            '        <p class="text-ax-ink/70 leading-relaxed text-sm">%s</p>\n'
            '      </div>' % (q, a))
    return "\n".join(out)


def meta():
    faq_json = ",\n".join(
        '      {\n'
        '        "@type": "Question",\n'
        '        "name": "%s",\n'
        '        "acceptedAnswer": { "@type": "Answer", "text": "%s" }\n'
        '      }' % (esc(q), esc(a)) for q, a in FAQS)

    about = ",\n".join(
        '      { "@type": "Thing", "name": "%s", "sameAs": "%s" }' % (n, u)
        for n, u in [
            ("ISO/IEC 42001 AI management systems", "https://www.iso.org/standard/42001"),
            ("NIST AI Risk Management Framework", "https://www.nist.gov/itl/ai-risk-management-framework"),
            ("NIST SP 800-207 Zero Trust Architecture", "https://csrc.nist.gov/pubs/sp/800/207/final"),
            ("OWASP Top 10 for Large Language Model Applications",
             "https://owasp.org/www-project-top-10-for-large-language-model-applications/"),
        ])

    return u"""
  <title>AI Governance Control Mapping | ISO/IEC 42001 and NIST AI RMF | Axionalytics</title>
  <meta name="description" content="Twelve controls the platform operates, mapped to the ISO/IEC 42001 areas, NIST AI RMF functions, and SP 800-53 families each one speaks to — with how to verify every claim from inside a deployment.">
  <link rel="canonical" href="%(base)s/%(slug)s.html">
  <meta property="og:title" content="AI Governance Control Mapping | Axionalytics">
  <meta property="og:description" content="Every control mapped to the requirement it satisfies, and how to check it yourself. Not a certification claim.">
  <meta property="og:url" content="%(base)s/%(slug)s.html">

  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "TechArticle",
    "@id": "%(base)s/%(slug)s.html#article",
    "headline": "AI Governance Control Mapping",
    "description": "Controls the Axionalytics platform operates, mapped to ISO/IEC 42001 areas, NIST AI RMF functions and NIST SP 800-53 families, each with a stated verification method.",
    "inLanguage": ["en", "es"],
    "mainEntityOfPage": { "@type": "WebPage", "@id": "%(base)s/%(slug)s.html" },
    "author": { "@type": "Organization", "name": "Axionalytics", "url": "%(base)s/" },
    "publisher": {
      "@type": "Organization",
      "name": "Axionalytics",
      "url": "%(base)s/",
      "logo": { "@type": "ImageObject", "url": "%(base)s/assets/favicon-512.png" }
    },
    "about": [
%(about)s
    ],
    "citation": [
      { "@type": "CreativeWork", "name": "ISO/IEC 42001:2023 — AI management systems", "url": "https://www.iso.org/standard/42001", "publisher": { "@type": "Organization", "name": "ISO/IEC" } },
      { "@type": "CreativeWork", "name": "AI Risk Management Framework (AI RMF 1.0)", "url": "https://www.nist.gov/itl/ai-risk-management-framework", "publisher": { "@type": "Organization", "name": "NIST" } },
      { "@type": "CreativeWork", "name": "SP 800-53 Rev. 5: Security and Privacy Controls", "url": "https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final", "publisher": { "@type": "Organization", "name": "NIST" } },
      { "@type": "CreativeWork", "name": "SP 800-207: Zero Trust Architecture", "url": "https://csrc.nist.gov/pubs/sp/800/207/final", "publisher": { "@type": "Organization", "name": "NIST" } },
      { "@type": "CreativeWork", "name": "OWASP Top 10 for Large Language Model Applications", "url": "https://owasp.org/www-project-top-10-for-large-language-model-applications/", "publisher": { "@type": "Organization", "name": "OWASP" } }
    ]
  }
  </script>

  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
%(faq)s
    ]
  }
  </script>
""" % {"base": BASE, "slug": SLUG, "faq": faq_json, "about": about}


def main():
    body = BODY.format(
        home=bi("Home", "Inicio"),
        sec=bi("Zero-Trust AI Governance", "Gobernanza de IA de Confianza Cero"),
        crumb=bi("Control mapping", "Mapeo de controles"),
        h1=bi("Every control, against the requirement it answers",
              "Cada control, frente al requisito que responde"),
        lede=bi("Twelve controls this platform operates, mapped to the ISO/IEC 42001 areas, "
                "NIST AI RMF functions and SP 800-53 families each one speaks to. Every row "
                "states how to verify it from inside a deployment.",
                "Doce controles que opera esta plataforma, mapeados a las áreas de ISO/IEC 42001, "
                "las funciones del NIST AI RMF y las familias de SP 800-53 que corresponden. "
                "Cada fila indica cómo verificarlo desde dentro de un despliegue."),
        intro=bi("A security review asks its questions in the vocabulary of the frameworks it "
                 "is accountable to. The architecture already answers them; this page is the "
                 "translation. Each control below is documented in an architecture teardown, "
                 "and each states a check you can run yourself rather than a claim you have to "
                 "accept.",
                 "Una revisión de seguridad formula sus preguntas en el vocabulario de los marcos "
                 "ante los que responde. La arquitectura ya las contesta; esta página es la "
                 "traducción. Cada control está documentado en un desglose de arquitectura, y "
                 "cada uno indica una verificación que usted mismo puede ejecutar en lugar de "
                 "una afirmación que deba aceptar."),
        limits=bi("<strong>What this is not.</strong> It is not a certification claim. ISO/IEC 42001 "
                  "is a paywalled standard, so its Annex A areas are mapped by name and sub-clause "
                  "identifiers are deliberately not asserted — false precision would defeat the "
                  "purpose of the page. NIST AI RMF is mapped to its four Core functions and "
                  "SP 800-53 to control families. An organization pursuing certification can use "
                  "this to see which of its obligations the system supports and which remain its own.",
                  "<strong>Lo que esto no es.</strong> No es una afirmación de certificación. ISO/IEC 42001 "
                  "es una norma de pago, así que sus áreas del Anexo A se mapean por nombre y los "
                  "identificadores de subcláusula no se afirman deliberadamente: una precisión falsa "
                  "anularía el propósito de la página. El NIST AI RMF se mapea a sus cuatro funciones "
                  "y SP 800-53 a familias de controles. Una organización que busque certificarse puede "
                  "usar esto para ver qué obligaciones soporta el sistema y cuáles siguen siendo suyas."),
        th_control=bi("Control", "Control"),
        h2_controls=bi("The controls", "Los controles"),
        h2_faq=bi("What reviewers ask", "Lo que preguntan los revisores"),
        ref_label=bi("References", "Referencias"),
        rows=matrix_rows(),
        cards=control_cards(),
        faqs=faq_cards(),
    )

    io.open(os.path.join(OUT, SLUG + ".body.html"), "w", encoding="utf-8").write(body)
    io.open(os.path.join(OUT, SLUG + ".meta.html"), "w", encoding="utf-8").write(meta())

    print("  %s  %d controls, %d FAQ, %d frameworks"
          % (SLUG, len(CONTROLS), len(FAQS), 4))


if __name__ == "__main__":
    main()
